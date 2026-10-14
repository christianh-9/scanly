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
    monkeypatch.setattr(main, "RETRY_DELAY", 0)  # don't actually wait between retries in tests

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


def test_falls_back_when_primary_model_stays_busy(fake_gemini):
    calls = []

    async def primary_down(model, **_):
        calls.append(model)
        if model == main.MODELS[0]:
            raise BUSY
        return SimpleNamespace(text=json.dumps(GOOD))

    fake_gemini(primary_down)
    r = api.post("/api/analyze", files=PDF)
    assert r.status_code == 200
    # each group: primary tried, retried once, then the fallback model answered
    n = len(main.GROUPS)
    assert calls.count(main.MODELS[0]) == n * (1 + main.RETRIES)
    assert calls.count(main.MODELS[1]) == n
    timing = r.headers["server-timing"]
    assert f'model;desc="{main.MODELS[1]}"' in timing
    assert f"{main.MODELS[0]}:503" in timing.split('fallback;desc="')[1]


def test_momentary_busy_is_retried_on_same_model(fake_gemini):
    calls = []

    async def busy_once(model, **_):
        calls.append(model)
        if len(calls) == 1:
            raise BUSY
        return SimpleNamespace(text=json.dumps(GOOD))

    fake_gemini(busy_once)
    r = api.post("/api/analyze", files=PDF)
    assert r.status_code == 200
    assert main.MODELS[1] not in calls  # recovered on the primary model, no fallback needed
    timing = r.headers["server-timing"]
    assert "fallback" not in timing
    assert 'retries;desc="1"' in timing


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
    # each group tried Flash, retried once, and never fell back to another model
    assert calls == ["gemini-flash-latest"] * (len(main.GROUPS) * (1 + main.RETRIES))


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


def test_quota_429_falls_back_immediately_without_retry(fake_gemini):
    quota = errors.ClientError(429, {"error": {"code": 429, "message": "quota", "status": "RESOURCE_EXHAUSTED"}})
    calls = []

    async def primary_out_of_quota(model, **_):
        calls.append(model)
        if model == main.MODELS[0]:
            raise quota
        return SimpleNamespace(text=json.dumps(GOOD))

    fake_gemini(primary_out_of_quota)
    r = api.post("/api/analyze", files=PDF)
    assert r.status_code == 200
    # one Flash attempt per group (no wasted retry), then straight to the fallback model
    assert calls.count(main.MODELS[0]) == len(main.GROUPS)
    assert "retries" not in r.headers["server-timing"]


# --- Phase 5: Redis cache -----------------------------------------------------

class FakeRedis:
    """Just enough of redis.asyncio for the cache: get/set with a TTL, optionally broken."""
    def __init__(self, broken=False):
        self.data, self.ttls, self.broken = {}, {}, broken

    async def get(self, key):
        if self.broken:
            raise ConnectionError("redis down")
        return self.data.get(key)

    async def set(self, key, value, ex=None):
        if self.broken:
            raise ConnectionError("redis down")
        self.data[key], self.ttls[key] = value, ex


def counting_gemini(fake_gemini):
    calls = []

    async def generate_content(**_):
        calls.append(1)
        return SimpleNamespace(text=json.dumps(GOOD))

    fake_gemini(generate_content)
    return calls


def analyze(job="Software Engineer"):
    return api.post("/api/analyze", files={"resume": ("r.pdf", make_pdf(RESUME), "application/pdf")},
                    data={"jobTitle": job})


def test_repeat_request_is_served_from_cache(fake_gemini, monkeypatch):
    redis = FakeRedis()
    monkeypatch.setattr(main, "cache", redis)
    calls = counting_gemini(fake_gemini)

    first = analyze()
    assert first.status_code == 200 and 'cache;desc="miss"' in first.headers["server-timing"]
    gemini_calls_after_first = len(calls)

    second = analyze()
    assert second.status_code == 200 and 'cache;desc="hit"' in second.headers["server-timing"]
    assert len(calls) == gemini_calls_after_first  # no Gemini call on a hit
    assert second.json() == first.json()  # same review, so the same resume always gets the same score
    assert list(redis.ttls.values()) == [main.CACHE_TTL]


def test_different_job_is_a_cache_miss(fake_gemini, monkeypatch):
    monkeypatch.setattr(main, "cache", FakeRedis())
    counting_gemini(fake_gemini)
    analyze("Software Engineer")
    assert 'cache;desc="miss"' in analyze("Data Analyst").headers["server-timing"]


def test_redis_down_fails_open(fake_gemini, monkeypatch):
    monkeypatch.setattr(main, "cache", FakeRedis(broken=True))
    counting_gemini(fake_gemini)
    r = analyze()
    assert r.status_code == 200  # still analyzed, just uncached


def test_no_redis_configured_reports_cache_off(fake_gemini):
    counting_gemini(fake_gemini)
    assert 'cache;desc="off"' in analyze().headers["server-timing"]


def test_cache_key_changes_with_version(monkeypatch):
    before = main.cache_key("resume text", "SWE", "")
    monkeypatch.setattr(main, "CACHE_VERSION", "v2")
    assert main.cache_key("resume text", "SWE", "") != before
