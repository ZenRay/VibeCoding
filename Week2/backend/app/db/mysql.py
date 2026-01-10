"""MySQL 数据库适配器"""

import asyncio
from typing import Any

import aiomysql

from app.db.base import DatabaseAdapter


class MySQLAdapter(DatabaseAdapter):
    """MySQL 适配器"""

    def __init__(self) -> None:
        self.pool: aiomysql.Pool | None = None
        self.url: str = ""

    async def connect(self, url: str) -> None:
        """建立 MySQL 连接"""
        self.url = url
        # 解析 URL: mysql://user:pass@host:port/database
        from urllib.parse import urlparse

        parsed = urlparse(url)

        self.pool = await aiomysql.create_pool(
            host=parsed.hostname or "localhost",
            port=parsed.port or 3306,
            user=parsed.username,
            password=parsed.password,
            db=parsed.path.lstrip("/") if parsed.path else None,
            charset="utf8mb4",
        )

    async def _get_conn(self) -> aiomysql.Connection:
        """获取连接"""
        if not self.pool:
            raise RuntimeError("数据库未连接")
        return await self.pool.acquire()

    async def execute(
        self,
        sql: str,
        timeout: float = 30.0,
    ) -> list[dict[str, Any]]:
        """执行 SQL 查询"""
        conn = await self._get_conn()
        try:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await asyncio.wait_for(
                    cursor.execute(sql),
                    timeout=timeout,
                )
                rows = await cursor.fetchall()
                return list(rows)
        except TimeoutError:
            raise TimeoutError(f"查询超时（{timeout}秒）")
        finally:
            if self.pool:
                self.pool.release(conn)

    async def get_metadata(self) -> dict[str, Any]:
        """获取 MySQL 元数据"""
        conn = await self._get_conn()
        try:
            # 从 URL 中获取数据库名（更可靠）
            from urllib.parse import urlparse

            parsed = urlparse(self.url)
            db_name = parsed.path.lstrip("/") if parsed.path else None

            # 如果 URL 中没有数据库名，尝试从连接获取
            if not db_name:
                async with conn.cursor() as cursor:
                    await cursor.execute("SELECT DATABASE()")
                    result = await cursor.fetchone()
                    db_name = result[0] if result and result[0] else ""

            if not db_name:
                raise ValueError("无法确定数据库名称")

            # 获取所有表和视图
            # 使用 AS 别名确保字段名为小写（aiomysql.DictCursor 使用别名）
            tables_query = """
                SELECT
                    table_name as table_name,
                    table_type as table_type,
                    table_comment as table_comment
                FROM information_schema.tables
                WHERE table_schema = %s
                ORDER BY table_name
            """

            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute(tables_query, (db_name,))
                tables_rows = await cursor.fetchall()

            # 获取主键信息（一次性查询所有表的主键）
            # MySQL 8.0+ 需要指定约束名和表名匹配
            pk_query = """
                SELECT
                    kcu.TABLE_NAME as table_name,
                    kcu.COLUMN_NAME as column_name
                FROM information_schema.TABLE_CONSTRAINTS tc
                JOIN information_schema.KEY_COLUMN_USAGE kcu
                    ON tc.CONSTRAINT_NAME = kcu.CONSTRAINT_NAME
                    AND tc.TABLE_SCHEMA = kcu.TABLE_SCHEMA
                    AND tc.TABLE_NAME = kcu.TABLE_NAME
                WHERE tc.CONSTRAINT_TYPE = 'PRIMARY KEY'
                    AND tc.TABLE_SCHEMA = %s
            """

            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute(pk_query, (db_name,))
                pk_rows = await cursor.fetchall()

            # 构建主键映射 {table_name: {column_name: True}}
            pk_map: dict[str, set[str]] = {}
            for pk_row in pk_rows:
                # aiomysql.DictCursor 使用小写字段名（通过 AS 别名）
                table = pk_row.get("table_name")
                column = pk_row.get("column_name")
                if table and column:
                    if table not in pk_map:
                        pk_map[table] = set()
                    pk_map[table].add(column)

            tables: list[dict[str, Any]] = []
            views: list[dict[str, Any]] = []

            for row in tables_rows:
                # 安全获取字段值，兼容可能的字段名变化
                table_name = row.get("table_name") or row.get("TABLE_NAME")
                table_type = row.get("table_type") or row.get("TABLE_TYPE")
                table_comment = row.get("table_comment") or row.get("TABLE_COMMENT")

                if not table_name or not table_type:
                    continue  # 跳过无效行

                # 获取列信息
                # 使用 AS 别名确保字段名为小写
                columns_query = """
                    SELECT
                        column_name as column_name,
                        data_type as data_type,
                        is_nullable as is_nullable,
                        column_default as column_default,
                        column_comment as column_comment,
                        character_maximum_length as character_maximum_length,
                        numeric_precision as numeric_precision,
                        numeric_scale as numeric_scale
                    FROM information_schema.columns
                    WHERE table_schema = %s AND table_name = %s
                    ORDER BY ordinal_position
                """

                async with conn.cursor(aiomysql.DictCursor) as cursor:
                    await cursor.execute(columns_query, (db_name, table_name))
                    columns_rows = await cursor.fetchall()

                columns = []
                table_pks = pk_map.get(table_name, set())

                for col_row in columns_rows:
                    col_name = col_row.get("column_name")
                    data_type = col_row.get("data_type")

                    if not col_name or not data_type:
                        continue  # 跳过无效列

                    # 规范化数据类型（添加长度信息）
                    if col_row.get("character_maximum_length"):
                        data_type = f"{data_type}({col_row['character_maximum_length']})"
                    elif col_row.get("numeric_precision") and col_row.get("numeric_scale"):
                        data_type = f"{data_type}({col_row['numeric_precision']},{col_row['numeric_scale']})"
                    elif col_row.get("numeric_precision"):
                        data_type = f"{data_type}({col_row['numeric_precision']})"

                    columns.append(
                        {
                            "name": col_name,
                            "dataType": data_type,
                            "isNullable": col_row["is_nullable"] == "YES",
                            "isPrimaryKey": col_name in table_pks,
                            "defaultValue": col_row["column_default"],
                            "comment": col_row.get("column_comment") or None,
                        }
                    )

                table_info = {
                    "name": table_name,
                    "tableType": table_type.lower(),
                    "columns": columns,
                    "comment": table_comment,
                }

                if table_type == "BASE TABLE":
                    tables.append(table_info)
                elif table_type == "VIEW":
                    views.append(table_info)

            return {
                "tables": tables,
                "views": views,
            }
        finally:
            if self.pool:
                self.pool.release(conn)

    async def close(self) -> None:
        """关闭连接池"""
        if self.pool:
            self.pool.close()
            await self.pool.wait_closed()
            self.pool = None

    async def test_connection(self) -> bool:
        """测试连接"""
        try:
            conn = await self._get_conn()
            async with conn.cursor() as cursor:
                await cursor.execute("SELECT 1")
            if self.pool:
                self.pool.release(conn)
            return True
        except Exception:
            return False
