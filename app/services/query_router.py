from app.models import (
    EnrichedInsightReport,
    InputGuardResult,
    RawBugReport,
    RemediationResult,
    SearchHistoricalBugsInput,
)
from app.security.input_guard import inspect
from app.security.output_filter import validate as filter_output
from app.agents.triage_agent import run as triage_run
from app.agents.rca_agent import run as rca_run
from app.agents.remediation_agent import run as remediation_run
from app.agents.grader_agent import grade
from app.components.hybrid_retriever import hybrid_search
from app.components.reranker import rerank


def process(report: RawBugReport) -> EnrichedInsightReport | dict:
    guard: InputGuardResult = inspect(report)
    if not guard.is_safe:
        return {
            "error": "INPUT_REJECTED",
            "reason": f"Prompt injection detected: {guard.flagged_patterns}",
        }

    triage = triage_run(report)

    historical = hybrid_search(
        SearchHistoricalBugsInput(
            cleaned_error_signature=triage.normalized_signature,
            target_subsystem=triage.failing_module,
            limit=3,
        )
    )

    if historical.matches:
        best = historical.matches[0]
        rca_result = None
        remediation = RemediationResult(
            patch="",
            explanation=f"Historical match found: {best.bug_id} — {best.historical_diagnostic}",
        )
    else:
        rca_result = rca_run(triage)

        grade_result = grade(triage, rca_result)
        if not grade_result.is_relevant:
            rca_result = rca_run(triage)
            grade_result = grade(triage, rca_result)
            if not grade_result.is_relevant:
                return {
                    "error": "INSUFFICIENT_CONTEXT",
                    "message": "Insufficient context to safely diagnose this error",
                }

        remediation = remediation_run(rca_result)

    report_out = EnrichedInsightReport(
        raw_signature=triage.normalized_signature,
        triage=triage,
        root_cause=rca_result,
        remediation=remediation,
    )

    filter_result = filter_output(report_out)
    if not filter_result.is_valid:
        return {
            "error": "OUTPUT_REJECTED",
            "issues": filter_result.issues,
        }

    return report_out
