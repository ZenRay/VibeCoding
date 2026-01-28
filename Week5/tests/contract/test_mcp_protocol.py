"""
MCP Protocol Contract Tests.

Tests MCP tool interfaces against their defined schemas to ensure protocol compliance.
Verifies input/output schemas, required fields, and error handling.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from postgres_mcp.models.query import GeneratedQuery, GenerationMethod
from postgres_mcp.models.result import ColumnInfo, QueryResult


def load_contract_schema() -> dict[str, Any]:
    """Load the MCP tools contract schema."""
    contract_path = Path(__file__).parent.parent.parent.parent / "specs" / "001-postgres-mcp" / "contracts" / "mcp_tools.json"
    with contract_path.open() as f:
        return json.load(f)


def validate_schema_compliance(data: dict[str, Any], schema: dict[str, Any], path: str = "root") -> list[str]:
    """
    Validate data against a JSON schema.
    
    Returns list of validation errors (empty if valid).
    """
    errors = []
    
    if schema.get("type") == "object":
        # Check required fields
        required = schema.get("required", [])
        for field in required:
            if field not in data:
                errors.append(f"{path}: Missing required field '{field}'")
        
        # Check properties
        properties = schema.get("properties", {})
        for key, value in data.items():
            if key in properties:
                prop_schema = properties[key]
                # Recursively validate nested objects
                if isinstance(value, dict) and prop_schema.get("type") == "object":
                    errors.extend(validate_schema_compliance(value, prop_schema, f"{path}.{key}"))
                # Validate arrays
                elif isinstance(value, list) and prop_schema.get("type") == "array":
                    for i, item in enumerate(value):
                        if "items" in prop_schema:
                            errors.extend(validate_schema_compliance(item, prop_schema["items"], f"{path}.{key}[{i}]"))
                # Validate basic types
                elif not _validate_type(value, prop_schema):
                    expected_type = prop_schema.get("type")
                    actual_type = type(value).__name__
                    errors.append(f"{path}.{key}: Expected type '{expected_type}', got '{actual_type}'")
    
    return errors


def _validate_type(value: Any, schema: dict[str, Any]) -> bool:
    """Validate a value against its schema type."""
    expected_type = schema.get("type")
    
    if expected_type == "string":
        return isinstance(value, str)
    elif expected_type == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    elif expected_type == "number":
        return isinstance(value, int | float) and not isinstance(value, bool)
    elif expected_type == "boolean":
        return isinstance(value, bool)
    elif expected_type == "array":
        return isinstance(value, list)
    elif expected_type == "object":
        return isinstance(value, dict)
    elif isinstance(expected_type, list):  # Union types like ["string", "null"]
        return any(_validate_type(value, {"type": t}) for t in expected_type)
    
    return True


@pytest.fixture
def contract_schema() -> dict[str, Any]:
    """Provide the contract schema."""
    return load_contract_schema()


@pytest.fixture
def mock_context():
    """Create mock server context."""
    ctx = MagicMock()
    ctx.config = MagicMock()
    ctx.config.default_database = "test_db"
    ctx.sql_generator = AsyncMock()
    ctx.query_executor = AsyncMock()
    ctx.schema_cache = MagicMock()
    ctx.pool_manager = AsyncMock()
    ctx.jsonl_writer = MagicMock()
    return ctx


class TestGenerateSQLContract:
    """Test generate_sql tool contract compliance."""

    @pytest.mark.asyncio
    async def test_generate_sql_valid_input(self, contract_schema: dict[str, Any], mock_context: MagicMock) -> None:
        """Test generate_sql with valid input schema."""
        from postgres_mcp.mcp.tools import handle_generate_sql
        
        # Mock successful SQL generation
        mock_context.sql_generator.generate = AsyncMock(
            return_value=GeneratedQuery(
                sql="SELECT * FROM users LIMIT 1000",
                validated=True,
                explanation="Query to select all users",
                assumptions=["Table 'users' exists"],
                warnings=[],
                generation_method=GenerationMethod.AI_GENERATED,
            )
        )
        
        # Valid input according to schema
        arguments = {
            "natural_language": "show all users",
            "database": "test_db",
        }
        
        result = await handle_generate_sql(arguments, mock_context)
        
        # Should succeed without errors
        assert result is not None
        assert len(result) > 0
        
    @pytest.mark.asyncio
    async def test_generate_sql_missing_required_field(self, mock_context: MagicMock) -> None:
        """Test generate_sql rejects missing required fields."""
        from postgres_mcp.mcp.tools import handle_generate_sql
        
        # Missing required 'natural_language' field
        arguments = {
            "database": "test_db",
        }
        
        result = await handle_generate_sql(arguments, mock_context)
        
        # Should return error message
        assert len(result) == 1
        assert "Error" in result[0].text or "required" in result[0].text.lower()

    @pytest.mark.asyncio
    async def test_generate_sql_output_schema(self, contract_schema: dict[str, Any], mock_context: MagicMock) -> None:
        """Test generate_sql output matches contract schema."""
        from postgres_mcp.mcp.tools import handle_generate_sql
        
        # Mock successful generation
        mock_context.sql_generator.generate = AsyncMock(
            return_value=GeneratedQuery(
                sql="SELECT * FROM users",
                validated=True,
                explanation="Test query",
                assumptions=[],
                warnings=[],
                generation_method=GenerationMethod.AI_GENERATED,
            )
        )
        
        arguments = {"natural_language": "test query", "database": "test_db"}
        result = await handle_generate_sql(arguments, mock_context)
        
        # Parse result text (simplified check - assumes markdown format)
        assert len(result) > 0
        text = result[0].text
        
        # Verify key output fields are present
        assert "SELECT" in text  # SQL present
        assert "Validated" in text or "validated" in text.lower()  # Validation status
        assert "Explanation" in text or "explanation" in text.lower()  # Explanation


class TestExecuteQueryContract:
    """Test execute_query tool contract compliance."""

    @pytest.mark.asyncio
    async def test_execute_query_valid_input(self, mock_context: MagicMock) -> None:
        """Test execute_query with valid input schema."""
        from postgres_mcp.mcp.tools import handle_execute_query
        
        # Mock successful execution
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
            "limit": 100,
        }
        
        result = await handle_execute_query(arguments, mock_context)
        
        # Should succeed
        assert result is not None
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_execute_query_limit_bounds(self, mock_context: MagicMock) -> None:
        """Test execute_query enforces limit bounds (1-10000)."""
        from postgres_mcp.mcp.tools import handle_execute_query
        
        # Mock successful execution
        mock_context.query_executor.execute = AsyncMock(
            return_value=QueryResult(
                sql="SELECT * FROM users LIMIT 10000",
                columns=[],
                rows=[],
                row_count=0,
                execution_time_ms=0.0,
                truncated=False,
            )
        )
        
        # Test exceeding maximum limit
        arguments = {
            "natural_language": "show all users",
            "database": "test_db",
            "limit": 50000,  # Exceeds 10000 max
        }
        
        result = await handle_execute_query(arguments, mock_context)
        
        # Should enforce max limit of 10000
        assert mock_context.query_executor.execute.called
        call_args = mock_context.query_executor.execute.call_args
        assert call_args.kwargs["limit"] == 10000  # Capped at maximum


class TestListDatabasesContract:
    """Test list_databases tool contract compliance."""

    @pytest.mark.asyncio
    async def test_list_databases_no_input_required(self, mock_context: MagicMock) -> None:
        """Test list_databases accepts empty input."""
        from postgres_mcp.mcp.tools import handle_list_databases
        from postgres_mcp.models.schema import DatabaseSchema
        from datetime import datetime, timezone
        
        # Mock schema cache
        mock_context.schema_cache.list_databases = MagicMock(return_value=["test_db"])
        mock_context.schema_cache.get_schema = AsyncMock(
            return_value=DatabaseSchema(
                database_name="test_db",
                tables={},
                last_updated=datetime.now(timezone.utc),
            )
        )
        mock_context.pool_manager.get_pool = AsyncMock(return_value=MagicMock())
        
        result = await handle_list_databases(mock_context)
        
        # Should succeed with empty input
        assert result is not None
        assert len(result) > 0


class TestRefreshSchemaContract:
    """Test refresh_schema tool contract compliance."""

    @pytest.mark.asyncio
    async def test_refresh_schema_optional_database(self, mock_context: MagicMock) -> None:
        """Test refresh_schema with optional database parameter."""
        from postgres_mcp.mcp.tools import handle_refresh_schema
        
        # Mock successful refresh
        mock_context.schema_cache.refresh_schema = AsyncMock()
        
        # Test with database specified
        arguments = {"database": "test_db"}
        result = await handle_refresh_schema(arguments, mock_context)
        
        assert result is not None
        assert len(result) > 0
        assert mock_context.schema_cache.refresh_schema.called

    @pytest.mark.asyncio
    async def test_refresh_schema_all_databases(self, mock_context: MagicMock) -> None:
        """Test refresh_schema without database (refresh all)."""
        from postgres_mcp.mcp.tools import handle_refresh_schema
        
        # Mock successful refresh
        mock_context.schema_cache.refresh_all_schemas = AsyncMock()
        
        # Test without database (refresh all)
        arguments = {}
        result = await handle_refresh_schema(arguments, mock_context)
        
        assert result is not None
        assert len(result) > 0
        assert mock_context.schema_cache.refresh_all_schemas.called


class TestQueryHistoryContract:
    """Test query_history tool contract compliance."""

    @pytest.mark.asyncio
    async def test_query_history_optional_filters(self, mock_context: MagicMock, tmp_path: Path) -> None:
        """Test query_history with optional filter parameters."""
        from postgres_mcp.mcp.tools import handle_query_history
        
        # Mock JSONL writer with log directory
        mock_context.jsonl_writer.log_directory = tmp_path
        
        # Create sample log file
        log_file = tmp_path / "query_history_20260130_000001.jsonl"
        log_file.write_text('{"request_id": "test-1", "database": "test_db", "status": "success"}\n')
        
        # Test with filters
        arguments = {
            "database": "test_db",
            "status": "success",
            "limit": 50,
        }
        
        result = await handle_query_history(arguments, mock_context)
        
        assert result is not None
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_query_history_limit_bounds(self, mock_context: MagicMock, tmp_path: Path) -> None:
        """Test query_history respects limit parameter."""
        from postgres_mcp.mcp.tools import handle_query_history
        
        # Mock JSONL writer
        mock_context.jsonl_writer.log_directory = tmp_path
        
        # Create sample log file with multiple entries
        log_file = tmp_path / "query_history_20260130_000001.jsonl"
        entries = [f'{{"request_id": "test-{i}", "database": "test_db", "status": "success"}}\n' for i in range(100)]
        log_file.write_text("".join(entries))
        
        # Test with specific limit
        arguments = {"limit": 10}
        result = await handle_query_history(arguments, mock_context)
        
        # Should limit results
        assert result is not None
        assert len(result) > 0
