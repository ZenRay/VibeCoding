"""
PostgreSQL Schema Inspector.

Extracts database schema information using asyncpg.
"""

import asyncpg
import structlog

from postgres_mcp.models.schema import (
    ColumnSchema,
    DatabaseSchema,
    ForeignKeySchema,
    IndexSchema,
    TableSchema,
)

logger = structlog.get_logger(__name__)


class SchemaInspector:
    """
    PostgreSQL schema inspector using asyncpg.

    Connects to a PostgreSQL database and extracts schema information
    including tables, columns, indexes, and foreign keys.
    """

    def __init__(
        self,
        host: str,
        port: int,
        user: str,
        password: str,
        database: str,
    ):
        """
        Initialize schema inspector.

        Args:
        ----------
            host: Database host
            port: Database port
            user: Database user
            password: Database password
            database: Database name
        """
        self._host = host
        self._port = port
        self._user = user
        self._password = password
        self._database = database
        self._pool: asyncpg.Pool | None = None

    async def connect(self) -> None:
        """
        Create connection pool to database.

        Raises:
        ----------
            Exception: When connection fails
        """
        self._pool = await asyncpg.create_pool(
            host=self._host,
            port=self._port,
            user=self._user,
            password=self._password,
            database=self._database,
            min_size=1,
            max_size=5,
        )
        logger.info(
            "schema_inspector_connected",
            host=self._host,
            database=self._database,
        )

    async def disconnect(self) -> None:
        """Close connection pool."""
        if self._pool:
            await self._pool.close()
            await self._pool.wait_closed()
            self._pool = None
            logger.info("schema_inspector_disconnected", database=self._database)

    async def inspect_schema(self) -> DatabaseSchema:
        """
        Inspect database schema and extract all metadata.

        Returns:
        ----------
            DatabaseSchema with complete schema information

        Raises:
        ----------
            RuntimeError: When not connected to database

        Example:
        ----------
            >>> inspector = SchemaInspector("localhost", 5432, "user", "pass", "mydb")
            >>> await inspector.connect()
            >>> schema = await inspector.inspect_schema()
            >>> assert len(schema.tables) > 0
        """
        if not self._pool:
            raise RuntimeError("SchemaInspector is not connected to database")

        async with self._pool.acquire() as conn:
            # Get all tables
            tables_query = """
                SELECT table_name, table_type
                FROM information_schema.tables
                WHERE table_schema = 'public'
                  AND table_type = 'BASE TABLE'
                ORDER BY table_name;
            """
            table_rows = await conn.fetch(tables_query)

            tables: dict[str, TableSchema] = {}

            for table_row in table_rows:
                table_name = table_row["table_name"]

                # Get primary keys first
                pk_columns = await self._get_primary_keys(table_name)

                # Get columns (with pk info)
                columns = await self._get_table_columns(table_name, pk_columns)

                # Get indexes
                indexes = await self._get_indexes(table_name)

                # Get foreign keys
                foreign_keys = await self._get_foreign_keys(table_name)

                tables[table_name] = TableSchema(
                    name=table_name,
                    columns=columns,
                    indexes=indexes,
                    foreign_keys=foreign_keys,
                )

            logger.info(
                "schema_inspection_complete",
                database=self._database,
                table_count=len(tables),
            )

            return DatabaseSchema(database_name=self._database, tables=tables)

    async def _get_table_columns(self, table_name: str, pk_columns: set[str]) -> list[ColumnSchema]:
        """
        Get columns for a specific table.

        Args:
        ----------
            table_name: Name of the table
            pk_columns: Set of primary key column names

        Returns:
        ----------
            List of column schemas
        """
        if not self._pool:
            raise RuntimeError("Not connected")

        async with self._pool.acquire() as conn:
            columns_query = """
                SELECT
                    column_name,
                    data_type,
                    is_nullable,
                    column_default
                FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name = $1
                ORDER BY ordinal_position;
            """
            column_rows = await conn.fetch(columns_query, table_name)

            columns = []
            for row in column_rows:
                columns.append(
                    ColumnSchema(
                        name=row["column_name"],
                        data_type=row["data_type"],
                        nullable=row["is_nullable"] == "YES",
                        default=row["column_default"],
                        primary_key=row["column_name"] in pk_columns,  # Set based on pk_columns
                    )
                )

            return columns

    async def _get_primary_keys(self, table_name: str) -> set[str]:
        """
        Get primary key columns for a table.

        Args:
        ----------
            table_name: Name of the table

        Returns:
        ----------
            Set of primary key column names
        """
        if not self._pool:
            raise RuntimeError("Not connected")

        async with self._pool.acquire() as conn:
            pk_query = """
                SELECT a.attname as column_name
                FROM pg_index i
                JOIN pg_attribute a ON a.attrelid = i.indrelid
                    AND a.attnum = ANY(i.indkey)
                WHERE i.indrelid = $1::regclass
                  AND i.indisprimary;
            """
            pk_rows = await conn.fetch(pk_query, table_name)
            return {row["column_name"] for row in pk_rows}

    async def _get_indexes(self, table_name: str) -> list[IndexSchema]:
        """
        Get indexes for a table.

        Args:
        ----------
            table_name: Name of the table

        Returns:
        ----------
            List of index schemas
        """
        if not self._pool:
            raise RuntimeError("Not connected")

        async with self._pool.acquire() as conn:
            indexes_query = """
                SELECT
                    indexname as index_name,
                    indexdef as index_definition
                FROM pg_indexes
                WHERE schemaname = 'public'
                  AND tablename = $1;
            """
            index_rows = await conn.fetch(indexes_query, table_name)

            indexes = []
            for row in index_rows:
                # Parse index definition to determine uniqueness
                index_def = row["index_definition"]
                is_unique = "UNIQUE" in index_def.upper()

                # Extract column name (simplified parsing)
                # Format: CREATE [UNIQUE] INDEX name ON table (column)
                import re

                col_match = re.search(r"\(([^)]+)\)", index_def)
                column_name = col_match.group(1) if col_match else "unknown"

                indexes.append(
                    IndexSchema(
                        name=row["index_name"],
                        columns=[column_name],
                        unique=is_unique,
                    )
                )

            return indexes

    async def _get_foreign_keys(self, table_name: str) -> list[ForeignKeySchema]:
        """
        Get foreign keys for a table.

        Args:
        ----------
            table_name: Name of the table

        Returns:
        ----------
            List of foreign key schemas
        """
        if not self._pool:
            raise RuntimeError("Not connected")

        async with self._pool.acquire() as conn:
            fk_query = """
                SELECT
                    tc.constraint_name,
                    kcu.column_name,
                    ccu.table_name AS foreign_table_name,
                    ccu.column_name AS foreign_column_name
                FROM information_schema.table_constraints AS tc
                JOIN information_schema.key_column_usage AS kcu
                    ON tc.constraint_name = kcu.constraint_name
                    AND tc.table_schema = kcu.table_schema
                JOIN information_schema.constraint_column_usage AS ccu
                    ON ccu.constraint_name = tc.constraint_name
                    AND ccu.table_schema = tc.table_schema
                WHERE tc.constraint_type = 'FOREIGN KEY'
                  AND tc.table_name = $1;
            """
            fk_rows = await conn.fetch(fk_query, table_name)

            foreign_keys = []
            for row in fk_rows:
                foreign_keys.append(
                    ForeignKeySchema(
                        name=row["constraint_name"],
                        column=row["column_name"],
                        foreign_table=row["foreign_table_name"],
                        foreign_column=row["foreign_column_name"],
                    )
                )

            return foreign_keys
