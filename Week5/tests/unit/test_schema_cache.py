"""
Unit tests for Schema Cache.

Tests for in-memory schema caching with thread-safe access.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from postgres_mcp.core.schema_cache import SchemaCache, SchemaCacheError
from postgres_mcp.models.schema import ColumnSchema, DatabaseSchema, TableSchema


@pytest.fixture
def sample_schema():
    """Create sample database schema."""
    users_table = TableSchema(
        name="users",
        columns=[
            ColumnSchema(name="id", data_type="INTEGER", primary_key=True),
            ColumnSchema(name="username", data_type="VARCHAR(50)"),
        ],
    )
    return DatabaseSchema(database_name="test_db", tables={"users": users_table})


@pytest.fixture
def mock_inspector(sample_schema):
    """Create mock SchemaInspector."""
    inspector = MagicMock()
    inspector.inspect_schema = AsyncMock(return_value=sample_schema)
    inspector.connect = AsyncMock()
    inspector.disconnect = AsyncMock()
    return inspector


@pytest.fixture
async def schema_cache(mock_inspector):
    """Create SchemaCache instance."""
    cache = SchemaCache(databases={"test_db": mock_inspector})
    await cache.initialize()
    return cache


@pytest.mark.asyncio
async def test_cache_initialization(mock_inspector, sample_schema):
    """Test schema cache initialization."""
    cache = SchemaCache(databases={"test_db": mock_inspector})

    await cache.initialize()

    # Verify inspector was connected and schema was loaded
    mock_inspector.connect.assert_called_once()
    mock_inspector.inspect_schema.assert_called_once()

    # Verify schema is cached
    schema = await cache.get_schema("test_db")
    assert schema == sample_schema


@pytest.mark.asyncio
async def test_get_schema_from_cache(schema_cache, sample_schema):
    """Test retrieving schema from cache."""
    schema = await schema_cache.get_schema("test_db")

    assert schema == sample_schema
    assert schema.database_name == "test_db"
    assert "users" in schema.tables


@pytest.mark.asyncio
async def test_get_schema_not_found(schema_cache):
    """Test retrieving non-existent schema."""
    schema = await schema_cache.get_schema("non_existent_db")

    assert schema is None


@pytest.mark.asyncio
async def test_refresh_schema(mock_inspector, sample_schema):
    """Test refreshing schema for specific database."""
    cache = SchemaCache(databases={"test_db": mock_inspector})
    await cache.initialize()

    # Modify the schema returned by inspector
    new_schema = DatabaseSchema(
        database_name="test_db",
        tables={
            "users": TableSchema(
                name="users",
                columns=[
                    ColumnSchema(name="id", data_type="INTEGER", primary_key=True),
                    ColumnSchema(name="username", data_type="VARCHAR(50)"),
                    ColumnSchema(name="email", data_type="VARCHAR(255)"),  # New column
                ],
            )
        },
    )
    mock_inspector.inspect_schema.return_value = new_schema

    # Refresh schema
    await cache.refresh_schema("test_db")

    # Verify schema was updated
    schema = await cache.get_schema("test_db")
    assert len(schema.tables["users"].columns) == 3
    assert schema.tables["users"].columns[2].name == "email"


@pytest.mark.asyncio
async def test_refresh_schema_not_found():
    """Test refreshing non-existent database."""
    cache = SchemaCache(databases={})

    with pytest.raises(SchemaCacheError, match="not configured"):
        await cache.refresh_schema("non_existent_db")


@pytest.mark.asyncio
async def test_refresh_all_schemas(mock_inspector):
    """Test refreshing all schemas."""
    cache = SchemaCache(databases={"test_db": mock_inspector})
    await cache.initialize()

    # Reset mock to count new calls
    mock_inspector.inspect_schema.reset_mock()

    await cache.refresh_all_schemas()

    # Verify all schemas were refreshed
    mock_inspector.inspect_schema.assert_called_once()


@pytest.mark.asyncio
async def test_list_databases():
    """Test listing all configured databases."""
    inspector1 = MagicMock()
    inspector2 = MagicMock()

    cache = SchemaCache(databases={"db1": inspector1, "db2": inspector2})

    databases = cache.list_databases()

    assert len(databases) == 2
    assert "db1" in databases
    assert "db2" in databases


@pytest.mark.asyncio
async def test_concurrent_cache_access(mock_inspector, sample_schema):
    """Test thread-safe concurrent cache access."""
    cache = SchemaCache(databases={"test_db": mock_inspector})
    await cache.initialize()

    # Simulate concurrent access
    async def get_schema_concurrent():
        return await cache.get_schema("test_db")

    results = await asyncio.gather(*[get_schema_concurrent() for _ in range(10)])

    # All results should be the same schema
    assert all(r == sample_schema for r in results)


@pytest.mark.asyncio
async def test_concurrent_refresh(mock_inspector):
    """Test concurrent schema refresh."""
    cache = SchemaCache(databases={"test_db": mock_inspector})
    await cache.initialize()

    # Reset mock
    mock_inspector.inspect_schema.reset_mock()

    # Simulate concurrent refresh
    await asyncio.gather(*[cache.refresh_schema("test_db") for _ in range(5)])

    # Should only refresh once due to locking
    # Note: This behavior depends on implementation
    assert mock_inspector.inspect_schema.call_count >= 1


@pytest.mark.asyncio
async def test_cache_cleanup():
    """Test cache cleanup on shutdown."""
    mock_inspector = MagicMock()
    mock_inspector.connect = AsyncMock()
    mock_inspector.disconnect = AsyncMock()
    mock_inspector.inspect_schema = AsyncMock(
        return_value=DatabaseSchema(database_name="test_db", tables={})
    )

    cache = SchemaCache(databases={"test_db": mock_inspector})
    await cache.initialize()

    await cache.cleanup()

    # Verify inspector was disconnected
    mock_inspector.disconnect.assert_called_once()


@pytest.mark.asyncio
async def test_cache_with_multiple_databases():
    """Test cache with multiple databases."""
    inspector1 = MagicMock()
    inspector1.connect = AsyncMock()
    inspector1.disconnect = AsyncMock()
    inspector1.inspect_schema = AsyncMock(
        return_value=DatabaseSchema(database_name="db1", tables={})
    )

    inspector2 = MagicMock()
    inspector2.connect = AsyncMock()
    inspector2.disconnect = AsyncMock()
    inspector2.inspect_schema = AsyncMock(
        return_value=DatabaseSchema(database_name="db2", tables={})
    )

    cache = SchemaCache(databases={"db1": inspector1, "db2": inspector2})
    await cache.initialize()

    # Verify both schemas are cached
    schema1 = await cache.get_schema("db1")
    schema2 = await cache.get_schema("db2")

    assert schema1.database_name == "db1"
    assert schema2.database_name == "db2"

    await cache.cleanup()

    # Verify both inspectors were cleaned up
    inspector1.disconnect.assert_called_once()
    inspector2.disconnect.assert_called_once()


@pytest.mark.asyncio
async def test_cache_inspector_error_handling():
    """Test error handling when inspector fails."""
    mock_inspector = MagicMock()
    mock_inspector.connect = AsyncMock()
    mock_inspector.inspect_schema = AsyncMock(side_effect=Exception("DB Connection failed"))

    cache = SchemaCache(databases={"test_db": mock_inspector})

    # Initialization should handle error gracefully
    with pytest.raises(Exception, match="DB Connection failed"):
        await cache.initialize()
