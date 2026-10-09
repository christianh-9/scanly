"""Run: .venv/bin/python test_main.py  (fakes Gemini, so no API quota is used)"""
import json
import os
from types import SimpleNamespace

os.environ.setdefault("GEMINI_API_KEY", "test")
os.environ.setdefault("ALLOWED_ORIGINS", "https://scanly.example/, https://other.example")
from fastapi.testclient import TestClient

import main

section = {"score": 80, "tips": [{"type": "good", "tip": "t", "explanation": "e"}]}
good = {
    "overallScore": 75,
    "ATS": {"score": 70, "tips": [{"type": "improve", "tip": "t"}]},
    "toneAndStyle": section, "content": section, "structure": section, "skills": section,
}


def fake_ai(text):
    async def generate_content(**_):
        return SimpleNamespace(text=text)
    main.client = SimpleNamespace(aio=SimpleNamespace(models=SimpleNamespace(generate_content=generate_content)))


api = TestClient(main.app)
pdf = {"resume": ("r.pdf", b"%PDF-1.4", "application/pdf")}

fake_ai(json.dumps(good))
r = api.post("/api/analyze", files=pdf, data={"jobTitle": "Dev"})
assert r.status_code == 200 and r.json()["overallScore"] == 75, r.text

assert api.post("/api/analyze", files={"resume": ("r.txt", b"hi", "text/plain")}).status_code == 400

fake_ai('{"overallScore": "not json schema"}')
assert api.post("/api/analyze", files=pdf).status_code == 502

# overloaded primary model falls back to the next one
from google.genai import errors
calls = []
async def flaky(model, **_):
    calls.append(model)
    if len(calls) == 1:
        raise errors.ServerError(503, {"error": {"code": 503, "message": "busy", "status": "UNAVAILABLE"}})
    return SimpleNamespace(text=json.dumps(good))
main.client = SimpleNamespace(aio=SimpleNamespace(models=SimpleNamespace(generate_content=flaky)))
assert api.post("/api/analyze", files=pdf).status_code == 200 and calls == main.MODELS, calls

# every model overloaded -> friendly 503
async def busy(**_):
    raise errors.ServerError(503, {"error": {"code": 503, "message": "busy", "status": "UNAVAILABLE"}})
main.client = SimpleNamespace(aio=SimpleNamespace(models=SimpleNamespace(generate_content=busy)))
r = api.post("/api/analyze", files=pdf)
assert r.status_code == 503 and "overloaded" in r.json()["detail"], r.text

# health check for waking the server
assert api.get("/api/health").json() == {"ok": True}

# CORS: listed origins allowed (trailing slash tolerated), others not
pre = lambda origin: api.options("/api/analyze", headers={"Origin": origin, "Access-Control-Request-Method": "POST"})
assert pre("https://scanly.example").headers.get("access-control-allow-origin") == "https://scanly.example"
assert pre("https://other.example").headers.get("access-control-allow-origin") == "https://other.example"
assert "access-control-allow-origin" not in pre("https://evil.example").headers

print("ok")
