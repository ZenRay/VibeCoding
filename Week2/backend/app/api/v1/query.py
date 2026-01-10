"""查询 API 路由"""

import time

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.models.query import (
    NaturalLanguageQueryRequest,
    NaturalLanguageQueryResult,
    QueryRequest,
    QueryResult,
)
from app.services.ai_service import generate_sql
from app.services.metadata_service import MetadataService
from app.services.query_service import QueryService
from app.storage.local_db import LocalStorage, get_db
from app.utils.error_handler import ErrorCode, create_error_response

router = APIRouter(prefix="/dbs/{name}/query", tags=["query"])


@router.post("", response_model=QueryResult)
async def execute_query(
    name: str,
    request: QueryRequest,
    db: Session = Depends(get_db),
) -> QueryResult:
    """执行 SQL 查询"""
    connection = LocalStorage.get_connection_by_name(db, name)
    if not connection:
        raise create_error_response(
            ErrorCode.NOT_FOUND,
            f"数据库连接 '{name}' 不存在",
        )

    return await QueryService.execute_query(db, connection, request)


@router.post("/natural", response_model=NaturalLanguageQueryResult)
async def natural_language_query(
    name: str,
    request: NaturalLanguageQueryRequest,
    db: Session = Depends(get_db),
) -> NaturalLanguageQueryResult:
    """自然语言生成 SQL"""
    connection = LocalStorage.get_connection_by_name(db, name)
    if not connection:
        raise create_error_response(
            ErrorCode.NOT_FOUND,
            f"数据库连接 '{name}' 不存在",
        )

    # 获取元数据
    metadata = await MetadataService.extract_metadata(db, connection)

    # 生成 SQL
    start_time = time.time()
    try:
        generated_sql = await generate_sql(
            request.prompt,
            metadata,
            dialect=connection.db_type,
        )
        generation_time_ms = int((time.time() - start_time) * 1000)

        return NaturalLanguageQueryResult(
            generated_sql=generated_sql,
            result=None,
            generation_time_ms=generation_time_ms,
        )
    except Exception as e:
        # 错误已在 generate_sql 中处理
        raise
