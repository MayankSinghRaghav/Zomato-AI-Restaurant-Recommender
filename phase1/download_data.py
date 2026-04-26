import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from data_utils import load_and_prepare_data


def main() -> None:
    parser = argparse.ArgumentParser(description="Phase 1: download and normalize restaurant data.")
    parser.add_argument("--sample-limit", type=int, default=5000, help="Max rows to load before normalization.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parent / "artifacts",
        help="Directory where normalized files are saved.",
    )
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    df, col_map = load_and_prepare_data(sample_limit=args.sample_limit)

    csv_path = args.output_dir / "restaurants_normalized.csv"
    json_path = args.output_dir / "column_map.json"

    df.to_csv(csv_path, index=False)
    json_path.write_text(json.dumps(col_map, indent=2), encoding="utf-8")

    print(f"Downloaded and normalized rows: {len(df)}")
    print(f"Saved data to: {csv_path}")
    print(f"Saved column map to: {json_path}")


if __name__ == "__main__":
    main()
