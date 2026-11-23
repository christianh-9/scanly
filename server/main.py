import asyncio
import hashlib
import json
import logging
import os
import statistics
import time
from dataclasses import dataclass
from typing import Any, Literal

import pymupdf
import redis.asyncio as aioredis
from dotenv import load_dotenv
from fastapi import FastAPI, Form, HTTPException, Response, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from google import genai
from google.genai import errors, types
from pydantic import BaseModel, Field, ValidationError

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger("scanly")

MAX_PDF_BYTES = 20 * 1024 * 1024  # same limit as the uploader

# Lite first: faster and a much bigger free quota. Override with GEMINI_MODELS.
MODELS = [m.strip() for m in os.environ.get("GEMINI_MODELS", "gemini-flash-lite-latest,gemini-flash-latest").split(",") if m.strip()]
BUSY_CODES = {429, 500, 503}
FALLBACK_CODES = BUSY_CODES | {404}  # 404 = model name gone, try the next one

# Overloads usually pass quickly, so retry once. Don't retry 429s, the quota won't come back in a second.
RETRIES = 1
RETRY_CODES = {500, 503}
RETRY_DELAY = 1.0

# Users can't fix key/billing problems, so keep the message vague and log the real error.
UNAVAILABLE = "Analysis is temporarily unavailable. Please try again later."
BAD_FILE = "Couldn't analyze this file. Export your resume as a PDF again and retry."


def friendly_error(e: Exception) -> HTTPException:
    code = getattr(e, "code", None)
    log.error(f"gemini error code={code}: {getattr(e, 'message', None) or e}")
    if code == 400:
        return HTTPException(422, BAD_FILE)
    return HTTPException(503, UNAVAILABLE)


RESUME_INPUT = os.environ.get("RESUME_INPUT", "auto")  # "pdf" skips text extraction
MIN_TEXT_CHARS = 200  # below this it's probably a scanned PDF

# -latest aliases only exist on v1beta
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"], http_options=types.HttpOptions(api_version="v1beta"))

# Optional. Short timeouts so a dead Redis doesn't hold up requests.
REDIS_URL = os.environ.get("REDIS_URL", "")
CACHE_TTL = 7 * 24 * 3600
CACHE_VERSION = "v1"  # bump when the prompt or models change
cache = aioredis.from_url(REDIS_URL, socket_timeout=0.5, socket_connect_timeout=0.5) if REDIS_URL else None
app = FastAPI(title="Scanly API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip().rstrip("/") for o in os.environ.get("ALLOWED_ORIGINS", "").split(",") if o.strip()],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


# Pinged to wake the server. HEAD is for uptime monitors.
# Also pings Redis so Upstash doesn't archive it for inactivity (free DBs go after 14 idle days).
@app.api_route("/api/health", methods=["GET", "HEAD"])
async def health() -> dict:
    if cache is not None:
        try:
            await cache.ping()
        except Exception as e:
            log.info(f"redis ping failed: {e}")
    return {"ok": True}


class AtsTip(BaseModel):
    type: Literal["good", "improve"]
    tip: str


class Tip(AtsTip):
    explanation: str


class AtsSection(BaseModel):
    score: int = Field(ge=0, le=100)
    tips: list[AtsTip]


class Section(BaseModel):
    score: int = Field(ge=0, le=100)
    tips: list[Tip]


class Feedback(BaseModel):
    """Same shape as Feedback in types/index.d.ts."""

    overallScore: int = Field(ge=0, le=100)
    ATS: AtsSection
    toneAndStyle: Section
    content: Section
    structure: Section
    skills: Section


def build_prompt(job_title: str, job_description: str) -> str:
    # Short output = faster response
    return f"""You are an expert in ATS (Applicant Tracking System) and resume analysis.
Analyze and rate this resume and suggest how to improve it.
The rating can be low if the resume is bad. Point out the most important mistakes.
Give exactly 3 tips per section. "tip" is a short title of at most 8 words.
"explanation" is one sentence of at most 20 words.
Return compact JSON on a single line, with no indentation or line breaks.
If provided, take the job into consideration.
Job title: {job_title or "(not provided)"}
Job description: {job_description or "(not provided)"}"""


def extract_text(pdf: bytes) -> str:
    """All the text in the PDF, or "" for a scanned one."""
    with pymupdf.open(stream=pdf, filetype="pdf") as doc:
        return "\n".join(page.get_text() for page in doc).strip()


# One Gemini call per group, run in parallel. More groups = faster but more API calls.
# The first group also returns overallScore (an average was too generous on weak resumes).
GROUPS = [["ATS", "toneAndStyle", "content"], ["structure", "skills"]]


@dataclass
class GroupResult:
    sections: dict[str, Any]
    model: str
    skipped: list[str]
    usage: Any
    seconds: float
    retries: int = 0


def group_schema(fields: list[str]) -> dict:
    full = Feedback.model_json_schema()
    return {**full, "properties": {k: full["properties"][k] for k in fields}, "required": list(fields)}


async def score_group(group: list[str], resume_part: Any, prompt: str, with_overall: bool = False) -> GroupResult:
    """Try each model until one answers. Raises HTTPException if none do."""
    start = time.perf_counter()
    skipped: list[str] = []
    fields = ["overallScore", *group] if with_overall else group
    ask = f"{prompt}\nOnly return these sections: {', '.join(group)}."
    if with_overall:
        ask += " Also return overallScore: your overall judgement of the whole resume for this job, not an average."
    retries = 0
    for model in MODELS:
        for attempt in range(1 + RETRIES):
            try:
                result = await client.aio.models.generate_content(
                    model=model,
                    contents=[resume_part, ask],
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_json_schema=group_schema(fields),
                    ),
                )
            except errors.APIError as e:
                if e.code not in FALLBACK_CODES:
                    raise friendly_error(e)
                if attempt < RETRIES and e.code in RETRY_CODES:
                    retries += 1
                    await asyncio.sleep(RETRY_DELAY)
                    continue
                skipped.append(f"{model}:{e.code}")
                break
            except Exception as e:
                raise friendly_error(e)
            try:
                data = json.loads(result.text or "")
            except json.JSONDecodeError:
                raise HTTPException(502, "AI returned feedback in an unexpected format, please try again")
            if not isinstance(data, dict):
                raise HTTPException(502, "AI returned feedback in an unexpected format, please try again")
            sections = {k: data.get(k) for k in fields}
            return GroupResult(sections, model, skipped, getattr(result, "usage_metadata", None),
                               time.perf_counter() - start, retries)
    log.info(f"group {'+'.join(group)} failed: all models busy ({', '.join(skipped)})")
    raise HTTPException(503, "Gemini is overloaded right now. Wait a minute and try again.")


def combine(sections: dict[str, Any]) -> Feedback:
    """Merge the groups into one Feedback. Falls back to the average if overallScore is missing."""
    sections = dict(sections)
    overall = sections.pop("overallScore", None)
    parsed = {k: Feedback.model_fields[k].annotation.model_validate(v) for k, v in sections.items()}
    if overall is None:
        overall = round(statistics.mean(section.score for section in parsed.values()))
    return Feedback(overallScore=overall, **parsed)


def cache_key(resume: str | bytes, job_title: str, job_description: str) -> str:
    # Uses the text when we have it, so a re-exported copy of the same resume still hits
    h = hashlib.sha256()
    for part in (CACHE_VERSION, ",".join(MODELS), ",".join("+".join(g) for g in GROUPS),
                 job_title.strip(), job_description.strip()):
        h.update(part.encode())
        h.update(b"\0")
    h.update(resume.encode() if isinstance(resume, str) else resume)
    return f"scanly:review:{h.hexdigest()}"


async def cache_get(key: str) -> Feedback | None:
    # Any Redis problem counts as a miss
    if cache is None:
        return None
    try:
        raw = await cache.get(key)
    except Exception as e:
        log.info(f"cache get failed, continuing uncached: {e}")
        return None
    if raw is None:
        return None
    try:
        return Feedback.model_validate_json(raw)
    except ValidationError:
        return None


async def cache_set(key: str, feedback: Feedback) -> None:
    if cache is None:
        return
    try:
        await cache.set(key, feedback.model_dump_json(), ex=CACHE_TTL)
    except Exception as e:
        log.info(f"cache set failed: {e}")


@app.post("/api/analyze", response_model=Feedback)
async def analyze(
    response: Response,
    resume: UploadFile,
    jobTitle: str = Form(""),
    jobDescription: str = Form(""),
) -> Feedback:
    # time per step, for the log and the Server-Timing header
    timings: dict[str, float] = {}
    last = time.perf_counter()

    def lap(step: str) -> None:
        nonlocal last
        now = time.perf_counter()
        timings[step] = now - last
        last = now

    if resume.content_type != "application/pdf":
        raise HTTPException(400, "Resume must be a PDF")
    pdf = await resume.read()
    if len(pdf) > MAX_PDF_BYTES:
        raise HTTPException(413, "Resume must be 20 MB or smaller")
    lap("validate")

    text = ""
    if RESUME_INPUT != "pdf":
        try:
            text = extract_text(pdf)
        except Exception as e:  # let Gemini try the PDF instead
            log.info(f"text extraction failed, sending PDF: {e}")
    send_text = len(text) >= MIN_TEXT_CHARS
    resume_part = f"Resume text:\n{text}" if send_text else types.Part.from_bytes(data=pdf, mime_type="application/pdf")
    lap("extract")

    key = cache_key(text if send_text else pdf, jobTitle, jobDescription)
    cached = await cache_get(key)
    lap("cache")
    if cached is not None:
        total = sum(timings.values())
        log.info("analyze cache=hit " + " ".join(f"{k}={v:.3f}s" for k, v in timings.items()) + f" total={total:.3f}s")
        response.headers["Server-Timing"] = ", ".join(
            [f"{k};dur={v * 1000:.1f}" for k, v in timings.items()] + ['cache;desc="hit"'])
        return cached

    outcomes = await asyncio.gather(
        *(score_group(group, resume_part, build_prompt(jobTitle, jobDescription), with_overall=(i == 0))
          for i, group in enumerate(GROUPS)),
        return_exceptions=True,
    )
    failed = [o for o in outcomes if isinstance(o, BaseException)]
    if failed:
        log.info(f"analyze failed: {len(failed)}/{len(GROUPS)} parallel calls failed: {failed[0]}")
        first = failed[0]
        raise first if isinstance(first, HTTPException) else friendly_error(first)
    lap("gemini")

    try:
        feedback = combine({k: v for o in outcomes for k, v in o.sections.items()})
    except (ValidationError, TypeError, AttributeError):
        raise HTTPException(502, "AI returned feedback in an unexpected format, please try again")
    lap("parse")
    await cache_set(key, feedback)
    cache_status = "off" if cache is None else "miss"

    total = sum(timings.values())
    models = "|".join(dict.fromkeys(o.model for o in outcomes))
    fallback = "|".join(x for o in outcomes for x in o.skipped)  # not "," since that splits the header
    retries = sum(o.retries for o in outcomes)
    usages = [o.usage for o in outcomes if o.usage]
    tokens = (f"in={sum(u.prompt_token_count or 0 for u in usages)} out={sum(u.candidates_token_count or 0 for u in usages)} "
              f"think={sum(u.thoughts_token_count or 0 for u in usages)} calls={len(outcomes)}") if usages else ""
    log.info(
        "analyze " + " ".join(f"{k}={v:.3f}s" for k, v in timings.items())
        + f" total={total:.3f}s cache={cache_status} model={models} input={'text' if send_text else 'pdf'}"
        + " calls=[" + " ".join(f"{'+'.join(o.sections)}:{o.seconds:.2f}s" for o in outcomes) + "]"
        + (f" tokens[{tokens}]" if tokens else "")
        + (f" fallback={fallback}" if fallback else "")
        + (f" retries={retries}" if retries else "")
    )
    # shows up in DevTools > Network > Timing
    entries = [f"{k};dur={v * 1000:.1f}" for k, v in timings.items()]
    entries += [f"call{i + 1};dur={o.seconds * 1000:.1f};desc=\"{'+'.join(o.sections)}\"" for i, o in enumerate(outcomes)]
    entries += [f'model;desc="{models}"', f'input;desc="{"text" if send_text else "pdf"}"', f'cache;desc="{cache_status}"']
    if fallback:
        entries.append(f'fallback;desc="{fallback}"')
    if tokens:
        entries.append(f'tokens;desc="{tokens}"')
    if retries:
        entries.append(f'retries;desc="{retries}"')
    response.headers["Server-Timing"] = ", ".join(entries)
    return feedback
