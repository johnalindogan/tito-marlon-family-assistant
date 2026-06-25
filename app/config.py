from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    openai_api_key: str = ""
    openai_model: str = "gpt-4.1-mini"
    openai_image_model: str = "gpt-image-1"
    database_url: str = ""
    app_env: str = "development"
    log_level: str = "INFO"
    message_max_length: int = Field(default=2000, ge=1, le=10000)
    media_public_base_url: str = ""
    r2_account_id: str = ""
    r2_bucket_name: str = ""
    r2_access_key_id: str = ""
    r2_secret_access_key: str = ""
    john_messenger_sender_id: str = ""
    john_notify_webhook_url: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()
