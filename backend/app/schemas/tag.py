"""Tag 相关的 Pydantic 模式"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class TagBase(BaseModel):
    """Tag 基础模式"""

    name: str = Field(..., max_length=50, description="标签名称", example="BACKEND后端")
    color: str = Field(
        default="#6B7280",
        pattern="^#[0-9A-Fa-f]{6}$",
        description="标签颜色（HEX 格式）",
        example="#3B82F6",
    )


class TagCreate(TagBase):
    """创建 Tag 的请求模式"""

    class Config:
        json_schema_extra = {
            "example": {
                "name": "frontend前端",
                "color": "#10B981",
            }
        }


class TagUpdate(BaseModel):
    """更新 Tag 的请求模式"""

    name: Optional[str] = Field(None, max_length=50, description="标签名称")
    color: Optional[str] = Field(None, pattern="^#[0-9A-Fa-f]{6}$", description="标签颜色（HEX 格式）")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "frontend dev前端开发",
                "color": "#10B981",
            }
        }


class Tag(TagBase):
    """Tag 响应模式"""

    id: int
    created_at: datetime
    ticket_count: Optional[int] = Field(None, description="使用该标签的 Ticket 数量")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "name": "BACKEND后端",
                "color": "#3B82F6",
                "created_at": "2026-01-08T10:00:00Z",
                "ticket_count": 15,
            }
        }


class TagList(BaseModel):
    """Tag 列表响应模式"""

    data: List[Tag] = Field(..., description="标签列表")

    class Config:
        json_schema_extra = {
            "example": {
                "data": [
                    {
                        "id": 1,
                        "name": "BACKEND后端",
                        "color": "#3B82F6",
                        "created_at": "2026-01-08T10:00:00Z",
                        "ticket_count": 15,
                    }
                ]
            }
        }
