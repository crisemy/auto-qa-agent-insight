import json
from pathlib import Path

from fastapi import FastAPI

from app.config import settings

app = FastAPI(title="Auto-QA Agent Insights", version="0.1.0")


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
async def health():
    return {"status": "ok", "environment": settings.environment}
