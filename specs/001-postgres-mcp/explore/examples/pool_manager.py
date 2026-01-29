"""
Connection pool manager for asyncpg.

Manages multiple database connection pools with automatic lifecycle,
error handling, and monitoring.

Usage:
    # Initialize pool manager
    manager = PoolManager()

    # Create pool for database
    config = DBConfig(host="localhost", port=5432, database="mydb", ...)
    db_id = await manager.create_pool(config)

    # Execute queries
    result = await manager.execute_query(db_id, "SELECT * FROM users")

    # Get statistics
    stats = await manager.get_pool_stats(db_id)

    # Cleanup
    await manager.close_all()
"""

import asyncio
import hashlib
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

import asyncpg
from pybreaker import CircuitBreaker

logger = logging.getLogger(__name__)


@dataclass
class DBConfig:
    """Database connection configuration."""

    host: str
    port: int
    database: str
    user: str
    password: str
    ssl: bool = False
    pool_min_size: int = 5
    pool_max_size: int = 20
    max_queries: int = 50000
    max_inactive_connection_lifetime: float = 300.0
    command_timeout: float = 60.0
    statement_timeout: int = 30000  # milliseconds
    idle_in_transaction_timeout: int = 60000  # milliseconds

    def to_pool_kwargs(self) -> dict[str, Any]:
        """Convert config to asyncpg.create_pool kwargs."""
        return {
            "host": self.host,
            "port": self.port,
            "database": self.database,
            "user": self.user,
            "password": self.password,
            "ssl": self.ssl,
            "min_size": self.pool_min_size,
            "max_size": self.pool_max_size,
            "max_queries": self.max_queries,
            "max_inactive_connection_lifetime": self.max_inactive_connection_lifetime,
            "command_timeout": self.command_timeout,
            "server_settings": {
                "statement_timeout": str(self.statement_timeout),
                "idle_in_transaction_session_timeout": str(
                    self.idle_in_transaction_timeout
                ),
            },
        }

    def get_id(self) -> str:
        """Generate unique ID for this database connection."""
        connection_string = f"{self.user}@{self.host}:{self.port}/{self.database}"
        return hashlib.sha256(connection_string.encode()).hexdigest()[:16]


@dataclass
class PoolStats:
    """Connection pool statistics."""

    db_id: str
    size: int
    free: int
    max_size: int
    min_size: int
    queries_executed: int = 0
    avg_acquire_time_ms: float = 0.0
    last_used: datetime = field(default_factory=datetime.now)


class PoolManager:
    """
    Manages multiple asyncpg connection pools.

    Features:
    - Independent pool per database
    - Automatic pool lifecycle management
    - Connection health monitoring
    - Schema cache invalidation
    - Circuit breaker pattern
    - Background cleanup of idle pools

    Example:
        >>> manager = PoolManager()
        >>> config = DBConfig(host="localhost", port=5432, database="mydb", ...)
        >>> db_id = await manager.create_pool(config)
        >>> result = await manager.execute_query(db_id, "SELECT * FROM users")
        >>> await manager.close_all()
    """

    def __init__(
        self,
        idle_pool_timeout: timedelta = timedelta(minutes=30),
        enable_monitoring: bool = True,
        enable_cleanup: bool = True,
    ):
        """
        Initialize pool manager.

        Args:
            idle_pool_timeout: Close pools idle for this duration
            enable_monitoring: Enable background metrics collection
            enable_cleanup: Enable automatic cleanup of idle pools
        """
        self._pools: dict[str, asyncpg.Pool] = {}
        self._pool_configs: dict[str, DBConfig] = {}
        self._last_used: dict[str, datetime] = {}
        self._circuit_breakers: dict[str, CircuitBreaker] = {}
        self._lock = asyncio.Lock()
        self._background_tasks: set[asyncio.Task] = set()
        self._idle_pool_timeout = idle_pool_timeout
        self._enable_monitoring = enable_monitoring
        self._enable_cleanup = enable_cleanup
        self._acquire_times: dict[str, list[float]] = defaultdict(list)
        self._query_counts: dict[str, int] = defaultdict(int)

        # Start background tasks
        if self._enable_cleanup:
            task = asyncio.create_task(self._cleanup_idle_pools())
            self._background_tasks.add(task)
            task.add_done_callback(self._background_tasks.discard)

        if self._enable_monitoring:
            task = asyncio.create_task(self._monitor_pools())
            self._background_tasks.add(task)
            task.add_done_callback(self._background_tasks.discard)

    async def create_pool(self, config: DBConfig) -> str:
        """
        Create a new connection pool.

        Args:
            config: Database configuration

        Returns:
            Database ID (unique identifier for this pool)

        Raises:
            ConnectionError: If pool creation fails
        """
        db_id = config.get_id()

        async with self._lock:
            if db_id in self._pools:
                logger.info(f"Pool {db_id} already exists, skipping creation")
                return db_id

            try:
                logger.info(
                    f"Creating pool for {config.database} on {config.host}:{config.port}"
                )
                pool = await asyncpg.create_pool(**config.to_pool_kwargs())
                self._pools[db_id] = pool
                self._pool_configs[db_id] = config
                self._last_used[db_id] = datetime.now()

                # Create circuit breaker for this database
                self._circuit_breakers[db_id] = CircuitBreaker(
                    fail_max=5,  # Open circuit after 5 consecutive failures
                    timeout_duration=60,  # Try again after 60 seconds
                    exclude=[
                        asyncpg.PostgresSyntaxError,
                        asyncpg.InsufficientPrivilegeError,
                    ],
                )

                logger.info(f"Pool {db_id} created successfully")
                return db_id

            except Exception as e:
                logger.error(f"Failed to create pool {db_id}: {e}")
                raise ConnectionError(f"Failed to create database pool: {e}") from e

    async def get_pool(self, db_id: str) -> asyncpg.Pool | None:
        """
        Get existing pool by ID.

        Args:
            db_id: Database identifier

        Returns:
            Pool instance or None if not found
        """
        return self._pools.get(db_id)

    async def get_or_create_pool(self, config: DBConfig) -> tuple[str, asyncpg.Pool]:
        """
        Get existing pool or create new one.

        Args:
            config: Database configuration

        Returns:
            Tuple of (db_id, pool)
        """
        db_id = config.get_id()
        pool = await self.get_pool(db_id)

        if pool is None:
            db_id = await self.create_pool(config)
            pool = self._pools[db_id]

        self._last_used[db_id] = datetime.now()
        return db_id, pool

    async def close_pool(self, db_id: str) -> None:
        """
        Close and remove a specific pool.

        Args:
            db_id: Database identifier
        """
        async with self._lock:
            pool = self._pools.pop(db_id, None)
            if pool is not None:
                logger.info(f"Closing pool {db_id}")
                await pool.close()
                self._pool_configs.pop(db_id, None)
                self._last_used.pop(db_id, None)
                self._circuit_breakers.pop(db_id, None)
                self._acquire_times.pop(db_id, None)
                self._query_counts.pop(db_id, None)

    async def close_all(self) -> None:
        """Close all pools and stop background tasks."""
        logger.info("Closing all connection pools")

        # Cancel background tasks
        for task in self._background_tasks:
            task.cancel()
        await asyncio.gather(*self._background_tasks, return_exceptions=True)

        # Close all pools
        async with self._lock:
            for db_id in list(self._pools.keys()):
                await self.close_pool(db_id)

        logger.info("All pools closed")

    async def execute_query(
        self,
        db_id: str,
        query: str,
        timeout: float = 30.0,
        readonly: bool = True,
        max_retries: int = 2,
    ) -> list[dict[str, Any]]:
        """
        Execute query with automatic error handling and retries.

        Args:
            db_id: Database identifier
            query: SQL query to execute
            timeout: Query timeout in seconds
            readonly: Whether query is read-only
            max_retries: Maximum retry attempts

        Returns:
            List of result rows as dictionaries

        Raises:
            ValueError: If pool not found or invalid SQL
            TimeoutError: If query exceeds timeout
            PermissionError: If insufficient privileges
            ConnectionError: If database connection fails
        """
        pool = await self.get_pool(db_id)
        if pool is None:
            raise ValueError(f"Pool {db_id} not found")

        # Update last used timestamp
        self._last_used[db_id] = datetime.now()

        # Get circuit breaker for this database
        breaker = self._circuit_breakers[db_id]

        @breaker
        async def _execute():
            return await self._execute_with_recovery(
                pool, query, timeout, readonly, max_retries, db_id
            )

        return await _execute()

    async def _execute_with_recovery(
        self,
        pool: asyncpg.Pool,
        query: str,
        timeout: float,
        readonly: bool,
        max_retries: int,
        db_id: str,
    ) -> list[dict[str, Any]]:
        """Execute query with automatic error recovery."""
        for attempt in range(max_retries):
            try:
                # Track acquisition time
                start_time = asyncio.get_event_loop().time()

                async with pool.acquire(timeout=10.0) as conn:
                    acquire_time = (
                        asyncio.get_event_loop().time() - start_time
                    ) * 1000
                    self._acquire_times[db_id].append(acquire_time)
                    self._query_counts[db_id] += 1

                    # Execute in transaction (read-only if specified)
                    async with conn.transaction(
                        isolation="read_committed", readonly=readonly
                    ):
                        result = await asyncio.wait_for(
                            conn.fetch(query), timeout=timeout
                        )
                        return [dict(row) for row in result]

            except asyncpg.OutdatedSchemaCacheError:
                logger.warning("Schema cache outdated, reloading")
                async with pool.acquire() as conn:
                    await conn.reload_schema_state()
                if attempt < max_retries - 1:
                    continue
                raise

            except asyncpg.InvalidCachedStatementError:
                logger.warning("Cached statement invalid, retrying")
                if attempt < max_retries - 1:
                    continue
                raise

            except asyncpg.PoolTimeoutError as e:
                logger.error(f"Pool exhausted (attempt {attempt + 1}/{max_retries})")
                if attempt == max_retries - 1:
                    raise ConnectionError("Database pool exhausted") from e
                await asyncio.sleep(1.0 * (attempt + 1))
                continue

            except asyncpg.PostgresSyntaxError as e:
                logger.error(f"SQL syntax error: {e}")
                raise ValueError(f"Invalid SQL syntax: {e}") from e

            except asyncpg.InsufficientPrivilegeError as e:
                logger.error(f"Permission denied: {e}")
                raise PermissionError(f"Insufficient privileges: {e}") from e

            except asyncpg.QueryCanceledError as e:
                logger.error("Query canceled due to timeout")
                raise TimeoutError("Query timeout exceeded") from e

            except asyncio.TimeoutError as e:
                logger.error(f"Command timeout after {timeout}s")
                raise TimeoutError(f"Query timeout after {timeout}s") from e

            except (ConnectionResetError, OSError) as e:
                logger.error(
                    f"Network error (attempt {attempt + 1}/{max_retries}): {e}"
                )
                if attempt == max_retries - 1:
                    raise ConnectionError("Database connection lost") from e
                await asyncio.sleep(2.0 * (attempt + 1))
                continue

        raise RuntimeError("Max retries exceeded")

    async def get_pool_stats(self, db_id: str) -> PoolStats | None:
        """
        Get connection pool statistics.

        Args:
            db_id: Database identifier

        Returns:
            Pool statistics or None if pool not found
        """
        pool = await self.get_pool(db_id)
        if pool is None:
            return None

        # Calculate average acquire time
        acquire_times = self._acquire_times.get(db_id, [])
        avg_acquire_time = sum(acquire_times) / len(acquire_times) if acquire_times else 0.0

        # Keep only last 100 acquire times to prevent memory growth
        if len(acquire_times) > 100:
            self._acquire_times[db_id] = acquire_times[-100:]

        return PoolStats(
            db_id=db_id,
            size=pool.get_size(),
            free=pool.get_idle_size(),
            max_size=pool.get_max_size(),
            min_size=pool.get_min_size(),
            queries_executed=self._query_counts.get(db_id, 0),
            avg_acquire_time_ms=avg_acquire_time,
            last_used=self._last_used.get(db_id, datetime.now()),
        )

    async def invalidate_schema_cache(self, db_id: str) -> None:
        """
        Force schema cache reload for database.

        Args:
            db_id: Database identifier

        Raises:
            ValueError: If pool not found
        """
        pool = await self.get_pool(db_id)
        if pool is None:
            raise ValueError(f"Pool {db_id} not found")

        logger.info(f"Invalidating schema cache for {db_id}")
        async with pool.acquire() as conn:
            await conn.reload_schema_state()

    async def _cleanup_idle_pools(self) -> None:
        """Background task to close idle pools."""
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute

                now = datetime.now()
                idle_pools = []

                for db_id, last_used in self._last_used.items():
                    if now - last_used > self._idle_pool_timeout:
                        idle_pools.append(db_id)

                for db_id in idle_pools:
                    logger.info(f"Closing idle pool {db_id}")
                    await self.close_pool(db_id)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup task: {e}")

    async def _monitor_pools(self) -> None:
        """Background task to collect metrics."""
        while True:
            try:
                await asyncio.sleep(30)  # Monitor every 30 seconds

                for db_id in list(self._pools.keys()):
                    stats = await self.get_pool_stats(db_id)
                    if stats:
                        logger.debug(
                            f"Pool {db_id}: size={stats.size}/{stats.max_size}, "
                            f"free={stats.free}, queries={stats.queries_executed}, "
                            f"avg_acquire={stats.avg_acquire_time_ms:.2f}ms"
                        )

                        # Alert if pool is near exhaustion
                        if stats.free < 2 and stats.size >= stats.max_size:
                            logger.warning(
                                f"Pool {db_id} near exhaustion: "
                                f"free={stats.free}, size={stats.size}"
                            )

                        # Alert if acquire time is high
                        if stats.avg_acquire_time_ms > 100:
                            logger.warning(
                                f"Pool {db_id} slow acquire time: "
                                f"{stats.avg_acquire_time_ms:.2f}ms"
                            )

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring task: {e}")
