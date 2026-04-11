from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Telegram
    telegram_bot_token: str
    telegram_webhook_secret: str
    telegram_allowed_chat_id: int

    # OpenRouter
    openrouter_api_key: str
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    model_vision: str = "anthropic/claude-sonnet-4-6"
    model_fast: str = "anthropic/claude-haiku-4-5"

    # Supabase
    supabase_url: str = ""
    supabase_service_key: str = ""

    # Observability (SigNoz / OpenTelemetry)
    signoz_otlp_endpoint: str = "https://signoz-otel.nathanfiorito.com.br"
    otel_service_name: str = "personal-finances-backend"



settings = Settings()
