"""
Unit tests for Schema Inspector.

Tests for PostgreSQL schema inspection using asyncpg.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from postgres_mcp.db.schema_inspector import SchemaInspector
from postgres_mcp.models.schema import (
    DatabaseSchema,
    TableSchema,
    ColumnSchema,
    IndexSchema,
    ForeignKeySchema,
)


@pytest.fixture
async def schema_inspector():
    """Create SchemaInspector instance with mock connection pool."""
    inspector = SchemaInspector(
        host="localhost",
        port=5432,
        user="test_user",
        password="test_pass",
        database="test_db",
    )
    # Mock the connection pool with proper async context manager
    mock_pool = AsyncMock()
    mock_acquire = AsyncMock()
    mock_acquire.__aenter__ = AsyncMock()
    mock_acquire.__aexit__ = AsyncMock()
    mock_pool.acquire.return_value = mock_acquire
    inspector._pool = mock_pool
    return inspector


@pytest.mark.asyncio
async def test_inspector_initialization():
    """Test SchemaInspector initialization."""
    inspector = SchemaInspector(
        host="localhost",
        port=5432,
        user="testuser",
        password="testpass",
        database="testdb",
    )
    assert inspector._host == "localhost"
    assert inspector._port == 5432
    assert inspector._database == "testdb"
    assert inspector._pool is None


@pytest.mark.asyncio
async def test_connect_creates_pool(schema_inspector):
    """Test connection pool creation."""
    mock_pool = AsyncMock()
    
    with patch("asyncpg.create_pool", new_callable=AsyncMock) as mock_create_pool:
        mock_create_pool.return_value = mock_pool
        
        await schema_inspector.connect()
        
        mock_create_pool.assert_called_once()
        assert schema_inspector._pool == mock_pool


@pytest.mark.asyncio
async def test_disconnect_closes_pool(schema_inspector):
    """Test connection pool closure."""
    mock_pool = AsyncMock()
    schema_inspector._pool = mock_pool
    
    await schema_inspector.disconnect()
    
    mock_pool.close.assert_called_once()
    mock_pool.wait_closed.assert_called_once()
    assert schema_inspector._pool is None


@pytest.mark.asyncio
async def test_inspect_schema_success(schema_inspector):
    """Test successful schema inspection."""
    # Mock table data
    mock_tables = [
        {"table_name": "users", "table_type": "BASE TABLE"},
        {"table_name": "orders", "table_type": "BASE TABLE"},
    ]
    
    # Mock column data for users table
    mock_users_columns = [
        {
            "column_name": "id",
            "data_type": "integer",
            "is_nullable": "NO",
            "column_default": "nextval('users_id_seq'::regclass)",
        },
        {
            "column_name": "username",
            "data_type": "character varying",
            "is_nullable": "NO",
            "column_default": None,
        },
        {
            "column_name": "email",
            "data_type": "character varying",
            "is_nullable": "YES",
            "column_default": None,
        },
    ]
    
    # Mock column data for orders table
    mock_orders_columns = [
        {
            "column_name": "id",
            "data_type": "integer",
            "is_nullable": "NO",
            "column_default": "nextval('orders_id_seq'::regclass)",
        },
        {
            "column_name": "user_id",
            "data_type": "integer",
            "is_nullable": "NO",
            "column_default": None,
        },
    ]
    
    # Mock primary key data
    mock_users_pk = [{"column_name": "id"}]
    mock_orders_pk = [{"column_name": "id"}]
    
    # Mock index data
    mock_users_indexes = [
        {"index_name": "users_pkey", "column_name": "id", "is_unique": True}
    ]
    mock_orders_indexes = [
        {"index_name": "orders_pkey", "column_name": "id", "is_unique": True},
        {"index_name": "idx_orders_user_id", "column_name": "user_id", "is_unique": False},
    ]
    
    # Mock foreign key data
    mock_orders_fks = [
        {
            "constraint_name": "fk_orders_user",
            "column_name": "user_id",
            "foreign_table_name": "users",
            "foreign_column_name": "id",
        }
    ]
    
    # Setup mock connection
    mock_conn = AsyncMock()
    mock_conn.fetch = AsyncMock()
    
    # Configure mock responses
    async def mock_fetch(*args, **kwargs):
        query = args[0] if args else kwargs.get("query", "")
        
        if "information_schema.tables" in query:
            return mock_tables
        elif "information_schema.columns" in query and "users" in query:
            return mock_users_columns
        elif "information_schema.columns" in query and "orders" in query:
            return mock_orders_columns
        elif "pg_constraint" in query and "users" in query:
            return mock_users_pk
        elif "pg_constraint" in query and "orders" in query:
            return mock_orders_pk
        elif "pg_indexes" in query and "users" in query:
            return mock_users_indexes
        elif "pg_indexes" in query and "orders" in query:
            return mock_orders_indexes
        elif "information_schema.key_column_usage" in query and "orders" in query:
            return mock_orders_fks
        elif "information_schema.key_column_usage" in query and "users" in query:
            return []
        return []
    
    mock_conn.fetch.side_effect = mock_fetch
    schema_inspector._pool.acquire.return_value.__aenter__.return_value = mock_conn
    
    # Execute inspection
    schema = await schema_inspector.inspect_schema()
    
    # Verify results
    assert isinstance(schema, DatabaseSchema)
    assert schema.database_name == "test_db"
    assert len(schema.tables) == 2
    assert "users" in schema.tables
    assert "orders" in schema.tables
    
    # Verify users table
    users_table = schema.tables["users"]
    assert users_table.name == "users"
    assert len(users_table.columns) == 3
    assert users_table.columns[0].name == "id"
    assert users_table.columns[0].primary_key is True
    assert users_table.columns[1].name == "username"
    assert users_table.columns[1].nullable is False
    
    # Verify orders table
    orders_table = schema.tables["orders"]
    assert orders_table.name == "orders"
    assert len(orders_table.columns) == 2
    assert len(orders_table.foreign_keys) == 1
    assert orders_table.foreign_keys[0].foreign_table == "users"


@pytest.mark.asyncio
async def test_inspect_schema_empty_database(schema_inspector):
    """Test schema inspection on empty database."""
    mock_conn = AsyncMock()
    mock_conn.fetch = AsyncMock(return_value=[])
    schema_inspector._pool.acquire.return_value.__aenter__.return_value = mock_conn
    
    schema = await schema_inspector.inspect_schema()
    
    assert isinstance(schema, DatabaseSchema)
    assert schema.database_name == "test_db"
    assert len(schema.tables) == 0


@pytest.mark.asyncio
async def test_inspect_schema_without_connection():
    """Test schema inspection without connection raises error."""
    inspector = SchemaInspector(
        host="localhost",
        port=5432,
        user="test",
        password="test",
        database="test",
    )
    
    with pytest.raises(RuntimeError, match="not connected"):
        await inspector.inspect_schema()


@pytest.mark.asyncio
async def test_inspect_schema_connection_error(schema_inspector):
    """Test schema inspection with connection error."""
    schema_inspector._pool.acquire.side_effect = Exception("Connection failed")
    
    with pytest.raises(Exception, match="Connection failed"):
        await schema_inspector.inspect_schema()


@pytest.mark.asyncio
async def test_get_table_columns(schema_inspector):
    """Test fetching table columns."""
    mock_columns = [
        {
            "column_name": "id",
            "data_type": "integer",
            "is_nullable": "NO",
            "column_default": "nextval('test_id_seq'::regclass)",
        },
        {
            "column_name": "name",
            "data_type": "text",
            "is_nullable": "YES",
            "column_default": None,
        },
    ]
    
    mock_conn = AsyncMock()
    mock_conn.fetch = AsyncMock(return_value=mock_columns)
    schema_inspector._pool.acquire.return_value.__aenter__.return_value = mock_conn
    
    columns = await schema_inspector._get_table_columns("test_table")
    
    assert len(columns) == 2
    assert columns[0].name == "id"
    assert columns[0].data_type == "integer"
    assert columns[0].nullable is False
    assert columns[1].name == "name"
    assert columns[1].nullable is True


@pytest.mark.asyncio
async def test_get_primary_keys(schema_inspector):
    """Test fetching primary keys."""
    mock_pk = [{"column_name": "id"}, {"column_name": "tenant_id"}]
    
    mock_conn = AsyncMock()
    mock_conn.fetch = AsyncMock(return_value=mock_pk)
    schema_inspector._pool.acquire.return_value.__aenter__.return_value = mock_conn
    
    pk_columns = await schema_inspector._get_primary_keys("test_table")
    
    assert pk_columns == {"id", "tenant_id"}


@pytest.mark.asyncio
async def test_get_indexes(schema_inspector):
    """Test fetching table indexes."""
    mock_indexes = [
        {"index_name": "idx_name", "column_name": "name", "is_unique": True},
        {"index_name": "idx_email", "column_name": "email", "is_unique": False},
    ]
    
    mock_conn = AsyncMock()
    mock_conn.fetch = AsyncMock(return_value=mock_indexes)
    schema_inspector._pool.acquire.return_value.__aenter__.return_value = mock_conn
    
    indexes = await schema_inspector._get_indexes("test_table")
    
    assert len(indexes) == 2
    assert indexes[0].name == "idx_name"
    assert indexes[0].unique is True
    assert indexes[1].name == "idx_email"
    assert indexes[1].unique is False


@pytest.mark.asyncio
async def test_get_foreign_keys(schema_inspector):
    """Test fetching foreign keys."""
    mock_fks = [
        {
            "constraint_name": "fk_user",
            "column_name": "user_id",
            "foreign_table_name": "users",
            "foreign_column_name": "id",
        }
    ]
    
    mock_conn = AsyncMock()
    mock_conn.fetch = AsyncMock(return_value=mock_fks)
    schema_inspector._pool.acquire.return_value.__aenter__.return_value = mock_conn
    
    fks = await schema_inspector._get_foreign_keys("test_table")
    
    assert len(fks) == 1
    assert fks[0].name == "fk_user"
    assert fks[0].column == "user_id"
    assert fks[0].foreign_table == "users"
    assert fks[0].foreign_column == "id"
