from __future__ import annotations

import signal
from typing import Any, Callable, TypeVar

T = TypeVar("T")

_TIMEOUT_MS = 5000

_SIGALRM: int = getattr(signal, "SIGALRM", 0)
_alarm: Any = getattr(signal, "alarm", None)
_SIGALRM_SUPPORTED: bool = hasattr(signal, "SIGALRM") and hasattr(signal, "alarm")


def _timeout_handler(signum: int, frame: object) -> None:
    raise TimeoutError("Skill execution timed out")


def execute_with_safety(fn: Callable[[], T], label: str = "skill") -> T | dict[str, Any]:
    try:
        if _SIGALRM_SUPPORTED:
            signal.signal(_SIGALRM, _timeout_handler)
            _alarm(max(1, _TIMEOUT_MS // 1000))
        return fn()
    except (TimeoutError, FileNotFoundError, OSError, ConnectionError):
        return {
            "error": "SERVICE_UNAVAILABLE",
            "fallback_action": "CONTINUE_WITHOUT_CONTEXT",
        }
    finally:
        if _SIGALRM_SUPPORTED:
            _alarm(0)
