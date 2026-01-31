"""
FastAPI 主应用
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import config
from app.api.endpoints import router

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

# 注册路由
app.include_router(router)


@app.get("/")
async def root():
    """根路径"""
    return {"message": "AI Slide Generator API", "docs": "/docs"}
