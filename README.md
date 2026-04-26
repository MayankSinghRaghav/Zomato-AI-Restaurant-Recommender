# Zomato AI-Powered Restaurant Recommendation System

This project implements an AI-powered restaurant recommender for a Zomato use case.

It:
- Loads and preprocesses a real dataset from Hugging Face: `ManikaSaini/zomato-restaurant-recommendation`
- Collects user preferences (location, budget, cuisine, min rating, extra preference)
- Filters candidate restaurants
- Sends structured candidates into an LLM prompt
- Returns ranked recommendations with explanations
- Displays results in a user-friendly Streamlit app

## Tech stack

- Python
- Streamlit (UI)
- Hugging Face `datasets` (ingestion)
- Pandas (preprocessing/filtering)
- Google Gemini API (LLM layer via `requests`)

## Setup

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Add environment variables:

```bash
copy .env.example .env
```

Then set at least:
- `GEMINI_API_KEY=...`

Optional:
- `GEMINI_BASE_URL=https://generativelanguage.googleapis.com`
- `GEMINI_MODEL=gemini-1.5-flash`

## Run

```bash
streamlit run app.py
```

## Workflow mapping

### 1) Data ingestion
- Implemented in `data_utils.py` via `load_and_prepare_data()`
- Auto-detects likely columns and normalizes to:
  - `name`
  - `location`
  - `cuisines`
  - `cost_for_two`
  - `rating`
  - `highlights`
  - `budget_bucket`

### 2) User input
- Implemented in `app.py`
- Captures:
  - location
  - budget
  - cuisine
  - minimum rating
  - additional preference

### 3) Integration layer
- `filter_restaurants()` in `data_utils.py` performs deterministic filtering.
- `build_recommendation_prompt()` in `llm_utils.py` transforms filtered rows into a structured prompt.

### 4) Recommendation engine
- `call_llm_for_recommendations()` calls Gemini and expects JSON output.
- `fallback_recommendations()` provides ranked non-LLM output if API key/service is unavailable.

### 5) Output display
- `app.py` renders:
  - Restaurant Name
  - Cuisine
  - Rating
  - Estimated Cost
  - AI explanation
- Also includes filtered candidates table for transparency.

## Notes

- The app samples up to 5,000 rows by default for responsiveness.
- If the dataset schema changes, column auto-detection still attempts to map required fields.
