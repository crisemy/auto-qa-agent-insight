import json

from pydantic import BaseModel, ValidationError

from app.models import EnrichedInsightReport, OutputFilterResult


def validate(report: EnrichedInsightReport) -> OutputFilterResult:
    issues: list[str] = []

    if not report.raw_signature.strip():
        issues.append("raw_signature is empty")

    if not report.triage.normalized_signature.strip():
        issues.append("triage.normalized_signature is empty")

    if report.root_cause and not report.root_cause.file_path.strip():
        issues.append("root_cause.file_path is empty")

    if report.remediation and not report.remediation.patch.strip():
        issues.append("remediation.patch is empty")

    return OutputFilterResult(
        is_valid=len(issues) == 0,
        issues=issues,
    )
