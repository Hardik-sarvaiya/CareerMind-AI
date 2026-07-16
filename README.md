# ⚡ CareerMind AI

AI-powered career mentor built with FastAPI + Google Gemini API.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | HTML + CSS + Vanilla JS (Space Grotesk font) |
| Backend | Python FastAPI + SSE streaming |
| AI Model | Gemini 3.5 Flash (Google Gemini API) |
|

---

## AI Features (9 tools)

1. **Resume Analyzer** — structured feedback with score
2. **Skill Gap Detector** — current vs target role
3. **Roadmap Generator** — phase-by-phase learning plan
4. **Interview Prep** — questions + STAR frameworks
5. **Study Planner** — week-by-week schedule
6. **Course Finder** — curated platform recommendations
7. **ATS Score Checker** — keyword match + animated score ring
8. **LinkedIn Bio Generator** — tone-aware About section
9. **AI Career Chat** — multi-turn conversation with history

---


## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check (returns model name) |
| GET | `/` | Serve frontend |
| POST | `/api/resume` | Resume analysis |
| POST | `/api/skill-gap` | Skill gap detection |
| POST | `/api/roadmap` | Learning roadmap |
| POST | `/api/interview` | Interview questions |
| POST | `/api/planner` | Study planner |
| POST | `/api/courses` | Course recommendations |
| POST | `/api/ats` | ATS score check |
| POST | `/api/linkedin` | LinkedIn bio |
| POST | `/api/chat` | Multi-turn chat |

All AI endpoints return **Server-Sent Events (SSE)** for real-time streaming.

---

## Security

- `GEMINI_API_KEY` lives only in environment variables — never in code or git
- `.env` is in `.gitignore`
- Key is injected at runtime via App Runner environment variables
- Frontend never sees the API key

---

# CareerMind-AI
