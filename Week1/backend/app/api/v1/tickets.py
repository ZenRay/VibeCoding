"""Ticket API 路由"""

from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.ticket import Ticket, TicketCreate, TicketList, TicketQueryParams, TicketUpdate
from app.services.ticket_service import TicketService
from app.utils.exceptions import BaseAPIException

router = APIRouter()


@router.get(
    "/tickets",
    response_model=TicketList,
    summary="获取 Ticket 列表",
    description="获取 Ticket 列表，支持多种过滤、搜索和排序选项",
    response_description="返回 Ticket 列表和分页信息",
    tags=["Tickets"],
)
async def get_tickets(
    status: str | None = Query(
        None,
        description="Ticket 状态过滤",
        example="pending",
    ),
    include_deleted: bool = Query(
        False,
        description="是否包含已删除的 Ticket",
    ),
    only_deleted: bool = Query(
        False,
        description="仅显示已删除的 Ticket（回收站）",
    ),
    tag_ids: str | None = Query(
        None,
        description="标签 ID 列表，逗号分隔",
        example="1,2,3",
    ),
    tag_filter: str | None = Query(
        "and",
        description="标签过滤逻辑：and（同时包含所有标签）或 or（包含任一标签）",
        example="and",
    ),
    search: str | None = Query(
        None,
        description="搜索关键词（搜索标题）",
        example="认证",
    ),
    sort_by: str | None = Query(
        "created_at",
        description="排序字段：created_at（创建时间）、updated_at（更新时间）、title（标题）",
        example="created_at",
    ),
    sort_order: str | None = Query(
        "desc",
        description="排序顺序：asc（升序）或 desc（降序）",
        example="desc",
    ),
    page: int = Query(1, ge=1, description="页码，从 1 开始"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量，最大 100"),
    db: Session = Depends(get_db),
):
    """
    获取 Ticket 列表

    支持以下功能：
    - **状态过滤**：pending（未完成）、completed（已完成）、all（全部）
    - **软删除过滤**：include_deleted（包含已删除）、only_deleted（仅已删除）
    - **标签过滤**：支持多标签 AND/OR 逻辑
    - **全文搜索**：基于 PostgreSQL 全文搜索，搜索标题
    - **排序**：按创建时间、更新时间或标题排序
    - **分页**：支持分页查询

    **示例查询**：
    - 获取所有未完成的 Ticket：`?status=pending`
    - 搜索包含"认证"的 Ticket：`?search=认证`
    - 获取包含标签 1 和 2 的 Ticket：`?tag_ids=1,2&tag_filter=and`
    - 查看回收站：`?only_deleted=true`
    """
    # 解析 tag_ids
    tag_id_list = None
    if tag_ids:
        try:
            tag_id_list = [int(id.strip()) for id in tag_ids.split(",")]
        except ValueError:
            raise HTTPException(status_code=400, detail="tag_ids 格式错误，应为逗号分隔的数字")

    # 构建查询参数
    params = TicketQueryParams(
        status=status or "all",
        include_deleted=include_deleted,
        only_deleted=only_deleted,
        tag_ids=tag_id_list,
        tag_filter=tag_filter or "and",
        search=search,
        sort_by=sort_by or "created_at",
        sort_order=sort_order or "desc",
        page=page,
        page_size=page_size,
    )

    result = TicketService.get_tickets(db, params)
    return result.to_dict()


@router.get(
    "/tickets/{ticket_id}",
    response_model=Ticket,
    summary="获取单个 Ticket",
    description="根据 Ticket ID 获取详细信息，包括关联的标签",
    response_description="返回 Ticket 详细信息",
    tags=["Tickets"],
)
async def get_ticket(
    ticket_id: int = Path(..., description="Ticket ID", ge=1, example=1),
    include_deleted: bool = Query(
        False,
        description="是否包含已删除的 Ticket",
    ),
    db: Session = Depends(get_db),
):
    """
    获取单个 Ticket 的详细信息

    - **ticket_id**: Ticket 的唯一标识符（必填，≥1）
    - **include_deleted**: 是否包含已删除的 Ticket（可选，默认 false）

    返回包含以下信息的 Ticket：
    - 基本信息：标题、描述、状态
    - 关联标签列表
    - 时间戳：创建、更新、完成、删除时间
    """
    try:
        ticket = TicketService.get_ticket_by_id(db, ticket_id, include_deleted)
        return ticket
    except BaseAPIException as e:
        raise HTTPException(status_code=404, detail=e.message)


@router.post(
    "/tickets",
    response_model=Ticket,
    status_code=201,
    summary="创建 Ticket",
    description="创建新的 Ticket，可以同时关联多个标签",
    response_description="返回创建的 Ticket 对象",
    tags=["Tickets"],
)
async def create_ticket(
    ticket_data: TicketCreate = Body(
        ...,
        description="Ticket 创建数据",
        example={
            "title": "实现用户认证功能",
            "description": "添加 JWT 认证机制",
            "tag_ids": [1, 2],
        },
    ),
    db: Session = Depends(get_db),
):
    """
    创建新的 Ticket

    **请求体字段**：
    - **title**：Ticket 标题（必填，最大 200 字符）
    - **description**：Ticket 描述（可选，最大 5000 字符）
    - **tag_ids**：关联的标签 ID 列表（可选）

    **注意**：
    - 如果指定的标签不存在，会返回 404 错误
    - 创建的 Ticket 默认状态为 "pending"（未完成）
    """
    try:
        ticket = TicketService.create_ticket(db, ticket_data)
        return ticket
    except BaseAPIException as e:
        raise HTTPException(status_code=404, detail=e.message)


@router.put(
    "/tickets/{ticket_id}",
    response_model=Ticket,
    summary="更新 Ticket",
    description="更新 Ticket 的标题和描述",
    response_description="返回更新后的 Ticket 对象",
    tags=["Tickets"],
)
async def update_ticket(
    ticket_id: int = Path(..., description="Ticket ID", ge=1, example=1),
    ticket_data: TicketUpdate = Body(
        ...,
        description="Ticket 更新数据",
        example={"title": "更新后的标题", "description": "更新后的描述"},
    ),
    db: Session = Depends(get_db),
):
    """
    更新 Ticket 信息

    **可更新字段**：
    - **title**：Ticket 标题
    - **description**：Ticket 描述

    **注意**：
    - 只能更新标题和描述，不能更新状态、标签等
    - 已删除的 Ticket 无法更新
    """
    try:
        ticket = TicketService.update_ticket(db, ticket_id, ticket_data)
        return ticket
    except BaseAPIException as e:
        raise HTTPException(status_code=404, detail=e.message)


@router.delete(
    "/tickets/{ticket_id}",
    status_code=204,
    summary="删除 Ticket",
    description="删除 Ticket（默认软删除，可选永久删除）",
    tags=["Tickets"],
)
async def delete_ticket(
    ticket_id: int = Path(..., description="Ticket ID", ge=1, example=1),
    permanent: bool = Query(
        False,
        description="是否永久删除（true=永久删除，false=软删除）",
    ),
    db: Session = Depends(get_db),
):
    """
    删除 Ticket

    **删除方式**：
    - **软删除**（默认）：标记为已删除，可以恢复
    - **永久删除**：永久删除，无法恢复

    **注意**：
    - 软删除的 Ticket 可以通过 `/tickets/{id}/restore` 恢复
    - 永久删除操作不可逆，请谨慎使用
    """
    try:
        TicketService.delete_ticket(db, ticket_id, permanent)
        return None
    except BaseAPIException as e:
        raise HTTPException(status_code=404, detail=e.message)


@router.post(
    "/tickets/{ticket_id}/restore",
    response_model=Ticket,
    summary="恢复已删除的 Ticket",
    description="恢复软删除的 Ticket",
    response_description="返回恢复后的 Ticket 对象",
    tags=["Tickets"],
)
async def restore_ticket(
    ticket_id: int = Path(..., description="Ticket ID", ge=1, example=1),
    db: Session = Depends(get_db),
):
    """
    恢复已删除的 Ticket

    将软删除的 Ticket 恢复到正常状态。

    **注意**：
    - 只能恢复软删除的 Ticket
    - 永久删除的 Ticket 无法恢复
    """
    try:
        ticket = TicketService.restore_ticket(db, ticket_id)
        return ticket
    except BaseAPIException as e:
        if e.code == "VALIDATION_ERROR":
            raise HTTPException(status_code=400, detail=e.message)
        raise HTTPException(status_code=404, detail=e.message)


@router.patch(
    "/tickets/{ticket_id}/toggle-status",
    response_model=Ticket,
    summary="切换 Ticket 完成状态",
    description="切换 Ticket 的完成状态（pending ↔ completed）",
    response_description="返回更新后的 Ticket 对象",
    tags=["Tickets"],
)
async def toggle_ticket_status(
    ticket_id: int = Path(..., description="Ticket ID", ge=1, example=1),
    db: Session = Depends(get_db),
):
    """
    切换 Ticket 完成状态

    在以下状态之间切换：
    - **pending**（未完成）→ **completed**（已完成）
    - **completed**（已完成）→ **pending**（未完成）

    **注意**：
    - 状态切换时会自动更新 `completed_at` 字段（通过数据库触发器）
    - 已删除的 Ticket 无法切换状态
    """
    try:
        ticket = TicketService.toggle_ticket_status(db, ticket_id)
        return ticket
    except BaseAPIException as e:
        raise HTTPException(status_code=404, detail=e.message)


@router.post(
    "/tickets/{ticket_id}/tags",
    response_model=Ticket,
    summary="为 Ticket 添加标签",
    description="为 Ticket 添加一个标签",
    response_description="返回更新后的 Ticket 对象",
    tags=["Tickets"],
)
async def add_tag_to_ticket(
    ticket_id: int = Path(..., description="Ticket ID", ge=1, example=1),
    tag_id: int = Body(..., embed=True, description="标签 ID", example=1),
    db: Session = Depends(get_db),
):
    """
    为 Ticket 添加标签

    **请求体**：
    ```json
    {
      "tag_id": 1
    }
    ```

    **注意**：
    - 如果标签已关联到此 Ticket，会返回 409 冲突错误
    - Ticket 和标签都必须存在
    """
    try:
        ticket = TicketService.add_tag_to_ticket(db, ticket_id, tag_id)
        return ticket
    except BaseAPIException as e:
        if e.code == "CONFLICT":
            raise HTTPException(status_code=409, detail=e.message)
        raise HTTPException(status_code=404, detail=e.message)


@router.delete(
    "/tickets/{ticket_id}/tags/{tag_id}",
    response_model=Ticket,
    summary="从 Ticket 移除标签",
    description="从 Ticket 移除指定的标签",
    response_description="返回更新后的 Ticket 对象",
    tags=["Tickets"],
)
async def remove_tag_from_ticket(
    ticket_id: int = Path(..., description="Ticket ID", ge=1, example=1),
    tag_id: int = Path(..., description="标签 ID", ge=1, example=1),
    db: Session = Depends(get_db),
):
    """
    从 Ticket 移除标签

    **注意**：
    - 只删除关联关系，不删除标签本身
    - 如果标签未关联到此 Ticket，会返回 404 错误
    """
    try:
        ticket = TicketService.remove_tag_from_ticket(db, ticket_id, tag_id)
        return ticket
    except BaseAPIException as e:
        raise HTTPException(status_code=404, detail=e.message)
