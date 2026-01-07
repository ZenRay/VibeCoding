"""Ticket 相关的 Pydantic 模式"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

from app.schemas.tag import Tag


class TicketBase(BaseModel):
    """Ticket 基础模式"""

    title: str = Field(..., max_length=200, description="Ticket 标题", example="实现用户认证功能")
    description: Optional[str] = Field(None, max_length=5000, description="Ticket 详细描述", example="添加 JWT 认证机制")


class TicketCreate(TicketBase):
    """创建 Ticket 的请求模式"""

    tag_ids: Optional[List[int]] = Field(None, description="关联的标签 ID 列表", example=[1, 2])

    class Config:
        json_schema_extra = {
            "example": {
                "title": "实现用户认证功能",
                "description": "添加 JWT 认证机制，包括登录、注册和令牌刷新",
                "tag_ids": [1, 2],
            }
        }


class TicketUpdate(BaseModel):
    """更新 Ticket 的请求模式"""

    title: Optional[str] = Field(None, max_length=200, description="Ticket 标题")
    description: Optional[str] = Field(None, max_length=5000, description="Ticket 详细描述")

    class Config:
        json_schema_extra = {
            "example": {
                "title": "实现用户认证功能（更新）",
                "description": "添加 JWT 认证机制和刷新令牌",
            }
        }


class Ticket(TicketBase):
    """Ticket 响应模式"""

    id: int
    status: str = Field(..., description="Ticket 状态", example="pending")
    tags: List[Tag] = Field(default_factory=list, description="关联的标签列表")
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "title": "实现用户认证功能",
                "description": "添加 JWT 认证机制",
                "status": "pending",
                "tags": [
                    {"id": 1, "name": "BACKEND后端", "color": "#3B82F6"},
                    {"id": 2, "name": "HIGH高优先级", "color": "#EF4444"},
                ],
                "created_at": "2026-01-08T10:00:00Z",
                "updated_at": "2026-01-08T10:00:00Z",
                "completed_at": None,
                "deleted_at": None,
            }
        }


class TicketQueryParams(BaseModel):
    """Ticket 查询参数模式"""

    status: str = "all"
    include_deleted: bool = False
    only_deleted: bool = False
    tag_ids: Optional[List[int]] = None
    tag_filter: str = "and"
    search: Optional[str] = None
    sort_by: str = "created_at"
    sort_order: str = "desc"
    page: int = 1
    page_size: int = 20

    class Config:
        from_attributes = True


class TicketList(BaseModel):
    """Ticket 列表响应模式（含分页）"""

    data: List[Ticket] = Field(..., description="Ticket 列表")
    pagination: dict = Field(..., description="分页信息")

    class Config:
        json_schema_extra = {
            "example": {
                "data": [
                    {
                        "id": 1,
                        "title": "实现用户认证功能",
                        "description": "添加 JWT 认证机制",
                        "status": "pending",
                        "tags": [{"id": 1, "name": "BACKEND后端", "color": "#3B82F6"}],
                        "created_at": "2026-01-08T10:00:00Z",
                        "updated_at": "2026-01-08T10:00:00Z",
                        "completed_at": None,
                        "deleted_at": None,
                    }
                ],
                "pagination": {"page": 1, "page_size": 20, "total": 42, "total_pages": 3},
            }
        }
