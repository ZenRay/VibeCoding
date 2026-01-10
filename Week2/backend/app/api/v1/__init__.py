"""API v1 路由"""

from fastapi import APIRouter

from app.api.v1 import dbs, query

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(dbs.router)
api_router.include_router(query.router)
