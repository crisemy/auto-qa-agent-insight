# Context: Auto-QA Agent Insights

## 1. System Purpose

The system is an AI Engineering ecosystem and agentic framework designed to automate the triage, analysis, and root-cause diagnosis of software bug reports. Its primary goal is to transform "raw" input (noisy, incomplete, or highly technical log dumps) into actionable engineering insights, drastically reducing Mean Time to Resolution (MTTR) and preventing duplicate debugging efforts.

## 2. Problem Domain & Use Cases

In continuous deployment and robust QA environments, failure reports enter the pipeline via heterogeneous channels. The system must address three core operational workflows:

- **Triage & Indexing:** Automatically determine severity, classify the affected sub-system, and check if a similar issue was previously indexed in the historical knowledge base.
- **Root-Cause Analysis (RCA):** Correlate the bug report with the current source code architecture to pinpoint the exact function, class, or module causing the regression.
- **Remediation Proposal:** Generate a comprehensive technical diagnostic accompanied by a safe code patch or refactoring suggestion.

## 3. Information Flow & Cognitive Boundaries

The processing of any incoming bug report follows a strict, validated, and sequential pipeline:

```text
 [Raw Bug Report] 
         │
         ▼
 ┌───────────────┐      ┌─────────────────┐
 │ Input Guard   │ ───> │ Query Rewriter  │
 └───────────────┐      └─────────────────┘
                                 │
                                 ▼
                        ┌─────────────────┐      ┌─────────────────┐
                        │ Hybrid Search   │ <──> │ Vector DB / Logs│
                        └─────────────────┘      └─────────────────┘
                                 │
                                 ▼
                        ┌─────────────────┐      ┌─────────────────┐
                        │ Code Analyzer   │ <──> │ Code Repository │
                        └─────────────────┘      └─────────────────┘
                                 │
                                 ▼
 ┌───────────────┐      ┌─────────────────┐
 │ Output Filter │ <──> │ Document Grader │
 └───────────────┘      └─────────────────┘
         │
         ▼
 [Enriched Insight Report]
```

a. **Ingress & Sanitization**: The raw report passes through input guards to prevent prompt injections and infrastructure data leaks.

b. **Norm**alization: The query is rewritten to strip out irrelevant technical noise and optimize semantic vector search matching.

c. **External Retrieval (RAG)**: The system queries historical bug records, closed issues, and deployment metadata.

d. **Code Inspection**: The agent accesses the source code repository, surgically scoping down its visibility to the files relevant to the error stack trace.

e. **Context Qualification**: The context is validated for accuracy and relevance before generating the final engineer-facing assessment.

## 4. Project Glossary

- **Raw Bug Report**: Unstructured text payloads originating from Jenkins/GitHub Actions logs, Jira tickets, GitHub Issues, or raw stack traces.

- **Golden Dataset**: A curated, human-verified static testing dataset containing historical pairs of (Bug -> Correct Diagnostic). Used for quantitative offline evaluation of the AI pipeline.

- **Semantic Cache**: An optimization layer that stores previously resolved inquiries based on semantic meaning rather than exact string matching, minimizing latency and LLM token usage.

- **Document Grader**: A logical orchestration component that acts as a quality control gate, scoring the relevance of retrieved code fragments or historical docs against the core problem.

## 5. Success Criteria & Constraints

- **Evaluation Determinism**: System modifications must be quantitatively evaluated. No architectural or prompt change will be merged without passing the evaluation pipeline against the Golden Dataset.

- **Context Window Management**: No agent may saturate the LLM context window with entire codebases; code retrieval must be highly targeted and paginated.

- **Security by Design**: The system will operate strictly as an analytical advisor. It will not execute native shell code or push direct commits to the main branch without Human-in-the-Loop (HITL) approval.
