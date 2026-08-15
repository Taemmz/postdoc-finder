from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Supabase
    SKILLEDGEUP_SUPABASE_PROJECT_REF: str
    SKILLEDGEUP_SUPABASE_SERVICE_ROLE_KEY: str

    # Search APIs
    SERPER_API_KEY: str
    SERPAPI_API_KEY: str
    EXA_API_KEY: str

    # Telegram
    TELEGRAM_POSTDOC_BOT_TOKEN: str
    TELEGRAM_POSTDOC_CHAT_ID: str

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
