import re

from app.models import (
    CheckSemanticCacheInput,
    QueryRewriterInput,
    RawBugReport,
    Severity,
    TriageResult,
)
from app.services.query_rewriter import query_rewriter
from app.services.semantic_cache import lookup as cache_lookup


def run(report: RawBugReport) -> TriageResult:
    cleaned = query_rewriter(QueryRewriterInput(raw_log_payload=report.payload))

    cache_result = cache_lookup(
        CheckSemanticCacheInput(normalized_signature=cleaned.normalized_signature)
    )
    if cache_result.cache_hit:
        pass

    severity = _classify_severity(cleaned.extracted_exception_type, report.payload)
    failing_module = _extract_module(report.payload)

    return TriageResult(
        severity=severity,
        failing_module=failing_module,
        normalized_signature=cleaned.normalized_signature,
        exception_type=cleaned.extracted_exception_type,
    )


def _classify_severity(exception_type: str, raw: str) -> Severity:
    critical_exceptions = {"AuthenticationError", "AuthError", "ConnectionError"}
    major_exceptions = {"KeyError", "TypeError", "ValueError", "ValidationError", "RateLimitError"}

    if exception_type in critical_exceptions:
        return Severity.critical
    if exception_type in major_exceptions:
        return Severity.major

    critical_keywords = [
        "database", "crash", "outage", "segfault", "503",
        "authentication", "api.key", "unauthorized",
    ]
    major_keywords = [
        "timeout", "rate.limit", "quota", "denied",
        "unavailable", "invalid", "missing", "validation",
        "keyerror", "typeerror",
    ]

    lower = raw.lower()
    if any(kw in lower for kw in critical_keywords):
        return Severity.critical
    if any(kw in lower for kw in major_keywords):
        return Severity.major
    return Severity.minor


_PATH_WITH_LINE = re.compile(r"[\w./\\-]+\.\w{2,4}:\d+")
_PATH_NO_LINE = re.compile(r"(?:[\w./\\-]+\.\w{2,4})(?!:)")


def _extract_module(raw: str) -> str:
    for line in raw.splitlines():
        match = _PATH_WITH_LINE.search(line)
        if match:
            return match.group().rsplit(":", 1)[0]
    for line in raw.splitlines():
        match = _PATH_NO_LINE.search(line)
        if match:
            path = match.group()
            if "/" in path:
                return path
    for line in raw.splitlines():
        if "File" in line or "module" in line.lower():
            parts = line.strip().split()
            for p in parts:
                if "/" in p or "\\" in p:
                    return p.split(":")[0]
    return "unknown"
