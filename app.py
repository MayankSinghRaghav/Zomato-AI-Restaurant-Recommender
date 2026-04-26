import os
from pathlib import Path
from typing import Dict

import streamlit as st
from dotenv import load_dotenv

from data_utils import filter_restaurants, load_and_prepare_data
from llm_utils import build_recommendation_prompt, call_llm_for_recommendations, fallback_recommendations
from phase0 import get_preflight_report, get_runtime_config

load_dotenv(dotenv_path=Path(__file__).with_name(".env"), override=True)

st.set_page_config(page_title="Zomato AI Recommender", page_icon="🍽️", layout="wide")


def apply_theme() -> None:
    # Reverted to previous dark Zomato-style visual system.
    bg = "#0f0f10"
    panel = "#17181b"
    text = "#f4f4f5"
    mutetext = "#b7b8bf"
    primary = "#ef4f5f"
    border = "#2a2a2e"
    success_bg = "#173d2a"
    success_text = "#8ef0b3"

    st.markdown(
        f"""
<style>
.stApp {{
    background: {bg};
    color: {text};
}}
.hero {{
    background: linear-gradient(120deg, {primary}, #ff7a6d);
    color: white;
    border-radius: 16px;
    padding: 18px 20px;
    margin-bottom: 16px;
}}
.hero-title {{
    font-size: 1.4rem;
    font-weight: 700;
    margin: 0;
}}
.hero-sub {{
    font-size: 0.95rem;
    margin-top: 6px;
    opacity: 0.95;
}}
.status-chip {{
    display: inline-block;
    padding: 8px 12px;
    border-radius: 999px;
    border: 1px solid {border};
    background: {panel};
    color: {text};
    font-size: 0.9rem;
    font-weight: 600;
    margin-bottom: 10px;
}}
.kpi {{
    background: {success_bg};
    color: {success_text};
    border: 1px solid transparent;
    border-radius: 12px;
    padding: 10px 14px;
    margin-bottom: 12px;
    font-weight: 600;
}}
.rec-card {{
    border: 1px solid {border};
    background: {panel};
    border-radius: 14px;
    padding: 14px 16px;
    margin-bottom: 12px;
}}
.rec-title {{
    color: {text};
    font-size: 1.1rem;
    font-weight: 700;
    margin-bottom: 8px;
}}
.rec-meta {{
    color: {mutetext};
    margin-bottom: 8px;
    font-size: 0.95rem;
}}
.rec-exp {{
    color: {text};
    font-size: 0.95rem;
}}
div[data-testid="stTextInput"] input, div[data-testid="stSelectbox"] div[data-baseweb="select"] > div {{
    border-radius: 10px !important;
}}
div.stButton > button {{
    background: {primary};
    color: #fff;
    border: none;
    border-radius: 10px;
    font-weight: 700;
}}
div.stButton > button:hover {{
    background: #d63f52;
    color: #fff;
}}
</style>
        """,
        unsafe_allow_html=True,
    )


def fmt_cost(value):
    if value is None:
        return "N/A"
    try:
        return f"Rs {int(float(value))}"
    except Exception:
        return str(value)


# Keep debug off in normal UI (no sidebar toggle).
show_debug = False

apply_theme()

st.markdown(
    """
<div class="hero">
  <p class="hero-title">Zomato AI Restaurant Recommender</p>
  <p class="hero-sub">Personalized picks by cuisine, budget, ratings, and preferences.</p>
</div>
""",
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner=True)
def get_data():
    return load_and_prepare_data(sample_limit=5000)


with st.spinner("Loading and preprocessing Zomato dataset..."):
    df, col_map = get_data()
runtime_config = get_runtime_config()
preflight = get_preflight_report(col_map=col_map, total_rows=len(df))

st.markdown(f'<div class="kpi">Loaded {len(df):,} restaurants.</div>', unsafe_allow_html=True)

if show_debug:
    st.write("Phase 0 Runtime")
    st.json(
        {
            "llm_provider": runtime_config.llm_provider,
            "llm_model": runtime_config.llm_model,
            "llm_key_present": runtime_config.llm_key_present,
            "schema_ok": preflight["schema_ok"],
        }
    )
    with st.expander("Detected dataset columns used"):
        st.json(col_map)

st.subheader("Your Preferences")

locations = sorted([loc for loc in df["location"].dropna().unique().tolist() if loc and loc != "Unknown"])

# Build cuisine catalog for type-ahead suggestions.
cuisine_catalog = sorted(
    {
        cuisine.strip()
        for raw in df["cuisines"].dropna().astype(str).tolist()
        for cuisine in raw.split(",")
        if cuisine.strip() and cuisine.strip().lower() != "unknown"
    }
)

typed_cuisine = st.text_input("Cuisine (e.g., Italian, Chinese, North Indian)", value="")
cuisine_hint = typed_cuisine.strip()

query = typed_cuisine.strip().lower()
if query:
    matched_cuisines = [c for c in cuisine_catalog if query in c.lower()][:15]
else:
    matched_cuisines = cuisine_catalog[:15]

if matched_cuisines and query:
    # Auto-detect closest cuisine from typed text, but keep user input if no good match.
    exact_match = next((c for c in matched_cuisines if c.lower() == query), None)
    if exact_match:
        cuisine_hint = exact_match
    else:
        cuisine_hint = matched_cuisines[0]

    preview = ", ".join(matched_cuisines[:5])
    st.caption(f"Detected cuisine: `{cuisine_hint}` | Matches: {preview}")
elif query:
    st.caption("No close cuisine suggestions found. Your typed value will be used.")

col1, col2, col3 = st.columns(3)
with col1:
    location = st.selectbox("Location", options=[""] + locations, index=0)
with col2:
    budget = st.selectbox("Budget", options=["any", "low", "medium", "high"], index=0)
with col3:
    min_rating = st.slider("Minimum rating", min_value=0.0, max_value=5.0, value=3.5, step=0.1)

extra_pref = st.text_input("Additional preference (optional)", value="", placeholder="family-friendly, quick service")
top_k = st.slider("How many recommendations?", min_value=3, max_value=10, value=5, step=1)

run_clicked = st.button("Generate AI Recommendations", type="primary")

if run_clicked:
    user_preferences: Dict[str, str] = {
        "location": location,
        "budget": budget,
        "cuisine": cuisine_hint,
        "min_rating": min_rating,
        "extra_preference": extra_pref,
    }

    filtered_df = filter_restaurants(
        df=df,
        location=location,
        budget=budget,
        cuisine=cuisine_hint,
        min_rating=min_rating,
        extra_preference=extra_pref,
        limit=30,
    )

    used_fallback = False
    fallback_note = ""
    if filtered_df.empty:
        # Progressive relaxation so users still get useful outputs if constraints are too strict
        # or if requested city is not represented in this dataset.
        fallback_variants = [
            ("Removed additional preference filter.", dict(extra_preference="")),
            ("Ignored budget filter for broader matching.", dict(extra_preference="", budget="any")),
            ("Ignored location and budget filters to find best cuisine/rating matches.", dict(location="", budget="any", extra_preference="")),
        ]
        for note, overrides in fallback_variants:
            trial_location = overrides.get("location", location)
            trial_budget = overrides.get("budget", budget)
            trial_extra = overrides.get("extra_preference", extra_pref)
            trial_df = filter_restaurants(
                df=df,
                location=trial_location,
                budget=trial_budget,
                cuisine=cuisine_hint,
                min_rating=min_rating,
                extra_preference=trial_extra,
                limit=30,
            )
            if not trial_df.empty:
                filtered_df = trial_df
                used_fallback = True
                fallback_note = note
                break

    llm_status = "Fallback mode"
    llm_reason = "No matching restaurants found."

    if filtered_df.empty:
        st.warning("No restaurants matched those filters. Try relaxing location/budget/rating constraints.")
    else:
        if used_fallback:
            st.info(
                f"No exact matches were found for all constraints. {fallback_note} "
                "Showing closest available matches from the dataset."
            )
        candidates = filtered_df.to_dict(orient="records")
        prompt = build_recommendation_prompt(user_preferences, candidates, top_k=top_k)

        if show_debug:
            with st.expander("Prompt sent to LLM"):
                st.code(prompt)

        try:
            if runtime_config.llm_key_present:
                with st.spinner("Asking the LLM to rank and explain recommendations..."):
                    result = call_llm_for_recommendations(
                        prompt,
                        model=runtime_config.llm_model,
                    )
                llm_status = "Gemini connected"
                llm_reason = "AI explanations are generated from Gemini."
            else:
                result = fallback_recommendations(candidates, top_k=top_k)
                llm_status = "Smart ranking mode"
                llm_reason = "Showing recommendations without AI explanations."
        except Exception as exc:
            err_text = str(exc)
            if show_debug:
                st.warning(f"LLM unavailable ({err_text}). Showing smart fallback ranking.")
            llm_status = "Smart ranking mode"
            llm_reason = "Gemini unavailable, fallback recommendations shown."
            result = fallback_recommendations(candidates, top_k=top_k)

        st.markdown(
            f'<div class="status-chip">LLM Status: {llm_status} - {llm_reason}</div>',
            unsafe_allow_html=True,
        )

        recommendations = result.get("recommendations", [])
        if not recommendations:
            st.error("No recommendations returned.")
        else:
            st.subheader("Top Recommendations")
            for idx, rec in enumerate(recommendations, start=1):
                st.markdown(
                    f"""
<div class="rec-card">
  <div class="rec-title">{idx}. {rec.get('name', 'Unknown')}</div>
  <div class="rec-meta">
    Cuisine: {rec.get('cuisine', 'Unknown')} | Rating: {rec.get('rating', 'N/A')} | Estimated Cost (for two): {fmt_cost(rec.get('estimated_cost_for_two'))}
  </div>
  <div class="rec-exp">{rec.get('explanation', 'No explanation provided.')}</div>
</div>
                    """,
                    unsafe_allow_html=True,
                )

            if show_debug:
                st.subheader("Filtered Candidate Restaurants (debug)")
                st.dataframe(
                    filtered_df[
                        ["name", "location", "cuisines", "rating", "cost_for_two", "budget_bucket", "highlights"]
                    ]
                )

st.markdown("---")
st.caption("Powered by Zomato-style smart restaurant matching.")
