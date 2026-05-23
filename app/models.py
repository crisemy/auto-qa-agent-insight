from __future__ import annotations

from enum import Enum
from pydantic import BaseModel


class Severity(str, Enum):
    critical = "Critical"
    major = "Major"
    minor = "Minor"


class ResolutionStatus(str, Enum):
    resolved = "RESOLVED"
    unresolved = "UNRESOLVED"


class RawBugReport(BaseModel):
    payload: str
    source: str = "unknown"


class QueryRewriterOutput(BaseModel):
    normalized_signature: str
    extracted_exception_type: str


class TriageResult(BaseModel):
    severity: Severity
    failing_module: str
    normalized_signature: str
    exception_type: str


class HistoricalBugMatch(BaseModel):
    bug_id: str
    similarity_score: float
    historical_diagnostic: str
    resolution_status: ResolutionStatus


class SearchHistoricalBugsOutput(BaseModel):
    matches: list[HistoricalBugMatch]


class RerankDocument(BaseModel):
    content: str
    metadata: dict = {}


class RerankContextDocumentsOutput(BaseModel):
    ordered_documents: list[RerankDocument]
    relevance_cutoff_applied: bool


class LocateTargetFilesOutput(BaseModel):
    verified_file_paths: list[str]


class ReadCodeBlockSurgicallyOutput(BaseModel):
    file_path: str
    code_segment: str
    total_file_lines: int


class RcaResult(BaseModel):
    file_path: str
    line_number: int
    function_name: str
    failure_mechanism: str


class RemediationResult(BaseModel):
    patch: str
    explanation: str


class SemanticCacheEntry(BaseModel):
    normalized_signature: str
    report: str


class CheckSemanticCacheOutput(BaseModel):
    cache_hit: bool
    cached_report: str | None = None


class EnrichedInsightReport(BaseModel):
    raw_signature: str
    triage: TriageResult
    root_cause: RcaResult | None = None
    remediation: RemediationResult | None = None
