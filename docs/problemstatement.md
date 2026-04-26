# Problem Statement: Zomato AI-Powered Restaurant Recommendation System

## Objective

Build an AI-assisted restaurant recommendation system that converts a simple user query into a high-quality shortlist of restaurants, each with clear reasoning.  
The product must combine deterministic filtering (objective constraints) with LLM reasoning (context-aware ranking and explanation).

## Why This Problem Matters

Food discovery platforms often overwhelm users with long, unprioritized lists.  
Users usually want a quick answer to: "Given my location, budget, and taste, where should I go right now?"

This project addresses that gap by delivering:
- concise and trustworthy top recommendations,
- transparent ranking logic,
- and natural-language explanations that are easy to understand.

## Target Users

- Individuals looking for immediate nearby dining options
- Families and groups balancing budget, cuisine, and quality
- Users who prefer curated shortlists over manual browsing

## Input Contract

The system accepts these user inputs:
- `location` (city/locality, e.g., Bellandur)
- `budget` (numeric value or bucket)
- `cuisine` (optional preference)
- `minimum_rating`
- `additional_preference` (optional, e.g., family-friendly, quick service)

In Phase 0, a **basic web UI** is the mandatory source of user input.

## Data Source

- Dataset: [ManikaSaini/zomato-restaurant-recommendation](https://huggingface.co/datasets/ManikaSaini/zomato-restaurant-recommendation)
- Access method: Hugging Face `datasets`
- Internal normalized schema:
  - `name`
  - `location`
  - `cuisines`
  - `cost_for_two`
  - `rating`
  - `highlights`
  - `budget_bucket`

## Functional Requirements

1. **Ingestion and normalization**
   - Load dataset with retries and caching
   - Auto-map schema variations
   - Parse dirty/mixed rating and cost formats

2. **Candidate selection**
   - Filter by location, budget, cuisine, and rating
   - Support progressive relaxation when no exact match exists

3. **Recommendation generation**
   - Send structured candidates + user preferences to an LLM
   - Return top-k ranked recommendations
   - Explain each recommendation in clear natural language

4. **Resilient fallback**
   - Provide deterministic recommendations when the LLM is unavailable
   - Avoid user-facing failures for key/network/service issues

5. **User output**
   - Display ranked results with name, cuisines, rating, estimated cost, and explanation
   - Indicate whether output came from LLM mode or fallback mode

## Non-Functional Requirements

- **Reliability:** The application should still work when API services fail.
- **Usability:** Input and output should be quick, clear, and beginner-friendly.
- **Resilience:** Handle missing keys, network failures, and sparse data gracefully.
- **Extensibility:** Support phased evolution into a production-ready full-stack system.

## Success Criteria

- Users receive useful top recommendations for most valid queries.
- LLM responses are grounded in candidate data and user preferences.
- Fallback mode remains useful and transparent when AI is unavailable.
- Architecture remains modular enough to scale phase by phase.
