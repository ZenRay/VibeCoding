"""
应用配置管理
"""
import os
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()


class Config:
    """应用配置类"""
    
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    
    # CORS 配置
    CORS_ORIGINS = [
        "http://localhost:5173",  # Vite 默认端口
        "http://127.0.0.1:5173",
    ]
    
    @classmethod
    def validate(cls):
        """验证必需的配置项"""
        if not cls.GEMINI_API_KEY:
            print("Warning: GEMINI_API_KEY is not set. Using stub mode for image generation.")


config = Config()
config.validate()
