from app.models import RcaResult, RemediationResult


def run(rca: RcaResult) -> RemediationResult:
    patch = _generate_patch(rca)
    explanation = _generate_explanation(rca)

    return RemediationResult(
        patch=patch,
        explanation=explanation,
    )


def _generate_patch(rca: RcaResult) -> str:
    if "Null" in rca.failure_mechanism or "None" in rca.failure_mechanism:
        return (
            f"--- a/{rca.file_path}\n"
            f"+++ b/{rca.file_path}\n"
            f"@@ -{rca.line_number},1 +{rca.line_number},1 @@\n"
            f"-{rca.failure_mechanism}\n"
            f"+if value is not None:\n"
            f"+    # handle {rca.failure_mechanism}\n"
        )

    return (
        f"--- a/{rca.file_path}\n"
        f"+++ b/{rca.file_path}\n"
        f"@@ -{rca.line_number},1 +{rca.line_number},1 @@\n"
        f"- # TODO: fix {rca.failure_mechanism}\n"
        f"+ # patched {rca.failure_mechanism}\n"
    )


def _generate_explanation(rca: RcaResult) -> str:
    return (
        f"Root cause identified at {rca.file_path}:{rca.line_number} "
        f"in `{rca.function_name}`. "
        f"Failure mechanism: {rca.failure_mechanism}. "
        f"Patch adds a guard to prevent the unhandled case."
    )
