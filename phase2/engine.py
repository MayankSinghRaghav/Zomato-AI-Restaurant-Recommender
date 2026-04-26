from typing import Dict, List

from data_utils import filter_restaurants


def _budget_to_bucket(budget: int) -> str:
    if budget <= 600:
        return "low"
    if budget <= 1500:
        return "medium"
    return "high"


def generate_candidates(df, user_input: Dict, limit: int = 30) -> List[Dict]:
    budget_bucket = _budget_to_bucket(int(user_input.get("budget", 0)))

    location = user_input.get("location", "")
    cuisine = user_input.get("cuisine", "")
    min_rating = float(user_input.get("minimum_rating", 0.0))
    extra = user_input.get("additional_preference", "")

    filtered = filter_restaurants(
        df=df,
        location=location,
        budget=budget_bucket,
        cuisine=cuisine,
        min_rating=min_rating,
        extra_preference=extra,
        limit=limit,
    )

    if filtered.empty:
        # Progressive relaxation in strict -> broad order.
        attempts = [
            dict(extra_preference=""),
            dict(extra_preference="", budget="any"),
            dict(location="", budget="any", extra_preference=""),
        ]
        for override in attempts:
            filtered = filter_restaurants(
                df=df,
                location=override.get("location", location),
                budget=override.get("budget", budget_bucket),
                cuisine=cuisine,
                min_rating=min_rating,
                extra_preference=override.get("extra_preference", extra),
                limit=limit,
            )
            if not filtered.empty:
                break

    return filtered.to_dict(orient="records")
