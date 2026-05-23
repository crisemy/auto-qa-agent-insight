# Project Roadmap & Execution Checklist

This tracking document outlines the step-by-step execution plan for building the **Auto-QA Agent Insights** framework.

## Phase 1: Foundations & Infrastructure (Week 1)

- [x] Initialize Git repository and verify directory skeleton structure.
- [x] Set up `pyproject.toml` with strict dependencies (`fastapi`, `pydantic`, `langchain-core`).
- [x] Implement `app/config.py` using Pydantic Settings to handle environment variables safely.
- [x] Design structural data contracts in `app/models.py` (schemas for raw bug logs, triage results, and diagnostics).
- [x] Build a basic FastAPI entry point (`app/main.py`) with a `/health` check endpoint.

## Phase 2: Core Retrieval & Processing (Week 2)

- [x] Create `app/services/query_rewriter.py` to strip PID/timestamp noise from raw logs using regex or minor LLM invocations.
- [x] Build `app/components/hybrid_retriever.py` to simulate/execute keyword and vector matches against sample bug data.
- [x] Implement `app/components/reranker.py` to prioritize retrieved code blocks/historical context.
- [x] Write unit tests in `tests/test_retrieval.py` to ensure the retrieval pipeline meets accuracy criteria.

## Phase 3: Cognitive Layer & Security (Week 3)

- [x] Write `app/security/input_guard.py` to detect and intercept prompt injection attempts in raw logs.
- [x] Implement `app/security/output_filter.py` to ensure generated solutions don't hallucinate invalid structural formats.
- [x] Develop individual agent runtimes under `app/agents/` based on contracts in `AGENTS.md`.
- [x] Build `app/agents/tools/code_search.py` to allow agents to surgically scan line ranges of project files.
- [x] Connect agents via an execution state machine or router (`app/services/query_router.py`).

## Phase 4: Observability, Evaluation & QA (Week 4)

- [x] Build `app/observability/cost_tracker.py` to log exact token expenditure per run.
- [x] Create `evaluation/golden_dataset.json` containing 10 curated pairs of raw bugs and correct diagnostics.
- [x] Write `evaluation/offline_eval.py` to run the framework against the golden dataset and output deterministic accuracy scores.
- [x] Complete the containerization layout using `Dockerfile` and `docker-compose.yml`.
- [x] Finalize documentation and verify all tests pass in a clean environment.

## Phase 5: Production Hardening & Real Infrastructure (Week 5–6)

Goal: Replace all stubs and simulated components with real infrastructure — vector database, live LLM inference, persistent caching, and CI/CD pipelines.

### Task 5.1 — FAISS Vector Store for Historical Bug Embeddings

- [ ] Add `sentence-transformers` and `faiss-cpu` to `pyproject.toml`.
- [ ] Implement `app/components/vector_store.py` with functions:
  - `index_bugs(bugs: list[dict])` — embeds bug signatures and stores in FAISS index.
  - `search(query: str, k: int) -> list[str]` — returns top-k similar bug IDs.
- [ ] Seed the index with the 10 golden dataset entries on startup.
- [ ] Replace in-memory search in `hybrid_retriever.py` with real FAISS vector search + BM25 keyword fallback.
- [ ] Write tests in `tests/test_vector_store.py`.

### Task 5.2 — Live LLM Agent Inference

- [ ] Add `openai` client to `app/services/llm_client.py` — reads `OPENAI_API_KEY` and `LLM_MODEL` from config.
- [ ] Rewrite `grader_agent.py` to call the LLM with the agent's system prompt (from `AGENTS.md`) and the triage+RCA context, returning a relevance score via structured output.
- [ ] Rewrite `remediation_agent.py` to call the LLM with the RCA diagnosis to generate a contextual code patch instead of the current template patch.
- [ ] Implement `app/agents/tools/prompt_templates.py` to store all agent system prompts as constants (mirroring AGENTS.md verbatim).
- [ ] Wire cost tracking into every LLM call using `app/observability/cost_tracker.py`.

### Task 5.3 — Persistent Semantic Cache

- [ ] Replace the stub `semantic_cache.py` with a real Redis-backed cache (using `redis-py`).
- [ ] On cache write: store normalized_signature → full EnrichedInsightReport with a 24-hour TTL.
- [ ] On cache read: compute vector distance between incoming signature and cached keys; return report if distance < threshold.
- [ ] Fall back to `CONTINUE_WITHOUT_CONTEXT` if Redis is unreachable (SKILLS.md §4).

### Task 5.4 — CI/CD Pipeline

- [ ] Create `.github/workflows/ci.yml` with jobs: lint (`ruff`), typecheck (`mypy`), test (`pytest`), evaluate (`offline_eval.py` — fail if < 100%).
- [ ] Create `.github/workflows/publish.yml` to build and publish to PyPI on tagged releases.

### Task 5.5 — API Endpoints for Direct Submission

- [ ] Add `POST /analyze` endpoint in `app/main.py` that accepts a raw bug report and returns `EnrichedInsightReport`.
- [ ] Add `GET /history?limit=20` to return recent cached analyses.
- [ ] Wire cost tracker to log every `/analyze` request.
- [ ] Write integration tests in `tests/test_api.py`.

## Definition of Done (DoD) per Task

For any task in this document to be marked as complete, it must meet the following criteria:

* Linting & Code Quality: Code complies with clean architectural standards, passes static analysis checking, and includes descriptive type hinting.
* Robust Exception Coverage: Network failures, bad authentication, and rate exhaustion scenarios are explicitly accounted for and gracefully handled without throwing an unhandled trace dump.
* No Hardcoded Configurations: All structural endpoint variations must reside entirely inside environment configurations or decoupled static resource JSON registries.
