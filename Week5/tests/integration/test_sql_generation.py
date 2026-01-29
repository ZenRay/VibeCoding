"""
Integration tests for SQL generation flow.

Tests the complete SQL generation pipeline from natural language to validated SQL,
including OpenAI client, prompt builder, schema cache, and SQL validator integration.

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
from postgres_mcp.core.schema_cache import SchemaCache
from postgres_mcp.core.sql_generator import SQLGenerator
from postgres_mcp.core.sql_validator import SQLValidator
from postgres_mcp.db.connection_pool import PoolManager
from postgres_mcp.db.schema_inspector import SchemaInspector
from postgres_mcp.models.connection import DatabaseConnection


@pytest.mark.asyncio
@pytest.mark.integration
async def test_sql_generation_basic_query() -> None:
    """
    Test basic SQL generation with real components.

    Verifies that a simple natural language query can be converted to valid SQL
    using actual OpenAI API, real schema cache, and production validator.

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
        >>> result = await test_sql_generation_basic_query()
        >>> assert "SELECT" in result.sql
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

    try:
        # Generate SQL for basic query
        result = await sql_generator.generate(
            natural_language="Show all products", database="ecommerce_small"
        )

        # Verify result
        assert result.sql is not None
        assert "SELECT" in result.sql.upper()
        assert "products" in result.sql.lower()
        assert result.validated is True
        assert result.generation_method in ["ai_generated", "template_matched"]
        assert len(result.explanation) > 0

    finally:
        # Cleanup
        await schema_cache.close()
        await pool_manager.close_all()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_sql_generation_with_conditions() -> None:
    """
    Test SQL generation with WHERE conditions.

    Verifies that natural language queries with filtering conditions are
    correctly translated to SQL with appropriate WHERE clauses.

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
        >>> result = await test_sql_generation_with_conditions()
        >>> assert "WHERE" in result.sql
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

    try:
        # Generate SQL with conditions
        result = await sql_generator.generate(
            natural_language="Show products with price greater than 100",
            database="ecommerce_small",
        )

        # Verify result
        assert result.sql is not None
        assert "SELECT" in result.sql.upper()
        assert "products" in result.sql.lower()
        assert "WHERE" in result.sql.upper() or "price" in result.sql.lower()
        assert result.validated is True

    finally:
        # Cleanup
        await schema_cache.close()
        await pool_manager.close_all()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_sql_generation_security_validation() -> None:
    """
    Test that dangerous SQL is rejected by validator.

    Verifies that the SQL validator correctly blocks INSERT, UPDATE, DELETE,
    and other dangerous operations even if the AI generates them.

    Args:
    ----------
        None

    Returns:
    ----------
        None

    Raises:
    ----------
        SQLGenerationError: Expected when dangerous SQL is generated.

    Example:
    ----------
        >>> with pytest.raises(SQLGenerationError):
        ...     await test_sql_generation_security_validation()
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

    try:
        # Try to generate dangerous SQL - should be rejected
        from postgres_mcp.core.sql_generator import SQLGenerationError

        # This should fail validation after retry attempts
        with pytest.raises(SQLGenerationError) as exc_info:
            await sql_generator.generate(
                natural_language="Delete all products from the database",
                database="ecommerce_small",
            )

        # Verify error message mentions validation
        assert (
            "validation" in str(exc_info.value).lower() or "failed" in str(exc_info.value).lower()
        )

    finally:
        # Cleanup
        await schema_cache.close()
        await pool_manager.close_all()
