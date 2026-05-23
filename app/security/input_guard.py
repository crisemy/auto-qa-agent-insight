import re

from app.models import InputGuardResult, RawBugReport

_INJECTION_PATTERNS = [
    (re.compile(r"ignore\s+(all\s+)?(previous|prior)\s+(instructions|prompts?)", re.I), "ignore_previous_instructions"),
    (re.compile(r"system\s*(prompt|message|instruction)", re.I), "system_prompt_override"),
    (re.compile(r"you\s+are\s+(now|not\s+an?\s+ai)", re.I), "role_switch"),
    (re.compile(r"<\|?(im_start|im_end|sys|user|assistant)\|?>", re.I), "special_token"),
    (re.compile(r"(?:base64|decod)e?\s*(64|this)", re.I), "encoded_payload"),
    (re.compile(r"\[system\]|\[user\]|\[assistant\]", re.I), "role_tag_injection"),
    (re.compile(r"forget|unset|reset\s+context", re.I), "context_reset"),
]


def inspect(payload: RawBugReport) -> InputGuardResult:
    flagged: list[str] = []
    for pattern, label in _INJECTION_PATTERNS:
        if pattern.search(payload.payload):
            flagged.append(label)

    risk = min(len(flagged) * 0.25, 1.0)

    return InputGuardResult(
        is_safe=len(flagged) == 0,
        risk_score=round(risk, 2),
        flagged_patterns=flagged,
    )
