from app.models import (
    RawBugReport,
    TriageResult,
    Severity,
    RcaResult,
    CheckSemanticCacheInput,
)
from app.agents.triage_agent import run as triage_run
from app.agents.rca_agent import run as rca_run
from app.agents.remediation_agent import run as remediation_run
from app.agents.grader_agent import grade
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
    def test_generates_patch(self):
        rca = RcaResult(
            file_path="app/services/db.py",
            line_number=42,
            function_name="connect",
            failure_mechanism="Unhandled TimeoutError in app/services/db.py",
        )
        result = remediation_run(rca)
        assert result.patch
        assert result.explanation
        assert "db.py" in result.patch


class TestGraderAgent:
    def test_relevant_when_tokens_overlap(self):
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

    def test_irrelevant_when_no_overlap(self):
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


class TestSemanticCache:
    def test_returns_no_hit_by_default(self):
        result = lookup(CheckSemanticCacheInput(normalized_signature="test error"))
        assert result.cache_hit is False
        assert result.cached_report is None
