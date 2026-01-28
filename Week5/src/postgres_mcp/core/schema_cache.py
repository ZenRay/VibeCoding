"""
Schema Cache implementation.

In-memory caching of database schemas with thread-safe access.
"""

import asyncio

import structlog

from postgres_mcp.db.schema_inspector import SchemaInspector
from postgres_mcp.models.schema import DatabaseSchema

logger = structlog.get_logger(__name__)


class SchemaCacheError(Exception):
    """Schema cache error."""

    pass


class SchemaCache:
    """
    Thread-safe in-memory cache for database schemas.

    Manages schema caching, refreshing, and concurrent access control.
    """

    def __init__(
        self,
        databases: dict[str, SchemaInspector],
        auto_refresh_interval: int = 300,  # 5 minutes
    ):
        """
        Initialize schema cache.

        Args:
        ----------
            databases: Mapping of database name to SchemaInspector
            auto_refresh_interval: Auto-refresh interval in seconds (0 = disabled)
        """
        self._databases = databases
        self._cache: dict[str, DatabaseSchema] = {}
        self._locks: dict[str, asyncio.Lock] = {db: asyncio.Lock() for db in databases}
        self._auto_refresh_interval = auto_refresh_interval
        self._refresh_task: asyncio.Task | None = None
        self._shutdown = False

    async def initialize(self) -> None:
        """
        Initialize cache by connecting to all databases and loading schemas.

        Raises:
        ----------
            Exception: When connection or inspection fails
        """
        logger.info("schema_cache_initializing", database_count=len(self._databases))

        for db_name, inspector in self._databases.items():
            async with self._locks[db_name]:
                # Connect to database
                await inspector.connect()

                # Load initial schema
                schema = await inspector.inspect_schema()
                self._cache[db_name] = schema

                logger.info(
                    "schema_cached",
                    database=db_name,
                    table_count=len(schema.tables),
                )

        # Start auto-refresh task if enabled
        if self._auto_refresh_interval > 0:
            self._refresh_task = asyncio.create_task(self._auto_refresh_loop())

        logger.info("schema_cache_initialized", database_count=len(self._databases))

    async def cleanup(self) -> None:
        """
        Cleanup cache and disconnect from all databases.
        """
        self._shutdown = True

        # Stop refresh task
        if self._refresh_task:
            self._refresh_task.cancel()
            try:
                await self._refresh_task
            except asyncio.CancelledError:
                pass

        # Disconnect all inspectors
        for inspector in self._databases.values():
            await inspector.disconnect()

        logger.info("schema_cache_cleaned_up")

    async def get_schema(self, database: str) -> DatabaseSchema | None:
        """
        Get cached schema for a database.

        Args:
        ----------
            database: Database name

        Returns:
        ----------
            DatabaseSchema if found, None otherwise

        Example:
        ----------
            >>> cache = SchemaCache({"mydb": inspector})
            >>> await cache.initialize()
            >>> schema = await cache.get_schema("mydb")
            >>> assert schema is not None
        """
        async with self._locks.get(database, asyncio.Lock()):
            return self._cache.get(database)

    async def refresh_schema(self, database: str) -> None:
        """
        Refresh schema for a specific database.

        Args:
        ----------
            database: Database name

        Raises:
        ----------
            SchemaCacheError: When database is not configured
        """
        if database not in self._databases:
            raise SchemaCacheError(f"Database '{database}' is not configured")

        async with self._locks[database]:
            inspector = self._databases[database]
            schema = await inspector.inspect_schema()
            self._cache[database] = schema

            logger.info(
                "schema_refreshed",
                database=database,
                table_count=len(schema.tables),
            )

    async def refresh_all_schemas(self) -> None:
        """
        Refresh schemas for all databases.
        """
        logger.info("refreshing_all_schemas", database_count=len(self._databases))

        for db_name in self._databases:
            try:
                await self.refresh_schema(db_name)
            except Exception as e:
                logger.error(
                    "schema_refresh_failed",
                    database=db_name,
                    error=str(e),
                )

    def list_databases(self) -> list[str]:
        """
        Get list of all configured databases.

        Returns:
        ----------
            List of database names
        """
        return list(self._databases.keys())

    async def _auto_refresh_loop(self) -> None:
        """
        Background task for automatic schema refresh.

        Runs every auto_refresh_interval seconds.
        """
        logger.info(
            "auto_refresh_started",
            interval_seconds=self._auto_refresh_interval,
        )

        while not self._shutdown:
            try:
                await asyncio.sleep(self._auto_refresh_interval)

                if self._shutdown:
                    break

                await self.refresh_all_schemas()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("auto_refresh_error", error=str(e))

        logger.info("auto_refresh_stopped")
