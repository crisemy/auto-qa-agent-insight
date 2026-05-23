from app.models import GraderResult, RcaResult, TriageResult


def grade(triage: TriageResult, rca: RcaResult) -> GraderResult:
    score = _compute_relevance(triage, rca)

    return GraderResult(
        relevance_score=round(score, 2),
        is_relevant=score >= 0.50,
    )


import re


def _tokenize(text: str) -> list[str]:
    return re.sub(r"[^\w\s/.\-]", " ", text.lower()).split()


def _compute_relevance(triage: TriageResult, rca: RcaResult) -> float:
    triage_tokens = _tokenize(triage.normalized_signature)
    rca_text = f"{rca.file_path} {rca.function_name} {rca.failure_mechanism}".lower()

    if not triage_tokens:
        return 0.0

    matches = sum(1 for t in triage_tokens if t in rca_text)
    score = matches / len(triage_tokens)

    if rca.file_path == "unknown":
        score *= 0.5

    return score
