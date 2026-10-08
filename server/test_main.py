"""Run: .venv/bin/python test_main.py  (fakes Gemini, so no API quota is used)"""
import json
import os
from types import SimpleNamespace

os.environ.setdefault("GEMINI_API_KEY", "test")
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

print("ok")
