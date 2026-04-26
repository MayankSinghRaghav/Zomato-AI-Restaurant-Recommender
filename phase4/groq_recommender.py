import json
import os
from pathlib import Path
from typing import Any, Dict, List

import requests
from dotenv import load_dotenv

from llm_utils import fallback_recommendations

load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env", override=True)


def build_prompt(user_input: Dict[str, Any], candidates: List[Dict[str, Any]], top_k: int = 5) -> str:
    rows = []
    for row in candidates[:30]:
        rows.append(
            f"- {row.get('name', 'Unknown')} | Location: {row.get('location', 'Unknown')} | "
            f"Cuisines: {row.get('cuisines', 'Unknown')} | Rating: {row.get('rating', 'N/A')} | "
            f"Cost for two: {row.get('cost_for_two', 'N/A')} | Highlights: {row.get('highlights', '')}"
        )

    return f"""
You are a restaurant recommendation engine.
Rank the best {top_k} restaurants based on user preferences and candidates.

User preferences:
- Location: {user_input.get("location", "")}
- Budget (INR for two): {user_input.get("budget", "")}
- Cuisine: {user_input.get("cuisine", "")}
- Minimum rating: {user_input.get("minimum_rating", "")}
- Additional preference: {user_input.get("additional_preference", "")}

Candidates:
{chr(10).join(rows)}

Return ONLY strict JSON in this format:
{{
  "recommendations": [
    {{
      "name": "string",
      "cuisine": "string",
      "rating": number,
      "estimated_cost_for_two": number,
      "explanation": "string"
    }}
  ]
}}
""".strip()


def _extract_json(raw: str) -> Dict[str, Any]:
    text = raw.strip()
    if text.startswith("```"):
        text = text.replace("```json", "").replace("```", "").strip()
    return json.loads(text)


def get_groq_recommendations(
    user_input: Dict[str, Any], candidates: List[Dict[str, Any]], top_k: int = 5
) -> Dict[str, Any]:
    key = (os.getenv("GROQ_API_KEY") or "").strip().strip("\"'")
    model = (os.getenv("GROQ_MODEL") or "llama-3.1-70b-versatile").strip()

    if not key:
        return fallback_recommendations(candidates, top_k=top_k)

    prompt = build_prompt(user_input=user_input, candidates=candidates, top_k=top_k)
    url = "https://api.groq.com/openai/v1/chat/completions"
    payload = {
        "model": model,
        "temperature": 0.2,
        "messages": [
            {"role": "system", "content": "Return valid JSON only."},
            {"role": "user", "content": prompt},
        ],
    }
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=90)
        response.raise_for_status()
        data = response.json()
        message = data["choices"][0]["message"]["content"]
        parsed = _extract_json(message)
        if "recommendations" not in parsed:
            raise RuntimeError("Groq response missing recommendations key.")
        return parsed
    except Exception:
        return fallback_recommendations(candidates, top_k=top_k)
