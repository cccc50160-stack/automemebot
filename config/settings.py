import os
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    # Telegram Main Bot
    telegram_bot_token: str = Field(default="")
    telegram_channel_id: str = Field(default="")
    telegram_channel_username: str = Field(default="")

    # Telegram Logger Bot
    logger_bot_token: str = Field(default="")
    admin_chat_id: int = Field(default=0)

    # Groq API
    groq_api_key: str = Field(default="")
    groq_model: str = Field(default="llama-3.1-70b-versatile")

    # HuggingFace (optional)
    hf_api_token: str = Field(default="")

    # Database
    db_host: str = Field(default="localhost")
    db_port: int = Field(default=5432)
    db_name: str = Field(default="automemebot")
    db_user: str = Field(default="botuser")
    db_password: str = Field(default="secure_password")

    # Redis
    redis_host: str = Field(default="localhost")
    redis_port: int = Field(default=6379)

    # Reddit API (optional)
    reddit_client_id: str = Field(default="")
    reddit_client_secret: str = Field(default="")
    reddit_user_agent: str = Field(default="AutoMemeBot/1.0")

    # System settings
    log_level: str = Field(default="INFO")
    max_queue_size: int = Field(default=50)
    min_queue_size: int = Field(default=10)
    posts_per_day: int = Field(default=3)

    # Logging settings
    enable_telegram_logging: bool = Field(default=True)
    log_batch_interval: int = Field(default=300)
    daily_report_time: str = Field(default="23:00")
    weekly_report_day: str = Field(default="sunday")
    weekly_report_time: str = Field(default="20:00")

    @property
    def database_url(self) -> str:
        return f"postgresql+asyncpg://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

    @property
    def database_url_sync(self) -> str:
        return f"postgresql+psycopg2://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

    @property
    def redis_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/0"

    @property
    def data_dir(self) -> Path:
        return BASE_DIR / "data"

    @property
    def templates_dir(self) -> Path:
        return self.data_dir / "meme_templates"

    @property
    def fonts_dir(self) -> Path:
        return self.data_dir / "fonts"

    class Config:
        env_file = str(BASE_DIR / ".env")
        env_file_encoding = "utf-8"


settings = Settings()
