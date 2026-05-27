from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    environment: str = "development"
    openai_api_key: str = ""
    llm_model: str = "gpt-4o-mini"
    redis_url: str = "redis://localhost:6379/0"
    semantic_cache_distance_threshold: float = 0.3


settings = Settings()
