from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_LOG_DIR = Path("observability")
_LOG_FILE = _LOG_DIR / "cost_log.jsonl"

_RUN_ID: int = 0


def _next_run_id() -> int:
    global _RUN_ID
    _RUN_ID += 1
    return _RUN_ID


def _estimate_tokens(text: str) -> int:
    return max(1, len(text) // 4)


def log_run(
    input_text: str,
    output: Any,
    duration_ms: float,
    model: str = "",
    cost_usd: float = 0.0,
) -> dict[str, Any]:
    _LOG_DIR.mkdir(parents=True, exist_ok=True)

    input_tokens = _estimate_tokens(input_text)
    output_text = json.dumps(output, default=str)
    output_tokens = _estimate_tokens(output_text)

    entry = {
        "run_id": _next_run_id(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": input_tokens + output_tokens,
        "duration_ms": round(duration_ms, 2),
        "model": model,
        "cost_usd": round(cost_usd, 6),
    }

    with open(_LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")

    return entry
