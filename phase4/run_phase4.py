import argparse
import json
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from data_utils import load_and_prepare_data
from phase2.engine import generate_candidates
from phase4.groq_recommender import get_groq_recommendations

load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env", override=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Phase 4: Groq ranking for top restaurant recommendations.")
    parser.add_argument("--location", required=True)
    parser.add_argument("--budget", required=True, type=int, help="Budget for two in INR.")
    parser.add_argument("--minimum-rating", required=True, type=float)
    parser.add_argument("--cuisine", default="")
    parser.add_argument("--additional-preference", default="")
    parser.add_argument("--top-k", type=int, default=5)
    args = parser.parse_args()

    user_input = {
        "location": args.location,
        "budget": args.budget,
        "minimum_rating": args.minimum_rating,
        "cuisine": args.cuisine,
        "additional_preference": args.additional_preference,
    }

    df, _ = load_and_prepare_data(sample_limit=5000)
    candidates = generate_candidates(df=df, user_input=user_input, limit=40)
    if len(candidates) < args.top_k:
        relaxed_input = dict(user_input)
        relaxed_input["minimum_rating"] = 0.0
        relaxed_input["location"] = ""
        relaxed_input["additional_preference"] = ""
        extra_candidates = generate_candidates(df=df, user_input=relaxed_input, limit=40)
        if extra_candidates:
            candidates = extra_candidates
    result = get_groq_recommendations(user_input=user_input, candidates=candidates, top_k=args.top_k)

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
