from app.components import vector_store
from app.components.hybrid_retriever import hybrid_search
from app.models import SearchHistoricalBugsInput


class TestVectorStore:
    def setup_method(self) -> None:
        vector_store.reset()

    def test_index_and_search_returns_similar_bugs(self) -> None:
        bugs = [
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
        ]
        vector_store.index_bugs(bugs)
        results = vector_store.search("database connection timeout", k=5)
        assert len(results) > 0
        assert results[0]["bug_id"] == "BUG-001"
        assert results[0]["similarity_score"] > 0.70

    def test_search_returns_low_score_for_unrelated_query(self) -> None:
        bugs = [
            {
                "bug_id": "BUG-001",
                "signature": "database connection timeout error",
                "subsystem": "db",
                "diagnostic": "pool exhausted",
                "status": "RESOLVED",
            }
        ]
        vector_store.index_bugs(bugs)
        results = vector_store.search("quantum flux capacitor overflow", k=5)
        assert len(results) == 1
        assert results[0]["similarity_score"] < 0.70

    def test_search_respects_k(self) -> None:
        bugs = [
            {
                "bug_id": f"BUG-{i:03d}",
                "signature": f"error type {i}",
                "subsystem": "test",
                "diagnostic": f"diagnostic {i}",
                "status": "RESOLVED",
            }
            for i in range(10)
        ]
        vector_store.index_bugs(bugs)
        results = vector_store.search("error type", k=3)
        assert len(results) <= 3

    def test_index_multiple_batches(self) -> None:
        vector_store.index_bugs(
            [
                {
                    "bug_id": "BUG-001",
                    "signature": "error one",
                    "subsystem": "a",
                    "diagnostic": "d1",
                    "status": "RESOLVED",
                }
            ]
        )
        vector_store.index_bugs(
            [
                {
                    "bug_id": "BUG-002",
                    "signature": "error two",
                    "subsystem": "b",
                    "diagnostic": "d2",
                    "status": "RESOLVED",
                }
            ]
        )
        results = vector_store.search("error", k=5)
        assert len(results) == 2

    def test_search_on_empty_index_returns_empty_list(self) -> None:
        results = vector_store.search("anything at all", k=5)
        assert results == []

    def test_reset_clears_index_and_registry(self) -> None:
        vector_store.index_bugs(
            [
                {
                    "bug_id": "BUG-001",
                    "signature": "some error",
                    "subsystem": "x",
                    "diagnostic": "d",
                    "status": "RESOLVED",
                }
            ]
        )
        vector_store.reset()
        results = vector_store.search("some error", k=5)
        assert results == []

    def test_faiss_and_bm25_fallback_same_interface(self) -> None:
        vector_store.index_bugs(
            [
                {
                    "bug_id": "BUG-099",
                    "signature": "PostgreSQL deadlock detected on table orders",
                    "subsystem": "database",
                    "diagnostic": "Deadlock caused by concurrent transaction on same row",
                    "status": "RESOLVED",
                }
            ]
        )

        result = hybrid_search(
            SearchHistoricalBugsInput(
                cleaned_error_signature="PostgreSQL deadlock on orders table",
                target_subsystem="database",
                limit=3,
            )
        )
        assert len(result.matches) > 0
        assert result.matches[0].bug_id == "BUG-099"
        assert result.matches[0].similarity_score >= 0.70
