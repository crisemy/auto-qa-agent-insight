# Project Roadmap & Execution Checklist

This tracking document outlines the step-by-step execution plan for building the **Auto-QA Agent Insights** framework.

## Phase 1: Foundations & Infrastructure (Week 1)

- [ ] Initialize Git repository and verify directory skeleton structure.
- [ ] Set up `pyproject.toml` with strict dependencies (`fastapi`, `pydantic`, `langchain-core`).
- [ ] Implement `app/config.py` using Pydantic Settings to handle environment variables safely.
- [ ] Design structural data contracts in `app/models.py` (schemas for raw bug logs, triage results, and diagnostics).
- [ ] Build a basic FastAPI entry point (`app/main.py`) with a `/health` check endpoint.

## Phase 2: Core Retrieval & Processing (Week 2)

- [ ] Create `app/services/query_rewriter.py` to strip PID/timestamp noise from raw logs using regex or minor LLM invocations.
- [ ] Build `app/components/hybrid_retriever.py` to simulate/execute keyword and vector matches against sample bug data.
- [ ] Implement `app/components/reranker.py` to prioritize retrieved code blocks/historical context.
- [ ] Write unit tests in `tests/test_retrieval.py` to ensure the retrieval pipeline meets accuracy criteria.

## Phase 3: Cognitive Layer & Security (Week 3)

- [ ] Write `app/security/input_guard.py` to detect and intercept prompt injection attempts in raw logs.
- [ ] Implement `app/security/output_filter.py` to ensure generated solutions don't hallucinate invalid structural formats.
- [ ] Develop individual agent runtimes under `app/agents/` based on contracts in `AGENTS.md`.
- [ ] Build `app/agents/tools/code_search.py` to allow agents to surgically scan line ranges of project files.
- [ ] Connect agents via an execution state machine or router (`app/services/query_router.py`).

## Phase 4: Observability, Evaluation & QA (Week 4)

- [ ] Build `app/observability/cost_tracker.py` to log exact token expenditure per run.
- [ ] Create `evaluation/golden_dataset.json` containing 10 curated pairs of raw bugs and correct diagnostics.
- [ ] Write `evaluation/offline_eval.py` to run the framework against the golden dataset and output deterministic accuracy scores.
- [ ] Complete the containerization layout using `Dockerfile` and `docker-compose.yml`.
- [ ] Finalize documentation and verify all tests pass in a clean environment.
