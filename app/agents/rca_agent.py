from app.agents.tools.code_search import locate_files, read_block
from app.models import (
    LocateTargetFilesInput,
    RcaResult,
    ReadCodeBlockSurgicallyInput,
    TriageResult,
)


def run(triage: TriageResult) -> RcaResult:
    file_hints = [triage.failing_module]
    if triage.exception_type:
        file_hints.append(triage.exception_type.lower())

    located = locate_files(
        LocateTargetFilesInput(
            file_hints=file_hints,
            extension_whitelist=[".py", ".ts", ".go"],
        )
    )

    if not located.verified_file_paths:
        return RcaResult(
            file_path=triage.failing_module,
            line_number=0,
            function_name="unknown",
            failure_mechanism="No matching source files found",
        )

    target = located.verified_file_paths[0]
    snippet = read_block(
        ReadCodeBlockSurgicallyInput(
            file_path=target,
            start_line=1,
            end_line=50,
        )
    )

    line_number = _pinpoint_line(snippet.code_segment, triage.exception_type)

    error_desc = " ".join(
        w for w in triage.normalized_signature.lower().split()
        if w not in ("a", "an", "the", "at", "in", "of", "to", ":", "-", "|", "error", "warning", "critical", "fatal")
    )[:80]

    if triage.exception_type:
        mechanism = f"Unhandled {triage.exception_type}: {error_desc} in {target}"
    else:
        mechanism = f"Unhandled error: {error_desc} in {target}"

    return RcaResult(
        file_path=target,
        line_number=line_number,
        function_name=_extract_function(snippet.code_segment, line_number),
        failure_mechanism=mechanism,
    )


def _pinpoint_line(code: str, exception_type: str) -> int:
    for i, line in enumerate(code.splitlines(), start=1):
        if exception_type.lower() in line.lower():
            return i
    return 1


def _extract_function(code: str, line_number: int) -> str:
    lines = code.splitlines()
    for i in range(min(line_number - 1, len(lines) - 1), -1, -1):
        line = lines[i].strip()
        if line.startswith("def ") or line.startswith("async def "):
            return line.split("(")[0].replace("def ", "").replace("async ", "").strip()
    return "unknown"
