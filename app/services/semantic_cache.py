from __future__ import annotations

import hashlib
import json
from typing import Any

import numpy as np
import redis
from sentence_transformers import SentenceTransformer

from app.config import settings
from app.models import (
    CheckSemanticCacheInput,
    CheckSemanticCacheOutput,
    EnrichedInsightReport,
)

_CACHE_PREFIX = "semantic_cache:"
_CACHE_TTL_SECONDS = 86400

_embedder: SentenceTransformer | None = None
_redis_client: redis.Redis | None = None


def _get_embedder() -> SentenceTransformer:
    global _embedder
    if _embedder is None:
        _embedder = SentenceTransformer("all-MiniLM-L6-v2")
    return _embedder


def _get_redis() -> redis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(settings.redis_url, decode_responses=True)
    return _redis_client


def _signature_key(signature: str) -> str:
    return f"{_CACHE_PREFIX}{hashlib.sha256(signature.encode()).hexdigest()}"


def lookup(params: CheckSemanticCacheInput) -> CheckSemanticCacheOutput:
    try:
        r = _get_redis()
        embedder = _get_embedder()
        threshold = settings.semantic_cache_distance_threshold

        incoming_vec = embedder.encode(
            [params.normalized_signature], normalize_embeddings=True
        )[0]

        cursor = 0
        best_distance = float("inf")
        best_report: str | None = None

        while True:
            cursor, keys = r.scan(
                cursor=cursor, match=f"{_CACHE_PREFIX}*", count=200
            )
            if not keys:
                if cursor == 0:
                    break
                continue

            pipe = r.pipeline()
            for key in keys:
                pipe.get(key)
            values = pipe.execute()

            for value in values:
                if value is None:
                    continue
                entry: dict[str, Any] = json.loads(value)
                stored_vec = np.array(entry["embedding"], dtype=np.float32)
                distance = float(np.linalg.norm(incoming_vec - stored_vec))
                if distance < best_distance:
                    best_distance = distance
                    best_report = entry["report"]

            if cursor == 0:
                break

        if best_distance < threshold and best_report is not None:
            return CheckSemanticCacheOutput(
                cache_hit=True, cached_report=best_report
            )

        return CheckSemanticCacheOutput(cache_hit=False, cached_report=None)

    except Exception:
        return CheckSemanticCacheOutput(
            cache_hit=False,
            cached_report=None,
            error="SERVICE_UNAVAILABLE",
            fallback_action="CONTINUE_WITHOUT_CONTEXT",
        )


def store(signature: str, report: EnrichedInsightReport) -> None:
    try:
        r = _get_redis()
        embedder = _get_embedder()

        vec = embedder.encode([signature], normalize_embeddings=True)[0]
        key = _signature_key(signature)

        entry = {
            "signature": signature,
            "embedding": vec.tolist(),
            "report": report.model_dump_json(),
        }

        r.setex(key, _CACHE_TTL_SECONDS, json.dumps(entry))
    except Exception:
        pass
