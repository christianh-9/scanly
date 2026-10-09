import os
from typing import Literal

from dotenv import load_dotenv
from fastapi import FastAPI, Form, HTTPException, UploadFile
from google import genai
from google.genai import errors, types
from pydantic import BaseModel, Field, ValidationError

load_dotenv()

MAX_PDF_BYTES = 20 * 1024 * 1024  # matches the limit in FileUploader.tsx
# aliases track the current models, so they won't get retired under us; lite is the fallback when Flash is overloaded
MODELS = ["gemini-flash-latest", "gemini-flash-lite-latest"]
BUSY_CODES = {429, 500, 503}

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
app = FastAPI(title="Scanly API")


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
    return f"""You are an expert in ATS (Applicant Tracking System) and resume analysis.
Analyze and rate this resume and suggest how to improve it.
The rating can be low if the resume is bad. Be thorough and point out mistakes.
Give 3-4 tips per section. For tips with an explanation, keep "tip" a short title and put the detail in "explanation".
If provided, take the job into consideration.
Job title: {job_title or "(not provided)"}
Job description: {job_description or "(not provided)"}"""


@app.post("/api/analyze", response_model=Feedback)
async def analyze(
    resume: UploadFile,
    jobTitle: str = Form(""),
    jobDescription: str = Form(""),
) -> Feedback:
    if resume.content_type != "application/pdf":
        raise HTTPException(400, "Resume must be a PDF")
    pdf = await resume.read()
    if len(pdf) > MAX_PDF_BYTES:
        raise HTTPException(413, "Resume must be 20 MB or smaller")

    response = None
    for model in MODELS:
        try:
            response = await client.aio.models.generate_content(
                model=model,
                contents=[
                    types.Part.from_bytes(data=pdf, mime_type="application/pdf"),
                    build_prompt(jobTitle, jobDescription),
                ],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_json_schema=Feedback.model_json_schema(),
                ),
            )
            break
        except errors.APIError as e:
            if e.code not in BUSY_CODES:
                raise HTTPException(502, f"AI request failed: {e.message or e}")
        except Exception as e:
            raise HTTPException(502, f"AI request failed: {e}")
    if response is None:
        raise HTTPException(503, "Gemini is overloaded right now. Wait a minute and try again.")

    try:
        return Feedback.model_validate_json(response.text or "")
    except ValidationError:
        raise HTTPException(502, "AI returned feedback in an unexpected format, please try again")
