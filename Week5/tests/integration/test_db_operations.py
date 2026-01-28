"""
Integration tests for database operations.

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

import os

import pytest

from postgres_mcp.db.connection_pool import PoolManager
from postgres_mcp.models.connection import DatabaseConnection


@pytest.mark.asyncio
async def test_pool_manager_executes_simple_query() -> None:
    """
    Ensure PoolManager can execute a basic SELECT query.

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

    host = os.getenv("TEST_DB_HOST")
    port = os.getenv("TEST_DB_PORT")
    database = os.getenv("TEST_DB_NAME")
    user = os.getenv("TEST_DB_USER")
    password = os.getenv("TEST_DB_PASSWORD")

    if not all([host, port, database, user, password]):
        pytest.skip("Integration database environment variables are not set")

    config = DatabaseConnection(
        name="integration",
        host=host,
        port=int(port),
        database=database,
        user=user,
        password_env_var="TEST_DB_PASSWORD",
        ssl_mode="prefer",
        min_pool_size=1,
        max_pool_size=2,
    )

    manager = PoolManager([config])
    await manager.initialize()

    async with manager.get_connection("integration") as connection:
        result = await connection.fetchval("SELECT 1")
        assert result == 1

    await manager.close_all()
