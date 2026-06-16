import json
from openai import OpenAI

SYSTEM_PROMPT = """You are an expert Python software engineer. Given a task plan, write clean, working Python code
that implements all the tasks.

Return ONLY valid JSON with this structure:
{
  "files": [
    {
      "filename": "example.py",
      "description": "what this file does",
      "content": "full file content as a string"
    }
  ],
  "setup_instructions": "brief setup/run instructions",
  "dependencies": ["package1", "package2"]
}

Write production-quality code with proper error handling. Each file should be complete and runnable."""


REVISE_PROMPT = """You are an expert Python software engineer revising existing code based on a code review.

You will be given the original plan, the existing implementation, and the reviewer's feedback (issues +
recommendations). Produce an improved implementation that addresses every critical and major issue, and
addresses minor issues where reasonable. Keep working parts intact. Do not introduce regressions.

Return ONLY valid JSON with the same structure as before:
{
  "files": [
    { "filename": "example.py", "description": "what this file does", "content": "full file content" }
  ],
  "setup_instructions": "brief setup/run instructions",
  "dependencies": ["package1", "package2"]
}

Each file must be complete and runnable. Do not return partial diffs."""


def run(context: dict) -> dict:
    client = OpenAI()
    plan = context["plan"]
    plan_json = json.dumps(plan, indent=2)

    if context.get("revise"):
        prev_code = context.get("code", {})
        review = context.get("review", {})
        files_summary = "\n\n".join(
            f"### {f['filename']}\n{f['content']}" for f in prev_code.get("files", [])
        )
        user_message = (
            f"## Plan\n{plan_json}\n\n"
            f"## Existing Implementation\n{files_summary}\n\n"
            f"## Review Feedback\n{json.dumps(review, indent=2)}\n\n"
            "Rewrite the code to address the review."
        )
        system_prompt = REVISE_PROMPT
    else:
        user_message = f"Implement all tasks from this plan:\n\n{plan_json}"
        system_prompt = SYSTEM_PROMPT

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        response_format={"type": "json_object"},
    )

    raw = response.choices[0].message.content
    code_output = json.loads(raw)

    context["code"] = code_output
    context["coder_raw"] = raw
    return context
