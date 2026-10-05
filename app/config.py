from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "openbb-bot-multi-engine"
    APP_ENV: str = "development"
    REDIS_URL: str = "redis://localhost:6379/0"
    OPENAI_API_KEY: str = ""
    MODEL_NAME: str = "gpt-4o-mini"
    DISCORD_TOKEN: str = ""
    TELEGRAM_TOKEN: str = ""
    SLACK_BOT_TOKEN: str = ""
    SLACK_SIGNING_SECRET: str = ""
    GMAIL_WEBHOOK_SECRET: str = ""
    AGENT_TIMEOUT_SECONDS: int = 30
    MCP_CONFIG_PATH: str = "mcp_servers_config.json"
    MCP_HOT_RELOAD_INTERVAL: float = 2.0

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
