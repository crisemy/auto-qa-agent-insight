# Skills Specification: Executable Agent Capabilities

This document details the functional contracts for all tools and programmatic capabilities available to the agentic layer. Every skill must be implemented as a deterministic, type-hinted function with explicit error handling.

---

## 1. Retrieval Skills (`skills/retrieval`)

### 1.1 `Search_Historical_Bugs`

- **Description:** Performs a hybrid search (semantic vector embedding + keyword BM25) across historical bug records, closed issues, and past post-mortems to identify duplicate regressions.

- **Input Schema (JSON):**

```json
  {
    "cleaned_error_signature": "string",
    "target_subsystem": "string",
    "limit": 5
  }
```

- **Output Schema (JSON):**

```json
{
  "matches": [
    {
      "bug_id": "string",
      "similarity_score": 0.89,
      "historical_diagnostic": "string",
      "resolution_status": "RESOLVED"
    }
  ]
}
```

- **Boundary Rules**: If the highest similarity score is below 0.70, the skill must return an empty list, signaling to the agent that this is a net-new issue.

### 1.2 Rerank_Context_Documents`Code_Search_Vector_Retrieval`

- **Description**: Takes a raw list of retrieved historical documents and reranks them using a Cross-Encoder model to maximize contextual relevance against the active stack trace.

- **Input Schema (JSON)**:

```json
{
    "query": "string",
    "documents": "array of objects"
}
```

- **Output Schema (JSON)**:

```json
{
  "ordered_documents": "array of objects",
  "relevance_cutoff_applied": "boolean"
}
```

## 2. Code Forensics Skills (skills/code_forensics)

### 2.1 Locate_Target_Files

- **Description**: Searches the local repository workspace for source code filenames or module paths mentioned in the raw error log or stack trace.

- **Input Schema (JSON)**:

```json
{
  "file_hints": ["string"],
  "extension_whitelist": [".py", ".ts", ".go"]
}
```

- **Output Schema (JSON):**

```json
{
  "verified_file_paths": ["string"]
}
```

### 2.2 Read_Code_Block_Surgically

- **Description**: Reads an exact line range of a verified source code file. This prevents context window saturation by keeping file reads precise.

- **Input Schema (JSON)*:

```json
{
  "file_path": "string",
  "start_line": 10,
  "end_line": 50
}
```

- **Output Schema (JSON)**:

```json
{
  "file_path": "string",
  "code_segment": "string",
  "total_file_lines": 150
}
```

- **Boundary Rules**: Cannot read more than 200 lines of code in a single execution. Requests exceeding this threshold must be truncated and flagged.

## 3. Utility & Optimization Skills (skills/utilities)

### 3.1 Query_Rewriter_Transformer

- **Description**: Strips infrastructure noise (timestamps, thread IDs, memory addresses, PIDs) from raw stack traces to generate a clean, normalized error signature optimized for vector DB lookups.

- **Input Schema (JSON)**:

```json
{
  "raw_log_payload": "string"
}
```

- **Output Schema (JSON)**:

```json
{
  "normalized_signature": "string",
  "extracted_exception_type": "string"
}
```

### 3.2 Check_Semantic_Cache

- **Description**: Queries an in-memory Redis or local cache layer using vector distance to determine if an identical or highly similar error signature was fully diagnosed within the last 24 hours.

- Input Schema (JSON):

```json
JSON
{
  "normalized_signature": "string"
}
```

- **Output Schema (JSON)**:

```json
{
  "cache_hit": "boolean",
  "cached_report": "object | null"
}
```

## 4. Safety and Error Fallbacks

Every skill execution must adhere to a strict error-handling protocol:

- **Timeout Threshold**: No external skill execution (DB lookup, file system read) can exceed a hard limit of 5000ms.
- **Graceful Failures**: If a skill encounters an infrastructural failure (e.g., Vector DB connection dropped), it must return a structured JSON response containing {"error": "SERVICE_UNAVAILABLE", "fallback_action": "CONTINUE_WITHOUT_CONTEXT"} instead of raising unhandled exceptions that crash the agent loop.
