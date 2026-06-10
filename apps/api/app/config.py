from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str
    supabase_url: str
    supabase_service_role_key: str
    cors_origins: str = "http://localhost:3000"
    log_level: str = "INFO"

    # Twilio webhooks (ticket 2.02) — credentials from 2.01
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    public_api_base_url: str = "http://localhost:8000"
    twilio_media_stream_path: str = "/webhooks/twilio/media"
    twilio_signature_validation: bool = True

    # Deepgram (tickets 2.05, 2.07) — Pipecat pipeline + Aura-1 TTS provider
    deepgram_api_key: str = ""
    deepgram_voice: str = "aura-2-helena-en"

    # DeepSeek (ticket 2.09) — V4 Flash via OpenAI-compatible native API
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-v4-flash"
    deepseek_timeout_s: float = 30.0

    # Internal dashboard (ticket 3.01)
    internal_user_email: str = ""

    @property
    def cors_origin_list(self) -> list[str]:
        return [
            origin.strip() for origin in self.cors_origins.split(",") if origin.strip()
        ]


@lru_cache
def get_settings() -> Settings:
    return Settings()
