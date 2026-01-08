"""API v1 路由"""

from fastapi import APIRouter
from fastapi.responses import JSONResponse

# 创建 API v1 路由器
api_router = APIRouter()


@api_router.get(
    "",
    summary="API v1 根端点",
    description="返回 API v1 版本信息和可用端点",
    tags=["API"],
)
async def api_v1_root():
    """
    API v1 根端点

    返回 API 版本信息和主要端点列表
    """
    return JSONResponse(
        content={
            "version": "1.0.0",
            "name": "Project Alpha API",
            "description": "基于标签的 Ticket 管理系统 API",
            "endpoints": {
                "tickets": "/api/v1/tickets",
                "tags": "/api/v1/tags",
                "health": "/health",
                "docs": "/docs",
                "redoc": "/redoc",
            },
            "resources": {
                "tickets": {
                    "list": "GET /api/v1/tickets",
                    "get": "GET /api/v1/tickets/{id}",
                    "create": "POST /api/v1/tickets",
                    "update": "PUT /api/v1/tickets/{id}",
                    "delete": "DELETE /api/v1/tickets/{id}",
                    "restore": "POST /api/v1/tickets/{id}/restore",
                    "toggle_status": "PATCH /api/v1/tickets/{id}/toggle-status",
                    "add_tag": "POST /api/v1/tickets/{id}/tags",
                    "remove_tag": "DELETE /api/v1/tickets/{id}/tags/{tag_id}",
                },
                "tags": {
                    "list": "GET /api/v1/tags",
                    "get": "GET /api/v1/tags/{id}",
                    "create": "POST /api/v1/tags",
                    "update": "PUT /api/v1/tags/{id}",
                    "delete": "DELETE /api/v1/tags/{id}",
                },
            },
        }
    )


# 导入并注册各个路由模块
from app.api.v1 import tags, tickets

api_router.include_router(tickets.router, tags=["Tickets"])
api_router.include_router(tags.router, tags=["Tags"])
