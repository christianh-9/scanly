// Backend base URL: empty in local dev (Vite proxies /api), the Render URL in production (set VITE_API_URL on Vercel).
export const API_URL = (import.meta.env.VITE_API_URL ?? '').replace(/\/$/, '')

// Render's free tier sleeps when idle; ping early so the server is awake by the time someone submits a resume.
// Hits /api/health only: no Gemini call, no quota used.
export const wakeBackend = () => { fetch(`${API_URL}/api/health`).catch(() => {}) }
