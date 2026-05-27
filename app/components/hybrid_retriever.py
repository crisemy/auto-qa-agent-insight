from app.components import vector_store
from app.models import (
    HistoricalBugMatch,
    ResolutionStatus,
    SearchHistoricalBugsInput,
    SearchHistoricalBugsOutput,
)


def _tokenize(text: str) -> list[str]:
    return text.lower().split()


def _keyword_score(query_tokens: set[str], doc_tokens: list[str]) -> float:
    if not query_tokens:
        return 0.0
    matches = 0
    for qtok in query_tokens:
        if any(qtok in dtok for dtok in doc_tokens):
            matches += 1
    return matches / len(query_tokens)


def _build_matches(
    results: list[dict], limit: int
) -> list[HistoricalBugMatch]:
    return [
        HistoricalBugMatch(
            bug_id=r["bug_id"],
            similarity_score=r["similarity_score"],
            historical_diagnostic=r.get("diagnostic", ""),
            resolution_status=ResolutionStatus(r.get("status", "UNRESOLVED")),
        )
        for r in results[:limit]
    ]


def hybrid_search(params: SearchHistoricalBugsInput) -> SearchHistoricalBugsOutput:
    faiss_results = vector_store.search(
        params.cleaned_error_signature, k=params.limit * 2
    )

    if params.target_subsystem:
        faiss_results = [
            r for r in faiss_results if r.get("subsystem", "") == params.target_subsystem
        ]

    faiss_results = faiss_results[: params.limit]

    if faiss_results and faiss_results[0]["similarity_score"] >= 0.70:
        return SearchHistoricalBugsOutput(
            matches=_build_matches(faiss_results, params.limit)
        )

    query_tokens = set(_tokenize(params.cleaned_error_signature))
    registry = vector_store.get_registry()
    scored: list[tuple[float, dict]] = []

    for bug in registry:
        if params.target_subsystem and params.target_subsystem != bug.get("subsystem", ""):
            continue
        doc_tokens = _tokenize(bug.get("signature", bug.get("payload", "")))
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
            historical_diagnostic=bug.get("diagnostic", ""),
            resolution_status=ResolutionStatus(bug.get("status", "UNRESOLVED")),
        )
        for score, bug in top
    ]
    return SearchHistoricalBugsOutput(matches=matches)
