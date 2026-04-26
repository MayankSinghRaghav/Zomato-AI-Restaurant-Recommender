import os
from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class RuntimeConfig:
    llm_key_present: bool
    llm_model: str
    llm_provider: str


def _clean_env(value: str) -> str:
    return (value or "").strip().strip("\"' ")


def resolve_gemini_key() -> str:
    """Return configured Gemini key from supported env vars."""
    return _clean_env(os.getenv("GEMINI_API_KEY", "") or os.getenv("GOOGLE_API_KEY", ""))


def get_runtime_config() -> RuntimeConfig:
    key = resolve_gemini_key()
    return RuntimeConfig(
        llm_key_present=bool(key),
        llm_model=_clean_env(os.getenv("GEMINI_MODEL", "")) or "gemini-1.5-flash",
        llm_provider="gemini",
    )


def get_preflight_report(col_map: Dict[str, str], total_rows: int) -> Dict[str, object]:
    required_columns: List[str] = ["name", "location", "cuisines", "cost", "rating"]
    missing_mappings = [col for col in required_columns if not col_map.get(col)]

    return {
        "total_rows": total_rows,
        "missing_mappings": missing_mappings,
        "schema_ok": len(missing_mappings) == 0,
    }
