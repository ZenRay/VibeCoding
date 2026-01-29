"""
Asyncpg connection pool manager with health checks.

Args:
----------
    None

Returns:
----------
    None

Raises:
----------
    None
"""

from __future__ import annotations

import asyncio
import os
from collections.abc import AsyncIterator, Iterable
from contextlib import asynccontextmanager
from dataclasses import dataclass

import asyncpg
from pybreaker import CircuitBreaker

from postgres_mcp.models.connection import DatabaseConnection


class PoolManagerError(Exception):
    """
    Base exception for pool manager failures.

    Args:
    ----------
        message: Error message.

    Returns:
    ----------
        None

    Raises:
    ----------
        None
    """


class DatabaseNotFoundError(PoolManagerError):
    """
    Raised when a configured database is not found.

    Args:
    ----------
        message: Error message.

    Returns:
    ----------
        None

    Raises:
    ----------
        None
    """


class PoolUnavailableError(PoolManagerError):
    """
    Raised when a connection pool is unavailable.

    Args:
    ----------
        message: Error message.

    Returns:
    ----------
        None

    Raises:
    ----------
        None
    """


@dataclass(frozen=True)
class PoolSettings:
    """
    Default asyncpg pool settings.

    Args:
    ----------
        max_queries: Max queries before recycling a connection.
        max_inactive_connection_lifetime: Idle lifetime in seconds.
        command_timeout: Client command timeout.
        statement_timeout_ms: Server statement timeout in milliseconds.
        idle_in_transaction_timeout_ms: Idle in transaction timeout in milliseconds.
        breaker_fail_max: Failures before opening the circuit.
        breaker_reset_timeout: Circuit breaker reset timeout in seconds.

    Returns:
    ----------
        None

    Raises:
    ----------
        None
    """

    max_queries: int = 50_000
    max_inactive_connection_lifetime: float = 300.0
    command_timeout: float = 60.0
    statement_timeout_ms: int = 30_000
    idle_in_transaction_timeout_ms: int = 60_000
    breaker_fail_max: int = 5
    breaker_reset_timeout: int = 60


class PoolManager:
    """
    Manage asyncpg pools across multiple databases.

    Args:
    ----------
        db_configs: Database configuration entries.
        pool_settings: Optional pool settings override.

    Returns:
    ----------
        None

    Raises:
    ----------
        None
    """

    def __init__(
        self, db_configs: Iterable[DatabaseConnection], pool_settings: PoolSettings | None = None
    ) -> None:
        self._configs = {config.name: config for config in db_configs}
        self._pools: dict[str, asyncpg.Pool] = {}
        self._breakers: dict[str, CircuitBreaker] = {}
        self._pool_settings = pool_settings or PoolSettings()
        self._health_task: asyncio.Task | None = None

    async def initialize(self) -> None:
        """
        Initialize pools for all configured databases.

        Args:
        ----------
            None

        Returns:
        ----------
            None

        Raises:
        ----------
            asyncpg.PostgresError: If pool creation fails.
        """

        tasks = [self._create_pool(name, config) for name, config in self._configs.items()]
        await asyncio.gather(*tasks)

    async def close_all(self) -> None:
        """
        Close all pools and stop health checks.

        Args:
        ----------
            None

        Returns:
        ----------
            None

        Raises:
        ----------
            None
        """

        await self.stop_health_checks()
        for pool in self._pools.values():
            await pool.close()
        self._pools.clear()
        self._breakers.clear()

    def start_health_checks(self, interval_seconds: float = 60.0) -> None:
        """
        Start background health checks for all pools.

        Args:
        ----------
            interval_seconds: Interval between health checks.

        Returns:
        ----------
            None

        Raises:
        ----------
            ValueError: If interval_seconds is less than 1.
        """

        if interval_seconds < 1:
            raise ValueError("interval_seconds must be >= 1")
        if self._health_task is None or self._health_task.done():
            self._health_task = asyncio.create_task(self._run_health_checks(interval_seconds))

    async def stop_health_checks(self) -> None:
        """
        Stop background health checks if running.

        Args:
        ----------
            None

        Returns:
        ----------
            None

        Raises:
        ----------
            None
        """

        if self._health_task is not None:
            self._health_task.cancel()
            try:
                await self._health_task
            except asyncio.CancelledError:
                pass
            self._health_task = None

    async def health_check(self, database: str) -> bool:
        """
        Run a health check for a specific database pool.

        Args:
        ----------
            database: Database name to check.

        Returns:
        ----------
            True if the pool is healthy, otherwise False.

        Raises:
        ----------
            DatabaseNotFoundError: If the database is not configured.
        """

        if database not in self._configs:
            raise DatabaseNotFoundError(f"database not configured: {database}")

        pool = self._pools.get(database)
        if pool is None:
            await self._create_pool(database, self._configs[database])
            return True

        connection = None
        try:
            connection = await pool.acquire()
            await connection.execute("SELECT 1")
            return True
        except Exception:
            await self._reconnect(database)
            return False
        finally:
            if connection is not None:
                await pool.release(connection)

    async def health_check_all(self) -> dict[str, bool]:
        """
        Run health checks for all pools.

        Args:
        ----------
            None

        Returns:
        ----------
            Mapping of database name to health status.

        Raises:
        ----------
            None
        """

        results: dict[str, bool] = {}
        for name in self._configs:
            results[name] = await self.health_check(name)
        return results

    @asynccontextmanager
    async def get_connection(self, database: str) -> AsyncIterator[asyncpg.Connection]:
        """
        Acquire a connection from a pool.

        Args:
        ----------
            database: Database name to acquire a connection for.

        Returns:
        ----------
            Async iterator yielding an asyncpg connection.

        Raises:
        ----------
            DatabaseNotFoundError: If the database is not configured.
            PoolUnavailableError: If the pool is unavailable or circuit is open.
        """

        if database not in self._pools:
            raise DatabaseNotFoundError(f"database not configured: {database}")

        breaker = self._breakers[database]
        if breaker.current_state == "open":
            raise PoolUnavailableError("connection pool circuit breaker is open")

        pool = self._pools[database]
        connection = None
        try:
            connection = await pool.acquire()
            yield connection
        except asyncpg.TooManyConnectionsError as exc:
            raise PoolUnavailableError("connection pool exhausted") from exc
        except Exception as exc:
            raise PoolUnavailableError("connection pool error") from exc
        finally:
            if connection is not None:
                await pool.release(connection)

    async def _run_health_checks(self, interval_seconds: float) -> None:
        """
        Background task loop for health checks.

        Args:
        ----------
            interval_seconds: Interval between checks.

        Returns:
        ----------
            None

        Raises:
        ----------
            None
        """

        while True:
            await self.health_check_all()
            await asyncio.sleep(interval_seconds)

    async def _reconnect(self, database: str) -> None:
        """
        Reconnect a pool after a failed health check.

        Args:
        ----------
            database: Database name to reconnect.

        Returns:
        ----------
            None

        Raises:
        ----------
            DatabaseNotFoundError: If the database is not configured.
        """

        if database not in self._configs:
            raise DatabaseNotFoundError(f"database not configured: {database}")

        pool = self._pools.get(database)
        if pool is not None:
            await pool.close()
        await self._create_pool(database, self._configs[database])

    async def _create_pool(self, name: str, config: DatabaseConnection) -> None:
        """
        Create and register a pool for a database.

        Args:
        ----------
            name: Database config name.
            config: Database connection configuration.

        Returns:
        ----------
            None

        Raises:
        ----------
            asyncpg.PostgresError: If pool creation fails.
        """

        password = os.getenv(config.password_env_var)
        pool = await asyncpg.create_pool(
            host=config.host,
            port=config.port,
            database=config.database,
            user=config.user,
            password=password,
            min_size=config.min_pool_size,
            max_size=config.max_pool_size,
            max_queries=self._pool_settings.max_queries,
            max_inactive_connection_lifetime=self._pool_settings.max_inactive_connection_lifetime,
            command_timeout=self._pool_settings.command_timeout,
            server_settings={
                "statement_timeout": str(self._pool_settings.statement_timeout_ms),
                "idle_in_transaction_session_timeout": str(
                    self._pool_settings.idle_in_transaction_timeout_ms
                ),
            },
        )
        self._pools[name] = pool
        self._breakers[name] = CircuitBreaker(
            fail_max=self._pool_settings.breaker_fail_max,
            reset_timeout=self._pool_settings.breaker_reset_timeout,
        )
