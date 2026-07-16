# ⚡ CareerMind AI

AI-powered career mentor built with FastAPI + Google Gemini API + Docker, deployed on AWS App Runner.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | HTML + CSS + Vanilla JS (Space Grotesk font) |
| Backend | Python FastAPI + SSE streaming |
| AI Model | Gemini 2.0 Flash (Google Gemini API) |
| Container | Docker |
| Registry | Amazon ECR |
| Hosting | AWS App Runner |

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

## Local Development

### 1. Get a Gemini API key

Go to https://aistudio.google.com/app/apikey and create a free API key.

### 2. Clone and configure

```bash
git clone <your-repo>
cd careermind
cp .env.example .env
# Edit .env → set GEMINI_API_KEY=your-key-here
```

### 3. Install dependencies

```bash
pip install -r backend/requirements.txt
```

### 4. Run the server

```bash
uvicorn backend.main:app --reload --port 8000
```

Visit: https://careermind-ai-seven.vercel.app/

---

## Docker Build & Run

```bash
docker build -t careermind-ai .

docker run -p 8000:8000 -e GEMINI_API_KEY=your-key-here careermind-ai
```

Visit: https://careermind-ai-seven.vercel.app
---

## AWS Deployment (App Runner via ECR)

### Step 1 — Create ECR repository

```bash
aws ecr create-repository --repository-name careermind-ai --region us-east-1
```

### Step 2 — Authenticate Docker to ECR

```bash
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin \
  123456789012.dkr.ecr.us-east-1.amazonaws.com
```

### Step 3 — Build, tag, push

```bash
docker buildx build --platform linux/amd64 -t careermind-ai .

docker tag careermind-ai:latest \
  123456789012.dkr.ecr.us-east-1.amazonaws.com/careermind-ai:latest

docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/careermind-ai:latest
```

### Step 4 — Deploy on App Runner

1. AWS Console → **App Runner** → **Create service**
2. Source: **Container registry** → **Amazon ECR**
3. Select image: `careermind-ai:latest`
4. Port: **8000**
5. Environment variables:
   - `GEMINI_API_KEY` = `your-gemini-api-key`
6. Click **Create & Deploy**

### Step 5 — Get your public URL

```
https://xxxxxxxx.us-east-1.awsapprunner.com
```

Paste this into your Project Concept Note and Report.

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

## Cost Estimate

Gemini 2.0 Flash has a **free tier** via Google AI Studio:
- 15 RPM / 1,500 requests per day free
- No credit card required for development

For production, AWS App Runner free tier covers 2M requests/month.
# CareerMind-AI
