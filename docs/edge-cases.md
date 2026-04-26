# Detailed Edge Cases

This list is derived from `problemstatement.md` and `phased-architecture.md`.

## 1) Phase 0 - Input UI and Runtime Config

- Web UI submits blank location and no optional filters; system must still return usable results.
- Numeric budget is entered as text (`"2k"`, `"2000rs"`, `"2,000"`); parsing must be tolerant.
- `.env` file exists but key names are wrong (`GROQ_KEY` instead of `GROQ_API_KEY`).
- API key values include quotes/spaces copied from docs and fail authentication.
- Runtime status leaks sensitive values in logs or UI (must only show key presence, never raw key).

## 2) Phase 1 - Data Download and Normalization

- Hugging Face transient failures: timeout, 429, or network disconnect during download.
- Dataset split names differ (`train` missing, alternate split available).
- Column schema drift (`Average Cost for two` renamed unexpectedly).
- Mixed rating/cost formats (`NEW`, `4.2/5`, `1,200 for two`) causing parse failures.
- Large duplicate clusters create biased recommendations if not deduplicated.

## 3) Phase 2 - Deterministic Filtering

- Location mismatch caused by spelling variants (`Bellandur` vs `Bellanduru`).
- Zero-match case with strict combinations (budget + cuisine + high rating).
- Restaurants with missing `cost_for_two` are excluded even when otherwise relevant.
- Cuisine filtering fails for multi-cuisine strings with separators and spacing noise.
- Relaxation sequence returns off-target restaurants without informing user what changed.

## 4) Phase 3 - Orchestration and Contracts

- Request payload misses required fields or has wrong types.
- Top-k requested exceeds available candidates.
- Pipeline partially fails (data load passes, filter fails) without clean error propagation.
- Logs are not correlated per request, making debugging hard.

## 5) Phase 4 - Groq LLM Integration

- `GROQ_API_KEY` missing or invalid.
- Model name is unsupported for selected endpoint.
- Groq returns markdown/plain text instead of strict JSON.
- Response JSON does not include `recommendations` key.
- Latency spikes produce timeout while deterministic fallback exists.
- Prompt includes too many candidates and exceeds token budget.

## 6) Phase 5 - Backend/Frontend Split

- Frontend and backend schemas drift (field names/types mismatch).
- CORS blocks frontend requests in local development.
- Backend URL/environment not configured in frontend.
- Frontend assumes LLM mode fields that fallback responses do not include.

## 7) Phase 5 - Full-Stack Runtime

- Backend starts but data artifact is missing; endpoint returns 500.
- Frontend submits valid request but error rendering hides backend message.
- Parallel user requests cause repeated expensive data loads without caching.
- Network failures between FE and BE leave stale loading state in UI.

## 8) Output Quality and Trust

- LLM recommendations ignore budget/rating constraints.
- Explanations are generic and not grounded in candidate metadata.
- Same restaurant appears multiple times under slightly different names.
- Users cannot distinguish LLM output from deterministic fallback mode.

## Mitigation Summary

- Strict input validation + tolerant parsing for UI values.
- Retry + split fallback + schema auto-mapping for ingestion.
- Deterministic relaxation strategy with explicit user messaging.
- JSON-first prompt contract with robust response parsing.
- Mandatory fallback ranking path for every LLM failure mode.
- Shared request/response schemas between frontend and backend.
