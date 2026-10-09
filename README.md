# Scanly

Scanly reviews your resume the way a strict recruiter would. Upload a PDF, optionally paste the job you're applying for, and get an overall score, five category scores, and specific fixes, with low scores where they're earned.

## Features

- **Scored against the job.** Add a company, job title and description and the review is tailored to that posting. Leave them blank for a general review.
- **Blunt verdict.** An overall score out of 100 with a one-line verdict ("Needs work before you apply."), plus scores for ATS, tone and style, content, structure, and skills.
- **Specific fixes first.** Each category lists what to fix before what's working, with an explanation for every tip. The weakest category opens first.
- **Resume beside the feedback.** The review page shows your resume's first page next to the scores so you can check each point.
- **Live analysis log.** Uploading shows each step (render, analyze, upload, save) with timings, and a clear error and retry if something fails.
- **Review history.** Every review is saved to your account; reopen or delete any of them.

## Tech stack

| Part | Built with |
|---|---|
| Frontend | React Router 7 (SPA mode), React 19, TypeScript, Tailwind CSS 4 |
| Backend | FastAPI, Pydantic, Google Gen AI SDK |
| AI | Gemini (`gemini-flash-latest`, falling back to `gemini-flash-lite-latest` when it's overloaded) |
| Sign-in and storage | [Puter](https://puter.com) (puter.js): accounts, file storage, key-value store |
| PDF rendering | pdf.js |

## How it works

1. The browser renders the PDF's first page to a PNG with pdf.js.
2. The PDF and job details go to the FastAPI backend at `POST /api/analyze`, which sends the PDF to Gemini and validates the response against the feedback schema before returning it.
3. The browser uploads the PDF and preview image to your Puter storage and saves the review in Puter's key-value store.

The Gemini API key lives only on the backend and is never sent to the browser.

## Getting started

### Prerequisites

- Node.js 20+
- Python 3.11+
- A free Gemini API key from [Google AI Studio](https://aistudio.google.com/apikey)
- A Puter account (you can create one when you first sign in to Scanly)

### 1. Install

```bash
git clone git@github.com:christianh-9/scanly.git
cd scanly
npm install
```

### 2. Start the backend

```bash
cd server
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env    # then put your key in .env: GEMINI_API_KEY=...
.venv/bin/uvicorn main:app --reload --port 8001
```

Leave this terminal running. API docs are at http://localhost:8001/docs.

> Keep your key in `server/.env`, which is git-ignored. Never put it in `.env.example`.

### 3. Start the frontend

In a second terminal, from the project root:

```bash
npm run dev
```

Open http://localhost:5173. The dev server forwards `/api` requests to the backend on port 8001.

## Tests

The backend has a self-check that fakes Gemini, so it uses no API quota:

```bash
cd server
.venv/bin/python test_main.py
```

Type-check the frontend with:

```bash
npm run typecheck
```

## Project structure

```
app/
  routes/        home (review history), upload, resume (review page), auth, wipe
  components/    UI pieces: score summary, ATS panel, detail sections, delete dialog, icons
  lib/           Puter wrapper, PDF-to-image, score helpers
server/
  main.py        FastAPI app and the /api/analyze endpoint
  test_main.py   backend self-check
DESIGN.md        design system (colors, type, components)
PRODUCT.md       product goals and principles
```

## Troubleshooting

- **"Gemini is overloaded right now"**: Gemini's free tier is busy. Wait a minute and try again.
- **"Analysis failed… Is the backend running?"**: start the backend (step 2).
- **`KeyError: 'GEMINI_API_KEY'` on backend start**: `server/.env` is missing or empty.
- **`address already in use`**: another program is using the port. Pick a different one and update the proxy in `vite.config.ts` to match.

## Deployment

The frontend and backend deploy separately, and both redeploy automatically on `git push`.

**Backend on [Render](https://render.com)** (free Web Service):

| Setting | Value |
|---|---|
| Root Directory | `server` |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `uvicorn main:app --host 0.0.0.0 --port $PORT` |
| Environment | `GEMINI_API_KEY`, `PYTHON_VERSION=3.12.12`, `ALLOWED_ORIGINS=https://your-site.vercel.app` (comma-separate extra domains) |

Free Render services sleep after 15 idle minutes. The upload page pings `/api/health` when it opens so the server is usually awake by the time you submit.

**Frontend on [Vercel](https://vercel.com):** import the repo and set `VITE_API_URL` to the Render URL (for example `https://scanly-api.onrender.com`). Vite bakes this in at build time, so redeploy after changing it.

## Privacy

Resumes are sent to Google Gemini for analysis. Files and reviews are stored in your own Puter account, and deleting a review removes its PDF and preview image too.

## License

No license has been specified. All rights reserved by christianh-9.

## Acknowledgments

- [pdf.js](https://mozilla.github.io/pdf.js/) for rendering PDFs
- [Puter](https://puter.com) for sign-in and storage
- [Google Gemini](https://ai.google.dev/) for analysis
- Icons adapted from [Lucide](https://lucide.dev) (ISC)
