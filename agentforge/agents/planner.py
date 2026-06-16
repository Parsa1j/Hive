import json
from openai import OpenAI

SYSTEM_PROMPT = """You are a software planning agent. Given a natural language prompt describing a software task,
break it down into a structured list of concrete implementation tasks.

Return ONLY valid JSON with this structure:
{
  "project_name": "short name for the project",
  "description": "one-sentence summary",
  "tasks": [
    {
      "id": 1,
      "title": "task title",
      "description": "what needs to be implemented",
      "acceptance_criteria": ["criterion 1", "criterion 2"]
    }
  ]
}

Keep tasks focused and implementable. Aim for 3-6 tasks."""


def run(context: dict) -> dict:
    client = OpenAI()
    prompt = context["prompt"]

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Plan the implementation for: {prompt}"},
        ],
        response_format={"type": "json_object"},
    )

    raw = response.choices[0].message.content
    plan = json.loads(raw)

    context["plan"] = plan
    context["planner_raw"] = raw
    return context
