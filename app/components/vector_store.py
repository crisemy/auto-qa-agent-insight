from __future__ import annotations

from typing import Any

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

_embedder: SentenceTransformer | None = None
_index: faiss.IndexFlatL2 | None = None
_bug_registry: list[dict[str, Any]] = []

_EMBEDDING_DIM = 384
_MODEL_NAME = "all-MiniLM-L6-v2"


def _get_embedder() -> SentenceTransformer:
    global _embedder
    if _embedder is None:
        _embedder = SentenceTransformer(_MODEL_NAME)
    return _embedder


def _get_index() -> faiss.IndexFlatL2:
    global _index
    if _index is None:
        _index = faiss.IndexFlatL2(_EMBEDDING_DIM)
    return _index


def index_bugs(bugs: list[dict[str, Any]]) -> None:
    if not bugs:
        return
    embedder = _get_embedder()
    idx = _get_index()
    texts = [bug.get("signature", bug.get("payload", "")) for bug in bugs]
    embeddings = embedder.encode(texts, normalize_embeddings=True)
    idx.add(np.array(embeddings, dtype=np.float32))
    _bug_registry.extend(bugs)


def search(query: str, k: int = 5) -> list[dict[str, Any]]:
    if _index is None or _index.ntotal == 0:
        return []
    embedder = _get_embedder()
    idx = _get_index()
    query_vec = embedder.encode([query], normalize_embeddings=True)
    distances, indices = idx.search(np.array(query_vec, dtype=np.float32), k)
    results: list[dict[str, Any]] = []
    for dist, idx_pos in zip(distances[0], indices[0]):
        if idx_pos == -1 or idx_pos >= len(_bug_registry):
            continue
        bug = dict(_bug_registry[idx_pos])
        bug["similarity_score"] = round(1.0 / (1.0 + float(dist)), 4)
        results.append(bug)
    return results


def get_registry() -> list[dict[str, Any]]:
    return list(_bug_registry)


def reset() -> None:
    global _index, _bug_registry
    _index = None
    _bug_registry = []
