from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # App
    APP_NAME: str = "Stock Market Advisor"
    APP_ENV: str = "development"
    DEBUG: bool = False
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Database
    DATABASE_URL: str
    SYNC_DATABASE_URL: Optional[str] = None

    # Redis
    REDIS_URL: str
    CACHE_TTL_SECONDS: int = 300

    # OpenAI
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o"

    # News
    NEWS_API_KEY: str = ""

    # Telegram
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_CHAT_ID: str = ""

    # Email
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    ALERT_EMAIL_TO: str = ""

    # Portfolio Rules
    MAX_SINGLE_STOCK_ALLOCATION: float = 10.0   # percent
    MAX_SINGLE_SECTOR_ALLOCATION: float = 25.0  # percent

    # Scheduler
    PRE_MARKET_ANALYSIS_TIME: str = "08:00"
    INTRADAY_INTERVAL_MINUTES: int = 30
    POST_MARKET_ANALYSIS_TIME: str = "16:00"
    DAILY_REPORT_TIME: str = "17:00"
    WEEKLY_REPORT_DAY: str = "friday"

    # CORS
    ALLOWED_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:5173"]

    @property
    def sync_db_url(self) -> str:
        if self.SYNC_DATABASE_URL:
            return self.SYNC_DATABASE_URL
        return self.DATABASE_URL.replace("+asyncpg", "")


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
