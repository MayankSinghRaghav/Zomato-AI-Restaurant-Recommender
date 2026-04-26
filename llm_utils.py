import json
import os
from typing import Any, Dict, List

import requests
from phase0 import resolve_gemini_key


def _restaurant_to_prompt_row(row: Dict[str, Any]) -> str:
    return (
        f"- {row.get('name', 'Unknown')} | Location: {row.get('location', 'Unknown')} | "
        f"Cuisines: {row.get('cuisines', 'Unknown')} | Rating: {row.get('rating', 'N/A')} | "
        f"Cost for two: {row.get('cost_for_two', 'N/A')} | Highlights: {row.get('highlights', '')}"
    )


def build_recommendation_prompt(
    user_preferences: Dict[str, Any], candidate_restaurants: List[Dict[str, Any]], top_k: int
) -> str:
    rows = "\n".join(_restaurant_to_prompt_row(r) for r in candidate_restaurants)
    return f"""
You are an expert local food concierge. 
Given user preferences and candidate restaurants, rank the best {top_k} matches.

User preferences:
- Location: {user_preferences.get('location', 'any')}
- Budget: {user_preferences.get('budget', 'any')}
- Cuisine: {user_preferences.get('cuisine', 'any')}
- Minimum rating: {user_preferences.get('min_rating', 'any')}
- Additional preference: {user_preferences.get('extra_preference', '')}

Candidate restaurants:
{rows}

Instructions:
1) Return ONLY valid JSON.
2) Pick up to {top_k} restaurants.
3) For each recommendation include:
   - name
   - cuisine
   - rating
   - estimated_cost_for_two
   - explanation (1-2 natural sentences, specific to user preferences)
4) Consider location, budget fit, cuisine match, rating, and additional preference.

Expected JSON schema:
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


def call_llm_for_recommendations(
    prompt: str, model: str = "gemini-1.5-flash", temperature: float = 0.3
) -> Dict[str, Any]:
    api_key = resolve_gemini_key()
    base_url = os.getenv("GEMINI_BASE_URL", "https://generativelanguage.googleapis.com").rstrip("/")

    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set. Add it in your environment or .env file.")

    url = f"{base_url}/v1beta/models/{model}:generateContent?key={api_key}"
    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": (
                            "You produce only valid JSON responses.\n\n"
                            f"{prompt}"
                        )
                    }
                ]
            }
        ],
        "generationConfig": {
            "temperature": temperature,
            "responseMimeType": "application/json",
        },
    }
    headers = {"Content-Type": "application/json"}

    response = requests.post(url, headers=headers, json=payload, timeout=90)
    response.raise_for_status()
    data = response.json()

    content = (
        data.get("candidates", [{}])[0]
        .get("content", {})
        .get("parts", [{}])[0]
        .get("text", "")
    )
    if not content:
        raise RuntimeError(f"Gemini returned empty response: {data}")

    try:
        return json.loads(content.strip().removeprefix("```json").removesuffix("```").strip())
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Gemini returned non-JSON response: {content}") from exc


def fallback_recommendations(candidate_restaurants: List[Dict[str, Any]], top_k: int) -> Dict[str, Any]:
    sorted_candidates = sorted(
        candidate_restaurants,
        key=lambda r: (r.get("rating") or 0, -(r.get("cost_for_two") or 999999)),
        reverse=True,
    )[:top_k]

    recommendations = []
    for r in sorted_candidates:
        recommendations.append(
            {
                "name": r.get("name", "Unknown"),
                "cuisine": r.get("cuisines", "Unknown"),
                "rating": r.get("rating", 0),
                "estimated_cost_for_two": r.get("cost_for_two", 0),
                "explanation": (
                    "Strong baseline match based on your filters and restaurant rating."
                ),
            }
        )
    return {"recommendations": recommendations}
