# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users
Primarily a portfolio piece: recruiters and hiring engineers evaluating the developer's craft, who will click through the real flow (sign in, upload a resume, read the review). Actual job seekers using it to check a resume before applying are a secondary audience.

## Product Purpose
Scanly reviews a resume PDF, optionally against a specific job title and description, and returns an overall score plus ATS, tone and style, content, structure, and skills scores with concrete tips. Success: a visitor uploads a resume, gets a review they find credible and specific within about a minute, and remembers the product as distinct from the many resume-analyzer tutorial clones.

## Positioning
Honest, blunt feedback. Scanly tells you plainly what is wrong with your resume, the way a strict recruiter would, and is allowed to give low scores. It is not a cheerleader.

## Operating Context
- Sign-in, file storage, and the per-user resume history are provided by Puter (puter.js in the browser).
- Analysis runs on the project's own FastAPI backend (`server/`, deployed on Render), which sends the PDF to Gemini and validates the JSON against the Feedback schema. The frontend is deployed on Vercel at scanlycv.vercel.app.
- Flow: home (list of past reviews) → upload (company, job title, job description, PDF up to 20 MB) → processing → review page (resume preview beside scores and tips).

## Capabilities and Constraints
- Stack: React Router v7 (SPA mode), Tailwind CSS v4, TypeScript; FastAPI + Gemini backend.
- Feedback shape is fixed by `types/index.d.ts` / `server/main.py`: overallScore, ATS (score + tips), toneAndStyle, content, structure, skills (score + tips with explanations). Each tip is "good" or "improve".
- Users can view and delete past reviews; deleting removes the record plus its stored PDF and preview image.
- PDF only. The first page is rendered to a PNG for previews.

## Brand Commitments
- The name "Scanly" stays. Everything else visual (gradient, colors, illustrations, loading GIFs) may be replaced.
- Visual reference (user-pinned, 2026-10-08): Vercel's product UI, meaning dark, precise, engineered. Borrow its craft level and grammar, never its logo, wordmark, or name.

## Evidence on Hand
- No testimonials, user counts, accuracy benchmarks, or company logos exist. Do not invent them.
- Sample resume images exist at `public/images/resume_01.png` through `resume_03.png`.

## Product Principles
1. Candor over comfort: scores and copy say what is wrong plainly and do not inflate.
2. Specific over generic: every tip should point at something in this resume or this job.
3. Show the work: the resume and the verdict sit side by side so a claim can be checked.
4. A real product, not a demo: real states for loading, errors, empty history, and deletion.
