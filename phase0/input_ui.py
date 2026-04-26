from pathlib import Path
from typing import Any, Dict

import streamlit as st
from dotenv import load_dotenv

from phase0 import get_runtime_config

load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env", override=True)


def collect_user_input() -> Dict[str, Any]:
    st.title("Phase 0 - Basic Web UI Input")
    st.caption("This UI is the primary source of recommendation input.")

    location = st.text_input("Location", value="Bellandur")
    budget = st.number_input("Budget for two (INR)", min_value=100, max_value=10000, value=2000, step=100)
    cuisine = st.text_input("Cuisine preference (optional)", value="")
    minimum_rating = st.slider("Minimum rating", min_value=0.0, max_value=5.0, value=4.0, step=0.1)
    additional_preference = st.text_input("Additional preference (optional)", value="")

    values = {
        "location": location.strip(),
        "budget": int(budget),
        "cuisine": cuisine.strip(),
        "minimum_rating": float(minimum_rating),
        "additional_preference": additional_preference.strip(),
    }
    return values


def main() -> None:
    runtime = get_runtime_config()
    st.info(
        f"Provider: {runtime.llm_provider} | Model: {runtime.llm_model} | "
        f"LLM key configured: {runtime.llm_key_present}"
    )

    payload = collect_user_input()
    if st.button("Submit Input"):
        st.success("Input captured successfully.")
        st.json(payload)


if __name__ == "__main__":
    main()
