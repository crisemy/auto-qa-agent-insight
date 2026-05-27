import json
from unittest.mock import patch

import numpy as np

from app.agents.grader_agent import grade
from app.agents.rca_agent import run as rca_run
from app.agents.remediation_agent import run as remediation_run
from app.agents.triage_agent import run as triage_run
from app.models import (
    CheckSemanticCacheInput,
    RawBugReport,
    RcaResult,
    Severity,
    TriageResult,
)
from app.services.semantic_cache import lookup


class TestTriageAgent:
    def test_classifies_critical_severity(self):
        report = RawBugReport(
            payload="CRITICAL: database connection lost on main cluster"
        )
        result = triage_run(report)
        assert result.severity == Severity.critical
        assert result.normalized_signature

    def test_classifies_minor_severity(self):
        report = RawBugReport(payload="warning: deprecation notice for v2 api")
        result = triage_run(report)
        assert result.severity == Severity.minor

    def test_extracts_exception_type(self):
        report = RawBugReport(payload="ValueError: invalid input")
        result = triage_run(report)
        assert result.exception_type == "ValueError"


class TestRcaAgent:
    def test_returns_failure_mechanism(self):
        triage = TriageResult(
            severity=Severity.major,
            failing_module="app/services/db.py",
            normalized_signature="connection timeout",
            exception_type="TimeoutError",
        )
        result = rca_run(triage)
        assert "TimeoutError" in result.failure_mechanism

    def test_unknown_file_path(self):
        triage = TriageResult(
            severity=Severity.minor,
            failing_module="nonexistent_module",
            normalized_signature="minor warning",
            exception_type="",
        )
        result = rca_run(triage)
        assert "nonexistent_module" in result.file_path


class TestRemediationAgent:
    @patch("app.agents.remediation_agent.call_llm")
    def test_generates_patch(self, mock_call_llm):
        mock_call_llm.return_value = json.dumps({
            "patch": (
                "--- a/app/services/db.py\n"
                "+++ b/app/services/db.py\n"
                "@@ -42,1 +42,1 @@\n"
                "-connect()\n"
                "+if connection is not None: connect()"
            ),
            "explanation": "Added null guard before connection call",
        })
        rca = RcaResult(
            file_path="app/services/db.py",
            line_number=42,
            function_name="connect",
            failure_mechanism="Unhandled TimeoutError in app/services/db.py",
        )
        result = remediation_run(rca)
        assert result.patch
        assert "db.py" in result.patch
        assert "null guard" in result.explanation


class TestGraderAgent:
    @patch("app.agents.grader_agent.call_llm")
    def test_relevant_when_tokens_overlap(self, mock_call_llm):
        mock_call_llm.return_value = '{"relevance_score": 0.85, "is_relevant": true}'
        triage = TriageResult(
            severity=Severity.major,
            failing_module="app/db.py",
            normalized_signature="timeout connecting to database",
            exception_type="TimeoutError",
        )
        rca = RcaResult(
            file_path="app/db.py",
            line_number=10,
            function_name="connect",
            failure_mechanism="database timeout error",
        )
        result = grade(triage, rca)
        assert result.is_relevant is True
        assert result.relevance_score == 0.85

    @patch("app.agents.grader_agent.call_llm")
    def test_irrelevant_when_no_overlap(self, mock_call_llm):
        mock_call_llm.return_value = '{"relevance_score": 0.15, "is_relevant": false}'
        triage = TriageResult(
            severity=Severity.major,
            failing_module="app/db.py",
            normalized_signature="api rate limit exceeded",
            exception_type="RateLimitError",
        )
        rca = RcaResult(
            file_path="app/db.py",
            line_number=10,
            function_name="connect",
            failure_mechanism="null pointer in config parser",
        )
        result = grade(triage, rca)
        assert result.is_relevant is False
        assert result.relevance_score == 0.15


class TestSemanticCache:
    @patch("app.services.semantic_cache._get_redis")
    @patch("app.services.semantic_cache._get_embedder")
    def test_returns_no_hit_on_cache_miss(self, mock_embedder, mock_redis):
        mock_redis.return_value.scan.return_value = (0, [])
        mock_embedder.return_value.encode.return_value = [[0.1, 0.2, 0.3]]
        result = lookup(CheckSemanticCacheInput(normalized_signature="test error"))
        assert result.cache_hit is False
        assert result.cached_report is None

    @patch("app.services.semantic_cache._get_redis")
    @patch("app.services.semantic_cache._get_embedder")
    def test_returns_cache_hit_when_distance_below_threshold(self, mock_embedder, mock_redis):
        mock_embedder_instance = mock_embedder.return_value
        mock_embedder_instance.encode.return_value = [[0.1, 0.2, 0.3]]
        mock_redis_instance = mock_redis.return_value
        mock_redis_instance.scan.return_value = (0, ["semantic_cache:abc123"])
        mock_redis_instance.pipeline.return_value.execute.return_value = [
            (
                '{"signature": "old error", "embedding": [0.1, 0.2, 0.3],'
                ' "report": "cached_report_data"}'
            )
        ]
        result = lookup(CheckSemanticCacheInput(normalized_signature="new error"))
        assert result.cache_hit is True
        assert result.cached_report == "cached_report_data"

    @patch("app.services.semantic_cache._get_redis")
    def test_falls_back_on_redis_unreachable(self, mock_redis):
        mock_redis.return_value.scan.side_effect = ConnectionError("Redis down")
        result = lookup(CheckSemanticCacheInput(normalized_signature="test error"))
        assert result.cache_hit is False
        assert result.error == "SERVICE_UNAVAILABLE"
        assert result.fallback_action == "CONTINUE_WITHOUT_CONTEXT"

    @patch("app.services.semantic_cache._get_redis")
    @patch("app.services.semantic_cache._get_embedder")
    def test_store_writes_to_redis_with_ttl(self, mock_embedder, mock_redis):
        from app.models import EnrichedInsightReport, Severity, TriageResult
        mock_embedder_instance = mock_embedder.return_value
        mock_embedder_instance.encode.return_value = np.array(
            [[0.1, 0.2, 0.3]], dtype=np.float32
        )
        mock_redis_instance = mock_redis.return_value
        report = EnrichedInsightReport(
            raw_signature="sig",
            triage=TriageResult(
                severity=Severity.major,
                failing_module="app/test.py",
                normalized_signature="sig",
                exception_type="TypeError",
            ),
        )
        from app.services.semantic_cache import store
        store("test signature", report)
        mock_redis_instance.setex.assert_called_once()
        args, _ = mock_redis_instance.setex.call_args
        assert args[1] == 86400
        assert "sig" in args[2]
