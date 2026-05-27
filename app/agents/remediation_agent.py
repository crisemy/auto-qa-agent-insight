import json

from app.agents.tools.prompt_templates import REMEDIATION_SYSTEM_PROMPT
from app.models import RcaResult, RemediationResult
from app.services.llm_client import call_llm


def run(rca: RcaResult) -> RemediationResult:
    user_message = (
        "Generate a code patch to fix the root cause described below.\n\n"
        f"RCA Diagnosis:\n{json.dumps(rca.model_dump(), indent=2)}\n\n"
        "Return a JSON object with exactly two fields:\n"
        '  "patch": a string containing the unified diff patch\n'
        '  "explanation": a brief technical explanation of why this fix is safe\n'
        "Do not include any other text."
    )

    try:
        response_text = call_llm(REMEDIATION_SYSTEM_PROMPT, user_message)
        result = json.loads(response_text)
        patch = result.get("patch", "")
        explanation = result.get("explanation", "")
    except (json.JSONDecodeError, TypeError, ValueError, RuntimeError):
        patch = ""
        explanation = "LLM call failed — unable to generate patch"

    return RemediationResult(patch=patch, explanation=explanation)
