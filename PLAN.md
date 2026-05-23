# Free-LLM Failover Routing Framework

This document outlines the iterative development lifecycle for creating free-llm, an intelligent, CLI-driven routing framework that dynamically distributes LLM requests across zero-cost providers and implements automatic, context-aware failover handling.

## Project Vision

To eliminate the fragility of free-tier AI development by providing an elegant CLI interface and unified abstraction layer that seamlessly masks rate limits (429), server timeouts, and API disruptions via a high-availability fallback queue.

## Development Iterations at a Glance

| Iteration | Focus | Core Deliverable |
| ----------- | ------- | ----------------- |
| Iteration 1 | Foundation & Unified Interface | JSON Provider Registry & Core Failover Client Engine |
| Iteration 2 | CLI Layer & Interactive UX | Interactive free-llm CLI with Priority Stack configuration |
| Iteration 3 | Resilience & State Management | Circuit Breaker Pattern & Cool-down Quarantine Engine |
| Iteration 4 | Performance & Analytics | Benchmarking Engine (free-llm bench) & Context Optimization |
| Iteration 5 | Distribution & Packaging | PyPI Packaging, GitHub Actions CI/CD setup, & Extension Guide |

## Detailed Breakdown & Tasks

Goal: Establish the underlying abstraction layer capable of standardizing different OpenAI-compatible endpoints and implementing basic try/except fallback logic.

[ ] Task 1.1: Design Structured Configuration Schema

* Create providers.json or a YAML registry specifying properties for each free provider: name, base_url, model_alias, env_token_key, max_context_window, and tier.

[ ] Task 1.2: Build Abstract Provider Wrapper

* Initialize standard openai.OpenAI clients dynamically injecting values from the registry.
* Standardize common exceptions (openai.RateLimitError, openai.APIConnectionError, openai.APIStatusError) into unified framework-level exceptions.

[ ] Task 1.3: Implement Linear Fallback Router Loop

* Write the primary request router logic that iterates over a queue of active providers.
* Ensure that if a provider fails, the current index increments, the payload is transparently retried on the next node, and the failed provider is rotated to the back of the queue.

## Iteration 2: CLI Layer & Interactive UX

Goal: Expose the internal routing capabilities through an intuitive, interactive command-line experience.

[ ] Task 2.1: Establish CLI Command Structure

* Implement a command-line interface parser (using argparse, click, or typer) recognizing commands like free-llm run, free-llm config, and free-llm status.

[ ] Task 2.2: Add Interactive Stack Selector

* Integrate a rich terminal interface library (like inquirer or questionary) allowing the user to view the top 5 working providers, select which ones to use, and reorder their fallback priority interactively.

[ ] Task 2.3: Visual Request Stream Logger

* Incorporate status indicators (like rich or halo) to show live terminal updates during execution (e.g., 🔄 Connecting to Groq... Rate limited! 🔄 Switching to TogetherAI... Success!).

## Iteration 3: Resilience & State Management

Goal: Transition the framework from a naive execution loop to an enterprise-grade resilient routing engine by introducing memory states.

[ ] Task 3.1: Implement Circuit Breaker & Quarantine Memory

* Create an ephemeral cache or file-backed state to store failed nodes.
* If a provider throws a 429 RateLimitError, place that provider in a "Quarantine" state with an explicitly stamped cool-down timestamp (e.g., 5 minutes). Ensure subsequent API calls skip this node entirely until the timer expires.

[ ] Task 3.2: Concurrent Smart Retries with Exponential Backoff

* For transient errors (such as 503 Service Unavailable or temporary network glitches), execute up to 2 rapid localized retries with jitter before entirely abandoning the node and rolling over to the next provider.

## Iteration 4: Performance & Analytics

Goal: Provide data-driven priority sorting based on real-time endpoint latency and optimize conversational memory constraints.

[ ] Task 4.1: Develop Live Benchmarking Utility (free-llm bench)

* Write a background routing script that issues a lightweight, standardized 5-token query to all currently configured active endpoints.
* Measure Time-To-First-Token (TTFT) and success rates, then dynamically generate a leaderboard in the terminal and reorder the default entry list inside providers.json using the fastest nodes.

[ ] Task 4.2: Adaptive Context Window Compression

* When a fallback event switches mid-conversation to a provider with a smaller context window limit (e.g., swapping from a 128k context model to an 8k model), execute a running calculation of the rolling array conversation tokens.
* Implement an adaptive trimmer to gracefully compact or summarize early historical system items to fit within the fallback node's specific max_context_window.

## Iteration 5: Distribution & Packaging

Goal: Polish the code base, prepare documentation, and package the framework for seamless integration across global codebases.

[ ] Task 5.1: Package and Publish to PyPI

* Write a complete pyproject.toml or setup.py module configuration.
* Expose the framework as a globally executable system binary so developers can call free-llm natively from anywhere within their local terminal space.

[ ] Task 5.2: CI/CD Pipeline Configuration

* Establish a GitHub Actions linting workflow executing automated testing sequences across multiple Python runtimes (3.9 through 3.12).

[ ] Task 5.3: Documentation & Extension Architecture

* Finalize a comprehensive README.md instructing other developers how to import the module as a native Python library dependency to guard their internal automation scripts and test suites against external API failures.

## Definition of Done (DoD) per Task

For any task in this document to be marked as complete, it must meet the following criteria:

* Linting & Code Quality: Code complies with clean architectural standards, passes static analysis checking, and includes descriptive type hinting.
* Robust Exception Coverage: Network failures, bad authentication, and rate exhaustion scenarios are explicitly accounted for and gracefully handled without throwing an unhandled trace dump.
* No Hardcoded Configurations: All structural endpoint variations must reside entirely inside environment configurations or decoupled static resource JSON registries.
