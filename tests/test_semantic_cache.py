from unittest.mock import patch

import numpy as np

from app.models import (
    CheckSemanticCacheInput,
    EnrichedInsightReport,
    Severity,
    TriageResult,
)
from app.services.semantic_cache import lookup, store


@patch("app.services.semantic_cache._get_redis")
@patch("app.services.semantic_cache._get_embedder")
def test_lookup_empty_cache_returns_no_hit(mock_embedder, mock_redis):
    mock_redis.return_value.scan.return_value = (0, [])
    mock_embedder.return_value.encode.return_value = [[0.1, 0.2, 0.3]]
    result = lookup(CheckSemanticCacheInput(normalized_signature="test error"))
    assert result.cache_hit is False
    assert result.cached_report is None


@patch("app.services.semantic_cache._get_redis")
@patch("app.services.semantic_cache._get_embedder")
def test_lookup_hit_when_distance_below_threshold(mock_embedder, mock_redis):
    embedder_instance = mock_embedder.return_value
    embedder_instance.encode.return_value = [[0.1, 0.2, 0.3]]
    redis_instance = mock_redis.return_value
    redis_instance.scan.return_value = (0, ["semantic_cache:abc"])
    redis_instance.pipeline.return_value.execute.return_value = [
        '{"signature": "old err", "embedding": [0.1, 0.2, 0.3], "report": "cached"}'
    ]
    result = lookup(CheckSemanticCacheInput(normalized_signature="new err"))
    assert result.cache_hit is True
    assert result.cached_report == "cached"


@patch("app.services.semantic_cache._get_redis")
@patch("app.services.semantic_cache._get_embedder")
def test_lookup_miss_when_distance_above_threshold(mock_embedder, mock_redis):
    embedder_instance = mock_embedder.return_value
    embedder_instance.encode.return_value = [[0.9, 0.9, 0.9]]
    redis_instance = mock_redis.return_value
    redis_instance.scan.return_value = (0, ["semantic_cache:abc"])
    redis_instance.pipeline.return_value.execute.return_value = [
        '{"signature": "old err", "embedding": [0.1, 0.2, 0.3], "report": "cached"}'
    ]
    result = lookup(CheckSemanticCacheInput(normalized_signature="very different err"))
    assert result.cache_hit is False
    assert result.cached_report is None


@patch("app.services.semantic_cache._get_redis")
def test_lookup_fallback_on_redis_down(mock_redis):
    mock_redis.return_value.scan.side_effect = ConnectionError("Redis unreachable")
    result = lookup(CheckSemanticCacheInput(normalized_signature="test"))
    assert result.cache_hit is False
    assert result.error == "SERVICE_UNAVAILABLE"
    assert result.fallback_action == "CONTINUE_WITHOUT_CONTEXT"


@patch("app.services.semantic_cache._get_redis")
@patch("app.services.semantic_cache._get_embedder")
def test_store_writes_to_redis(mock_embedder, mock_redis):
    embedder_instance = mock_embedder.return_value
    embedder_instance.encode.return_value = np.array([[0.1, 0.2, 0.3]], dtype=np.float32)
    redis_instance = mock_redis.return_value

    report = EnrichedInsightReport(
        raw_signature="sig",
        triage=TriageResult(
            severity=Severity.major,
            failing_module="app/test.py",
            normalized_signature="sig",
            exception_type="TypeError",
        ),
    )
    store("my signature", report)
    redis_instance.setex.assert_called_once()
    key, ttl, value = redis_instance.setex.call_args[0]
    assert ttl == 86400
    assert "sig" in value


@patch("app.services.semantic_cache._get_redis")
@patch("app.services.semantic_cache._get_embedder")
def test_store_silent_failure_on_redis_down(mock_embedder, mock_redis):
    mock_redis.return_value.setex.side_effect = ConnectionError("Redis down")

    report = EnrichedInsightReport(
        raw_signature="sig",
        triage=TriageResult(
            severity=Severity.major,
            failing_module="app/test.py",
            normalized_signature="sig",
            exception_type="TypeError",
        ),
    )
    store("my signature", report)
    assert True


@patch("app.services.semantic_cache._get_redis")
@patch("app.services.semantic_cache._get_embedder")
def test_lookup_scans_multiple_pages(mock_embedder, mock_redis):
    embedder_instance = mock_embedder.return_value
    embedder_instance.encode.return_value = [[0.1, 0.2, 0.3]]
    redis_instance = mock_redis.return_value
    redis_instance.scan.side_effect = [
        (5, ["semantic_cache:a"]),
        (0, ["semantic_cache:b"]),
    ]
    redis_instance.pipeline.return_value.execute.side_effect = [
        ['{"signature": "a", "embedding": [0.1, 0.2, 0.3], "report": "report_a"}'],
        ['{"signature": "b", "embedding": [0.1, 0.2, 0.3], "report": "report_b"}'],
    ]

    result = lookup(CheckSemanticCacheInput(normalized_signature="test"))
    assert result.cache_hit is True
    assert result.cached_report == "report_a"
    assert redis_instance.scan.call_count == 2
