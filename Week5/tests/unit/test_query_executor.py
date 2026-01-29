"""
Unit tests for QueryExecutor.

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

from unittest.mock import AsyncMock

import pytest

from postgres_mcp.core.query_executor import QueryExecutionError, QueryExecutor
from postgres_mcp.models.query import GeneratedQuery
from postgres_mcp.models.result import ColumnInfo, QueryResult


@pytest.fixture
def mock_sql_generator() -> AsyncMock:
    """
    Create a mock SQL generator.

    Args:
    ----------
        None

    Returns:
    ----------
        Mock SQLGenerator.

    Raises:
    ----------
        None
    """
    mock = AsyncMock()
    mock.generate.return_value = GeneratedQuery(
        sql="SELECT * FROM users LIMIT 1000",
        validated=True,
        warnings=[],
        explanation="Query to select all users",
        assumptions=[],
        generation_method="ai_generated",
    )
    return mock


@pytest.fixture
def mock_pool_manager() -> AsyncMock:
    """
    Create a mock pool manager.

    Args:
    ----------
        None

    Returns:
    ----------
        Mock PoolManager.

    Raises:
    ----------
        None
    """
    mock = AsyncMock()
    mock_connection = AsyncMock()

    # Create a proper async context manager
    from contextlib import asynccontextmanager

    @asynccontextmanager
    async def mock_get_connection(database):
        yield mock_connection

    mock.get_connection = mock_get_connection
    return mock


@pytest.fixture
def mock_query_runner() -> AsyncMock:
    """
    Create a mock query runner.

    Args:
    ----------
        None

    Returns:
    ----------
        Mock QueryRunner.

    Raises:
    ----------
        None
    """
    mock = AsyncMock()
    mock.execute.return_value = QueryResult(
        columns=[
            ColumnInfo(name="id", type="integer"),
            ColumnInfo(name="name", type="text"),
        ],
        rows=[{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}],
        row_count=2,
        execution_time_ms=15.5,
        truncated=False,
    )
    return mock


@pytest.fixture
def query_executor(
    mock_sql_generator: AsyncMock, mock_pool_manager: AsyncMock, mock_query_runner: AsyncMock
) -> QueryExecutor:
    """
    Create a QueryExecutor instance for testing.

    Args:
    ----------
        mock_sql_generator: Mock SQL generator.
        mock_pool_manager: Mock pool manager.
        mock_query_runner: Mock query runner.

    Returns:
    ----------
        QueryExecutor instance.

    Raises:
    ----------
        None
    """
    return QueryExecutor(
        sql_generator=mock_sql_generator,
        pool_manager=mock_pool_manager,
        query_runner=mock_query_runner,
    )


@pytest.mark.asyncio
async def test_execute_success(
    query_executor: QueryExecutor,
    mock_sql_generator: AsyncMock,
    mock_pool_manager: AsyncMock,
    mock_query_runner: AsyncMock,
) -> None:
    """
    Test successful query execution.

    Args:
    ----------
        query_executor: QueryExecutor fixture.
        mock_sql_generator: Mock SQL generator.
        mock_pool_manager: Mock pool manager.
        mock_query_runner: Mock query runner.

    Returns:
    ----------
        None

    Raises:
    ----------
        None
    """
    result = await query_executor.execute("Show all users", "test_db")

    assert result.sql == "SELECT * FROM users LIMIT 1000"
    assert result.row_count == 2
    assert len(result.rows) == 2
    mock_sql_generator.generate.assert_called_once_with("Show all users", "test_db")
    mock_query_runner.execute.assert_called_once()


@pytest.mark.asyncio
async def test_execute_with_limit(
    query_executor: QueryExecutor,
    mock_sql_generator: AsyncMock,
    mock_pool_manager: AsyncMock,
    mock_query_runner: AsyncMock,
) -> None:
    """
    Test query execution with custom limit.

    Args:
    ----------
        query_executor: QueryExecutor fixture.
        mock_sql_generator: Mock SQL generator.
        mock_pool_manager: Mock pool manager.
        mock_query_runner: Mock query runner.

    Returns:
    ----------
        None

    Raises:
    ----------
        None
    """
    result = await query_executor.execute("Show all users", "test_db", limit=500)

    assert result.row_count == 2
    mock_query_runner.execute.assert_called_once()
    # Verify limit was passed to query_runner
    call_args = mock_query_runner.execute.call_args
    assert call_args.kwargs.get("limit") == 500


@pytest.mark.asyncio
async def test_execute_validation_failed(
    query_executor: QueryExecutor, mock_sql_generator: AsyncMock
) -> None:
    """
    Test query execution when validation fails.

    Args:
    ----------
        query_executor: QueryExecutor fixture.
        mock_sql_generator: Mock SQL generator.

    Returns:
    ----------
        None

    Raises:
    ----------
        None
    """
    mock_sql_generator.generate.return_value = GeneratedQuery(
        sql="DELETE FROM users",
        validated=False,
        warnings=["Contains DML statement"],
        explanation="",
        assumptions=[],
        generation_method="ai_generated",
    )

    with pytest.raises(QueryExecutionError) as exc_info:
        await query_executor.execute("Delete all users", "test_db")

    assert "failed validation" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_execute_generation_error(
    query_executor: QueryExecutor, mock_sql_generator: AsyncMock
) -> None:
    """
    Test query execution when SQL generation fails.

    Args:
    ----------
        query_executor: QueryExecutor fixture.
        mock_sql_generator: Mock SQL generator.

    Returns:
    ----------
        None

    Raises:
    ----------
        None
    """
    mock_sql_generator.generate.side_effect = Exception("AI service unavailable")

    with pytest.raises(QueryExecutionError) as exc_info:
        await query_executor.execute("Show all users", "test_db")

    assert "ai service unavailable" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_execute_connection_error(
    query_executor: QueryExecutor, mock_pool_manager: AsyncMock
) -> None:
    """
    Test query execution when connection fails.

    Args:
    ----------
        query_executor: QueryExecutor fixture.
        mock_pool_manager: Mock pool manager.

    Returns:
    ----------
        None

    Raises:
    ----------
        None
    """
    from contextlib import asynccontextmanager

    @asynccontextmanager
    async def mock_get_connection_error(database):
        raise Exception("Connection failed")
        yield  # pragma: no cover

    mock_pool_manager.get_connection = mock_get_connection_error

    with pytest.raises(QueryExecutionError) as exc_info:
        await query_executor.execute("Show all users", "test_db")

    assert "connection failed" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_execute_runner_error(
    query_executor: QueryExecutor, mock_query_runner: AsyncMock
) -> None:
    """
    Test query execution when query runner fails.

    Args:
    ----------
        query_executor: QueryExecutor fixture.
        mock_query_runner: Mock query runner.

    Returns:
    ----------
        None

    Raises:
    ----------
        None
    """
    mock_query_runner.execute.side_effect = Exception("Query execution failed")

    with pytest.raises(QueryExecutionError) as exc_info:
        await query_executor.execute("Show all users", "test_db")

    assert "query execution failed" in str(exc_info.value).lower()
