"""数据库连接 API 路由"""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.models.database import (
    DatabaseConnectionCreate,
    DatabaseConnectionResponse,
    DatabaseListResponse,
)
from app.models.metadata import DatabaseMetadata
from app.services.db_service import DatabaseService
from app.services.metadata_service import MetadataService
from app.storage.local_db import LocalStorage, get_db
from app.utils.error_handler import ErrorCode, create_error_response

router = APIRouter(prefix="/dbs", tags=["databases"])


@router.get("", response_model=DatabaseListResponse)
async def list_databases(db: Session = Depends(get_db)) -> DatabaseListResponse:
    """获取所有数据库连接"""
    connections = DatabaseService.list_connections(db)
    return DatabaseListResponse(
        databases=connections,
        total=len(connections),
    )


@router.put("/{name}", response_model=DatabaseConnectionResponse)
async def upsert_database(
    name: str,
    request: DatabaseConnectionCreate,
    db: Session = Depends(get_db),
) -> DatabaseConnectionResponse:
    """添加或更新数据库连接（Upsert 语义）"""
    # 检查连接是否已存在（使用 LocalStorage 避免异常）
    existing = LocalStorage.get_connection_by_name(db, name)

    if existing:
        # 更新现有连接
        return await DatabaseService.update_connection(db, name, request.url)
    else:
        # 创建新连接
        return await DatabaseService.add_connection(db, name, request.url)


@router.get("/{name}", response_model=DatabaseConnectionResponse)
async def get_database(
    name: str,
    db: Session = Depends(get_db),
) -> DatabaseConnectionResponse:
    """获取数据库连接"""
    return DatabaseService.get_connection(db, name)


@router.delete("/{name}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_database(
    name: str,
    db: Session = Depends(get_db),
) -> None:
    """删除数据库连接"""
    DatabaseService.delete_connection(db, name)


@router.get("/{name}/metadata", response_model=DatabaseMetadata)
async def get_database_metadata(
    name: str,
    refresh: bool = Query(False, description="是否强制刷新元数据"),
    db: Session = Depends(get_db),
) -> DatabaseMetadata:
    """获取数据库元数据"""
    connection = LocalStorage.get_connection_by_name(db, name)
    if not connection:
        raise create_error_response(
            ErrorCode.NOT_FOUND,
            f"数据库连接 '{name}' 不存在",
        )

    return await MetadataService.extract_metadata(db, connection, force_refresh=refresh)
