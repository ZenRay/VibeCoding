"""查询执行服务 - 增强版包含并发互斥锁和智能限制"""

import time

from sqlalchemy.orm import Session

from app.models.query import QueryRequest, QueryResult, QueryResultColumn
from app.services.db_service import get_adapter
from app.storage.models import DatabaseConnection
from app.utils.error_handler import ErrorCode, create_error_response
from app.utils.locks import get_query_lock, is_metadata_refreshing
from app.utils.sql_validator import add_limit_if_missing, validate_sql


class QueryService:
    """查询服务类"""

    @staticmethod
    async def execute_query(
        db: Session,
        connection: DatabaseConnection,
        request: QueryRequest,
    ) -> QueryResult:
        """执行 SQL 查询 (带并发互斥锁和元数据快照)"""

        # === 并发控制: 检查是否正在刷新元数据 ===
        if is_metadata_refreshing():
            raise create_error_response(ErrorCode.CONFLICT, "元数据刷新中,请稍候...")

        sql = request.sql.strip()

        # 验证 SQL - 映射数据库类型到 sqlglot 方言
        dialect_map = {
            "postgresql": "postgres",
            "mysql": "mysql",
            "sqlite": "sqlite",
        }
        dialect = dialect_map.get(connection.db_type, "postgres")
        is_valid, error_msg = validate_sql(sql, dialect)
        if not is_valid:
            raise create_error_response(
                (
                    ErrorCode.SYNTAX_ERROR
                    if "语法" in (error_msg or "")
                    else ErrorCode.INVALID_STATEMENT
                ),
                error_msg or "SQL 验证失败",
            )

        # 添加 LIMIT（如果需要）
        final_sql = add_limit_if_missing(sql, limit=1000)
        truncated = final_sql != sql

        # === 获取查询执行锁 ===
        query_lock = get_query_lock()
        async with query_lock:
            # 执行查询
            adapter = get_adapter(connection.db_type)
            await adapter.connect(connection.url)

            try:
                start_time = time.time()
                rows = await adapter.execute(final_sql, timeout=30.0)
                execution_time_ms = int((time.time() - start_time) * 1000)

                # 提取列信息
                columns: list[QueryResultColumn] = []
                if rows:
                    first_row = rows[0]
                    columns = [
                        QueryResultColumn(
                            name=key,
                            data_type=str(type(value).__name__),
                        )
                        for key, value in first_row.items()
                    ]

                return QueryResult(
                    columns=columns,
                    rows=rows,
                    row_count=len(rows),
                    execution_time_ms=execution_time_ms,
                    truncated=truncated,
                    sql=final_sql,
                )

            except TimeoutError:
                raise create_error_response(
                    ErrorCode.QUERY_TIMEOUT,
                    "查询超时（30秒）。建议：优化查询条件、减少返回行数或添加索引",
                )
            except Exception as e:
                raise create_error_response(
                    ErrorCode.INTERNAL_ERROR,
                    f"查询执行失败: {str(e)}",
                )
            finally:
                await adapter.close()
