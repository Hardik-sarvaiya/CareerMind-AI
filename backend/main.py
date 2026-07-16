from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional
from google import genai
from google.genai import types
import os
import json
from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()



app = FastAPI(title="CareerMind AI API", version="3.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
MODEL = "gemini-3.5-flash"

# ── SSE response headers ─────────────────────────────────────────────────────
# These four headers are all required for correct streaming through every layer:
#   nginx (X-Accel-Buffering), CDNs (no-transform), proxies (no-cache),
#   and HTTP/1.1 keep-alive connections.  Without them the entire generator
#   output is buffered by the first reverse-proxy layer and forwarded as a
#   single block — producing the "only first part received" symptom.
SSE_HEADERS = {
    "Content-Type":      "text/event-stream",
    "Cache-Control":     "no-cache, no-transform",
    "X-Accel-Buffering": "no",
    "Connection":        "keep-alive",
    "Transfer-Encoding": "chunked",
}

# ── Token budget ─────────────────────────────────────────────────────────────
# gemini-2.0-flash max output = 8192 tokens.
# Previous value was 1024 (~750 words) which silently truncated every long
# response (roadmap, interview prep, resume analysis all exceed 1024 tokens).
MAX_TOKENS = 8192


# ── Pydantic request models ──────────────────────────────────────────────────

class ResumeRequest(BaseModel):
    resume: str
    role: Optional[str] = ""

class SkillGapRequest(BaseModel):
    skills: str
    role: str

class RoadmapRequest(BaseModel):
    goal: str
    level: str
    hours_per_week: str

class InterviewRequest(BaseModel):
    role: str
    level: str
    question_type: str

class PlannerRequest(BaseModel):
    topic: str
    hours_per_day: str
    deadline: Optional[str] = "flexible"

class CourseRequest(BaseModel):
    skill: str
    format: str
    level: str

class ATSRequest(BaseModel):
    resume: str
    job_description: Optional[str] = ""

class LinkedInRequest(BaseModel):
    name: Optional[str] = ""
    role: str
    info: str
    tone: str

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: list[ChatMessage]


# ── Shared streaming helper ──────────────────────────────────────────────────

def stream_gemini(system: str, user: str) -> StreamingResponse:
    """
    Wraps a Gemini generate_content_stream call in an SSE StreamingResponse.

    Each text chunk is emitted as:   data: {"text": "..."}\n\n
    Stream termination is signalled:  data: [DONE]\n\n
    Exceptions surface as:            data: {"error": "..."}\n\n  then [DONE]

    This shape is what the frontend parseSseLine() expects.
    """
    def generator():
        prompt = f"{system}\n\n{user}"
        try:
            for chunk in client.models.generate_content_stream(
                model=MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    max_output_tokens=MAX_TOKENS,
                    temperature=0.7,
                ),
            ):
                if chunk.text:
                    yield f"data: {json.dumps({'text': chunk.text})}\n\n"
        except Exception as exc:
            yield f"data: {json.dumps({'error': str(exc)})}\n\n"
        finally:
            yield "data: [DONE]\n\n"

    return StreamingResponse(generator(), headers=SSE_HEADERS)


# ── Static frontend ──────────────────────────────────────────────────────────

FRONTEND_DIR = Path(__file__).parent.parent / "frontend"
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

@app.get("/health")
def health():
    return {
        "status": "ok",
        "model": MODEL,
        "max_output_tokens": MAX_TOKENS,
        "version": "3.1.0",
    }

@app.get("/")
def root():
    index = FRONTEND_DIR / "index.html"
    if index.exists():
        return FileResponse(str(index))
    return {"message": "CareerMind AI API v3.1 — frontend not found"}


# ── API routes ───────────────────────────────────────────────────────────────

@app.post("/api/resume")
def analyze_resume(req: ResumeRequest):
    system = (
        "You are an expert career coach and resume reviewer. "
        "Give thorough, structured, actionable feedback. Be specific and honest. "
        "Use markdown: ## headings, **bold**, bullet lists, numbered lists. "
        "Write the COMPLETE analysis — never truncate or summarise early."
    )
    user = (
        f"Analyse this resume"
        f"{' for the role of **' + req.role + '**' if req.role else ''}:\n\n"
        f"{req.resume}\n\n"
        "## Instructions\n"
        "Write every section fully. Do not stop early.\n\n"
        "### 1. Overall Score\n"
        "Give a score X/10 and a one-sentence verdict.\n\n"
        "### 2. Strengths ✅\n"
        "List every genuine strength with one line of explanation each.\n\n"
        "### 3. Weaknesses ❌\n"
        "Be honest. List every weakness with one line of explanation.\n\n"
        "### 4. Missing Keywords\n"
        "List missing keywords for the target role in a table.\n\n"
        "### 5. Top 5 Improvements\n"
        "Numbered, specific, actionable. Each at least 2 sentences.\n\n"
        "### 6. ATS Compatibility\n"
        "Score /10 and three specific ATS fixes.\n\n"
        "### 7. Final Recommendation\n"
        "Two to three sentences. Be direct."
    )
    return stream_gemini(system, user)


@app.post("/api/skill-gap")
def skill_gap(req: SkillGapRequest):
    system = (
        "You are an expert technical recruiter and career advisor. "
        "Analyse skill gaps thoroughly. Use markdown tables and lists. "
        "Always complete your full analysis — never truncate."
    )
    user = (
        f"**Target role:** {req.role}\n"
        f"**Current skills:** {req.skills}\n\n"
        "## Instructions — write every section in full\n\n"
        "### 1. Skills You Already Have ✅\n"
        "List all matching skills. For each say why it is relevant.\n\n"
        "### 2. Critical Missing Skills ❌\n"
        "For each skill: name, why it is required, difficulty to learn.\n\n"
        "### 3. Nice-to-Have Skills ⚡\n"
        "List with brief explanation.\n\n"
        "### 4. Priority Learning Order\n"
        "Numbered list with one-line rationale per item.\n\n"
        "### 5. Timeline\n"
        "Realistic estimate broken into phases (months).\n\n"
        "### 6. Resources for Top 3 Gaps\n"
        "For each gap: 2 specific resources (course name + platform)."
    )
    return stream_gemini(system, user)


@app.post("/api/roadmap")
def roadmap(req: RoadmapRequest):
    system = (
        "You are an expert learning path designer and career mentor. "
        "Create detailed, realistic, phase-by-phase roadmaps. "
        "Use ## for phases, ### for sub-sections, bullet lists for topics. "
        "Always write the COMPLETE roadmap — every phase, every detail."
    )
    user = (
        f"**Goal:** {req.goal}\n"
        f"**Current level:** {req.level}\n"
        f"**Time per week:** {req.hours_per_week}\n\n"
        "## Instructions\n"
        "Write a complete, detailed roadmap. Do not summarise any phase.\n\n"
        "Include for the overall plan:\n"
        "- Total duration estimate\n"
        "- Prerequisites checklist\n\n"
        "For EACH phase include:\n"
        "- Phase number, title, and duration\n"
        "- Specific topics with sub-topics\n"
        "- Hands-on project to build\n"
        "- Milestone / checkpoint\n"
        "- Two or three specific resources\n\n"
        "End with:\n"
        "- What to do after completing the roadmap\n"
        "- How to track progress\n"
        "- Common pitfalls to avoid"
    )
    return stream_gemini(system, user)


@app.post("/api/interview")
def interview(req: InterviewRequest):
    system = (
        "You are an expert technical interviewer and career coach. "
        "Generate comprehensive interview questions with detailed answer frameworks. "
        "Use markdown. Write ALL 8 questions fully — do not stop at question 4 or 5."
    )
    user = (
        f"**Role:** {req.role}\n"
        f"**Level:** {req.level}\n"
        f"**Question type:** {req.question_type}\n\n"
        "## Instructions\n"
        "Generate EXACTLY 8 interview questions numbered 1 through 8.\n"
        "For each question write all four subsections:\n\n"
        "**Question N: [question text]**\n\n"
        "**Why interviewers ask this:** one to two sentences.\n\n"
        "**Answer framework:** detailed framework (STAR for behavioural, "
        "step-by-step for technical, trade-offs for design).\n\n"
        "**Example talking points:** three to five bullet points.\n\n"
        "---\n\n"
        "Write all 8 questions completely before stopping."
    )
    return stream_gemini(system, user)


@app.post("/api/planner")
def planner(req: PlannerRequest):
    system = (
        "You are an expert study coach and learning strategist. "
        "Create structured, realistic, detailed study plans. "
        "Use markdown tables and lists. Write the COMPLETE plan."
    )
    user = (
        f"**Learning:** {req.topic}\n"
        f"**Daily study time:** {req.hours_per_day}\n"
        f"**Deadline:** {req.deadline}\n\n"
        "## Instructions — write every section fully\n\n"
        "### Overview Table\n"
        "A markdown table: Week | Focus Area | Goal | Project\n\n"
        "### Week-by-Week Breakdown\n"
        "For each week: daily schedule Mon-Fri, weekend task, milestone.\n"
        "Write at least the first 4 weeks in full daily detail.\n\n"
        "### Progress Checkpoints\n"
        "What to know/build at the end of each month.\n\n"
        "### Tips for Staying on Track\n"
        "Five specific, actionable tips."
    )
    return stream_gemini(system, user)


@app.post("/api/courses")
def courses(req: CourseRequest):
    system = (
        "You are an expert learning curator with deep knowledge of online "
        "education platforms. Recommend specific, real, high-quality courses. "
        "Use markdown. Write all 6 recommendations fully."
    )
    user = (
        f"**Skill:** {req.skill}\n"
        f"**Format preference:** {req.format}\n"
        f"**Level:** {req.level}\n\n"
        "## Instructions\n"
        "Recommend EXACTLY 6 courses or resources, numbered 1 through 6.\n"
        "For each course write all fields:\n\n"
        "### N. Course Name — Platform\n"
        "**Why it's the best choice:** one to two sentences.\n"
        "**What you will learn:** three to five bullet points.\n"
        "**Duration:** approximate hours or weeks.\n"
        "**Cost:** free / price.\n"
        "**URL:** full URL if you know it, otherwise leave blank.\n\n"
        "Write all 6 courses fully."
    )
    return stream_gemini(system, user)


@app.post("/api/ats")
def ats_check(req: ATSRequest):
    system = (
        "You are an ATS (Applicant Tracking System) expert. "
        "IMPORTANT: Your very first line must be exactly: SCORE: XX/100\n"
        "Then write a thorough, complete analysis using markdown."
    )
    user = (
        f"**Resume:**\n{req.resume}\n\n"
        f"**Job Description:**\n"
        f"{req.job_description or '(none provided — perform general ATS optimisation)'}\n\n"
        "## Instructions\n"
        "Line 1 of your response: SCORE: XX/100\n\n"
        "Then write every section:\n\n"
        "### Score Explanation\n"
        "Why this score — two to three sentences.\n\n"
        "### Matched Keywords ✅\n"
        "Table: Keyword | Found In | Importance\n\n"
        "### Missing Keywords ❌\n"
        "Table: Missing Keyword | Why It Matters | Where to Add\n\n"
        "### Formatting Issues ⚠️\n"
        "Bullet list of every formatting problem.\n\n"
        "### Section-by-Section Feedback\n"
        "For each resume section: current state and specific fix.\n\n"
        "### Rewrite Suggestions\n"
        "Show before → after for the three weakest bullet points.\n\n"
        "### Final Keyword List\n"
        "Ten keywords to add, comma-separated."
    )
    return stream_gemini(system, user)


@app.post("/api/linkedin")
def linkedin(req: LinkedInRequest):
    system = (
        "You are an expert LinkedIn profile writer and personal branding specialist. "
        "Write compelling, optimised LinkedIn profiles. "
        "Write everything fully — do not cut the response short."
    )
    user = (
        f"**Name:** {req.name or '[Name]'}\n"
        f"**Role/Title:** {req.role}\n"
        f"**Background/Skills:** {req.info}\n"
        f"**Tone:** {req.tone}\n\n"
        "## Instructions — write every section fully\n\n"
        "### LinkedIn About Section\n"
        "200-300 words. Must include:\n"
        "- Opening hook (first two sentences must grab attention)\n"
        "- Professional value proposition\n"
        "- Key skills and areas of expertise\n"
        "- Notable achievements or projects (specific numbers if possible)\n"
        "- What you are currently looking for\n"
        "- Call to action with contact method\n\n"
        "### 5 Headline Variations\n"
        "Numbered 1-5. Each under 220 characters. Vary the angle.\n\n"
        "### 10 Skills to Add\n"
        "Comma-separated. Mix technical and soft skills.\n\n"
        "### 3 Profile Visibility Tips\n"
        "Specific, actionable, not generic advice."
    )
    return stream_gemini(system, user)


@app.post("/api/chat")
def chat(req: ChatRequest):
    if not req.messages:
        return StreamingResponse(iter(["data: [DONE]\n\n"]), headers=SSE_HEADERS)

    system = (
        "You are CareerMind AI, an expert career mentor. "
        "Help with career advice, job searching, interview prep, skill development, "
        "salary negotiation, career transitions, and professional growth. "
        "Be warm, practical, specific, and thorough. "
        "Use markdown formatting where it improves readability. "
        "Never cut your response short."
    )

    history = []
    for m in req.messages[:-1]:
        gemini_role = "user" if m.role == "user" else "model"
        history.append(
            types.Content(role=gemini_role, parts=[types.Part(text=m.content)])
        )

    last_message = req.messages[-1].content

    def generator():
        try:
            chat_session = client.chats.create(
                model=MODEL,
                config=types.GenerateContentConfig(
                    system_instruction=system,
                    max_output_tokens=MAX_TOKENS,
                    temperature=0.7,
                ),
                history=history,
            )
            for chunk in chat_session.send_message_stream(last_message):
                if chunk.text:
                    yield f"data: {json.dumps({'text': chunk.text})}\n\n"
        except Exception as exc:
            yield f"data: {json.dumps({'error': str(exc)})}\n\n"
        finally:
            yield "data: [DONE]\n\n"

    return StreamingResponse(generator(), headers=SSE_HEADERS)
