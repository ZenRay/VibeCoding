"""SQLite 数据库适配器"""

import asyncio
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import aiosqlite

from app.db.base import DatabaseAdapter


class SQLiteAdapter(DatabaseAdapter):
    """SQLite 适配器"""

    def __init__(self) -> None:
        self.conn: aiosqlite.Connection | None = None
        self.url: str = ""

    async def connect(self, url: str) -> None:
        """建立 SQLite 连接"""
        self.url = url
        # 解析 URL: sqlite:///path/to/db.db
        parsed = urlparse(url)
        db_path = parsed.path.lstrip("/")

        # 确保目录存在
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        self.conn = await aiosqlite.connect(db_path)
        # 设置行工厂以返回字典
        self.conn.row_factory = aiosqlite.Row

    async def execute(
        self,
        sql: str,
        timeout: float = 30.0,
    ) -> list[dict[str, Any]]:
        """执行 SQL 查询"""
        if not self.conn:
            raise RuntimeError("数据库未连接")

        try:
            cursor = await asyncio.wait_for(
                self.conn.execute(sql),
                timeout=timeout,
            )
            rows = await asyncio.wait_for(
                cursor.fetchall(),
                timeout=timeout,
            )
            # 转换为字典列表
            return [dict(row) for row in rows]
        except TimeoutError:
            raise TimeoutError(f"查询超时（{timeout}秒）")

    async def get_metadata(self) -> dict[str, Any]:
        """获取 SQLite 元数据"""
        if not self.conn:
            raise RuntimeError("数据库未连接")

        # 获取所有表和视图
        tables_query = """
            SELECT name, type
            FROM sqlite_master
            WHERE type IN ('table', 'view') AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """

        cursor = await self.conn.execute(tables_query)
        tables_rows = await cursor.fetchall()

        tables: list[dict[str, Any]] = []
        views: list[dict[str, Any]] = []

        for row in tables_rows:
            table_name = row["name"]
            table_type = row["type"]

            # 使用 PRAGMA 获取列信息
            pragma_query = f"PRAGMA table_info({table_name})"
            cursor = await self.conn.execute(pragma_query)
            columns_rows = await cursor.fetchall()

            columns = []
            for col_row in columns_rows:
                columns.append(
                    {
                        "name": col_row["name"],
                        "dataType": col_row["type"] or "TEXT",
                        "isNullable": not col_row["notnull"],
                        "defaultValue": col_row["dflt_value"],
                    }
                )

            table_info = {
                "name": table_name,
                "tableType": table_type.lower(),
                "columns": columns,
            }

            if table_type == "table":
                tables.append(table_info)
            elif table_type == "view":
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
            cursor = await self.conn.execute("SELECT 1")
            await cursor.fetchone()
            return True
        except Exception:
            return False
