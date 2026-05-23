from app.models import (
    HistoricalBugMatch,
    SearchHistoricalBugsInput,
    SearchHistoricalBugsOutput,
    ResolutionStatus,
)

SAMPLE_BUGS: list[dict] = [
    {
        "bug_id": "BUG-001",
        "signature": "ConnectionError timeout connecting to database",
        "subsystem": "database",
        "diagnostic": "Connection pool exhausted due to slow queries",
        "status": "RESOLVED",
    },
    {
        "bug_id": "BUG-002",
        "signature": "KeyError missing required field user_id in payload",
        "subsystem": "api-gateway",
        "diagnostic": "Request validation missing required field check",
        "status": "RESOLVED",
    },
    {
        "bug_id": "BUG-003",
        "signature": "TypeError unsupported operand type for NoneType",
        "subsystem": "worker",
        "diagnostic": "Null propagation from uninitialized config value",
        "status": "UNRESOLVED",
    },
]


def _tokenize(text: str) -> list[str]:
    return text.lower().split()


def _keyword_score(query_tokens: set[str], doc_tokens: list[str]) -> float:
    matches = 0
    for qtok in query_tokens:
        if any(qtok in dtok for dtok in doc_tokens):
            matches += 1
    return matches / len(query_tokens) if query_tokens else 0.0


def hybrid_search(params: SearchHistoricalBugsInput) -> SearchHistoricalBugsOutput:
    query_tokens = set(_tokenize(params.cleaned_error_signature))
    scored: list[tuple[float, dict]] = []

    for bug in SAMPLE_BUGS:
        if params.target_subsystem and params.target_subsystem != bug["subsystem"]:
            continue

        doc_tokens = _tokenize(bug["signature"])
        kw_score = _keyword_score(query_tokens, doc_tokens)
        scored.append((kw_score, bug))

    scored.sort(key=lambda x: x[0], reverse=True)
    top = scored[: params.limit]

    if not top or top[0][0] < 0.70:
        return SearchHistoricalBugsOutput(matches=[])

    matches = [
        HistoricalBugMatch(
            bug_id=bug["bug_id"],
            similarity_score=round(score, 4),
            historical_diagnostic=bug["diagnostic"],
            resolution_status=ResolutionStatus(bug["status"]),
        )
        for score, bug in top
    ]

    return SearchHistoricalBugsOutput(matches=matches)
