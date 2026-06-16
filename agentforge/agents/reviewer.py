import json
from openai import OpenAI

SYSTEM_PROMPT = """You are a senior software engineer performing a code review. Given a plan and its implementation,
review the code for correctness, quality, security, and adherence to the plan.

Return ONLY valid JSON with this structure:
{
  "verdict": "pass" or "fail",
  "score": 1-10,
  "summary": "one paragraph overall assessment",
  "issues": [
    {
      "severity": "critical" | "major" | "minor",
      "file": "filename",
      "description": "what the issue is",
      "suggestion": "how to fix it"
    }
  ],
  "strengths": ["strength 1", "strength 2"],
  "recommendations": ["recommendation 1", "recommendation 2"]
}

Be thorough but fair. A score of 7+ with no critical issues should pass."""


def run(context: dict) -> dict:
    client = OpenAI()
    plan = context["plan"]
    code = context["code"]

    files_summary = "\n\n".join(
        f"### {f['filename']}\n{f['content']}" for f in code.get("files", [])
    )

    user_message = (
        f"## Plan\n{json.dumps(plan, indent=2)}\n\n"
        f"## Implementation\n{files_summary}"
    )

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        response_format={"type": "json_object"},
    )

    raw = response.choices[0].message.content
    review = json.loads(raw)

    context["review"] = review
    context["reviewer_raw"] = raw
    return context
