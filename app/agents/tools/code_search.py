from app.models import (
    LocateTargetFilesInput,
    LocateTargetFilesOutput,
    ReadCodeBlockSurgicallyInput,
    ReadCodeBlockSurgicallyOutput,
)
from app.services._safety import execute_with_safety

_MAX_LINES = 200


def locate_files(params: LocateTargetFilesInput) -> LocateTargetFilesOutput:
    matched: list[str] = []
    for hint in params.file_hints:
        for ext in params.extension_whitelist:
            candidate = hint if hint.endswith(ext) else f"{hint}{ext}"
            matched.append(candidate)
    return LocateTargetFilesOutput(verified_file_paths=matched)


def read_block(params: ReadCodeBlockSurgicallyInput) -> ReadCodeBlockSurgicallyOutput:
    start = params.start_line
    end = params.end_line

    if (end - start + 1) > _MAX_LINES:
        end = start + _MAX_LINES - 1

    def _read():
        with open(params.file_path) as f:
            return f.readlines()

    lines = execute_with_safety(_read, label="read_block")
    if isinstance(lines, dict):
        return ReadCodeBlockSurgicallyOutput(
            file_path=params.file_path, code_segment="", total_file_lines=0
        )

    total = len(lines)
    segment = "".join(lines[start - 1 : end])

    return ReadCodeBlockSurgicallyOutput(
        file_path=params.file_path,
        code_segment=segment,
        total_file_lines=total,
    )
