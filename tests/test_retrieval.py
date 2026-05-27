from app.components import vector_store
from app.components.hybrid_retriever import hybrid_search
from app.components.reranker import rerank
from app.models import (
    QueryRewriterInput,
    RerankContextDocumentsInput,
    RerankDocument,
    SearchHistoricalBugsInput,
)
from app.services.query_rewriter import query_rewriter


class TestQueryRewriter:
    def test_strips_timestamps(self):
        payload = "2025-03-15 14:23:01,456 ERROR: connection refused"
        result = query_rewriter(QueryRewriterInput(raw_log_payload=payload))
        assert "2025-03-15" not in result.normalized_signature
        assert "connection refused" in result.normalized_signature

    def test_strips_pid(self):
        payload = "[PID:7421] ValueError: null in data"
        result = query_rewriter(QueryRewriterInput(raw_log_payload=payload))
        assert "7421" not in result.normalized_signature
        assert "ValueError" in result.normalized_signature

    def test_strips_memory_address(self):
        payload = "Segfault at 0x7f8c4a0b6c00 in module"
        result = query_rewriter(QueryRewriterInput(raw_log_payload=payload))
        assert "0x7f8c4a0b6c00" not in result.normalized_signature

    def test_extracts_exception_type(self):
        payload = "KeyError: 'missing_field'"
        result = query_rewriter(QueryRewriterInput(raw_log_payload=payload))
        assert result.extracted_exception_type == "KeyError"

    def test_empty_payload(self):
        result = query_rewriter(QueryRewriterInput(raw_log_payload=""))
        assert result.normalized_signature == ""
        assert result.extracted_exception_type == ""


class TestHybridSearch:
    def setup_method(self) -> None:
        vector_store.reset()
        vector_store.index_bugs(
            [
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
        )

    def test_returns_matching_bugs(self):
        result = hybrid_search(
            SearchHistoricalBugsInput(
                cleaned_error_signature="database connection timeout",
                target_subsystem="database",
                limit=5,
            )
        )
        assert len(result.matches) > 0
        assert result.matches[0].bug_id == "BUG-001"

    def test_returns_empty_below_threshold(self):
        result = hybrid_search(
            SearchHistoricalBugsInput(
                cleaned_error_signature="quantum flux capacitor overflow",
                target_subsystem="",
                limit=5,
            )
        )
        assert result.matches == []

    def test_respects_limit(self):
        result = hybrid_search(
            SearchHistoricalBugsInput(
                cleaned_error_signature="error",
                target_subsystem="",
                limit=1,
            )
        )
        assert len(result.matches) <= 1


class TestReranker:
    def test_orders_by_relevance(self):
        docs = [
            RerankDocument(content="database timeout issue"),
            RerankDocument(content="unrelated UI bug"),
        ]
        result = rerank(
            RerankContextDocumentsInput(
                query="database connection timeout", documents=docs
            )
        )
        assert result.ordered_documents[0].content == "database timeout issue"

    def test_applies_cutoff_for_irrelevant(self):
        docs = [
            RerankDocument(content="buy milk and eggs"),
            RerankDocument(content="completely unrelated"),
        ]
        result = rerank(
            RerankContextDocumentsInput(query="database error", documents=docs)
        )
        assert result.relevance_cutoff_applied is True
