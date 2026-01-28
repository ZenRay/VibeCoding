"""SQL Generator tests.

Tests for SQL generator core functionality and workflow.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from postgres_mcp.core.sql_generator import (
    GenerationMethod,
    SQLGenerationError,
    SQLGenerator,
)
from postgres_mcp.models.query import GeneratedQuery
from postgres_mcp.models.schema import ColumnSchema, DatabaseSchema, TableSchema


@pytest.fixture
def sample_schema():
    """Sample database schema."""
    users_table = TableSchema(
        name="users",
        columns=[
            ColumnSchema(name="id", data_type="INTEGER", primary_key=True),
            ColumnSchema(name="username", data_type="VARCHAR(50)"),
            ColumnSchema(name="email", data_type="VARCHAR(255)"),
        ],
    )
    return DatabaseSchema(database_name="test_db", tables={"users": users_table})


@pytest.fixture
def mock_schema_cache(sample_schema):
    """Mock schema cache."""
    cache = MagicMock()
    cache.get_schema = AsyncMock(return_value=sample_schema)
    return cache


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client."""
    client = MagicMock()
    client.generate = AsyncMock()
    return client


@pytest.fixture
def mock_sql_validator():
    """Mock SQL validator."""
    validator = MagicMock()
    validator.validate = MagicMock()
    return validator


@pytest.fixture
def sql_generator(mock_schema_cache, mock_openai_client, mock_sql_validator):
    """SQL Generator fixture."""
    return SQLGenerator(
        schema_cache=mock_schema_cache,
        openai_client=mock_openai_client,
        sql_validator=mock_sql_validator,
    )


@pytest.mark.asyncio
async def test_generate_sql_success(sql_generator, mock_openai_client, mock_sql_validator):
    """Test successful SQL generation."""
    # Mock AI response
    mock_ai_result = MagicMock()
    mock_ai_result.sql = "SELECT * FROM users LIMIT 1000;"
    mock_ai_result.explanation = "Query all users"
    mock_ai_result.assumptions = []
    mock_openai_client.generate.return_value = mock_ai_result

    # Mock validation pass
    mock_validation = MagicMock()
    mock_validation.valid = True
    mock_validation.warnings = []
    mock_validation.cleaned_sql = None
    mock_sql_validator.validate.return_value = mock_validation

    result = await sql_generator.generate(natural_language="show all users", database="test_db")

    assert isinstance(result, GeneratedQuery)
    assert result.sql == "SELECT * FROM users LIMIT 1000;"
    assert result.validated is True
    assert result.generation_method == GenerationMethod.AI_GENERATED
    mock_openai_client.generate.assert_called_once()
    mock_sql_validator.validate.assert_called_once()


@pytest.mark.asyncio
async def test_generate_sql_validation_failure_retry(
    sql_generator, mock_openai_client, mock_sql_validator
):
    """Test retry after validation failure."""
    # First attempt fails
    mock_ai_result_1 = MagicMock()
    mock_ai_result_1.sql = "DELETE FROM users;"
    mock_ai_result_1.explanation = "Delete users"
    mock_ai_result_1.assumptions = []

    # Second attempt succeeds
    mock_ai_result_2 = MagicMock()
    mock_ai_result_2.sql = "SELECT * FROM users LIMIT 1000;"
    mock_ai_result_2.explanation = "Query users"
    mock_ai_result_2.assumptions = []

    mock_openai_client.generate.side_effect = [mock_ai_result_1, mock_ai_result_2]

    # First validation fails, second succeeds
    mock_validation_fail = MagicMock()
    mock_validation_fail.valid = False
    mock_validation_fail.errors = ["DELETE statements are not allowed (read-only queries only)"]

    mock_validation_success = MagicMock()
    mock_validation_success.valid = True
    mock_validation_success.warnings = []
    mock_validation_success.cleaned_sql = None

    mock_sql_validator.validate.side_effect = [
        mock_validation_fail,
        mock_validation_success,
    ]

    result = await sql_generator.generate(
        natural_language="show all users", database="test_db", max_retries=2
    )

    assert result.sql == "SELECT * FROM users LIMIT 1000;"
    assert result.validated is True
    assert mock_openai_client.generate.call_count == 2
    assert mock_sql_validator.validate.call_count == 2


@pytest.mark.asyncio
async def test_generate_sql_all_retries_failed(
    sql_generator, mock_openai_client, mock_sql_validator
):
    """Test all retries failed."""
    # Mock AI always returns invalid SQL
    mock_ai_result = MagicMock()
    mock_ai_result.sql = "DROP TABLE users;"
    mock_ai_result.explanation = "Drop table"
    mock_ai_result.assumptions = []
    mock_openai_client.generate.return_value = mock_ai_result

    # Mock validation always fails
    mock_validation = MagicMock()
    mock_validation.valid = False
    mock_validation.errors = ["DROP statements are not allowed (read-only queries only)"]
    mock_sql_validator.validate.return_value = mock_validation

    with pytest.raises(SQLGenerationError, match="Failed to generate valid SQL"):
        await sql_generator.generate(
            natural_language="delete users table", database="test_db", max_retries=2
        )

    assert mock_openai_client.generate.call_count == 2


@pytest.mark.asyncio
async def test_generate_sql_database_not_found(sql_generator, mock_schema_cache):
    """Test database not found."""
    mock_schema_cache.get_schema.return_value = None

    with pytest.raises(SQLGenerationError, match="Database.*not found"):
        await sql_generator.generate(natural_language="show data", database="non_existent_db")


@pytest.mark.asyncio
async def test_generate_sql_with_warnings(sql_generator, mock_openai_client, mock_sql_validator):
    """Test successful generation with warnings."""
    mock_ai_result = MagicMock()
    mock_ai_result.sql = "SELECT * FROM users;"
    mock_ai_result.explanation = "Query users"
    mock_ai_result.assumptions = ["Assuming all columns"]
    mock_openai_client.generate.return_value = mock_ai_result

    # Mock validation pass with warnings
    mock_validation = MagicMock()
    mock_validation.valid = True
    mock_validation.warnings = [
        "No LIMIT clause detected: Consider adding LIMIT to prevent large result sets"
    ]
    mock_validation.cleaned_sql = None
    mock_sql_validator.validate.return_value = mock_validation

    result = await sql_generator.generate(natural_language="show users", database="test_db")

    assert result.validated is True
    assert len(result.warnings) > 0
    assert "LIMIT" in result.warnings[0]


@pytest.mark.asyncio
async def test_generate_sql_caches_schema(
    sql_generator, mock_schema_cache, mock_openai_client, mock_sql_validator
):
    """Test schema cache usage."""
    # Setup proper mocks
    mock_ai_result = MagicMock()
    mock_ai_result.sql = "SELECT * FROM users LIMIT 100;"
    mock_ai_result.explanation = "Query users"
    mock_ai_result.assumptions = []
    mock_openai_client.generate.return_value = mock_ai_result

    mock_validation = MagicMock()
    mock_validation.valid = True
    mock_validation.warnings = []
    mock_validation.cleaned_sql = None
    mock_sql_validator.validate.return_value = mock_validation

    await sql_generator.generate(natural_language="test", database="test_db")
    await sql_generator.generate(natural_language="test2", database="test_db")

    # Schema should be fetched each time (no caching at generator level)
    assert mock_schema_cache.get_schema.call_count == 2
