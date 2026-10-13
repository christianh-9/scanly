import asyncio
import json
import logging
import os
import statistics
import time
from dataclasses import dataclass
from typing import Any, Literal

import pymupdf
from dotenv import load_dotenv
from fastapi import FastAPI, Form, HTTPException, Response, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from google import genai
from google.genai import errors, types
from pydantic import BaseModel, Field, ValidationError

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger("scanly")

MAX_PDF_BYTES = 20 * 1024 * 1024  # matches the limit in FileUploader.tsx
# aliases track the current models, so they won't get retired under us; lite is the fallback when Flash is overloaded.
# GEMINI_MODELS overrides the order (comma-separated), e.g. "gemini-flash-latest" alone to benchmark Flash without fallback.
MODELS = [m.strip() for m in os.environ.get("GEMINI_MODELS", "gemini-flash-latest,gemini-flash-lite-latest").split(",") if m.strip()]
BUSY_CODES = {429, 500, 503}
# "auto": send extracted text when the PDF has enough of it, else the PDF itself. "pdf": always send the PDF
# (the pre-Phase-1 behaviour; used for side-by-side benchmarks and as an instant rollback).
RESUME_INPUT = os.environ.get("RESUME_INPUT", "auto")
MIN_TEXT_CHARS = 200  # less than this means a scanned/image-only PDF, so Gemini needs to see the page itself

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
app = FastAPI(title="Scanly API")

# the deployed frontend lives on another domain; list it in ALLOWED_ORIGINS (comma-separated)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip().rstrip("/") for o in os.environ.get("ALLOWED_ORIGINS", "").split(",") if o.strip()],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


# the upload page pings this on load so a sleeping free-tier server wakes before the user submits
@app.get("/api/health")
def health() -> dict:
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
    """Mirrors the Feedback interface in types/index.d.ts."""

    overallScore: int = Field(ge=0, le=100)
    ATS: AtsSection
    toneAndStyle: Section
    content: Section
    structure: Section
    skills: Section


def build_prompt(job_title: str, job_description: str) -> str:
    # Output is generated token by token, so its length drives response time: keep tips short and the JSON compact.
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
    """Return all the text in a PDF, page by page, as one string ("" if there is none).

    Used to send Gemini plain text instead of the whole PDF. A scanned resume (just an image of the page)
    has no text layer, so this returns "" or almost nothing, and the caller falls back to sending the PDF.

    TODO:
    - open the PDF from bytes, not from a file path: pymupdf.open(stream=pdf, filetype="pdf")
    - loop over the pages; page.get_text() returns that page's text
    - join the pages with a newline so words from different pages don't run together
    - strip leading/trailing whitespace from the result
    - close the document when done (a `with` block does this for you)
    - a corrupt or non-PDF file makes pymupdf.open raise; let that propagate, the caller handles it
    """
    with pymupdf.open(stream=pdf, filetype="pdf") as doc:
        return "\n".join(page.get_text() for page in doc).strip()


# Sections scored together in one Gemini call; the groups run in parallel. Fewer groups = fewer API calls,
# more groups = less output per call (faster) but more calls per analysis against the per-minute rate limit.
# [[all five]] is one call; [["ATS"], ["toneAndStyle"], ...] is one call per section.
GROUPS = [["ATS", "toneAndStyle", "content"], ["structure", "skills"]]
# The first group also returns overallScore: the model's judgement of the whole resume, which is harsher on weak or
# mismatched resumes than an average of section scores (measured: a mismatched resume averaged ~50 vs ~37 holistic).


@dataclass
class GroupResult:
    sections: dict[str, Any]
    model: str
    skipped: list[str]
    usage: Any
    seconds: float


def group_schema(fields: list[str]) -> dict:
    """The Feedback JSON schema cut down to just these fields."""
    full = Feedback.model_json_schema()
    return {**full, "properties": {k: full["properties"][k] for k in fields}, "required": list(fields)}


async def score_group(group: list[str], resume_part: Any, prompt: str, with_overall: bool = False) -> GroupResult:
    """Score one group of sections, trying each model in MODELS until one isn't busy.

    Raises HTTPException (503 if every model was busy, 502 for any other failure) so the caller can fail the
    whole request clearly instead of returning a review with sections missing.
    """
    start = time.perf_counter()
    skipped: list[str] = []
    fields = ["overallScore", *group] if with_overall else group
    ask = f"{prompt}\nOnly return these sections: {', '.join(group)}."
    if with_overall:
        ask += " Also return overallScore: your overall judgement of the whole resume for this job, not an average."
    for model in MODELS:
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
            if e.code not in BUSY_CODES:
                raise HTTPException(502, f"AI request failed: {e.message or e}")
            skipped.append(f"{model}:{e.code}")
            continue
        except Exception as e:
            raise HTTPException(502, f"AI request failed: {e}")
        try:
            data = json.loads(result.text or "")
        except json.JSONDecodeError:
            raise HTTPException(502, "AI returned feedback in an unexpected format, please try again")
        if not isinstance(data, dict):
            raise HTTPException(502, "AI returned feedback in an unexpected format, please try again")
        sections = {k: data.get(k) for k in fields}  # ignore anything outside this group
        return GroupResult(sections, model, skipped, getattr(result, "usage_metadata", None), time.perf_counter() - start)
    log.info(f"group {'+'.join(group)} failed: all models busy ({', '.join(skipped)})")
    raise HTTPException(503, "Gemini is overloaded right now. Wait a minute and try again.")


def combine(sections: dict[str, Any]) -> Feedback:
    """Validate each section and build the Feedback the frontend expects.

    overallScore comes from the first group's call; if it's missing, fall back to the average of the sections.
    """
    sections = dict(sections)
    overall = sections.pop("overallScore", None)
    parsed = {k: Feedback.model_fields[k].annotation.model_validate(v) for k, v in sections.items()}
    if overall is None:
        overall = round(statistics.mean(section.score for section in parsed.values()))
    return Feedback(overallScore=overall, **parsed)


@app.post("/api/analyze", response_model=Feedback)
async def analyze(
    response: Response,
    resume: UploadFile,
    jobTitle: str = Form(""),
    jobDescription: str = Form(""),
) -> Feedback:
    # seconds spent in each step, filled in by lap(); logged and sent back in a Server-Timing header
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
        except Exception as e:  # unreadable PDF: let Gemini try the file itself
            log.info(f"text extraction failed, sending PDF: {e}")
    send_text = len(text) >= MIN_TEXT_CHARS
    resume_part = f"Resume text:\n{text}" if send_text else types.Part.from_bytes(data=pdf, mime_type="application/pdf")
    lap("extract")

    # all groups at once: the wait is roughly the slowest group, not the sum of them
    outcomes = await asyncio.gather(
        *(score_group(group, resume_part, build_prompt(jobTitle, jobDescription), with_overall=(i == 0))
          for i, group in enumerate(GROUPS)),
        return_exceptions=True,
    )
    failed = [o for o in outcomes if isinstance(o, BaseException)]
    if failed:
        log.info(f"analyze failed: {len(failed)}/{len(GROUPS)} parallel calls failed: {failed[0]}")
        first = failed[0]
        raise first if isinstance(first, HTTPException) else HTTPException(502, f"AI request failed: {first}")
    lap("gemini")

    try:
        feedback = combine({k: v for o in outcomes for k, v in o.sections.items()})
    except (ValidationError, TypeError, AttributeError):
        raise HTTPException(502, "AI returned feedback in an unexpected format, please try again")
    lap("parse")

    total = sum(timings.values())
    models = "|".join(dict.fromkeys(o.model for o in outcomes))  # unique, in order
    fallback = "|".join(x for o in outcomes for x in o.skipped)  # "|" not ",": commas separate Server-Timing entries
    # output (and hidden "thinking") tokens are generated one by one, so they drive most of the Gemini time
    usages = [o.usage for o in outcomes if o.usage]
    tokens = (f"in={sum(u.prompt_token_count or 0 for u in usages)} out={sum(u.candidates_token_count or 0 for u in usages)} "
              f"think={sum(u.thoughts_token_count or 0 for u in usages)} calls={len(outcomes)}") if usages else ""
    log.info(
        "analyze " + " ".join(f"{k}={v:.3f}s" for k, v in timings.items())
        + f" total={total:.3f}s model={models} input={'text' if send_text else 'pdf'}"
        + " calls=[" + " ".join(f"{'+'.join(o.sections)}:{o.seconds:.2f}s" for o in outcomes) + "]"
        + (f" tokens[{tokens}]" if tokens else "")
        + (f" fallback={fallback}" if fallback else "")
    )
    # standard header (shows in browser DevTools); durations in milliseconds; desc carries labels
    entries = [f"{k};dur={v * 1000:.1f}" for k, v in timings.items()]
    entries += [f"call{i + 1};dur={o.seconds * 1000:.1f};desc=\"{'+'.join(o.sections)}\"" for i, o in enumerate(outcomes)]
    entries += [f'model;desc="{models}"', f'input;desc="{"text" if send_text else "pdf"}"']
    if fallback:
        entries.append(f'fallback;desc="{fallback}"')
    if tokens:
        entries.append(f'tokens;desc="{tokens}"')
    response.headers["Server-Timing"] = ", ".join(entries)
    return feedback
