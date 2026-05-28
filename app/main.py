import json
import time
from pathlib import Path
from typing import Any

import redis
from fastapi import FastAPI, HTTPException, Query

from app.config import settings
from app.models import EnrichedInsightReport, RawBugReport
from app.observability.cost_tracker import log_run
from app.services.query_router import process

app = FastAPI(title="Auto-QA Agent Insights", version="0.1.0")

_redis_client: redis.Redis | None = None


def _get_redis() -> redis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(settings.redis_url, decode_responses=True)
    return _redis_client


def _record_history(report: EnrichedInsightReport) -> None:
    """Push a completed analysis to the recent-history Redis list (capped at 100)."""
    try:
        r = _get_redis()
        r.lpush("recent_analyses", report.model_dump_json())
        r.ltrim("recent_analyses", 0, 99)
    except Exception:
        pass


@app.on_event("startup")
async def seed_vector_store() -> None:
    golden_path = (
        Path(__file__).resolve().parent.parent / "evaluation" / "golden_dataset.json"
    )
    if not golden_path.exists():
        return
    with open(golden_path) as f:
        golden = json.load(f)
    bugs = []
    for entry in golden:
        module = entry["expected"]["failing_module"]
        subsystem = module.split("/")[0] if module and module != "unknown" else ""
        bugs.append(
            {
                "bug_id": entry["id"],
                "signature": entry["payload"],
                "subsystem": subsystem,
                "diagnostic": entry["expected"]["diagnostic_summary"],
                "status": "RESOLVED",
            }
        )
    from app.components.vector_store import index_bugs

    index_bugs(bugs)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "environment": settings.environment}


@app.post("/analyze", response_model=EnrichedInsightReport)
async def analyze(report: RawBugReport) -> EnrichedInsightReport:
    start = time.perf_counter()
    result = process(report)
    duration = (time.perf_counter() - start) * 1000

    log_run(
        input_text=report.payload,
        output=result,
        duration_ms=duration,
    )

    if isinstance(result, dict):
        raise HTTPException(status_code=422, detail=result)

    _record_history(result)
    return result


@app.get("/history")
async def history(limit: int = Query(20, ge=1, le=100)) -> dict[str, Any]:
    try:
        r = _get_redis()
        entries = r.lrange("recent_analyses", 0, limit - 1)
        reports = [json.loads(e) for e in entries]
        return {"results": reports, "count": len(reports)}
    except Exception:
        return {"results": [], "count": 0}
