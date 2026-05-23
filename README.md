# Auto-QA Agent Insights

An enterprise-grade, production-ready AI Engineering framework designed to automate software bug triage, root-cause analysis (RCA), and remediation proposals using Context-Driven Architecture.

## System Architecture Overview

The framework avoids fragile, unstructured conversational loops by implementing a deterministic, sequential multi-agent processing pipeline protected by security and quality guardrails.

```text
 [Raw Bug Report] -> [Input Guard] -> [Query Rewriter] -> [Hybrid Search + Rerank]
                                                                  │
 [Enriched Report] <- [Output Filter] <- [Document Grader] <- [Code Forensics Agent]
 ```

## Key Architectural Pillars

* Context-Driven Design: The system's rules, agents, and tool signatures are explicitly declared in Markdown specifications (CONTEXT.md, AGENTS.md, SKILLS.md) before implementation, ensuring high alignment and minimal token waste.
* Surgical Code Forensics: Rather than saturating context windows with whole source files, specialized tools target exact line ranges extracted from stack traces.
* Deterministic Quality Gates: An internal Document Grader evaluates context relevance before generation, applying a hard circuit-breaker to prevent LLM hallucinations.
* Enterprise Security & Observability: Out-of-the-box input/output sanitization filters combined with dynamic token cost-tracking per evaluation cycle.

## Project Structure

```text
production-ai-app/
├── app/
│   ├── main.py                 # FastAPI entry point
│   ├── config.py               # Pydantic environment configuration
│   ├── models.py               # Strict Pydantic data schemas
│   ├── components/             # Retrieval & optimization layers (Retriever, Reranker)
│   ├── services/               # Core workflow logic (Query routing, semantic cache)
│   ├── agents/                 # Specialized agent personas and micro-tools
│   └── security/               # Ingress/egress guardrails (Prompt injection defense)
├── evaluation/                 # Testing datasets and offline metric evaluators
├── observability/              # Token monitoring, cost logging, and tracing
├── data/                       # Local vector indexes and raw/processed assets
└── tests/                      # Pytest automation suite for CI/CD readiness
```

## Prerequisites & Installation

Technical Stack

* Runtime: Python >= 3.11
* Frameworks: FastAPI, Pydantic v2, Pydantic Settings
* Orchestration: LangChain Core (Type-Safe Interface Structural Design)
* Vector Vector Space: Local FAISS / Numpy (for portfolio portability)

### Local Deployment

* Clone the repository:

```bash
git clone [https://github.com/your-username/auto-qa-agent-insights.git](https://github.com/your-username/auto-qa-agent-insights.git)
cd auto-qa-agent-insights
```

* Install dependencies using modern build system conventions:

```bash
pip install .
# For development dependencies (testing, linting)
pip install -e ".[dev]"
```

* Configure environment variables:
Create a .env file in the root directory:

```bash
ENVIRONMENT=development
OPENAI_API_KEY=your_actual_api_key_here
LLM_MODEL=gpt-4o-mini
```

* Execute the application service:

```bash
uvicorn app.main:app --reload
```

## Testing & Evaluation Pipeline

* Running Unit Tests:

```bash
pytest tests/
```

* Executing Offline AI Evaluation
To measure the semantic accuracy of the system against a static, human-curated benchmark:

```bash
python scripts/evaluate.py
```
