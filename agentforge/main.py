import json
import sys
import os

# Make sure sibling packages resolve correctly when running from the agentforge/ dir
sys.path.insert(0, os.path.dirname(__file__))

# Load .env BEFORE importing agents so OPENAI_API_KEY is in os.environ at import time.
# Checks agentforge/.env first, then the project root (Agent_forge/.env).
from dotenv import load_dotenv
_here = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(_here, ".env"))
load_dotenv(os.path.join(_here, "..", ".env"))

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from core.orchestrator import run_pipeline, run_revision
from agents import prototype

app = FastAPI(title="AgentForge")
app.mount("/static", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "static")), name="static")


class RunRequest(BaseModel):
    prompt: str


class ReviseRequest(BaseModel):
    prompt: str
    plan: dict
    code: dict
    review: dict


class PrototypeRequest(BaseModel):
    prompt: str
    plan: dict
    code: dict


def _sse(generator):
    def event_stream():
        for event in generator:
            yield f"data: {json.dumps(event)}\n\n"
        yield 'data: {"agent": "__done__", "status": "done"}\n\n'

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/", response_class=HTMLResponse)
async def index():
    html_path = os.path.join(os.path.dirname(__file__), "static", "index.html")
    with open(html_path, encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


@app.post("/run")
async def run(request: RunRequest):
    """Streams the full pipeline (Planner → Coder → Reviewer → Tester) over SSE."""
    prompt = request.prompt.strip()
    if not prompt:
        return {"error": "prompt is required"}
    return _sse(run_pipeline(prompt))


@app.post("/revise")
async def revise(request: ReviseRequest):
    """Streams a revision pass (Coder in revise mode → Reviewer → Tester) over SSE."""
    prompt = request.prompt.strip()
    if not prompt:
        return {"error": "prompt is required"}
    return _sse(run_revision(prompt, request.plan, request.code, request.review))


@app.post("/prototype")
async def build_prototype(request: PrototypeRequest):
    """Generates a single-file HTML prototype for the project."""
    try:
        result = prototype.run(request.prompt, request.plan, request.code)
        html = (result or {}).get("html", "")
        if not html:
            return JSONResponse({"error": "Prototype agent returned no html"}, status_code=500)
        return {"html": html}
    except Exception as exc:
        return JSONResponse({"error": str(exc)}, status_code=500)
