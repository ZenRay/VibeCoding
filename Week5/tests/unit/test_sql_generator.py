"""SQL Generator 测试。

测试 SQL 生成器的核心功能和流程。
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
    """示例 schema。"""
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
    """Mock schema cache。"""
    cache = MagicMock()
    cache.get_schema = AsyncMock(return_value=sample_schema)
    return cache


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client。"""
    client = MagicMock()
    client.generate = AsyncMock()
    return client


@pytest.fixture
def mock_sql_validator():
    """Mock SQL validator。"""
    validator = MagicMock()
    validator.validate = MagicMock()
    return validator


@pytest.fixture
def sql_generator(mock_schema_cache, mock_openai_client, mock_sql_validator):
    """SQL Generator fixture。"""
    return SQLGenerator(
        schema_cache=mock_schema_cache,
        openai_client=mock_openai_client,
        sql_validator=mock_sql_validator,
    )


@pytest.mark.asyncio
async def test_generate_sql_success(sql_generator, mock_openai_client, mock_sql_validator):
    """测试成功生成 SQL。"""
    # Mock AI 响应
    mock_ai_result = MagicMock()
    mock_ai_result.sql = "SELECT * FROM users LIMIT 1000;"
    mock_ai_result.explanation = "查询所有用户"
    mock_ai_result.assumptions = []
    mock_openai_client.generate.return_value = mock_ai_result

    # Mock 验证通过
    mock_validation = MagicMock()
    mock_validation.valid = True
    mock_validation.warnings = []
    mock_sql_validator.validate.return_value = mock_validation

    result = await sql_generator.generate(natural_language="显示所有用户", database="test_db")

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
    """测试验证失败后重试。"""
    # 第一次生成失败
    mock_ai_result_1 = MagicMock()
    mock_ai_result_1.sql = "DELETE FROM users;"
    mock_ai_result_1.explanation = "删除用户"
    mock_ai_result_1.assumptions = []

    # 第二次生成成功
    mock_ai_result_2 = MagicMock()
    mock_ai_result_2.sql = "SELECT * FROM users LIMIT 1000;"
    mock_ai_result_2.explanation = "查询用户"
    mock_ai_result_2.assumptions = []

    mock_openai_client.generate.side_effect = [mock_ai_result_1, mock_ai_result_2]

    # 第一次验证失败，第二次成功
    mock_validation_fail = MagicMock()
    mock_validation_fail.valid = False
    mock_validation_fail.error = "检测到 DELETE 操作"

    mock_validation_success = MagicMock()
    mock_validation_success.valid = True
    mock_validation_success.warnings = []

    mock_sql_validator.validate.side_effect = [
        mock_validation_fail,
        mock_validation_success,
    ]

    result = await sql_generator.generate(
        natural_language="显示所有用户", database="test_db", max_retries=2
    )

    assert result.sql == "SELECT * FROM users LIMIT 1000;"
    assert result.validated is True
    assert mock_openai_client.generate.call_count == 2
    assert mock_sql_validator.validate.call_count == 2


@pytest.mark.asyncio
async def test_generate_sql_all_retries_failed(
    sql_generator, mock_openai_client, mock_sql_validator
):
    """测试所有重试都失败。"""
    # Mock AI 始终返回无效 SQL
    mock_ai_result = MagicMock()
    mock_ai_result.sql = "DROP TABLE users;"
    mock_ai_result.explanation = "删除表"
    mock_ai_result.assumptions = []
    mock_openai_client.generate.return_value = mock_ai_result

    # Mock 验证始终失败
    mock_validation = MagicMock()
    mock_validation.valid = False
    mock_validation.error = "检测到 DDL 操作"
    mock_sql_validator.validate.return_value = mock_validation

    with pytest.raises(SQLGenerationError, match="无法生成有效 SQL"):
        await sql_generator.generate(
            natural_language="删除用户表", database="test_db", max_retries=2
        )

    assert mock_openai_client.generate.call_count == 2


@pytest.mark.asyncio
async def test_generate_sql_database_not_found(sql_generator, mock_schema_cache):
    """测试数据库不存在。"""
    mock_schema_cache.get_schema.return_value = None

    with pytest.raises(SQLGenerationError, match="数据库.*未找到"):
        await sql_generator.generate(natural_language="显示数据", database="non_existent_db")


@pytest.mark.asyncio
async def test_generate_sql_with_warnings(sql_generator, mock_openai_client, mock_sql_validator):
    """测试带警告的成功生成。"""
    mock_ai_result = MagicMock()
    mock_ai_result.sql = "SELECT * FROM users;"
    mock_ai_result.explanation = "查询用户"
    mock_ai_result.assumptions = ["假设返回所有列"]
    mock_openai_client.generate.return_value = mock_ai_result

    # Mock 验证通过但有警告
    mock_validation = MagicMock()
    mock_validation.valid = True
    mock_validation.warnings = ["建议添加 LIMIT 子句"]
    mock_sql_validator.validate.return_value = mock_validation

    result = await sql_generator.generate(natural_language="显示用户", database="test_db")

    assert result.validated is True
    assert len(result.warnings) > 0
    assert "建议添加 LIMIT" in result.warnings[0]


@pytest.mark.asyncio
async def test_generate_sql_caches_schema(sql_generator, mock_schema_cache):
    """测试 schema 缓存使用。"""
    await sql_generator.generate(natural_language="test", database="test_db")
    await sql_generator.generate(natural_language="test2", database="test_db")

    # Schema 应该只被获取一次（缓存）
    assert mock_schema_cache.get_schema.call_count == 2  # 每次调用都会获取
