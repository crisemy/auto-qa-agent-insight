import json

from app.agents.tools.prompt_templates import GRADER_SYSTEM_PROMPT
from app.models import GraderResult, RcaResult, TriageResult
from app.services.llm_client import call_llm


def grade(triage: TriageResult, rca: RcaResult) -> GraderResult:
    user_message = (
        "Evaluate the relevance between the triage and root-cause analysis below.\n\n"
        f"Triage:\n{json.dumps(triage.model_dump(), indent=2)}\n\n"
        f"Root-Cause Analysis:\n{json.dumps(rca.model_dump(), indent=2)}\n\n"
        "Return a JSON object with exactly two fields:\n"
        '  "relevance_score": a float between 0.0 and 1.0\n'
        '  "is_relevant": true if relevance_score >= 0.50, otherwise false\n'
        "Do not include any other text."
    )

    try:
        response_text = call_llm(GRADER_SYSTEM_PROMPT, user_message)
        result = json.loads(response_text)
        score = float(result.get("relevance_score", 0.0))
        score = max(0.0, min(1.0, score))
        is_relevant = bool(result.get("is_relevant", score >= 0.50))
    except (json.JSONDecodeError, TypeError, ValueError, RuntimeError):
        score = 0.0
        is_relevant = False

    return GraderResult(
        relevance_score=round(score, 2),
        is_relevant=is_relevant,
    )
