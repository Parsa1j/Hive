import json
from openai import OpenAI

SYSTEM_PROMPT = """You are a senior QA engineer. Given a software implementation and its review, write comprehensive
unit tests using pytest.

Return ONLY valid JSON with this structure:
{
  "test_files": [
    {
      "filename": "test_example.py",
      "description": "what these tests cover",
      "content": "full pytest file content as a string"
    }
  ],
  "coverage_summary": "description of what is and isn't covered",
  "test_count": 5,
  "run_command": "pytest test_example.py -v"
}

Write real, runnable pytest tests. Use mocking where appropriate for external dependencies.
Cover happy paths, edge cases, and error conditions."""


def run(context: dict) -> dict:
    client = OpenAI()
    plan = context["plan"]
    code = context["code"]
    review = context["review"]

    files_summary = "\n\n".join(
        f"### {f['filename']}\n{f['content']}" for f in code.get("files", [])
    )

    issues_summary = (
        "\n".join(
            f"- [{i['severity']}] {i['file']}: {i['description']}"
            for i in review.get("issues", [])
        )
        or "No issues reported."
    )

    user_message = (
        f"## Plan\n{json.dumps(plan, indent=2)}\n\n"
        f"## Implementation\n{files_summary}\n\n"
        f"## Review Issues to Address in Tests\n{issues_summary}"
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
    tests = json.loads(raw)

    context["tests"] = tests
    context["tester_raw"] = raw
    return context
