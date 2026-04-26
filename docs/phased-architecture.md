# Phase-Wise Architecture

This document defines the delivery roadmap for the Zomato AI-powered recommendation platform.

## Phase 0: Input Foundation (Basic Web UI + Runtime Guardrails)

### Goal
Establish the baseline user input flow and runtime safety checks.

### Scope
- Basic web UI as the single source of user input
- Environment loading and validation
- Runtime diagnostics (key presence, model/provider readiness)
- Non-blocking operation if LLM key is missing

### Deliverables
- `phase0/` module for web input capture and runtime checks
- `.env` support and config bootstrap
- Clear "LLM enabled/disabled" status for debugging

---

## Phase 1: Data Ingestion and Persistence

### Goal
Download and normalize restaurant data from Hugging Face into local storage.

### Scope
- Resilient dataset download with retries
- Schema normalization and type cleaning
- Save normalized data into local artifacts (`csv` / `json`)

### Deliverables
- `phase1/` data pipeline scripts
- Download command that materializes local data files

---

## Phase 2: Deterministic Recommendation Engine

### Goal
Build a dependable filter-and-rank engine before LLM involvement.

### Scope
- Deterministic filtering using location, budget, cuisine, rating
- Progressive relaxation strategy for zero-match scenarios
- Top-k candidate selection contract

### Deliverables
- `phase2/` recommendation core
- Reusable filtering and ranking functions

---

## Phase 3: Orchestration Layer

### Goal
Connect input, data, and deterministic engine into a callable application workflow.

### Scope
- Pipeline orchestration (load -> filter -> package candidates)
- Request/response schema standardization
- Better traceability and operational logs

### Deliverables
- `phase3/` orchestration module
- CLI or service entrypoint for end-to-end deterministic flow

---

## Phase 4: LLM Ranking Layer (Groq)

### Goal
Use Groq-hosted LLM models to produce top recommendations with explanations.

### Scope
- Groq API integration and prompt contract
- Parse structured JSON responses
- Deterministic fallback if Groq is unavailable
- Live query execution for user scenarios

### Deliverables
- `phase4/` Groq client + prompt builder + fallback layer
- Executable script to fetch top-5 recommendations from Groq

---

## Phase 5: Product Split (Backend + Frontend Architecture)

### Goal
Evolve from a single-app flow into proper backend and frontend boundaries.

### Scope
- Backend API (recommendation endpoint, health endpoint)
- Frontend app consuming backend APIs
- Shared request/response contracts and validation
- API-key handling isolated to backend only

### Deliverables
- Updated architecture with clear FE/BE separation
- Service contracts ready for implementation

---

## Phase 6: Full-Stack Implementation

### Goal
Implement the phase-5 architecture with working backend and frontend modules.

### Scope
- Backend server exposing recommendation APIs
- Frontend web app submitting inputs and rendering top results
- Integrated execution path from UI to Groq-backed recommendations

### Deliverables
- `phase6/backend/` implementation
- `phase6/frontend/` implementation
- End-to-end run instructions

---

## Architecture Flow (After Phase 6)

1. **Frontend UI** captures user preferences  
2. **Backend API** validates and orchestrates query execution  
3. **Data Layer** loads normalized candidate restaurants  
4. **Deterministic Engine** performs constraint filtering and relaxation  
5. **Groq LLM Layer** ranks top-k and generates explanations  
6. **Fallback Engine** returns deterministic output on LLM failure  
7. **Frontend Presentation** renders final ranked recommendations with mode status  
