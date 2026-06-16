# AgentForge

**AI multi-agent task orchestration platform** — turn a single natural-language prompt into a planned, coded, reviewed, and tested software solution, streamed live to your browser.

AgentForge runs four specialized LLM agents in a pipeline. Each one builds on the last: the **Planner** breaks your prompt into tasks, the **Coder** implements them, the **Reviewer** critiques the result, and the **Tester** writes pytest coverage. You can then apply the review feedback in a one-click revision pass, or generate an interactive HTML prototype of the finished project.

## Screenshots

<!-- Add screenshots here, e.g.: -->
<!-- ![Pipeline running](docs/screenshot-pipeline.png) -->
<!-- ![Review output](docs/screenshot-review.png) -->

## Features

- **Four-stage agent pipeline** — Planner → Coder → Reviewer → Tester, each agent passing an enriched context to the next.
- **Live streaming UI** — results appear agent-by-agent over Server-Sent Events; no waiting for the full run to finish.
- **Feedback-driven revision** — when the Reviewer finds issues, one click re-runs the Coder against the review and re-reviews + re-tests the result.
- **Interactive prototypes** — generate a single-file, sandboxed HTML prototype of the project and preview it in-app.
- **Zero-build frontend** — a single dependency-free `index.html` (GitHub-dark themed) talks to the FastAPI backend.

## Setup

```bash
cd agentforge
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
uvicorn main:app --reload
```

Open http://localhost:8000 in your browser.

## Architecture

```
                    ┌──────────────┐
   prompt  ───────▶ │ Orchestrator │   core/orchestrator.py
                    └──────┬───────┘
                           │  context = { prompt }
          ┌────────────────┼────────────────┬────────────────┐
          ▼                ▼                 ▼                ▼
     ┌─────────┐      ┌─────────┐      ┌──────────┐     ┌─────────┐
     │ Planner │ ───▶ │  Coder  │ ───▶ │ Reviewer │ ──▶ │ Tester  │
     └─────────┘      └─────────┘      └──────────┘     └─────────┘
       +plan            +code            +review          +tests
          └────────────────┴────────────────┴────────────────┘
                           │  SSE stream of agent events
                           ▼
              FastAPI /run endpoint → browser UI
```

A single **shared context dict** travels through the pipeline, growing as it goes — every agent sees all previous agents' outputs. The orchestrator iterates the pipeline and `yield`s a status event after each agent; the FastAPI endpoint wraps that generator in an SSE stream, so the browser renders incremental updates.

| Agent    | Input used               | Adds to context |
|----------|--------------------------|-----------------|
| Planner  | `prompt`                 | `plan`          |
| Coder    | `plan`                   | `code`          |
| Reviewer | `plan`, `code`           | `review`        |
| Tester   | `plan`, `code`, `review` | `tests`         |

### Why SSE over WebSockets?

The pipeline is a one-shot, server-to-client stream — a perfect fit for Server-Sent Events. SSE is unidirectional, needs no extra libraries, works over plain HTTP, and the browser's streaming `fetch` API handles it natively. WebSockets would add bidirectional complexity for no benefit here.

### Why gpt-4o-mini?

Four sequential API calls make latency and cost the primary constraints. `gpt-4o-mini` delivers sufficient quality for structured JSON outputs at roughly 10× lower cost than `gpt-4o`, keeping end-to-end runs fast and cheap.

## Project Structure

```
agentforge/
├── main.py                 # FastAPI app: /run, /revise, /prototype SSE endpoints
├── agents/
│   ├── planner.py          # Breaks the prompt into a structured task list
│   ├── coder.py            # Implements tasks as Python files (+ revise mode)
│   ├── reviewer.py         # Reviews code, returns verdict + score + issues
│   ├── tester.py           # Writes pytest unit tests
│   └── prototype.py        # Generates a single-file interactive HTML prototype
├── core/
│   └── orchestrator.py     # Runs the pipeline, yields SSE events
├── static/
│   └── index.html          # Dark-themed single-page UI (no build step)
├── .env.example
└── requirements.txt
```

## Tech Stack

FastAPI · OpenAI · Server-Sent Events · vanilla JS/HTML/CSS (no frontend framework)
