import os
from pathlib import Path
from typing import Dict

import streamlit as st
from dotenv import load_dotenv

from data_utils import filter_restaurants, load_and_prepare_data
from llm_utils import build_recommendation_prompt, call_llm_for_recommendations, fallback_recommendations
from phase0 import get_preflight_report, get_runtime_config

load_dotenv(dotenv_path=Path(__file__).with_name(".env"), override=True)

st.set_page_config(page_title="Zomato AI Recommender", page_icon="🍽️", layout="centered", initial_sidebar_state="collapsed")


def apply_theme() -> None:
    st.markdown(
        """
        <style>
        /* Full page background */
        .stApp {
            background-image: linear-gradient(rgba(226, 55, 68, 0.75), rgba(0, 0, 0, 0.8)), url("https://images.unsplash.com/photo-1555939594-58d7cb561ad1?ixlib=rb-4.0.3&auto=format&fit=crop&w=1920&q=80");
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        }

        /* Hide default header */
        header {visibility: hidden;}

        /* White card container */
        .block-container {
            background-color: white;
            padding: 3rem 2.5rem 2rem 2.5rem !important;
            border-radius: 15px;
            box-shadow: 0 10px 20px rgba(0,0,0,0.2);
            max-width: 650px;
            margin-top: 80px;
            margin-bottom: 50px;
        }

        /* Input styling */
        .stTextInput>div>div>input, 
        .stNumberInput>div>div>input,
        .stTextArea>div>div>textarea {
            background-color: #f4f6f8;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            color: #333;
        }

        /* Labels */
        .stTextInput label, .stNumberInput label, .stSelectbox label, .stTextArea label, .stSlider label {
            font-weight: 600 !important;
            color: #1c1c1c !important;
            font-size: 0.85rem !important;
            margin-bottom: 0.25rem;
        }

        /* Primary button */
        .stButton>button {
            background-color: #e23744;
            color: white;
            width: 100%;
            border-radius: 8px;
            padding: 0.75rem 1rem;
            font-weight: 600;
            border: none;
            font-size: 1.1rem;
            transition: all 0.2s ease;
        }
        .stButton>button:hover {
            background-color: #cb202d;
            color: white;
            box-shadow: 0 4px 8px rgba(226, 55, 68, 0.3);
        }
        
        /* Tag styling */
        .tag-text {
            border: 1px solid #e0e0e0;
            border-radius: 20px;
            padding: 6px 16px;
            font-size: 13px;
            color: #555;
            margin: 0 6px;
            display: inline-block;
            background-color: white;
            font-weight: 500;
        }

        /* Recommendation display styling */
        .rec-card {
            border-bottom: 1px solid #e0e0e0;
            padding: 14px 0px;
            margin-bottom: 12px;
        }
        .rec-title {
            color: #1c1c1c;
            font-size: 1.1rem;
            font-weight: 700;
            margin-bottom: 4px;
        }
        .rec-meta {
            color: #555;
            margin-bottom: 8px;
            font-size: 0.9rem;
        }
        .rec-exp {
            color: #333;
            font-size: 0.95rem;
        }
        .status-chip {
            display: inline-block;
            padding: 8px 12px;
            border-radius: 8px;
            background: #f8f9fa;
            color: #555;
            font-size: 0.85rem;
            margin-bottom: 15px;
            border: 1px solid #e0e0e0;
        }
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

# Custom top header
st.markdown(
    """
    <div style="position: fixed; top: 0; left: 0; width: 100%; height: 60px; background-color: white; z-index: 99999; display: flex; align-items: center; justify-content: center; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
        <span style="color: #e23744; font-size: 26px; font-weight: 900; font-family: sans-serif; font-style: italic;">zomato AI recommender</span>
    </div>
    """,
    unsafe_allow_html=True
)

@st.cache_data(show_spinner=True)
def get_data():
    return load_and_prepare_data(sample_limit=5000)

df, col_map = get_data()
runtime_config = get_runtime_config()
preflight = get_preflight_report(col_map=col_map, total_rows=len(df))

# Title
st.markdown("<h2 style='text-align: center; color: #1c1c1c; font-size: 24px; font-weight: 700; margin-bottom: 15px;'>Find Your Perfect Meal with Zomato AI</h2>", unsafe_allow_html=True)

# Tags
st.markdown(
    """
    <div style='text-align: center; margin-bottom: 25px;'>
        <span class='tag-text'>Italian</span>
        <span class='tag-text'>Spicy</span>
        <span class='tag-text'>Dessert</span>
    </div>
    """,
    unsafe_allow_html=True
)

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

col1, col2 = st.columns(2)
with col1:
    location = st.selectbox("Location", options=[""] + locations, index=0)
    budget = st.selectbox("Budget", options=["any", "low", "medium", "high"], index=0)

with col2:
    typed_cuisine = st.text_input("Cuisine", value="North Indian")
    min_rating_str = st.selectbox("⭐ Minimum rating", ["3.5+ stars", "4.0+ stars", "4.5+ stars"])

specific_cravings = st.text_input("Specific Cravings", value="Spicy")

st.markdown("<div style='font-size: 14px; font-weight: 600; color: #1c1c1c; margin-top: 15px;'>Additional preferences</div>", unsafe_allow_html=True)
st.markdown("<div style='font-size: 12px; color: #777; margin-bottom: 8px; line-height: 1.4;'>Dietary needs, vibe, occasion, dishes to avoid—anything that helps narrow picks. Combined with cravings and budget notes: up to 4,000 characters.</div>", unsafe_allow_html=True)
extra_pref = st.text_area("", placeholder="e.g., vegetarian only, quiet place for a date, no peanuts...", label_visibility="collapsed")

rating_map = {"3.5+ stars": 3.5, "4.0+ stars": 4.0, "4.5+ stars": 4.5}
min_rating = rating_map.get(min_rating_str, 3.5)

cuisine_hint = typed_cuisine.strip()
query = typed_cuisine.strip().lower()
if query:
    matched_cuisines = [c for c in cuisine_catalog if query in c.lower()][:15]
    if matched_cuisines:
        exact_match = next((c for c in matched_cuisines if c.lower() == query), None)
        if exact_match:
            cuisine_hint = exact_match
        else:
            cuisine_hint = matched_cuisines[0]

st.markdown("<br>", unsafe_allow_html=True)
run_clicked = st.button("Find Restaurants", type="primary")

if run_clicked:
    # Combine cravings with extra preference
    combined_preference = f"{specific_cravings}. {extra_pref}".strip()
    if combined_preference == ".":
        combined_preference = ""

    user_preferences: Dict[str, str] = {
        "location": location,
        "budget": budget,
        "cuisine": cuisine_hint,
        "min_rating": min_rating,
        "extra_preference": combined_preference,
    }

    filtered_df = filter_restaurants(
        df=df,
        location=location,
        budget=budget,
        cuisine=cuisine_hint,
        min_rating=min_rating,
        extra_preference=combined_preference,
        limit=30,
    )

    used_fallback = False
    fallback_note = ""
    if filtered_df.empty:
        fallback_variants = [
            ("Removed additional preference filter.", dict(extra_preference="")),
            ("Ignored budget filter for broader matching.", dict(extra_preference="", budget="any")),
            ("Ignored location and budget filters to find best cuisine/rating matches.", dict(location="", budget="any", extra_preference="")),
        ]
        for note, overrides in fallback_variants:
            trial_location = overrides.get("location", location)
            trial_budget = overrides.get("budget", budget)
            trial_extra = overrides.get("extra_preference", combined_preference)
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
        prompt = build_recommendation_prompt(user_preferences, candidates, top_k=5)

        try:
            if runtime_config.llm_key_present:
                with st.spinner("Finding restaurants..."):
                    result = call_llm_for_recommendations(
                        prompt,
                        model=runtime_config.llm_model,
                    )
                llm_status = "Gemini connected"
                llm_reason = "AI explanations are generated from Gemini."
            else:
                with st.spinner("Finding restaurants..."):
                    result = fallback_recommendations(candidates, top_k=5)
                llm_status = "Smart ranking mode"
                llm_reason = "Showing recommendations without AI explanations."
        except Exception as exc:
            err_text = str(exc)
            llm_status = "Smart ranking mode"
            llm_reason = "Gemini unavailable, fallback recommendations shown."
            result = fallback_recommendations(candidates, top_k=5)

        # Hide the LLM info status chip as requested
        # st.markdown(
        #     f'<div class="status-chip">ℹ️ {llm_status} - {llm_reason}</div>',
        #     unsafe_allow_html=True,
        # )

        recommendations = result.get("recommendations", [])
        if not recommendations:
            st.error("No recommendations returned.")
        else:
            st.markdown("### Top Recommendations")
            for idx, rec in enumerate(recommendations, start=1):
                st.markdown(
                    f"""
<div class="rec-card">
  <div class="rec-title">{idx}. {rec.get('name', 'Unknown')}</div>
  <div class="rec-meta">
    Cuisine: {rec.get('cuisine', 'Unknown')} | ⭐ {rec.get('rating', 'N/A')} | Estimated Cost: {fmt_cost(rec.get('estimated_cost_for_two'))}
  </div>
  <div class="rec-exp">{rec.get('explanation', 'No explanation provided.')}</div>
</div>
                    """,
                    unsafe_allow_html=True,
                )
