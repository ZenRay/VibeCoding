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
    AI_MODE: str = os.getenv("AI_MODE", "stub")  # "stub" or "real"
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-image")  # 默认使用 Flash 模型
    AI_PROVIDER: str = os.getenv("AI_PROVIDER", "google")  # "google" or "openrouter"
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
    OPENROUTER_MODEL: str = os.getenv("OPENROUTER_MODEL", "google/gemini-2.5-flash-image")
    
    # Image generation configuration
    IMAGE_SIZE: str = os.getenv("IMAGE_SIZE", "1K")  # "1K", "2K", "4K"
    IMAGE_ASPECT_RATIO: str = os.getenv("IMAGE_ASPECT_RATIO", "16:9")  # "16:9", "4:3", "1:1"
    
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    
    # CORS 配置
    CORS_ORIGINS = [
        "http://localhost:5173",  # Vite 默认端口
        "http://127.0.0.1:5173",
        "http://localhost:5174",  # Vite 备用端口
        "http://127.0.0.1:5174",
    ]
    
    @classmethod
    def validate(cls):
        """验证必需的配置项"""
        print(f"INFO: Image configuration - Size: {cls.IMAGE_SIZE}, Aspect ratio: {cls.IMAGE_ASPECT_RATIO}")
        
        if cls.AI_MODE == "real":
            if cls.AI_PROVIDER == "openrouter":
                if not cls.OPENROUTER_API_KEY:
                    print("Error: AI_PROVIDER is 'openrouter' but OPENROUTER_API_KEY is not set!")
                    print("Get your API key from: https://openrouter.ai/keys")
                else:
                    print(f"INFO: Running in REAL AI mode (AI_PROVIDER=openrouter)")
                    print(f"INFO: Using model: {cls.OPENROUTER_MODEL}")
            else:  # google
                if not cls.GEMINI_API_KEY:
                    print("Error: AI_MODE is 'real' but GEMINI_API_KEY is not set!")
                    print("Please set GEMINI_API_KEY in .env file or change AI_MODE to 'stub'")
                else:
                    print(f"INFO: Running in REAL AI mode (AI_PROVIDER=google)")
                    print(f"INFO: Using model: {cls.GEMINI_MODEL}")
        elif cls.AI_MODE == "stub":
            print(f"INFO: Running in STUB mode (AI_MODE={cls.AI_MODE})")
        else:
            print(f"INFO: Running in REAL AI mode (AI_MODE={cls.AI_MODE})")


config = Config()
config.validate()
