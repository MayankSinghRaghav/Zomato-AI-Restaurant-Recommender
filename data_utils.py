import re
import time
from typing import Dict, List, Optional, Tuple

import pandas as pd
from datasets import load_dataset

DATASET_ID = "ManikaSaini/zomato-restaurant-recommendation"


def _load_dataset_with_retry(max_retries: int = 3, retry_delay_sec: float = 1.5):
    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            # Reuse local cache whenever available to reduce network/session flakiness.
            return load_dataset(DATASET_ID, download_mode="reuse_dataset_if_exists")
        except RuntimeError as exc:
            last_error = exc
            err_text = str(exc).lower()
            if "client has been closed" in err_text and attempt < max_retries:
                time.sleep(retry_delay_sec)
                continue
            raise
        except Exception as exc:  # pragma: no cover - defensive fallback for transient hub issues
            last_error = exc
            if attempt < max_retries:
                time.sleep(retry_delay_sec)
                continue
            raise

    # Defensive guard; loop should either return or raise beforehand.
    raise RuntimeError(f"Unable to load dataset after {max_retries} attempts: {last_error}")


def _first_existing_column(df: pd.DataFrame, candidates: List[str]) -> Optional[str]:
    lower_map = {col.lower(): col for col in df.columns}
    for candidate in candidates:
        if candidate.lower() in lower_map:
            return lower_map[candidate.lower()]
    return None


def _to_float(value) -> Optional[float]:
    if value is None:
        return None
    text = str(value)
    match = re.search(r"\d+(\.\d+)?", text)
    if not match:
        return None
    try:
        return float(match.group(0))
    except ValueError:
        return None


def _to_int(value) -> Optional[int]:
    if value is None:
        return None
    text = str(value).replace(",", "")
    match = re.search(r"\d+", text)
    if not match:
        return None
    try:
        return int(match.group(0))
    except ValueError:
        return None


def _budget_bucket(avg_cost: Optional[int]) -> str:
    if avg_cost is None:
        return "unknown"
    if avg_cost < 600:
        return "low"
    if avg_cost < 1500:
        return "medium"
    return "high"


def load_and_prepare_data(sample_limit: Optional[int] = 5000) -> Tuple[pd.DataFrame, Dict[str, str]]:
    dataset = _load_dataset_with_retry()

    split_name = "train" if "train" in dataset else list(dataset.keys())[0]
    df = dataset[split_name].to_pandas()

    if sample_limit and len(df) > sample_limit:
        df = df.sample(sample_limit, random_state=42).reset_index(drop=True)

    col_map = {
        "name": _first_existing_column(df, ["Restaurant Name", "name", "restaurant_name", "res_name"]),
        "location": _first_existing_column(
            df,
            ["City", "city", "Location", "location", "locality", "listed_in(city)", "address"],
        ),
        "cuisines": _first_existing_column(df, ["Cuisines", "cuisines", "Cuisine", "cuisine"]),
        "cost": _first_existing_column(
            df,
            [
                "Average Cost for two",
                "average_cost_for_two",
                "approx_cost(for two people)",
                "cost_for_two",
                "cost",
            ],
        ),
        "rating": _first_existing_column(df, ["Aggregate rating", "rating", "user_rating", "rate", "votes rating"]),
        "highlights": _first_existing_column(
            df,
            ["Highlights", "highlights", "features", "tags", "known_for", "dish_liked", "rest_type"],
        ),
    }

    # Build normalized columns that downstream logic can rely on.
    normalized = pd.DataFrame()
    normalized["name"] = (
        df[col_map["name"]].astype(str)
        if col_map["name"]
        else pd.Series(["Unknown"] * len(df), index=df.index)
    )
    normalized["location"] = (
        df[col_map["location"]].astype(str)
        if col_map["location"]
        else pd.Series(["Unknown"] * len(df), index=df.index)
    )
    normalized["cuisines"] = (
        df[col_map["cuisines"]].astype(str)
        if col_map["cuisines"]
        else pd.Series(["Unknown"] * len(df), index=df.index)
    )
    normalized["highlights"] = (
        df[col_map["highlights"]].astype(str)
        if col_map["highlights"]
        else pd.Series([""] * len(df), index=df.index)
    )
    normalized["cost_for_two"] = (
        df[col_map["cost"]].map(_to_int)
        if col_map["cost"]
        else pd.Series([None] * len(df), index=df.index)
    )
    normalized["rating"] = (
        df[col_map["rating"]].map(_to_float)
        if col_map["rating"]
        else pd.Series([None] * len(df), index=df.index)
    )
    normalized["budget_bucket"] = normalized["cost_for_two"].map(_budget_bucket)

    normalized = normalized.dropna(subset=["name"]).copy()
    normalized["name"] = normalized["name"].str.strip()
    normalized["location"] = normalized["location"].str.strip()
    normalized["cuisines"] = normalized["cuisines"].str.strip()

    normalized = normalized[normalized["name"] != ""]
    normalized = normalized.drop_duplicates(subset=["name", "location", "cuisines"]).reset_index(drop=True)

    return normalized, col_map


def filter_restaurants(
    df: pd.DataFrame,
    location: str,
    budget: str,
    cuisine: str,
    min_rating: float,
    extra_preference: str,
    limit: int = 30,
) -> pd.DataFrame:
    filtered = df.copy()

    if location:
        filtered = filtered[filtered["location"].str.contains(location, case=False, na=False)]

    if budget and budget != "any":
        # Keep rows with missing cost so we do not over-prune valid restaurants.
        filtered = filtered[
            (filtered["budget_bucket"] == budget) | filtered["cost_for_two"].isna() | (filtered["budget_bucket"] == "unknown")
        ]

    if cuisine:
        filtered = filtered[filtered["cuisines"].str.contains(cuisine, case=False, na=False)]

    filtered = filtered[filtered["rating"].fillna(0) >= min_rating]

    if extra_preference:
        extra_mask = filtered["highlights"].str.contains(extra_preference, case=False, na=False) | filtered[
            "cuisines"
        ].str.contains(extra_preference, case=False, na=False)
        filtered = filtered[extra_mask]

    filtered = filtered.sort_values(by=["rating", "cost_for_two"], ascending=[False, True]).head(limit).reset_index(
        drop=True
    )
    return filtered
