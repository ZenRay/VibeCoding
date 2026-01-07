"""Tag API 路由"""

from typing import Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.tag import Tag, TagCreate, TagList, TagUpdate
from app.services.tag_service import TagService
from app.utils.exceptions import BaseAPIException

router = APIRouter()


@router.get(
    "/tags",
    response_model=TagList,
    summary="获取标签列表",
    description="获取所有标签列表，支持排序",
    response_description="返回标签列表",
    tags=["Tags"],
)
async def get_tags(
    sort_by: Optional[str] = Query(
        "name",
        description="排序字段：name（名称）、created_at（创建时间）、usage_count（使用次数）",
        example="name",
    ),
    sort_order: Optional[str] = Query(
        "asc",
        description="排序顺序：asc（升序）或 desc（降序）",
        example="asc",
    ),
    db: Session = Depends(get_db),
):
    """
    获取标签列表

    支持以下排序选项：
    - **name**：按标签名称排序（默认）
    - **created_at**：按创建时间排序
    - **usage_count**：按使用次数排序

    **注意**：
    - 标签名称的英文字符会自动转换为大写（通过数据库触发器）
    - 每个标签会显示使用次数（ticket_count）
    """
    tags = TagService.get_tags(db, sort_by=sort_by or "name", sort_order=sort_order or "asc")
    return {"data": tags}


@router.get(
    "/tags/{tag_id}",
    response_model=Tag,
    summary="获取单个标签",
    description="根据标签 ID 获取详细信息",
    response_description="返回标签详细信息",
    tags=["Tags"],
)
async def get_tag(
    tag_id: int = Path(..., description="标签 ID", ge=1, example=1),
    db: Session = Depends(get_db),
):
    """
    获取单个标签的详细信息

    - **tag_id**: 标签的唯一标识符（必填，≥1）

    返回包含以下信息的标签：
    - 基本信息：名称、颜色
    - 使用次数：ticket_count
    - 创建时间：created_at
    """
    try:
        tag = TagService.get_tag_by_id(db, tag_id)
        return tag
    except BaseAPIException as e:
        raise HTTPException(status_code=404, detail=e.message)


@router.post(
    "/tags",
    response_model=Tag,
    status_code=201,
    summary="创建标签",
    description="创建新标签，标签名称会自动标准化（英文转大写）",
    response_description="返回创建的标签对象",
    tags=["Tags"],
)
async def create_tag(
    tag_data: TagCreate = Body(
        ...,
        description="标签创建数据",
        example={
            "name": "frontend前端",
            "color": "#10B981",
        },
    ),
    db: Session = Depends(get_db),
):
    """
    创建新标签

    **请求体字段**：
    - **name**：标签名称（必填，最大 50 字符）
    - **color**：标签颜色（可选，HEX 格式，默认 #6B7280）

    **标签名称标准化**：
    - 英文字符会自动转换为大写（如 "frontend" → "FRONTEND"）
    - 中文、数字和特殊字符保持原样
    - 自动去除首尾空格
    - 如果标签名称已存在，会返回 409 冲突错误

    **示例**：
    - 输入 "frontend前端" → 存储为 "FRONTEND前端"
    - 输入 "Bug修复" → 存储为 "BUG修复"
    - 输入 "v2.0" → 存储为 "V2.0"
    """
    try:
        tag = TagService.create_tag(db, tag_data)
        return tag
    except BaseAPIException as e:
        if e.code == "CONFLICT":
            raise HTTPException(status_code=409, detail=e.message)
        raise HTTPException(status_code=400, detail=e.message)


@router.put(
    "/tags/{tag_id}",
    response_model=Tag,
    summary="更新标签",
    description="更新标签的名称和颜色，名称会自动标准化",
    response_description="返回更新后的标签对象",
    tags=["Tags"],
)
async def update_tag(
    tag_id: int = Path(..., description="标签 ID", ge=1, example=1),
    tag_data: TagUpdate = Body(
        ...,
        description="标签更新数据",
        example={
            "name": "frontend dev前端开发",
            "color": "#10B981",
        },
    ),
    db: Session = Depends(get_db),
):
    """
    更新标签信息

    **可更新字段**：
    - **name**：标签名称（会自动标准化）
    - **color**：标签颜色（HEX 格式）

    **注意**：
    - 更新名称时同样会自动标准化（英文转大写）
    - 如果新名称与其他标签冲突，会返回 409 错误
    """
    try:
        tag = TagService.update_tag(db, tag_id, tag_data)
        return tag
    except BaseAPIException as e:
        if e.code == "CONFLICT":
            raise HTTPException(status_code=409, detail=e.message)
        raise HTTPException(status_code=404, detail=e.message)


@router.delete(
    "/tags/{tag_id}",
    status_code=204,
    summary="删除标签",
    description="删除标签，同时删除所有关联关系",
    tags=["Tags"],
)
async def delete_tag(
    tag_id: int = Path(..., description="标签 ID", ge=1, example=1),
    db: Session = Depends(get_db),
):
    """
    删除标签

    **注意**：
    - 删除标签时会同时删除所有 Ticket 与标签的关联关系（CASCADE）
    - 此操作不可逆，请谨慎使用
    """
    try:
        TagService.delete_tag(db, tag_id)
        return None
    except BaseAPIException as e:
        raise HTTPException(status_code=404, detail=e.message)
