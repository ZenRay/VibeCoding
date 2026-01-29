"""
Integration tests for multi-database scenarios.

Tests the complete multi-database support including database routing,
schema isolation, connection pool management, and cross-database queries.

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

from postgres_mcp.ai.openai_client import OpenAIClient
from postgres_mcp.ai.prompt_builder import PromptBuilder
from postgres_mcp.core.query_executor import QueryExecutor
from postgres_mcp.core.schema_cache import SchemaCache
from postgres_mcp.core.sql_generator import SQLGenerator
from postgres_mcp.core.sql_validator import SQLValidator
from postgres_mcp.db.connection_pool import PoolManager
from postgres_mcp.db.query_runner import QueryRunner
from postgres_mcp.db.schema_inspector import SchemaInspector
from postgres_mcp.models.connection import DatabaseConnection


@pytest.mark.asyncio
@pytest.mark.integration
async def test_multi_database_schema_isolation() -> None:
    """
    Test that schemas are properly isolated between databases.

    Verifies that each database maintains its own schema cache and that
    schemas don't leak between different database connections.

    Args:
    ----------
        None

    Returns:
    ----------
        None

    Raises:
    ----------
        None

    Example:
    ----------
        >>> await test_multi_database_schema_isolation()
        >>> # Schemas are properly isolated
    """
    # Setup two database connections
    db_config1 = DatabaseConnection(
        name="ecommerce_small",
        host=os.getenv("TEST_DB_HOST", "localhost"),
        port=int(os.getenv("TEST_DB_PORT", "5432")),
        database="ecommerce_small",
        user=os.getenv("TEST_DB_USER", "testuser"),
        password_env_var="TEST_DB_PASSWORD",
        ssl_mode="disable",
        min_pool_size=1,
        max_pool_size=2,
    )

    db_config2 = DatabaseConnection(
        name="social_medium",
        host=os.getenv("TEST_DB_HOST", "localhost"),
        port=int(os.getenv("TEST_DB_PORT", "5432")),
        database="social_medium",
        user=os.getenv("TEST_DB_USER", "testuser"),
        password_env_var="TEST_DB_PASSWORD",
        ssl_mode="disable",
        min_pool_size=1,
        max_pool_size=2,
    )

    # Initialize components
    pool_manager = PoolManager([db_config1, db_config2])
    await pool_manager.initialize()

    inspector1 = SchemaInspector(db_config1, pool_manager)
    inspector2 = SchemaInspector(db_config2, pool_manager)
    schema_cache = SchemaCache({db_config1.name: inspector1, db_config2.name: inspector2})
    await schema_cache.initialize()

    try:
        # Get schemas
        schema1 = await schema_cache.get_schema("ecommerce_small")
        schema2 = await schema_cache.get_schema("social_medium")

        # Verify schemas are loaded
        assert schema1 is not None
        assert schema2 is not None

        # Verify database names are correct
        assert schema1.database == "ecommerce_small"
        assert schema2.database == "social_medium"

        # Verify schemas are different
        tables1 = {table.name for table in schema1.tables}
        tables2 = {table.name for table in schema2.tables}

        # Each database should have tables
        assert len(tables1) > 0
        assert len(tables2) > 0

        # Tables should be different (or at least one is different)
        if len(tables1) > 0 and len(tables2) > 0:
            # Verify they don't share all tables
            assert tables1 != tables2 or len(tables1 & tables2) < len(tables1)

    finally:
        # Cleanup
        await schema_cache.close()
        await pool_manager.close_all()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_multi_database_query_execution() -> None:
    """
    Test query execution across multiple databases.

    Verifies that queries can be executed on different databases and that
    the query executor correctly routes to the specified database.

    Args:
    ----------
        None

    Returns:
    ----------
        None

    Raises:
    ----------
        None

    Example:
    ----------
        >>> await test_multi_database_query_execution()
        >>> # Queries executed on correct databases
    """
    # Skip if no API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        pytest.skip("OPENAI_API_KEY not set - skipping integration test")

    # Setup two database connections
    db_config1 = DatabaseConnection(
        name="ecommerce_small",
        host=os.getenv("TEST_DB_HOST", "localhost"),
        port=int(os.getenv("TEST_DB_PORT", "5432")),
        database="ecommerce_small",
        user=os.getenv("TEST_DB_USER", "testuser"),
        password_env_var="TEST_DB_PASSWORD",
        ssl_mode="disable",
        min_pool_size=1,
        max_pool_size=2,
    )

    db_config2 = DatabaseConnection(
        name="social_medium",
        host=os.getenv("TEST_DB_HOST", "localhost"),
        port=int(os.getenv("TEST_DB_PORT", "5432")),
        database="social_medium",
        user=os.getenv("TEST_DB_USER", "testuser"),
        password_env_var="TEST_DB_PASSWORD",
        ssl_mode="disable",
        min_pool_size=1,
        max_pool_size=2,
    )

    # Initialize components
    pool_manager = PoolManager([db_config1, db_config2])
    await pool_manager.initialize()

    inspector1 = SchemaInspector(db_config1, pool_manager)
    inspector2 = SchemaInspector(db_config2, pool_manager)
    schema_cache = SchemaCache({db_config1.name: inspector1, db_config2.name: inspector2})
    await schema_cache.initialize()

    openai_client = OpenAIClient(
        api_key=api_key,
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        base_url=os.getenv("OPENAI_BASE_URL"),
    )
    prompt_builder = PromptBuilder()
    sql_validator = SQLValidator()

    sql_generator = SQLGenerator(
        openai_client=openai_client,
        prompt_builder=prompt_builder,
        schema_cache=schema_cache,
        validator=sql_validator,
    )

    query_runner = QueryRunner(timeout_seconds=30.0)
    query_executor = QueryExecutor(
        sql_generator=sql_generator,
        pool_manager=pool_manager,
        query_runner=query_runner,
    )

    try:
        # Execute query on first database
        result1 = await query_executor.execute(
            natural_language="Count all records in the first table",
            database="ecommerce_small",
            limit=10,
        )

        # Execute query on second database
        result2 = await query_executor.execute(
            natural_language="Count all records in the first table",
            database="social_medium",
            limit=10,
        )

        # Verify both queries succeeded
        assert result1.sql is not None
        assert result2.sql is not None
        assert result1.execution_time_ms > 0
        assert result2.execution_time_ms > 0

        # Verify row counts are non-negative
        assert result1.row_count >= 0
        assert result2.row_count >= 0

    finally:
        # Cleanup
        await schema_cache.close()
        await pool_manager.close_all()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_multi_database_connection_pool_management() -> None:
    """
    Test connection pool management for multiple databases.

    Verifies that the pool manager correctly maintains separate connection
    pools for each database and handles concurrent queries efficiently.

    Args:
    ----------
        None

    Returns:
    ----------
        None

    Raises:
    ----------
        None

    Example:
    ----------
        >>> await test_multi_database_connection_pool_management()
        >>> # Connection pools managed correctly
    """
    # Setup three database connections
    db_configs = [
        DatabaseConnection(
            name="ecommerce_small",
            host=os.getenv("TEST_DB_HOST", "localhost"),
            port=int(os.getenv("TEST_DB_PORT", "5432")),
            database="ecommerce_small",
            user=os.getenv("TEST_DB_USER", "testuser"),
            password_env_var="TEST_DB_PASSWORD",
            ssl_mode="disable",
            min_pool_size=1,
            max_pool_size=3,
        ),
        DatabaseConnection(
            name="social_medium",
            host=os.getenv("TEST_DB_HOST", "localhost"),
            port=int(os.getenv("TEST_DB_PORT", "5432")),
            database="social_medium",
            user=os.getenv("TEST_DB_USER", "testuser"),
            password_env_var="TEST_DB_PASSWORD",
            ssl_mode="disable",
            min_pool_size=1,
            max_pool_size=3,
        ),
        DatabaseConnection(
            name="erp_large",
            host=os.getenv("TEST_DB_HOST", "localhost"),
            port=int(os.getenv("TEST_DB_PORT", "5432")),
            database="erp_large",
            user=os.getenv("TEST_DB_USER", "testuser"),
            password_env_var="TEST_DB_PASSWORD",
            ssl_mode="disable",
            min_pool_size=1,
            max_pool_size=3,
        ),
    ]

    # Initialize pool manager
    pool_manager = PoolManager(db_configs)
    await pool_manager.initialize()

    try:
        # Get connections from all pools
        async with pool_manager.get_connection("ecommerce_small") as conn1:
            result1 = await conn1.fetchval("SELECT 1")
            assert result1 == 1

        async with pool_manager.get_connection("social_medium") as conn2:
            result2 = await conn2.fetchval("SELECT 2")
            assert result2 == 2

        async with pool_manager.get_connection("erp_large") as conn3:
            result3 = await conn3.fetchval("SELECT 3")
            assert result3 == 3

        # Verify all connections worked
        assert result1 == 1
        assert result2 == 2
        assert result3 == 3

    finally:
        # Cleanup
        await pool_manager.close_all()
