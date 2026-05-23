from fastapi import FastAPI

from app.config import settings

app = FastAPI(title="Auto-QA Agent Insights", version="0.1.0")


@app.get("/health")
async def health():
    return {"status": "ok", "environment": settings.environment}
