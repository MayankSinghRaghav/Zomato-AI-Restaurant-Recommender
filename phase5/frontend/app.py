import os
import requests
import streamlit as st

BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8080")

st.set_page_config(page_title="Zomato AI Recommendation", page_icon="🍽️", layout="centered", initial_sidebar_state="collapsed")

# Custom CSS for styling
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
    </style>
    """,
    unsafe_allow_html=True
)

# Custom top header
st.markdown(
    """
    <div style="position: fixed; top: 0; left: 0; width: 100%; height: 60px; background-color: white; z-index: 99999; display: flex; align-items: center; justify-content: center; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
        <span style="color: #e23744; font-size: 26px; font-weight: 900; font-family: sans-serif; font-style: italic;">zomato AI recommender</span>
    </div>
    """,
    unsafe_allow_html=True
)

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

col1, col2 = st.columns(2)

with col1:
    location = st.selectbox("Location", ["Brookefield", "Bellandur", "Koramangala", "Indiranagar", "Whitefield", "HSR Layout"])
    budget = st.text_input("Budget", value="2000")
    
with col2:
    cuisine = st.text_input("Cuisine", value="North Indian")
    minimum_rating = st.selectbox("⭐ Minimum rating", ["3.5+ stars", "4.0+ stars", "4.5+ stars"])

specific_cravings = st.text_input("Specific Cravings", value="Spicy")

st.markdown("<div style='font-size: 14px; font-weight: 600; color: #1c1c1c; margin-top: 15px;'>Additional preferences</div>", unsafe_allow_html=True)
st.markdown("<div style='font-size: 12px; color: #777; margin-bottom: 8px; line-height: 1.4;'>Dietary needs, vibe, occasion, dishes to avoid—anything that helps narrow picks. Combined with cravings and budget notes: up to 4,000 characters.</div>", unsafe_allow_html=True)
additional_preference = st.text_area("", placeholder="e.g., vegetarian only, quiet place for a date, no peanuts...", label_visibility="collapsed")

# Map rating dropdown to actual float
rating_map = {
    "3.5+ stars": 3.5,
    "4.0+ stars": 4.0,
    "4.5+ stars": 4.5
}

st.markdown("<br>", unsafe_allow_html=True)

if st.button("Find Restaurants", type="primary"):
    with st.spinner("Finding restaurants..."):
        payload = {
            "location": location.strip(),
            "budget": int(budget) if budget.isdigit() else 2000,
            "minimum_rating": rating_map.get(minimum_rating, 4.0),
            "cuisine": cuisine.strip(),
            "additional_preference": f"{specific_cravings}. {additional_preference}".strip(),
            "top_k": 5,
        }

        try:
            response = requests.post(f"{BACKEND_URL}/recommend", json=payload, timeout=90)
            response.raise_for_status()
            result = response.json()
            recommendations = result.get("recommendations", [])
            if not recommendations:
                st.warning("No recommendations returned.")
            else:
                st.markdown("### Top Recommendations")
                for idx, rec in enumerate(recommendations, start=1):
                    with st.container():
                        st.markdown(
                            f"**{idx}. {rec.get('name', 'Unknown')}**  \n"
                            f"Cuisine: {rec.get('cuisine', 'Unknown')} | "
                            f"Rating: ⭐ {rec.get('rating', 'N/A')} | "
                            f"Cost for two: ₹{rec.get('estimated_cost_for_two', 'N/A')}  \n"
                            f"{rec.get('explanation', '')}"
                        )
                        st.divider()
        except Exception as exc:
            st.error(f"Backend call failed: {exc}")
