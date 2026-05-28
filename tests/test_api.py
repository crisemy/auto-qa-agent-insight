import json
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.main import app
from app.models import EnrichedInsightReport, Severity, TriageResult

client = TestClient(app)


class TestAnalyzeEndpoint:
    @patch("app.main.process")
    def test_analyze_success(self, mock_process):
        mock_process.return_value = EnrichedInsightReport(
            raw_signature="ValueError: invalid input",
            triage=TriageResult(
                severity=Severity.major,
                failing_module="app/services/parser.py",
                normalized_signature="ValueError: invalid input",
                exception_type="ValueError",
            ),
        )
        resp = client.post("/analyze", json={"payload": "ValueError: invalid input"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["triage"]["severity"] == "Major"
        assert data["triage"]["exception_type"] == "ValueError"
        assert data["triage"]["failing_module"] == "app/services/parser.py"
        assert data["raw_signature"] == "ValueError: invalid input"

    @patch("app.main.process")
    def test_analyze_rejected_input(self, mock_process):
        mock_process.return_value = {
            "error": "INPUT_REJECTED",
            "reason": "Prompt injection detected: ['sql_injection']",
        }
        resp = client.post(
            "/analyze", json={"payload": "DROP TABLE users; SELECT * FROM secrets"}
        )
        assert resp.status_code == 422
        detail = resp.json()["detail"]
        assert detail["error"] == "INPUT_REJECTED"

    @patch("app.main.process")
    def test_analyze_insufficient_context(self, mock_process):
        mock_process.return_value = {
            "error": "INSUFFICIENT_CONTEXT",
            "message": "Insufficient context to safely diagnose this error",
        }
        resp = client.post("/analyze", json={"payload": "obscure error in unknown module"})
        assert resp.status_code == 422
        assert resp.json()["detail"]["error"] == "INSUFFICIENT_CONTEXT"

    def test_analyze_missing_payload(self):
        resp = client.post("/analyze", json={})
        assert resp.status_code == 422


class TestHistoryEndpoint:
    @patch("app.main._get_redis")
    def test_history_returns_entries(self, mock_get_redis):
        mock_redis = MagicMock()
        mock_redis.lrange.return_value = [
            json.dumps(
                {
                    "raw_signature": "test error",
                    "triage": {
                        "severity": "Major",
                        "failing_module": "app/test.py",
                        "normalized_signature": "test error",
                        "exception_type": "ValueError",
                    },
                    "root_cause": None,
                    "remediation": None,
                }
            )
        ]
        mock_get_redis.return_value = mock_redis
        resp = client.get("/history?limit=10")
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 1
        assert data["results"][0]["triage"]["severity"] == "Major"

    @patch("app.main._get_redis")
    def test_history_empty(self, mock_get_redis):
        mock_redis = MagicMock()
        mock_redis.lrange.return_value = []
        mock_get_redis.return_value = mock_redis
        resp = client.get("/history")
        assert resp.status_code == 200
        assert resp.json()["count"] == 0

    @patch("app.main._get_redis")
    def test_history_default_limit(self, mock_get_redis):
        mock_redis = MagicMock()
        mock_redis.lrange.return_value = []
        mock_get_redis.return_value = mock_redis
        client.get("/history")
        mock_redis.lrange.assert_called_with("recent_analyses", 0, 19)

    @patch("app.main._get_redis")
    def test_history_fallback_on_redis_error(self, mock_get_redis):
        mock_get_redis.side_effect = ConnectionError("Redis down")
        resp = client.get("/history")
        assert resp.status_code == 200
        assert resp.json() == {"results": [], "count": 0}
