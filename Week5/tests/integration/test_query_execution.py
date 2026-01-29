"""
Integration tests for query execution.

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

import pytest

from postgres_mcp.ai.openai_client import OpenAIClient
from postgres_mcp.ai.prompt_builder import PromptBuilder
from postgres_mcp.core.query_executor import QueryExecutor
from postgres_mcp.core.schema_cache import SchemaCache
from postgres_mcp.core.sql_generator import SQLGenerator
from postgres_mcp.core.sql_validator import SQLValidator
from postgres_mcp.db.connection_pool import PoolManager
from postgres_mcp.db.query_runner import QueryRunner


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.skip(reason="Requires live database and OpenAI API - manual testing only")
async def test_execute_query_end_to_end(
    test_pool_manager: PoolManager, test_schema_cache: SchemaCache
) -> None:
    """
    Test end-to-end query execution with real components.

    Args:
    ----------
        test_pool_manager: Test pool manager fixture.
        test_schema_cache: Test schema cache fixture.

    Returns:
    ----------
        None

    Raises:
    ----------
        None

    Example:
    ----------
        >>> # This test requires:
        >>> # 1. Live PostgreSQL database
        >>> # 2. Valid OPENAI_API_KEY environment variable
        >>> # 3. Test data in database
        >>> result = await test_execute_query_end_to_end(pool_manager, cache)
        >>> assert result is not None
    """
    # Setup components
    openai_client = OpenAIClient(api_key="test-key", model="gpt-4o-mini")
    prompt_builder = PromptBuilder()
    sql_validator = SQLValidator()
    sql_generator = SQLGenerator(
        openai_client=openai_client,
        prompt_builder=prompt_builder,
        schema_cache=test_schema_cache,
        validator=sql_validator,
    )
    query_runner = QueryRunner(timeout_seconds=30.0)
    query_executor = QueryExecutor(
        sql_generator=sql_generator,
        pool_manager=test_pool_manager,
        query_runner=query_runner,
    )

    # Execute query
    result = await query_executor.execute(
        natural_language="Show all users created in the last 7 days",
        database="ecommerce_small",
        limit=100,
    )

    # Verify result
    assert result.sql is not None
    assert result.row_count >= 0
    assert result.execution_time_ms > 0
    assert len(result.columns) > 0
    assert "SELECT" in result.sql.upper()
    assert "FROM" in result.sql.upper()


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.skip(reason="Requires live database - manual testing only")
async def test_execute_query_timeout_handling(
    test_pool_manager: PoolManager, test_schema_cache: SchemaCache
) -> None:
    """
    Test query execution timeout handling.

    Args:
    ----------
        test_pool_manager: Test pool manager fixture.
        test_schema_cache: Test schema cache fixture.

    Returns:
    ----------
        None

    Raises:
    ----------
        QueryTimeoutError: Expected when query exceeds timeout.

    Example:
    ----------
        >>> # This test verifies timeout mechanism
        >>> with pytest.raises(QueryTimeoutError):
        ...     await test_execute_query_timeout_handling(pool_manager, cache)
    """
    # Setup with very short timeout
    openai_client = OpenAIClient(api_key="test-key", model="gpt-4o-mini")
    prompt_builder = PromptBuilder()
    sql_validator = SQLValidator()
    sql_generator = SQLGenerator(
        openai_client=openai_client,
        prompt_builder=prompt_builder,
        schema_cache=test_schema_cache,
        validator=sql_validator,
    )
    query_runner = QueryRunner(timeout_seconds=0.1)  # Very short timeout
    query_executor = QueryExecutor(
        sql_generator=sql_generator,
        pool_manager=test_pool_manager,
        query_runner=query_runner,
    )

    # This should timeout
    from postgres_mcp.db.query_runner import QueryTimeoutError

    with pytest.raises(QueryTimeoutError):
        await query_executor.execute(
            natural_language="Run a very slow query with pg_sleep(10)",
            database="ecommerce_small",
        )


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.skip(reason="Requires live database - manual testing only")
async def test_execute_query_with_large_result(
    test_pool_manager: PoolManager, test_schema_cache: SchemaCache
) -> None:
    """
    Test query execution with large result set and truncation.

    Args:
    ----------
        test_pool_manager: Test pool manager fixture.
        test_schema_cache: Test schema cache fixture.

    Returns:
    ----------
        None

    Raises:
    ----------
        None

    Example:
    ----------
        >>> result = await test_execute_query_with_large_result(pool_manager, cache)
        >>> assert result.truncated is True
    """
    # Setup components
    openai_client = OpenAIClient(api_key="test-key", model="gpt-4o-mini")
    prompt_builder = PromptBuilder()
    sql_validator = SQLValidator()
    sql_generator = SQLGenerator(
        openai_client=openai_client,
        prompt_builder=prompt_builder,
        schema_cache=test_schema_cache,
        validator=sql_validator,
    )
    query_runner = QueryRunner(timeout_seconds=30.0)
    query_executor = QueryExecutor(
        sql_generator=sql_generator,
        pool_manager=test_pool_manager,
        query_runner=query_runner,
    )

    # Execute query with low limit
    result = await query_executor.execute(
        natural_language="Show all orders",
        database="ecommerce_small",
        limit=10,  # Force truncation
    )

    # Verify truncation
    assert result.row_count <= 10
    if result.row_count == 10:
        assert result.truncated is True
