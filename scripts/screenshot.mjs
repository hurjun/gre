// Capture the README screenshots (docs/dashboard.png, docs/adaptive-question.png)
// from the *actually running* app, using headless Chromium via Playwright.
//
// Prerequisites (no MySQL required — uses a local SQLite database):
//
//   # 1. Backend on SQLite, seeded with the bundled content bank
//   cd backend
//   export GRE_DATABASE_URL="sqlite:///./demo.db"
//   python -m app.seed.seed
//   uvicorn app.main:app --port 8000 &
//
//   # 2. Frontend dev server (proxies /api -> :8000, see vite.config.js)
//   cd frontend && npm run dev -- --port 5173 &
//
//   # 3. Capture (Playwright is a one-off tooling dependency, not a project dep)
//   npx playwright install chromium
//   BASE=http://127.0.0.1:5173 OUT=docs node scripts/screenshot.mjs
//
// The progress shown in the dashboard is produced by answering questions through
// the real POST /api/answers endpoint, so every pixel is a genuine app render.

import { chromium } from 'playwright'

const BASE = process.env.BASE || 'http://127.0.0.1:5173'
const OUT = process.env.OUT || 'docs'

const browser = await chromium.launch()
const ctx = await browser.newContext({
  viewport: { width: 1200, height: 900 },
  deviceScaleFactor: 2,
})
const page = await ctx.newPage()

// Dashboard: per-section difficulty meters and progress bars.
await page.goto(`${BASE}/`, { waitUntil: 'networkidle' })
await page.waitForSelector('.card .level-meter', { timeout: 15000 })
await page.screenshot({ path: `${OUT}/dashboard.png`, fullPage: true })
console.log(`saved ${OUT}/dashboard.png`)

// Adaptive question view: a single unsolved question at the current level.
await page.goto(`${BASE}/quiz/se_tc`, { waitUntil: 'networkidle' })
await page.waitForSelector('.choices .choice', { timeout: 15000 })
await page.screenshot({ path: `${OUT}/adaptive-question.png`, fullPage: true })
console.log(`saved ${OUT}/adaptive-question.png`)

await browser.close()
