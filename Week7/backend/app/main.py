"""
FastAPI 主应用
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.core.config import config
from app.api.endpoints import router
import logging
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('api.log', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)

app = FastAPI(
    title="AI Slide Generator API",
    description="Backend API for AI-powered slide generation",
    version="1.0.0"
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件目录
assets_dir = Path(__file__).parent.parent.parent / "assets"
assets_dir.mkdir(exist_ok=True)
app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

# 注册路由
app.include_router(router)


@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    logger.info("AI Slide Generator API starting up...")
    logger.info(f"CORS origins: {config.CORS_ORIGINS}")
    logger.info(f"Gemini API configured: {bool(config.GEMINI_API_KEY)}")


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    logger.info("AI Slide Generator API shutting down...")


@app.get("/")
async def root():
    """根路径"""
    return {"message": "AI Slide Generator API", "docs": "/docs"}
