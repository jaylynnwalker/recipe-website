from functools import lru_cache
from pathlib import Path

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Our Kitchen API"
    database_url: str = "sqlite:///./data/our-kitchen.sqlite3"
    media_root: Path = Path("data/media")
    auth_mode: str = "cloudflare"
    cloudflare_access_team_domain: str | None = None
    cloudflare_access_audience: str | None = None
    max_upload_bytes: int = 8 * 1024 * 1024
    allowed_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    household_name: str = "Our Kitchen"
    openai_api_key: SecretStr | None = Field(default=None, validation_alias='OPENAI_API_KEY')
    openai_model: str = Field(default='gpt-6-luna', validation_alias='OPENAI_MODEL')
    model_config = SettingsConfigDict(env_file=".env", env_prefix="OUR_KITCHEN_", extra="ignore")

    @property
    def origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
