import os

import requests
import streamlit as st

BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8080")

st.set_page_config(page_title="Zomato AI FE", page_icon="🍽️", layout="centered")
st.title("Phase 6 Frontend")
st.caption("Frontend app connected to backend recommendation API.")

location = st.text_input("Location", value="Bellandur")
budget = st.number_input("Budget for two (INR)", min_value=100, max_value=10000, value=2000, step=100)
minimum_rating = st.slider("Minimum rating", min_value=0.0, max_value=5.0, value=4.0, step=0.1)
cuisine = st.text_input("Cuisine (optional)", value="")
additional_preference = st.text_input("Additional preference (optional)", value="")
top_k = st.slider("Top recommendations", min_value=1, max_value=10, value=5, step=1)

if st.button("Get Recommendations", type="primary"):
    payload = {
        "location": location.strip(),
        "budget": int(budget),
        "minimum_rating": float(minimum_rating),
        "cuisine": cuisine.strip(),
        "additional_preference": additional_preference.strip(),
        "top_k": int(top_k),
    }

    try:
        response = requests.post(f"{BACKEND_URL}/recommend", json=payload, timeout=90)
        response.raise_for_status()
        result = response.json()
        recommendations = result.get("recommendations", [])
        if not recommendations:
            st.warning("No recommendations returned.")
        else:
            for idx, rec in enumerate(recommendations, start=1):
                st.markdown(
                    f"**{idx}. {rec.get('name', 'Unknown')}**  \n"
                    f"Cuisine: {rec.get('cuisine', 'Unknown')} | "
                    f"Rating: {rec.get('rating', 'N/A')} | "
                    f"Cost for two: {rec.get('estimated_cost_for_two', 'N/A')}  \n"
                    f"{rec.get('explanation', '')}"
                )
    except Exception as exc:
        st.error(f"Backend call failed: {exc}")
