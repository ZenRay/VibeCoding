"""
Tests for PoolManager behavior with mocked asyncpg.

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

from typing import Any

import pytest

from postgres_mcp.db.connection_pool import PoolManager
from postgres_mcp.models.connection import DatabaseConnection


class _FakeConnection:
    def __init__(self, should_fail: bool = False) -> None:
        self.should_fail = should_fail

    async def execute(self, _query: str) -> str:
        if self.should_fail:
            raise RuntimeError("health check failed")
        return "OK"


class _FakePool:
    def __init__(self, connection: _FakeConnection) -> None:
        self._connection = connection
        self.closed = False

    async def acquire(self) -> _FakeConnection:
        return self._connection

    async def release(self, _connection: _FakeConnection) -> None:
        return None

    async def close(self) -> None:
        self.closed = True


def _db_config(name: str = "primary") -> DatabaseConnection:
    return DatabaseConnection(
        name=name,
        host="localhost",
        port=5432,
        database="app",
        user="readonly",
        password_env_var="PRIMARY_DB_PASSWORD",
        ssl_mode="prefer",
        min_pool_size=1,
        max_pool_size=2,
    )


@pytest.mark.asyncio
async def test_pool_manager_initialize(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Ensure initialize creates pools and breakers.

    Args:
    ----------
        monkeypatch: Pytest monkeypatch fixture.

    Returns:
    ----------
        None

    Raises:
    ----------
        None
    """

    async def fake_create_pool(**_kwargs: Any) -> _FakePool:
        return _FakePool(_FakeConnection())

    monkeypatch.setattr("asyncpg.create_pool", fake_create_pool)

    manager = PoolManager([_db_config()])
    await manager.initialize()

    assert "primary" in manager._pools
    assert "primary" in manager._breakers


@pytest.mark.asyncio
async def test_pool_manager_get_connection(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Ensure connection acquisition yields a connection.

    Args:
    ----------
        monkeypatch: Pytest monkeypatch fixture.

    Returns:
    ----------
        None

    Raises:
    ----------
        None
    """

    async def fake_create_pool(**_kwargs: Any) -> _FakePool:
        return _FakePool(_FakeConnection())

    monkeypatch.setattr("asyncpg.create_pool", fake_create_pool)

    manager = PoolManager([_db_config()])
    await manager.initialize()

    async with manager.get_connection("primary") as connection:
        assert isinstance(connection, _FakeConnection)


@pytest.mark.asyncio
async def test_health_check_reconnects(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Ensure health checks reconnect when a pool is unhealthy.

    Args:
    ----------
        monkeypatch: Pytest monkeypatch fixture.

    Returns:
    ----------
        None

    Raises:
    ----------
        None
    """

    pools: list[_FakePool] = []

    async def fake_create_pool(**_kwargs: Any) -> _FakePool:
        should_fail = len(pools) == 0
        pool = _FakePool(_FakeConnection(should_fail=should_fail))
        pools.append(pool)
        return pool

    monkeypatch.setattr("asyncpg.create_pool", fake_create_pool)

    manager = PoolManager([_db_config()])
    await manager.initialize()

    healthy = await manager.health_check("primary")
    assert healthy is False
    assert len(pools) == 2
