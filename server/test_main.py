"""Run from server/: .venv/bin/pytest  (Gemini is faked, so no API quota is used)"""
import json
import os
from types import SimpleNamespace

import pytest

os.environ.setdefault("GEMINI_API_KEY", "test")
os.environ.setdefault("ALLOWED_ORIGINS", "https://scanly.example/, https://other.example")
from fastapi.testclient import TestClient
from google.genai import errors

import main

SECTION = {"score": 80, "tips": [{"type": "good", "tip": "t", "explanation": "e"}]}
GOOD = {
    "overallScore": 75,
    "ATS": {"score": 70, "tips": [{"type": "improve", "tip": "t"}]},
    "toneAndStyle": SECTION, "content": SECTION, "structure": SECTION, "skills": SECTION,
}
PDF = {"resume": ("r.pdf", b"%PDF-1.4", "application/pdf")}
BUSY = errors.ServerError(503, {"error": {"code": 503, "message": "busy", "status": "UNAVAILABLE"}})

api = TestClient(main.app)


@pytest.fixture
def fake_gemini(monkeypatch):
    """Replace the Gemini client. Call it with an async function that stands in for generate_content."""
    def install(generate_content):
        fake = SimpleNamespace(aio=SimpleNamespace(models=SimpleNamespace(generate_content=generate_content)))
        monkeypatch.setattr(main, "client", fake)
    return install


def replies(text):
    async def generate_content(**_):
        return SimpleNamespace(text=text)
    return generate_content


def test_valid_analysis(fake_gemini):
    fake_gemini(replies(json.dumps(GOOD)))
    r = api.post("/api/analyze", files=PDF, data={"jobTitle": "Dev"})
    assert r.status_code == 200, r.text
    # overall comes from the first call's holistic judgement (GOOD says 75), not the section average (78)
    assert r.json()["overallScore"] == 75


def test_server_timing_header(fake_gemini):
    fake_gemini(replies(json.dumps(GOOD)))
    timing = api.post("/api/analyze", files=PDF).headers["server-timing"]
    for step in ("validate;dur=", "gemini;dur=", "parse;dur="):
        assert step in timing, timing
    assert f'model;desc="{main.MODELS[0]}"' in timing


def test_rejects_non_pdf():
    r = api.post("/api/analyze", files={"resume": ("r.txt", b"hi", "text/plain")})
    assert r.status_code == 400


def test_malformed_ai_output_is_502(fake_gemini):
    fake_gemini(replies('{"overallScore": "not json schema"}'))
    assert api.post("/api/analyze", files=PDF).status_code == 502


def test_falls_back_when_primary_model_busy(fake_gemini):
    calls = []

    async def flaky(model, **_):
        calls.append(model)
        if len(calls) == 1:
            raise BUSY
        return SimpleNamespace(text=json.dumps(GOOD))

    fake_gemini(flaky)
    r = api.post("/api/analyze", files=PDF)
    assert r.status_code == 200
    # one group hit the busy error and retried on the fallback model; the other answered first time
    assert calls.count(main.MODELS[1]) == 1
    timing = r.headers["server-timing"]
    assert main.MODELS[1] in timing.split('model;desc="')[1].split('"')[0]
    assert f'fallback;desc="{main.MODELS[0]}:503"' in timing


def test_no_fallback_entry_when_primary_answers(fake_gemini):
    fake_gemini(replies(json.dumps(GOOD)))
    assert "fallback" not in api.post("/api/analyze", files=PDF).headers["server-timing"]


def test_pinned_single_model_busy_is_503_not_silent_fallback(fake_gemini, monkeypatch):
    # GEMINI_MODELS="gemini-flash-latest" for benchmarking: a busy Flash must fail, not quietly switch to Lite
    monkeypatch.setattr(main, "MODELS", ["gemini-flash-latest"])
    calls = []

    async def busy(model, **_):
        calls.append(model)
        raise BUSY

    fake_gemini(busy)
    assert api.post("/api/analyze", files=PDF).status_code == 503
    assert calls == ["gemini-flash-latest"] * len(main.GROUPS)  # each group tried Flash once, none fell back


def test_all_models_busy_is_friendly_503(fake_gemini):
    async def busy(**_):
        raise BUSY

    fake_gemini(busy)
    r = api.post("/api/analyze", files=PDF)
    assert r.status_code == 503
    assert "overloaded" in r.json()["detail"]


def test_health():
    assert api.get("/api/health").json() == {"ok": True}


@pytest.mark.parametrize("origin, allowed", [
    ("https://scanly.example", True),   # listed with a trailing slash in the env var
    ("https://other.example", True),
    ("https://evil.example", False),
])
def test_cors(origin, allowed):
    r = api.options("/api/analyze", headers={"Origin": origin, "Access-Control-Request-Method": "POST"})
    assert (r.headers.get("access-control-allow-origin") == origin) is allowed


# --- Phase 1: text extraction -------------------------------------------------

def make_pdf(*pages: str) -> bytes:
    """Build a real PDF in memory; an empty string makes a page with no text (like a scanned image)."""
    import pymupdf
    doc = pymupdf.open()
    for text in pages:
        page = doc.new_page()
        if text:
            page.insert_textbox(pymupdf.Rect(72, 72, 540, 720), text)  # wraps long text instead of clipping it
    return doc.tobytes()


def test_extract_text_single_page():
    assert main.extract_text(make_pdf("Jane Doe, Software Engineer")) == "Jane Doe, Software Engineer"


def test_extract_text_keeps_pages_apart():
    text = main.extract_text(make_pdf("Page one ends here", "Page two starts here"))
    assert "Page one ends here" in text and "Page two starts here" in text
    assert "herePage" not in text  # pages must not run together


def test_extract_text_no_text_layer_returns_empty():
    assert main.extract_text(make_pdf("")) == ""


def test_extract_text_corrupt_pdf_raises():
    with pytest.raises(Exception):
        main.extract_text(b"%PDF-1.4 this is not really a pdf")


def capture(monkeypatch_target):
    """Fake Gemini that records what it was sent and replies with valid feedback."""
    sent = {}

    async def generate_content(contents, **_):
        sent["contents"] = contents
        return SimpleNamespace(text=json.dumps(GOOD))

    monkeypatch_target(generate_content)
    return sent


RESUME = "Jane Doe. Software Engineer at Acme building React and Python services. " * 5  # > MIN_TEXT_CHARS


def test_text_resume_sends_text_not_pdf(fake_gemini):
    sent = capture(fake_gemini)
    r = api.post("/api/analyze", files={"resume": ("r.pdf", make_pdf(RESUME), "application/pdf")})
    assert r.status_code == 200
    first = sent["contents"][0]
    assert isinstance(first, str) and "Jane Doe" in first
    assert 'input;desc="text"' in r.headers["server-timing"]
    assert "extract;dur=" in r.headers["server-timing"]


def test_scanned_resume_falls_back_to_pdf(fake_gemini):
    sent = capture(fake_gemini)
    r = api.post("/api/analyze", files={"resume": ("r.pdf", make_pdf(""), "application/pdf")})
    assert r.status_code == 200
    assert not isinstance(sent["contents"][0], str)  # a PDF Part, not text
    assert 'input;desc="pdf"' in r.headers["server-timing"]


def test_unreadable_pdf_falls_back_to_pdf(fake_gemini):
    sent = capture(fake_gemini)
    r = api.post("/api/analyze", files=PDF)  # b"%PDF-1.4": not a real PDF
    assert r.status_code == 200
    assert not isinstance(sent["contents"][0], str)


def test_resume_input_pdf_forces_pdf(fake_gemini, monkeypatch):
    monkeypatch.setattr(main, "RESUME_INPUT", "pdf")
    sent = capture(fake_gemini)
    r = api.post("/api/analyze", files={"resume": ("r.pdf", make_pdf(RESUME), "application/pdf")})
    assert r.status_code == 200
    assert not isinstance(sent["contents"][0], str)


def test_token_counts_in_header(fake_gemini):
    async def with_usage(**_):
        usage = SimpleNamespace(prompt_token_count=900, candidates_token_count=700, thoughts_token_count=1200)
        return SimpleNamespace(text=json.dumps(GOOD), usage_metadata=usage)

    fake_gemini(with_usage)
    # summed across the parallel calls
    n = len(main.GROUPS)
    assert (f'tokens;desc="in={900 * n} out={700 * n} think={1200 * n} calls={n}"'
            in api.post("/api/analyze", files=PDF).headers["server-timing"])


# --- Phase 3: parallel calls --------------------------------------------------

def test_groups_cover_every_section_exactly_once():
    flat = [k for g in main.GROUPS for k in g]
    assert sorted(flat) == sorted(["ATS", "toneAndStyle", "content", "structure", "skills"])


def test_each_call_asks_only_for_its_group(fake_gemini):
    asked = []

    async def record(config, **_):
        asked.append(sorted(config.response_json_schema["properties"]))
        return SimpleNamespace(text=json.dumps(GOOD))

    fake_gemini(record)
    assert api.post("/api/analyze", files=PDF).status_code == 200
    expected = [sorted(["overallScore", *main.GROUPS[0]])] + [sorted(g) for g in main.GROUPS[1:]]
    assert sorted(asked) == sorted(expected)


def test_calls_run_in_parallel(fake_gemini):
    """Each fake call waits until every group's call has started. Run one after another, the first call
    would wait forever (the test times out instead); run in parallel, they all start and finish."""
    import asyncio
    started, everyone_started = 0, asyncio.Event()

    async def wait_for_others(**_):
        nonlocal started
        started += 1
        if started == len(main.GROUPS):
            everyone_started.set()
        await asyncio.wait_for(everyone_started.wait(), timeout=2)
        return SimpleNamespace(text=json.dumps(GOOD))

    fake_gemini(wait_for_others)
    assert api.post("/api/analyze", files=PDF).status_code == 200
    assert started == len(main.GROUPS)


def test_one_group_failing_fails_the_whole_request_clearly(fake_gemini):
    # the group that includes "structure" is always busy; the other succeeds. The response must be a clear
    # 503, never a 200 with sections missing.
    async def structure_busy(config, **_):
        if "structure" in config.response_json_schema["properties"]:
            raise BUSY
        return SimpleNamespace(text=json.dumps(GOOD))

    fake_gemini(structure_busy)
    r = api.post("/api/analyze", files=PDF)
    assert r.status_code == 503
    assert "overloaded" in r.json()["detail"]


def test_one_group_bad_json_is_502(fake_gemini):
    async def half_garbage(config, **_):
        if "skills" in config.response_json_schema["properties"]:
            return SimpleNamespace(text="not json")
        return SimpleNamespace(text=json.dumps(GOOD))

    fake_gemini(half_garbage)
    assert api.post("/api/analyze", files=PDF).status_code == 502


def test_overall_falls_back_to_average_when_missing(fake_gemini):
    no_overall = {k: v for k, v in GOOD.items() if k != "overallScore"}
    assert main.combine(no_overall).overallScore == 78  # (70 + 80 * 4) / 5
