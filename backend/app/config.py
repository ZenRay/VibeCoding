"""应用配置管理"""

from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import List, Union


class Settings(BaseSettings):
    """应用配置"""

    # 数据库配置
    database_url: str = "postgresql://ticketuser:ticketpass123@localhost:5432/ticketdb"

    # 应用配置
    environment: str = "development"
    api_v1_prefix: str = "/api/v1"

    # CORS 配置（支持逗号分隔的字符串或列表）
    cors_origins: Union[str, List[str]] = "http://localhost:5173,http://localhost:3000"

    # 日志配置
    log_level: str = "info"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """解析 CORS origins，支持逗号分隔的字符串"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
