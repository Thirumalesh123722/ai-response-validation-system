from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    groq_api_key: str = ""
    groq_model: str = "qwen/qwen3.8-27b"
    groq_timeout: int = 90
    groq_inter_call_delay: float = 2.0
    chroma_persist_dir: str = "./data/chroma"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:5174,http://127.0.0.1:5174"

    database_url: str = "postgresql://postgres:testpass@localhost:5432/ai_eval_test"
    jwt_secret: str = "dev-only-secret-change-me-before-deploying"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 30

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
