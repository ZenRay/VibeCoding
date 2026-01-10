"""数据库连接服务"""

import re
from urllib.parse import urlparse

from sqlalchemy.orm import Session

from app.db.base import DatabaseAdapter
from app.db.mysql import MySQLAdapter
from app.db.postgres import PostgresAdapter
from app.db.sqlite import SQLiteAdapter
from app.models.database import DatabaseConnectionResponse, DatabaseType
from app.storage.local_db import LocalStorage
from app.utils.error_handler import ErrorCode, create_error_response


def parse_database_url(url: str) -> tuple[str, str, str | None, int | None, str]:
    """
    解析数据库连接 URL

    Returns:
        (db_type, url, host, port, database)
    """
    parsed = urlparse(url)

    if parsed.scheme == "postgresql" or parsed.scheme == "postgres":
        db_type = DatabaseType.POSTGRESQL
        host = parsed.hostname
        port = parsed.port or 5432
        database = parsed.path.lstrip("/")
        # sqlglot 使用 'postgres' 而非 'postgresql'
        dialect_for_validation = "postgres"
    elif parsed.scheme == "mysql":
        db_type = DatabaseType.MYSQL
        host = parsed.hostname
        port = parsed.port or 3306
        database = parsed.path.lstrip("/")
    elif parsed.scheme == "sqlite":
        db_type = DatabaseType.SQLITE
        host = None
        port = None
        database = parsed.path.lstrip("/")
    else:
        raise ValueError(f"不支持的数据库类型: {parsed.scheme}")

    return db_type.value, url, host, port, database


def validate_connection_name(name: str) -> None:
    """验证连接名称"""
    if not re.match(r"^[a-zA-Z0-9_-]+$", name):
        raise ValueError("连接名称仅允许字母、数字、下划线和连字符")
    if len(name) < 1 or len(name) > 100:
        raise ValueError("连接名称长度必须在 1-100 字符之间")


def get_adapter(db_type: str) -> DatabaseAdapter:
    """根据数据库类型获取适配器"""
    if db_type == DatabaseType.POSTGRESQL.value or db_type == "postgresql":
        return PostgresAdapter()
    elif db_type == DatabaseType.MYSQL.value or db_type == "mysql":
        return MySQLAdapter()
    elif db_type == DatabaseType.SQLITE.value or db_type == "sqlite":
        return SQLiteAdapter()
    else:
        raise ValueError(f"不支持的数据库类型: {db_type}")


async def validate_connection(url: str) -> tuple[bool, str | None]:
    """
    验证数据库连接

    Returns:
        (is_valid, error_message)
    """
    try:
        db_type, _, _, _, _ = parse_database_url(url)
        adapter = get_adapter(db_type)

        await adapter.connect(url)
        is_valid = await adapter.test_connection()
        await adapter.close()

        if not is_valid:
            return False, "连接测试失败"

        return True, None

    except Exception as e:
        error_msg = str(e)
        # 根据错误类型分类
        if "timeout" in error_msg.lower() or "unreachable" in error_msg.lower():
            return False, "网络不可达"
        elif "authentication" in error_msg.lower() or "password" in error_msg.lower():
            return False, "认证失败"
        elif "database" in error_msg.lower() and "not found" in error_msg.lower():
            return False, "数据库不存在"
        elif "permission" in error_msg.lower() or "denied" in error_msg.lower():
            return False, "权限拒绝"
        else:
            return False, f"连接失败: {error_msg}"


class DatabaseService:
    """数据库连接服务类"""

    @staticmethod
    async def add_connection(
        db: Session,
        name: str,
        url: str,
    ) -> DatabaseConnectionResponse:
        """添加数据库连接"""
        # 验证连接名称
        validate_connection_name(name)

        # 检查名称是否已存在
        existing = LocalStorage.get_connection_by_name(db, name)
        if existing:
            raise create_error_response(
                ErrorCode.VALIDATION_ERROR,
                f"连接名称 '{name}' 已存在",
            )

        # 验证连接
        is_valid, error_msg = await validate_connection(url)
        if not is_valid:
            raise create_error_response(
                ErrorCode.CONNECTION_FAILED,
                error_msg or "连接验证失败",
            )

        # 解析 URL
        db_type, _, host, port, database = parse_database_url(url)

        # 保存到本地存储
        conn = LocalStorage.create_connection(
            db,
            name=name,
            db_type=db_type,
            url=url,
            host=host,
            port=port,
            database=database,
        )

        return DatabaseConnectionResponse(
            name=conn.name,
            db_type=DatabaseType(conn.db_type),
            host=conn.host,
            port=conn.port,
            database=conn.database,
            created_at=conn.created_at,
            updated_at=conn.updated_at,
        )

    @staticmethod
    async def update_connection(
        db: Session,
        name: str,
        url: str,
    ) -> DatabaseConnectionResponse:
        """更新数据库连接"""
        # 获取现有连接
        conn = LocalStorage.get_connection_by_name(db, name)
        if not conn:
            raise create_error_response(
                ErrorCode.NOT_FOUND,
                f"数据库连接 '{name}' 不存在",
            )

        # 验证连接
        is_valid, error_msg = await validate_connection(url)
        if not is_valid:
            raise create_error_response(
                ErrorCode.CONNECTION_FAILED,
                error_msg or "连接验证失败",
            )

        # 解析 URL
        db_type, _, host, port, database = parse_database_url(url)

        # 更新连接
        updated_conn = LocalStorage.update_connection(
            db,
            conn,
            url=url,
            host=host,
            port=port,
            database=database,
        )

        return DatabaseConnectionResponse(
            name=updated_conn.name,
            db_type=DatabaseType(updated_conn.db_type),
            host=updated_conn.host,
            port=updated_conn.port,
            database=updated_conn.database,
            created_at=updated_conn.created_at,
            updated_at=updated_conn.updated_at,
        )

    @staticmethod
    def get_connection(
        db: Session,
        name: str,
    ) -> DatabaseConnectionResponse:
        """获取数据库连接"""
        conn = LocalStorage.get_connection_by_name(db, name)
        if not conn:
            raise create_error_response(
                ErrorCode.NOT_FOUND,
                f"数据库连接 '{name}' 不存在",
            )

        return DatabaseConnectionResponse(
            name=conn.name,
            db_type=DatabaseType(conn.db_type),
            host=conn.host,
            port=conn.port,
            database=conn.database,
            created_at=conn.created_at,
            updated_at=conn.updated_at,
        )

    @staticmethod
    def list_connections(db: Session) -> list[DatabaseConnectionResponse]:
        """列出所有数据库连接（按创建时间降序）"""
        connections = LocalStorage.get_all_connections(db)

        return [
            DatabaseConnectionResponse(
                name=conn.name,
                db_type=DatabaseType(conn.db_type),
                host=conn.host,
                port=conn.port,
                database=conn.database,
                created_at=conn.created_at,
                updated_at=conn.updated_at,
            )
            for conn in connections
        ]

    @staticmethod
    def delete_connection(db: Session, name: str) -> None:
        """删除数据库连接"""
        conn = LocalStorage.get_connection_by_name(db, name)
        if not conn:
            raise create_error_response(
                ErrorCode.NOT_FOUND,
                f"数据库连接 '{name}' 不存在",
            )

        LocalStorage.delete_connection(db, conn)
