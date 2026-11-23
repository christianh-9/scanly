// Empty in dev (Vite proxies /api)
export const API_URL = (import.meta.env.VITE_API_URL ?? '').replace(/\/$/, '')

// Render's free tier sleeps, so wake it before anyone uploads
export const wakeBackend = () => { fetch(`${API_URL}/api/health`).catch(() => {}) }
