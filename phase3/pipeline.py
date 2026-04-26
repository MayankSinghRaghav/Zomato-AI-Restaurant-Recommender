from typing import Any, Dict

from data_utils import load_and_prepare_data
from phase2.engine import generate_candidates


def run_phase3_pipeline(user_input: Dict[str, Any], sample_limit: int = 5000) -> Dict[str, Any]:
    df, _ = load_and_prepare_data(sample_limit=sample_limit)
    candidates = generate_candidates(df=df, user_input=user_input, limit=30)
    return {
        "status": "ok",
        "candidate_count": len(candidates),
        "candidates": candidates,
    }
