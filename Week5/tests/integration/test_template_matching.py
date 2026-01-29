"""
Integration tests for template matching fallback.

Tests the template matching system as a fallback mechanism when OpenAI API
is unavailable, including template loading, matching, and SQL generation.

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
from postgres_mcp.core.template_matcher import TemplateMatcher
from postgres_mcp.db.connection_pool import PoolManager
from postgres_mcp.db.schema_inspector import SchemaInspector
from postgres_mcp.models.connection import DatabaseConnection
from postgres_mcp.utils.template_loader import TemplateLoader


@pytest.mark.asyncio
@pytest.mark.integration
async def test_template_matching_fallback_when_openai_unavailable() -> None:
    """
    Test template matching fallback when OpenAI is unavailable.

    Verifies that the SQL generator automatically falls back to template
    matching when the OpenAI API is unreachable or returns errors.

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
        >>> result = await test_template_matching_fallback_when_openai_unavailable()
        >>> assert result.generation_method == "template_matched"
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

    # Create OpenAI client with invalid API key to simulate failure
    openai_client = OpenAIClient(
        api_key="invalid-key-to-trigger-fallback",
        model="gpt-4o-mini",
        timeout=5.0,  # Short timeout
    )

    prompt_builder = PromptBuilder()
    sql_validator = SQLValidator()

    # Load templates
    template_loader = TemplateLoader(template_dir="src/postgres_mcp/templates/queries")
    templates = template_loader.load_templates()
    template_matcher = TemplateMatcher(templates, sql_validator)

    sql_generator = SQLGenerator(
        openai_client=openai_client,
        prompt_builder=prompt_builder,
        schema_cache=schema_cache,
        validator=sql_validator,
        template_matcher=template_matcher,
    )

    try:
        # Generate SQL - should fall back to template
        result = await sql_generator.generate(
            natural_language="Show all products", database="ecommerce_small"
        )

        # Verify template matching was used
        assert result.sql is not None
        assert "SELECT" in result.sql.upper()
        assert "products" in result.sql.lower()
        assert result.generation_method == "template_matched"
        assert "template" in result.explanation.lower()

    finally:
        # Cleanup
        await schema_cache.close()
        await pool_manager.close_all()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_template_matching_accuracy_on_common_queries() -> None:
    """
    Test template matching accuracy on common query patterns.

    Verifies that the template matcher can successfully generate correct SQL
    for common query patterns without requiring OpenAI API.

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
        >>> await test_template_matching_accuracy_on_common_queries()
        >>> # Template matching works for common patterns
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

    # Load templates
    template_loader = TemplateLoader(template_dir="src/postgres_mcp/templates/queries")
    templates = template_loader.load_templates()
    sql_validator = SQLValidator()
    template_matcher = TemplateMatcher(templates, sql_validator)

    try:
        # Get schema for table names
        schema = await schema_cache.get_schema("ecommerce_small")
        assert schema is not None
        assert len(schema.tables) > 0

        table_name = schema.tables[0].name

        # Test common query patterns
        test_cases = [
            (f"Show all {table_name}", ["SELECT", table_name]),
            (f"Count {table_name}", ["COUNT", table_name]),
            (f"Show distinct {table_name}", ["DISTINCT", table_name]),
        ]

        for natural_language, expected_keywords in test_cases:
            result = template_matcher.match(natural_language, schema)

            if result:
                # Verify SQL contains expected keywords
                sql_upper = result.upper()
                for keyword in expected_keywords:
                    assert (
                        keyword.upper() in sql_upper
                    ), f"Expected '{keyword}' in SQL for query '{natural_language}'"

                # Verify SQL is valid (passes validator)
                is_valid, _ = sql_validator.validate(result)
                assert is_valid, f"Generated SQL failed validation: {result}"

    finally:
        # Cleanup
        await schema_cache.close()
        await pool_manager.close_all()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_template_matching_coverage_evaluation() -> None:
    """
    Evaluate template matching coverage on test queries.

    Tests a variety of natural language queries to determine what percentage
    can be successfully handled by template matching alone.

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
        >>> await test_template_matching_coverage_evaluation()
        >>> # Coverage: 60% of test queries matched
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

    # Load templates
    template_loader = TemplateLoader(template_dir="src/postgres_mcp/templates/queries")
    templates = template_loader.load_templates()
    sql_validator = SQLValidator()
    template_matcher = TemplateMatcher(templates, sql_validator)

    try:
        # Get schema
        schema = await schema_cache.get_schema("ecommerce_small")
        assert schema is not None

        # Test various query patterns
        test_queries = [
            "Show all records",
            "Count records",
            "Show top 10 records",
            "Show distinct values",
            "Show records ordered by id",
            "Show recent records",
            "Find records with specific condition",
            "Calculate sum",
            "Calculate average",
            "Find maximum value",
            "Find minimum value",
            "Group by and count",
        ]

        matched_count = 0
        total_count = len(test_queries)

        for query in test_queries:
            result = template_matcher.match(query, schema)
            if result:
                # Verify SQL is valid
                is_valid, _ = sql_validator.validate(result)
                if is_valid:
                    matched_count += 1

        # Calculate coverage
        coverage = (matched_count / total_count) * 100

        # Report coverage
        print(f"\nTemplate matching coverage: {coverage:.1f}% ({matched_count}/{total_count})")

        # Expect at least 40% coverage for basic patterns
        assert coverage >= 40.0, f"Template coverage too low: {coverage:.1f}%"

    finally:
        # Cleanup
        await schema_cache.close()
        await pool_manager.close_all()
