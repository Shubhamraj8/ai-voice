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

    # Call recording → Supabase Storage (ticket 2.14)
    recordings_bucket: str = "recordings"
    recording_signed_url_ttl_s: int = 3600
    twilio_recording_status_path: str = "/webhooks/twilio/recording"

    # Knowledge base → Supabase Storage (ticket 4.01)
    knowledge_bucket: str = "knowledge"

    # DPDP data export → Supabase Storage (ticket 5.12)
    exports_bucket: str = "exports"
    export_signed_url_ttl_s: int = 604800  # 7 days

    # Error monitoring — Sentry (ticket 5.17). No-op when DSN is unset.
    sentry_dsn: str = ""
    sentry_traces_sample_rate: float = 0.05
    sentry_environment: str = ""
    render_git_commit: str = ""  # release tag from the Render deploy

    # Embeddings + retrieval (tickets 4.03, 4.05)
    openai_api_key: str = ""
    openai_embedding_model: str = "text-embedding-3-small"
    embedding_cache_ttl_s: int = 300

    # Upstash Redis (REST) — query-embedding cache + tool rate limits (4.05, 4.12)
    upstash_redis_url: str = ""
    upstash_redis_token: str = ""

    # Escalation — Resend email + owner notify + portal link (ticket 4.10)
    resend_api_key: str = ""
    escalation_from_email: str = ""
    public_app_base_url: str = "http://localhost:3000"

    # Lead capture — team notification inbox (ticket 5.02)
    leads_notify_email: str = ""

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
