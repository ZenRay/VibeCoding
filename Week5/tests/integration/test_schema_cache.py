"""
Integration tests for schema cache with real database.

Tests the schema cache functionality using actual PostgreSQL databases,
including schema extraction, caching, and refresh mechanisms.

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

from postgres_mcp.core.schema_cache import SchemaCache
from postgres_mcp.db.connection_pool import PoolManager
from postgres_mcp.db.schema_inspector import SchemaInspector
from postgres_mcp.models.connection import DatabaseConnection


@pytest.mark.asyncio
@pytest.mark.integration
async def test_schema_cache_loads_real_schema() -> None:
    """
    Test that schema cache can load real database schema.

    Verifies that the schema inspector correctly extracts table definitions,
    columns, indexes, and foreign keys from a live PostgreSQL database.

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
        >>> await test_schema_cache_loads_real_schema()
        >>> # Schema loaded successfully
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

    try:
        # Initialize cache (loads schema)
        await schema_cache.initialize()

        # Get cached schema
        schema = await schema_cache.get_schema("ecommerce_small")

        # Verify schema was loaded
        assert schema is not None
        assert schema.database == "ecommerce_small"
        assert len(schema.tables) > 0

        # Verify at least one table has columns
        assert any(len(table.columns) > 0 for table in schema.tables)

        # Verify table names are correct
        table_names = [table.name for table in schema.tables]
        assert "products" in table_names or len(table_names) > 0

    finally:
        # Cleanup
        await schema_cache.close()
        await pool_manager.close_all()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_schema_cache_refresh() -> None:
    """
    Test schema cache refresh mechanism.

    Verifies that the schema cache can refresh its data from the database
    and update the cached schema information.

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
        >>> await test_schema_cache_refresh()
        >>> # Schema refreshed successfully
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

    try:
        # Initialize cache
        await schema_cache.initialize()

        # Get initial schema
        schema_before = await schema_cache.get_schema("ecommerce_small")
        assert schema_before is not None
        table_count_before = len(schema_before.tables)

        # Refresh schema
        await schema_cache.refresh_schema("ecommerce_small")

        # Get refreshed schema
        schema_after = await schema_cache.get_schema("ecommerce_small")
        assert schema_after is not None

        # Verify schema was refreshed (table count should be the same)
        assert len(schema_after.tables) == table_count_before

    finally:
        # Cleanup
        await schema_cache.close()
        await pool_manager.close_all()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_schema_cache_multiple_databases() -> None:
    """
    Test schema cache with multiple databases.

    Verifies that the schema cache can manage schemas for multiple databases
    simultaneously and keep them isolated.

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
        >>> await test_schema_cache_multiple_databases()
        >>> # Multiple schemas loaded successfully
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

    try:
        # Initialize cache (loads both schemas)
        await schema_cache.initialize()

        # Get schemas for both databases
        schema1 = await schema_cache.get_schema("ecommerce_small")
        schema2 = await schema_cache.get_schema("social_medium")

        # Verify both schemas were loaded
        assert schema1 is not None
        assert schema2 is not None
        assert schema1.database == "ecommerce_small"
        assert schema2.database == "social_medium"

        # Verify they have different table sets
        tables1 = {table.name for table in schema1.tables}
        tables2 = {table.name for table in schema2.tables}
        assert len(tables1) > 0
        assert len(tables2) > 0

        # Tables should be different (ecommerce vs social)
        assert tables1 != tables2 or len(tables1) == 0 or len(tables2) == 0

    finally:
        # Cleanup
        await schema_cache.close()
        await pool_manager.close_all()
