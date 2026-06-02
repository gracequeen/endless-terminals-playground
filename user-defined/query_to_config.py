"""
query_to_config.py — boilerplate skeleton

Converts a natural-language user query into a generation_config.json
that the pipeline can consume via --config.

Usage:
    python query_to_config.py \
        --query "60% DevOps (container, git), 40% security, mostly hard" \
        --out generation_config.json
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# The system prompt includes the full TASK_CATEGORIES list so the model can
# ground free-form user intent in recognized category names.
# ---------------------------------------------------------------------------
from generator.task_template_gen import TASK_CATEGORIES

SYSTEM_PROMPT = f"""You convert a user's generation request into a JSON config.

Output ONLY valid JSON matching this schema exactly — no commentary, no markdown fences:
{{
  "categories": [
    {{"name": "<category>", "weight": <float>}}
  ],
  "difficulty_distribution": {{
    "easy": <float>,
    "medium": <float>,
    "hard": <float>
  }},
  "num_tasks": <int>
}}

Rules:
- Map user intent to category names from this list when possible:
  {json.dumps(TASK_CATEGORIES, indent=2)}
- Weights are relative and will be normalized — they don't need to sum to 1.
- Difficulty distribution values should sum to 1.0.
- If the user doesn't specify num_tasks, default to 100.
- If the user doesn't specify difficulty, use {{"easy": 0.2, "medium": 0.5, "hard": 0.3}}.
- Free-form categories not in the list above are allowed; include them as-is.
"""


def query_to_config(
    query: str,
    model: str = "gpt-4o",
    client=None,  # openai.OpenAI or compatible
) -> dict:
    """
    Call the LLM to convert a query string into a config dict.
    Returns the parsed config dict.
    Raises ValueError if the LLM response cannot be parsed.
    """
    if client is None:
        raise ValueError("Must provide an OpenAI-compatible client.")

    for attempt in range(2):
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": query},
            ],
            response_format={"type": "json_object"},
            temperature=0.2,
        )
        raw = response.choices[0].message.content.strip()
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            if attempt == 1:
                raise ValueError(f"LLM returned non-JSON after 2 attempts:\n{raw}")

    raise ValueError("Unreachable")


def validate_config(config: dict) -> tuple[bool, list[str]]:
    """
    Lightweight pre-flight check. Returns (is_valid, warnings).
    Warnings are non-fatal; is_valid=False means the config cannot be used.
    """
    warnings: list[str] = []
    known = set(TASK_CATEGORIES)

    if config.get("num_tasks", 0) <= 0:
        return False, ["num_tasks must be > 0"]

    cats = config.get("categories", [])
    if cats:
        total_weight = sum(c.get("weight", 0) for c in cats)
        if total_weight <= 0:
            return False, ["All category weights are zero."]
        for c in cats:
            if c["name"] not in known:
                warnings.append(
                    f"Unrecognized category '{c['name']}' — will be used as a free-form hint."
                )

    diff = config.get("difficulty_distribution", {})
    if diff:
        total = sum(diff.values())
        if abs(total - 1.0) > 0.05:
            warnings.append(
                f"Difficulty distribution sums to {total:.2f}, expected 1.0 — will be normalized."
            )

    return True, warnings


def main() -> None:
    ap = argparse.ArgumentParser(description="Convert a query to a generation config.")
    ap.add_argument("--query", required=True, help="Natural-language generation request.")
    ap.add_argument("--out", type=Path, default=Path("generation_config.json"))
    ap.add_argument("--model", default="gpt-4o")
    args = ap.parse_args()

    # Build a client — adjust to your actual client setup (AzureOpenAI, vllm, etc.)
    from openai import OpenAI
    client = OpenAI()

    print(f"Converting query to config...")
    config = query_to_config(args.query, model=args.model, client=client)

    valid, warnings = validate_config(config)
    for w in warnings:
        print(f"  WARNING: {w}")
    if not valid:
        print("ERROR: config is not valid, aborting.")
        raise SystemExit(1)

    args.out.write_text(json.dumps(config, indent=2))
    print(f"Config written to {args.out}")
    print(json.dumps(config, indent=2))


if __name__ == "__main__":
    main()
