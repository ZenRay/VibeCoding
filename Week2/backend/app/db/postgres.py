"""PostgreSQL 数据库适配器"""

import asyncio
from typing import Any

import asyncpg

from app.db.base import DatabaseAdapter


class PostgresAdapter(DatabaseAdapter):
    """PostgreSQL 适配器"""

    def __init__(self) -> None:
        self.conn: asyncpg.Connection | None = None
        self.url: str = ""

    async def connect(self, url: str) -> None:
        """建立 PostgreSQL 连接"""
        self.url = url
        self.conn = await asyncpg.connect(url)

    async def execute(
        self,
        sql: str,
        timeout: float = 30.0,
    ) -> list[dict[str, Any]]:
        """执行 SQL 查询"""
        if not self.conn:
            raise RuntimeError("数据库未连接")

        try:
            rows = await asyncio.wait_for(
                self.conn.fetch(sql),
                timeout=timeout,
            )
            # asyncpg Record 转换为字典列表
            return [dict(row) for row in rows]
        except TimeoutError:
            raise TimeoutError(f"查询超时（{timeout}秒）")

    async def get_metadata(self) -> dict[str, Any]:
        """获取 PostgreSQL 元数据"""
        if not self.conn:
            raise RuntimeError("数据库未连接")

        # 获取所有表和视图
        tables_query = """
            SELECT table_name, table_type
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name
        """
        tables_rows = await self.conn.fetch(tables_query)

        # 获取主键信息（一次性查询所有表的主键）
        pk_query = """
            SELECT
                kcu.table_name,
                kcu.column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
                ON tc.constraint_name = kcu.constraint_name
                AND tc.table_schema = kcu.table_schema
            WHERE tc.constraint_type = 'PRIMARY KEY'
                AND tc.table_schema = 'public'
        """
        pk_rows = await self.conn.fetch(pk_query)

        # 构建主键映射 {table_name: {column_name: True}}
        pk_map: dict[str, set[str]] = {}
        for pk_row in pk_rows:
            table = pk_row["table_name"]
            column = pk_row["column_name"]
            if table not in pk_map:
                pk_map[table] = set()
            pk_map[table].add(column)

        tables: list[dict[str, Any]] = []
        views: list[dict[str, Any]] = []

        for row in tables_rows:
            table_name = row["table_name"]
            table_type = row["table_type"]

            # 获取列信息
            columns_query = """
                SELECT
                    column_name,
                    data_type,
                    is_nullable,
                    column_default,
                    character_maximum_length
                FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = $1
                ORDER BY ordinal_position
            """
            columns_rows = await self.conn.fetch(columns_query, table_name)

            columns = []
            table_pks = pk_map.get(table_name, set())

            for col_row in columns_rows:
                columns.append(
                    {
                        "name": col_row["column_name"],
                        "dataType": col_row["data_type"],
                        "isNullable": col_row["is_nullable"] == "YES",
                        "isPrimaryKey": col_row["column_name"] in table_pks,
                        "defaultValue": col_row["column_default"],
                    }
                )

            table_info = {
                "name": table_name,
                "tableType": table_type.lower(),
                "columns": columns,
            }

            if table_type == "BASE TABLE":
                tables.append(table_info)
            elif table_type == "VIEW":
                views.append(table_info)

        return {
            "tables": tables,
            "views": views,
        }

    async def close(self) -> None:
        """关闭连接"""
        if self.conn:
            await self.conn.close()
            self.conn = None

    async def test_connection(self) -> bool:
        """测试连接"""
        try:
            if not self.conn:
                return False
            await self.conn.fetchval("SELECT 1")
            return True
        except Exception:
            return False
