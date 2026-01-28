"""
Unit tests for database routing logic in MCP tools.

Tests the default database fallback mechanism when database parameter is not provided.
"""

from datetime import UTC
from unittest.mock import AsyncMock, MagicMock

import pytest

from postgres_mcp.models.query import GeneratedQuery, GenerationMethod


@pytest.fixture
def mock_context():
    """Create mock server context with config and generators."""
    ctx = MagicMock()

    # Mock config with default database
    ctx.config = MagicMock()
    ctx.config.default_database = "default_db"

    # Mock SQL generator
    ctx.sql_generator = AsyncMock()
    ctx.sql_generator.generate = AsyncMock(
        return_value=GeneratedQuery(
            sql="SELECT * FROM users LIMIT 1000",
            validated=True,
            explanation="Generated SQL for users query",
            assumptions=["Assuming 'users' table exists"],
            warnings=[],
            generation_method=GenerationMethod.AI_GENERATED,
        )
    )

    # Mock query executor
    ctx.query_executor = AsyncMock()

    # Mock schema cache
    ctx.schema_cache = MagicMock()

    return ctx


@pytest.mark.asyncio
async def test_generate_sql_with_explicit_database(mock_context):
    """Test generate_sql uses provided database parameter."""
    from postgres_mcp.mcp.tools import handle_generate_sql

    arguments = {
        "natural_language": "show all users",
        "database": "explicit_db",
    }

    await handle_generate_sql(arguments, mock_context)

    # Verify SQL generator was called with explicit database
    mock_context.sql_generator.generate.assert_called_once()
    call_kwargs = mock_context.sql_generator.generate.call_args.kwargs
    assert call_kwargs["database"] == "explicit_db"
    assert call_kwargs["natural_language"] == "show all users"


@pytest.mark.asyncio
async def test_generate_sql_with_default_database(mock_context):
    """Test generate_sql uses default database when not provided."""
    from postgres_mcp.mcp.tools import handle_generate_sql

    arguments = {
        "natural_language": "show all users",
        # database parameter omitted
    }

    await handle_generate_sql(arguments, mock_context)

    # Verify SQL generator was called with default database
    mock_context.sql_generator.generate.assert_called_once()
    call_kwargs = mock_context.sql_generator.generate.call_args.kwargs
    assert call_kwargs["database"] == "default_db"  # From mock_context.config.default_database
    assert call_kwargs["natural_language"] == "show all users"


@pytest.mark.asyncio
async def test_generate_sql_with_none_database(mock_context):
    """Test generate_sql uses default database when database is None."""
    from postgres_mcp.mcp.tools import handle_generate_sql

    arguments = {
        "natural_language": "show all users",
        "database": None,  # Explicitly None
    }

    await handle_generate_sql(arguments, mock_context)

    # Verify SQL generator was called with default database
    mock_context.sql_generator.generate.assert_called_once()
    call_kwargs = mock_context.sql_generator.generate.call_args.kwargs
    assert call_kwargs["database"] == "default_db"


@pytest.mark.asyncio
async def test_generate_sql_with_empty_database(mock_context):
    """Test generate_sql uses default database when database is empty string."""
    from postgres_mcp.mcp.tools import handle_generate_sql

    arguments = {
        "natural_language": "show all users",
        "database": "",  # Empty string
    }

    await handle_generate_sql(arguments, mock_context)

    # Verify SQL generator was called with default database
    mock_context.sql_generator.generate.assert_called_once()
    call_kwargs = mock_context.sql_generator.generate.call_args.kwargs
    assert call_kwargs["database"] == "default_db"


@pytest.mark.asyncio
async def test_execute_query_with_explicit_database(mock_context):
    """Test execute_query uses provided database parameter."""
    from postgres_mcp.mcp.tools import handle_execute_query
    from postgres_mcp.models.result import ColumnInfo, QueryResult

    # Mock query executor response
    mock_context.query_executor.execute = AsyncMock(
        return_value=QueryResult(
            sql="SELECT * FROM users LIMIT 1000",
            columns=[ColumnInfo(name="id", type="integer")],
            rows=[{"id": 1}],
            row_count=1,
            execution_time_ms=10.5,
            truncated=False,
        )
    )

    arguments = {
        "natural_language": "show all users",
        "database": "explicit_db",
        "limit": 100,
    }

    await handle_execute_query(arguments, mock_context)

    # Verify query executor was called with explicit database
    mock_context.query_executor.execute.assert_called_once()
    call_kwargs = mock_context.query_executor.execute.call_args.kwargs
    assert call_kwargs["database"] == "explicit_db"
    assert call_kwargs["natural_language"] == "show all users"
    assert call_kwargs["limit"] == 100


@pytest.mark.asyncio
async def test_execute_query_with_default_database(mock_context):
    """Test execute_query uses default database when not provided."""
    from postgres_mcp.mcp.tools import handle_execute_query
    from postgres_mcp.models.result import ColumnInfo, QueryResult

    # Mock query executor response
    mock_context.query_executor.execute = AsyncMock(
        return_value=QueryResult(
            sql="SELECT * FROM users LIMIT 1000",
            columns=[ColumnInfo(name="id", type="integer")],
            rows=[{"id": 1}],
            row_count=1,
            execution_time_ms=10.5,
            truncated=False,
        )
    )

    arguments = {
        "natural_language": "show all users",
        # database parameter omitted
        "limit": 100,
    }

    await handle_execute_query(arguments, mock_context)

    # Verify query executor was called with default database
    mock_context.query_executor.execute.assert_called_once()
    call_kwargs = mock_context.query_executor.execute.call_args.kwargs
    assert call_kwargs["database"] == "default_db"  # From mock_context.config.default_database
    assert call_kwargs["natural_language"] == "show all users"


@pytest.mark.asyncio
async def test_execute_query_with_none_database(mock_context):
    """Test execute_query uses default database when database is None."""
    from postgres_mcp.mcp.tools import handle_execute_query
    from postgres_mcp.models.result import ColumnInfo, QueryResult

    # Mock query executor response
    mock_context.query_executor.execute = AsyncMock(
        return_value=QueryResult(
            sql="SELECT * FROM users LIMIT 1000",
            columns=[ColumnInfo(name="id", type="integer")],
            rows=[{"id": 1}],
            row_count=1,
            execution_time_ms=10.5,
            truncated=False,
        )
    )

    arguments = {
        "natural_language": "show all users",
        "database": None,  # Explicitly None
    }

    await handle_execute_query(arguments, mock_context)

    # Verify query executor was called with default database
    mock_context.query_executor.execute.assert_called_once()
    call_kwargs = mock_context.query_executor.execute.call_args.kwargs
    assert call_kwargs["database"] == "default_db"


@pytest.mark.asyncio
async def test_execute_query_default_limit(mock_context):
    """Test execute_query uses default limit when not provided."""
    from postgres_mcp.mcp.tools import handle_execute_query
    from postgres_mcp.models.result import ColumnInfo, QueryResult

    # Mock query executor response
    mock_context.query_executor.execute = AsyncMock(
        return_value=QueryResult(
            sql="SELECT * FROM users LIMIT 1000",
            columns=[ColumnInfo(name="id", type="integer")],
            rows=[{"id": 1}],
            row_count=1,
            execution_time_ms=10.5,
            truncated=False,
        )
    )

    arguments = {
        "natural_language": "show all users",
        "database": "test_db",
        # limit parameter omitted
    }

    await handle_execute_query(arguments, mock_context)

    # Verify query executor was called with default limit (1000)
    mock_context.query_executor.execute.assert_called_once()
    call_kwargs = mock_context.query_executor.execute.call_args.kwargs
    assert call_kwargs["limit"] == 1000


@pytest.mark.asyncio
async def test_execute_query_enforces_max_limit(mock_context):
    """Test execute_query enforces maximum limit of 10000."""
    from postgres_mcp.mcp.tools import handle_execute_query
    from postgres_mcp.models.result import ColumnInfo, QueryResult

    # Mock query executor response
    mock_context.query_executor.execute = AsyncMock(
        return_value=QueryResult(
            sql="SELECT * FROM users LIMIT 10000",
            columns=[ColumnInfo(name="id", type="integer")],
            rows=[{"id": 1}],
            row_count=1,
            execution_time_ms=10.5,
            truncated=False,
        )
    )

    arguments = {
        "natural_language": "show all users",
        "database": "test_db",
        "limit": 50000,  # Exceeds maximum
    }

    await handle_execute_query(arguments, mock_context)

    # Verify query executor was called with enforced max limit (10000)
    mock_context.query_executor.execute.assert_called_once()
    call_kwargs = mock_context.query_executor.execute.call_args.kwargs
    assert call_kwargs["limit"] == 10000  # Capped at maximum


@pytest.mark.asyncio
async def test_list_databases_shows_default_marker(mock_context):
    """Test list_databases marks the default database."""
    from datetime import datetime

    from postgres_mcp.mcp.tools import handle_list_databases
    from postgres_mcp.models.schema import DatabaseSchema

    # Mock schema cache
    mock_context.schema_cache.list_databases = MagicMock(return_value=["default_db", "other_db"])
    mock_context.schema_cache.get_schema = AsyncMock(
        return_value=DatabaseSchema(
            database_name="test",
            tables={},
            last_updated=datetime.now(UTC),
        )
    )

    # Mock pool manager
    mock_context.pool_manager.get_pool = AsyncMock(return_value=MagicMock())

    result = await handle_list_databases(mock_context)

    # Verify response contains default marker
    assert len(result) == 1
    response_text = result[0].text
    assert "default_db **[DEFAULT]**" in response_text
    assert "other_db **[DEFAULT]**" not in response_text  # Only default_db should have marker
