# Core: AI Engineering Best Practices & Framework Methodology

This document outlines the engineering principles required to design scalable, deterministic, and reliable AI frameworks. It moves past standard "prompt wrapping" into robust software engineering systems.

## 1. Context-Driven Development (CDD) Lifecycle

Always design systems in language-natural specifications before producing runtime code. The workflow must strictly follow:

1. **Define Intent (`CONTEXT.md`):** Clarify the business domain boundaries, definitions, and limitations.
2. **Define Personas (`AGENTS.md`):** Establish precise system roles, limiting scope to prevent single-agent complexity.
3. **Define Interfaces (`SKILLS.md`):** Lock down exact JSON data contracts (inputs and outputs) for tools.
4. **Implement Infrastructure (`.py`):** Write code purely to fulfill the contracts established in steps 1-3.

## 2. Token Efficiency & Context Window Hygiene

- **Never dump entire codebases or logs into an LLM context window.** It increases financial overhead, drives up latency, and triggers the "lost in the middle" retrieval phenomenon.
- **Implement Chunking and Reranking:** Always use keyword/vector retrieval combinations followed by a Cross-Encoder reranker to pass only the most contextually relevant tokens.
- **Surgical Tooling:** Build specific tools (e.g., file readers targeting exact lines rather than whole files).

## 3. Determinism Over Stochastic Chaos

LLMs are inherently non-deterministic. AI Engineering frameworks must wrap models in deterministic software constraints:

- **Structured Inputs/Outputs:** Utilize validation tools like Pydantic or Instructor to guarantee that data moving between services conforms to explicit code schemas. If a model fails a schema validation, intercept it programmatically before it cascades.
- **State Machines Over Autonomous Loops:** Do not allow LLMs to autonomously decide when to call loops endlessly. Manage system states and agent step-transfers via predictable Python logic.
- **Quality Gatekeeping (Graders):** Implement programmatic assertions or narrow binary LLM checkpoints to validate the quality of context data before letting a main agent synthesize answers.

## 4. The Golden Dataset Mandate

- You cannot improve what you do not measure. Prompt adjustments designed to fix one edge case frequently break three others.
- Maintain a static **Golden Dataset** representing production problems.
- Run evaluation scripts quantitatively before merging any prompt or code change to verify that accuracy, groundedness, and retrieval hit-rates remain stable or improve.
