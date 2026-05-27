from __future__ import annotations

import time

from openai import OpenAI

from app.config import settings
from app.observability.cost_tracker import log_run

_client: OpenAI | None = None

_MODEL_PRICING: dict[str, dict[str, float]] = {
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-4o": {"input": 2.50, "output": 10.00},
}


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is not configured")
        _client = OpenAI(api_key=settings.openai_api_key)
    return _client


def _estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    pricing = _MODEL_PRICING.get(model, {"input": 0.15, "output": 0.60})
    input_cost = (input_tokens / 1_000_000) * pricing["input"]
    output_cost = (output_tokens / 1_000_000) * pricing["output"]
    return input_cost + output_cost


def call_llm(system_prompt: str, user_message: str, model: str | None = None) -> str:
    client = _get_client()
    model_name = model or settings.llm_model

    start = time.time()
    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
    )
    duration_ms = (time.time() - start) * 1000

    output_text = response.choices[0].message.content or ""

    usage = response.usage
    if usage:
        input_tokens = usage.prompt_tokens
        output_tokens = usage.completion_tokens
    else:
        input_tokens = len(system_prompt + user_message) // 4
        output_tokens = len(output_text) // 4

    cost_usd = _estimate_cost(model_name, input_tokens, output_tokens)

    log_run(
        input_text=system_prompt + user_message,
        output=output_text,
        duration_ms=duration_ms,
        model=model_name,
        cost_usd=cost_usd,
    )

    return output_text
