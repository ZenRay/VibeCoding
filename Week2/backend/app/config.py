"""应用配置管理"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # 数据库配置
    database_url: str = "sqlite:///../data/meta.db"

    # OpenAI API 配置
    openai_api_key: str | None = None

    # 日志配置
    log_level: str = "info"

    # CORS 配置
    cors_origins: list[str] = ["*"]

    # 应用配置
    app_name: str = "数据库查询工具"
    app_version: str = "0.1.0"
    debug: bool = False


settings = Settings()
