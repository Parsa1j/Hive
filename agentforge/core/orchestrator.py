import time
from typing import Generator
from agents import planner, coder, reviewer, tester

PIPELINE = [
    ("planner", "Planner", planner.run),
    ("coder", "Coder", coder.run),
    ("reviewer", "Reviewer", reviewer.run),
    ("tester", "Tester", tester.run),
]

REVISION_PIPELINE = [
    ("coder", "Coder", coder.run),
    ("reviewer", "Reviewer", reviewer.run),
    ("tester", "Tester", tester.run),
]


def run_pipeline(prompt: str) -> Generator[dict, None, None]:
    """
    Runs agents in sequence. Yields a status event dict after each agent completes.
    Each event has the shape:
      { "agent": str, "status": "running"|"done"|"error", "output": dict|None, "elapsed": float }
    """
    context = {"prompt": prompt}
    yield from _run_steps(PIPELINE, context)


def run_revision(prompt: str, plan: dict, code: dict, review: dict) -> Generator[dict, None, None]:
    """
    Re-runs Coder (in revise mode) → Reviewer → Tester using the existing plan and the latest review.
    Yields the same shape of events as run_pipeline.
    """
    context = {
        "prompt": prompt,
        "plan": plan,
        "code": code,
        "review": review,
        "revise": True,
    }
    yield from _run_steps(REVISION_PIPELINE, context)


def _run_steps(steps, context) -> Generator[dict, None, None]:
    for agent_id, agent_name, agent_fn in steps:
        yield {"agent": agent_id, "agent_name": agent_name, "status": "running", "output": None}

        start = time.perf_counter()
        try:
            context = agent_fn(context)
            elapsed = round(time.perf_counter() - start, 2)
            output = _extract_output(agent_id, context)
            yield {
                "agent": agent_id,
                "agent_name": agent_name,
                "status": "done",
                "output": output,
                "elapsed": elapsed,
            }
        except Exception as exc:
            elapsed = round(time.perf_counter() - start, 2)
            yield {
                "agent": agent_id,
                "agent_name": agent_name,
                "status": "error",
                "output": {"error": str(exc)},
                "elapsed": elapsed,
            }
            return  # abort pipeline on error


def _extract_output(agent_id: str, context: dict) -> dict:
    if agent_id == "planner":
        return context.get("plan", {})
    elif agent_id == "coder":
        return context.get("code", {})
    elif agent_id == "reviewer":
        return context.get("review", {})
    elif agent_id == "tester":
        return context.get("tests", {})
    return {}
