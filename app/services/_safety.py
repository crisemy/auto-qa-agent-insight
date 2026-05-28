from __future__ import annotations

import signal
from typing import Any, Callable, TypeVar

T = TypeVar("T")

_TIMEOUT_MS = 5000


def _timeout_handler(signum: int, frame: object) -> None:
    raise TimeoutError("Skill execution timed out")


def execute_with_safety(fn: Callable[[], T], label: str = "skill") -> T | dict[str, Any]:
    try:
        if hasattr(signal, "SIGALRM"):
            signal.signal(signal.SIGALRM, _timeout_handler)
            signal.alarm(max(1, _TIMEOUT_MS // 1000))  # type: ignore[attr-defined]
        return fn()
    except (TimeoutError, FileNotFoundError, OSError, ConnectionError):
        return {
            "error": "SERVICE_UNAVAILABLE",
            "fallback_action": "CONTINUE_WITHOUT_CONTEXT",
        }
    finally:
        if hasattr(signal, "SIGALRM"):
            signal.alarm(0)  # type: ignore[attr-defined]
