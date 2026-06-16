import json
from openai import OpenAI

SYSTEM_PROMPT = """You are a UI prototype designer. Given a software project (its prompt, plan, and code),
produce a SINGLE self-contained HTML file that demonstrates a working interactive prototype of the
user-facing side of the project.

Rules:
- Output a complete HTML document including <!DOCTYPE html> ... </html>.
- Inline ALL CSS in <style> and ALL JS in <script>. No external requests, no CDNs, no <link> to remote URLs.
- The prototype must run entirely in the browser. If the underlying code is server-side (e.g., a REST API,
  CLI tool, or data pipeline), build a client-side UI that mimics the same behavior using in-memory JS state.
- Make it interactive: the user should be able to perform the project's primary action and see a result.
- Style it cleanly with a dark theme so it fits a developer tool. Reasonable padding, readable fonts,
  rounded corners, subtle borders.
- It will be rendered inside an iframe with sandbox="allow-scripts" — do not depend on top-window navigation,
  cookies, localStorage, or external network calls.

Return ONLY valid JSON with this exact shape:
{ "html": "<!DOCTYPE html>...</html>" }
"""


def run(prompt: str, plan: dict, code: dict) -> dict:
    client = OpenAI()

    files_summary = "\n\n".join(
        f"### {f['filename']}\n{f.get('content','')}" for f in (code or {}).get("files", [])
    )

    user_message = (
        f"## Original prompt\n{prompt}\n\n"
        f"## Plan\n{json.dumps(plan or {}, indent=2)}\n\n"
        f"## Implementation\n{files_summary}\n\n"
        "Build a single-file interactive HTML prototype that shows what this project does."
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
    return json.loads(raw)
