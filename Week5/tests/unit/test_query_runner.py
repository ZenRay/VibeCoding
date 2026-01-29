"""
Unit tests for QueryRunner.

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

from unittest.mock import AsyncMock, MagicMock

import asyncpg
import pytest

from postgres_mcp.db.query_runner import (
    QueryExecutionError,
    QueryRunner,
    QueryTimeoutError,
)


@pytest.fixture
def query_runner() -> QueryRunner:
    """
    Create a QueryRunner instance for testing.

    Args:
    ----------
        None

    Returns:
    ----------
        QueryRunner instance.

    Raises:
    ----------
        None
    """
    return QueryRunner(timeout_seconds=5.0)


@pytest.mark.asyncio
async def test_execute_success(query_runner: QueryRunner) -> None:
    """
    Test successful query execution.

    Args:
    ----------
        query_runner: QueryRunner fixture.

    Returns:
    ----------
        None

    Raises:
    ----------
        None
    """
    mock_connection = AsyncMock(spec=asyncpg.Connection)
    mock_connection.fetch.return_value = [
        {"id": 1, "name": "Alice"},
        {"id": 2, "name": "Bob"},
    ]

    result = await query_runner.execute("SELECT * FROM users", mock_connection)

    assert result.row_count == 2
    assert len(result.rows) == 2
    assert result.rows[0] == {"id": 1, "name": "Alice"}
    assert result.execution_time_ms > 0
    mock_connection.fetch.assert_called_once_with("SELECT * FROM users")


@pytest.mark.asyncio
async def test_execute_with_limit(query_runner: QueryRunner) -> None:
    """
    Test query execution with row limit.

    Args:
    ----------
        query_runner: QueryRunner fixture.

    Returns:
    ----------
        None

    Raises:
    ----------
        None
    """
    mock_connection = AsyncMock(spec=asyncpg.Connection)
    mock_records = [{"id": i, "name": f"User{i}"} for i in range(1500)]
    mock_connection.fetch.return_value = mock_records

    result = await query_runner.execute("SELECT * FROM users", mock_connection, limit=1000)

    assert result.row_count == 1000
    assert len(result.rows) == 1000
    assert result.truncated is True


@pytest.mark.asyncio
async def test_execute_empty_result(query_runner: QueryRunner) -> None:
    """
    Test query execution with no results.

    Args:
    ----------
        query_runner: QueryRunner fixture.

    Returns:
    ----------
        None

    Raises:
    ----------
        None
    """
    mock_connection = AsyncMock(spec=asyncpg.Connection)
    mock_connection.fetch.return_value = []

    result = await query_runner.execute("SELECT * FROM users WHERE id = -1", mock_connection)

    assert result.row_count == 0
    assert len(result.rows) == 0
    assert result.truncated is False


@pytest.mark.asyncio
async def test_execute_timeout(query_runner: QueryRunner) -> None:
    """
    Test query execution timeout.

    Args:
    ----------
        query_runner: QueryRunner fixture.

    Returns:
    ----------
        None

    Raises:
    ----------
        None
    """
    mock_connection = AsyncMock(spec=asyncpg.Connection)
    mock_connection.fetch.side_effect = asyncpg.QueryCanceledError("timeout")

    with pytest.raises(QueryTimeoutError) as exc_info:
        await query_runner.execute("SELECT pg_sleep(100)", mock_connection)

    assert "timed out" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_execute_syntax_error(query_runner: QueryRunner) -> None:
    """
    Test query execution with syntax error.

    Args:
    ----------
        query_runner: QueryRunner fixture.

    Returns:
    ----------
        None

    Raises:
    ----------
        None
    """
    mock_connection = AsyncMock(spec=asyncpg.Connection)
    mock_connection.fetch.side_effect = asyncpg.PostgresSyntaxError("syntax error")

    with pytest.raises(QueryExecutionError) as exc_info:
        await query_runner.execute("SELECT * FORM users", mock_connection)

    assert "syntax error" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_execute_permission_error(query_runner: QueryRunner) -> None:
    """
    Test query execution with permission error.

    Args:
    ----------
        query_runner: QueryRunner fixture.

    Returns:
    ----------
        None

    Raises:
    ----------
        None
    """
    mock_connection = AsyncMock(spec=asyncpg.Connection)
    mock_connection.fetch.side_effect = asyncpg.InsufficientPrivilegeError("permission denied")

    with pytest.raises(QueryExecutionError) as exc_info:
        await query_runner.execute("SELECT * FROM secret_table", mock_connection)

    assert "permission denied" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_execute_connection_error(query_runner: QueryRunner) -> None:
    """
    Test query execution with connection error.

    Args:
    ----------
        query_runner: QueryRunner fixture.

    Returns:
    ----------
        None

    Raises:
    ----------
        None
    """
    mock_connection = AsyncMock(spec=asyncpg.Connection)
    mock_connection.fetch.side_effect = asyncpg.ConnectionDoesNotExistError("connection lost")

    with pytest.raises(QueryExecutionError) as exc_info:
        await query_runner.execute("SELECT * FROM users", mock_connection)

    assert "connection" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_get_column_info(query_runner: QueryRunner) -> None:
    """
    Test extraction of column information.

    Args:
    ----------
        query_runner: QueryRunner fixture.

    Returns:
    ----------
        None

    Raises:
    ----------
        None
    """
    mock_connection = AsyncMock(spec=asyncpg.Connection)
    mock_record = MagicMock()
    mock_record.keys.return_value = ["id", "name", "email"]
    mock_record.__getitem__ = lambda self, key: {
        "id": 1,
        "name": "Alice",
        "email": "alice@example.com",
    }[key]
    mock_connection.fetch.return_value = [mock_record]

    result = await query_runner.execute("SELECT * FROM users", mock_connection)

    assert len(result.columns) == 3
    assert result.columns[0].name == "id"
    assert result.columns[1].name == "name"
    assert result.columns[2].name == "email"
