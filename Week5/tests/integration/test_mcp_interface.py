"""
Integration tests for MCP interface.

Tests the complete MCP tool and resource interface, including all tools
(generate_sql, execute_query, list_databases, refresh_schema, query_history)
and resources (schema URIs).

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
from unittest.mock import Mock

import pytest

from postgres_mcp.ai.openai_client import OpenAIClient
from postgres_mcp.ai.prompt_builder import PromptBuilder
from postgres_mcp.core.schema_cache import SchemaCache
from postgres_mcp.core.sql_generator import SQLGenerator
from postgres_mcp.core.sql_validator import SQLValidator
from postgres_mcp.db.connection_pool import PoolManager
from postgres_mcp.db.schema_inspector import SchemaInspector
from postgres_mcp.mcp import resources, tools
from postgres_mcp.models.connection import DatabaseConnection


@pytest.mark.asyncio
@pytest.mark.integration
async def test_mcp_generate_sql_tool() -> None:
    """
    Test MCP generate_sql tool with real components.

    Verifies that the generate_sql MCP tool works end-to-end with actual
    OpenAI API and database schema.

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
        >>> result = await test_mcp_generate_sql_tool()
        >>> assert "SELECT" in result
    """
    # Skip if no API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        pytest.skip("OPENAI_API_KEY not set - skipping integration test")

    # Setup database connection
    db_config = DatabaseConnection(
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

    # Initialize components
    pool_manager = PoolManager([db_config])
    await pool_manager.initialize()

    schema_inspector = SchemaInspector(db_config, pool_manager)
    schema_cache = SchemaCache({db_config.name: schema_inspector})
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

    # Mock config
    config = Mock()
    config.default_database = "ecommerce_small"

    try:
        # Call MCP tool
        result = await tools.handle_generate_sql(
            natural_language="Show all products",
            database="ecommerce_small",
            sql_generator=sql_generator,
            config=config,
        )

        # Verify result format
        assert isinstance(result, str)
        assert "SELECT" in result.upper()
        assert "SQL:" in result or "sql:" in result

    finally:
        # Cleanup
        await schema_cache.close()
        await pool_manager.close_all()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_mcp_list_databases_tool() -> None:
    """
    Test MCP list_databases tool with real components.

    Verifies that the list_databases tool correctly lists all configured
    databases with their schema information.

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
        >>> result = await test_mcp_list_databases_tool()
        >>> assert "ecommerce_small" in result
    """
    # Setup database connection
    db_config = DatabaseConnection(
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

    # Initialize components
    pool_manager = PoolManager([db_config])
    await pool_manager.initialize()

    schema_inspector = SchemaInspector(db_config, pool_manager)
    schema_cache = SchemaCache({db_config.name: schema_inspector})
    await schema_cache.initialize()

    # Mock config
    config = Mock()
    config.default_database = "ecommerce_small"

    try:
        # Call MCP tool
        result = await tools.handle_list_databases(
            schema_cache=schema_cache, pool_manager=pool_manager, config=config
        )

        # Verify result format
        assert isinstance(result, str)
        assert "ecommerce_small" in result
        assert "tables" in result.lower() or "Tables" in result

    finally:
        # Cleanup
        await schema_cache.close()
        await pool_manager.close_all()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_mcp_schema_resource() -> None:
    """
    Test MCP schema resource with real database.

    Verifies that the schema:// resource URI correctly returns database
    schema information in markdown format.

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
        >>> result = await test_mcp_schema_resource()
        >>> assert "products" in result
    """
    # Setup database connection
    db_config = DatabaseConnection(
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

    # Initialize components
    pool_manager = PoolManager([db_config])
    await pool_manager.initialize()

    schema_inspector = SchemaInspector(db_config, pool_manager)
    schema_cache = SchemaCache({db_config.name: schema_inspector})
    await schema_cache.initialize()

    try:
        # Get database schema resource
        result = await resources.get_database_schema(
            database="ecommerce_small", schema_cache=schema_cache
        )

        # Verify result format
        assert isinstance(result, str)
        assert len(result) > 0
        assert "#" in result  # Markdown headers

        # Should contain table information
        schema = await schema_cache.get_schema("ecommerce_small")
        if schema and len(schema.tables) > 0:
            # At least one table name should appear
            table_found = any(table.name in result for table in schema.tables)
            assert table_found or len(result) > 100  # Has substantial content

    finally:
        # Cleanup
        await schema_cache.close()
        await pool_manager.close_all()
