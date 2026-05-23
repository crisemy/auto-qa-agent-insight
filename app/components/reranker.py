from app.models import (
    RerankContextDocumentsInput,
    RerankContextDocumentsOutput,
    RerankDocument,
)


def _tokenize(text: str) -> set[str]:
    return set(text.lower().split())


def _relevance_score(query_tokens: set[str], document: RerankDocument) -> float:
    doc_tokens = _tokenize(document.content)
    if not doc_tokens:
        return 0.0
    overlap = query_tokens & doc_tokens
    return len(overlap) / len(doc_tokens)


_RELEVANCE_THRESHOLD = 0.15


def rerank(params: RerankContextDocumentsInput) -> RerankContextDocumentsOutput:
    query_tokens = _tokenize(params.query)
    scored = [
        (_relevance_score(query_tokens, doc), doc) for doc in params.documents
    ]
    scored.sort(key=lambda x: x[0], reverse=True)

    cutoff = any(score < _RELEVANCE_THRESHOLD for score, _ in scored)

    return RerankContextDocumentsOutput(
        ordered_documents=[doc for _, doc in scored],
        relevance_cutoff_applied=cutoff,
    )
