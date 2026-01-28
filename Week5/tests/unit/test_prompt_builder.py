"""Prompt Builder 测试。

测试 SQL 生成的 Prompt 构建逻辑。
"""

import pytest

from postgres_mcp.ai.prompt_builder import PromptBuilder
from postgres_mcp.models.schema import (
    ColumnSchema,
    DatabaseSchema,
    TableSchema,
)


@pytest.fixture
def sample_schema():
    """示例 schema fixture。"""
    users_table = TableSchema(
        name="users",
        columns=[
            ColumnSchema(name="id", data_type="INTEGER", nullable=False, primary_key=True),
            ColumnSchema(name="username", data_type="VARCHAR(50)", nullable=False),
            ColumnSchema(name="email", data_type="VARCHAR(255)", nullable=False),
            ColumnSchema(name="created_at", data_type="TIMESTAMP", nullable=False),
            ColumnSchema(name="is_active", data_type="BOOLEAN", nullable=False),
        ],
    )

    orders_table = TableSchema(
        name="orders",
        columns=[
            ColumnSchema(name="id", data_type="INTEGER", nullable=False, primary_key=True),
            ColumnSchema(name="user_id", data_type="INTEGER", nullable=False, foreign_key=True),
            ColumnSchema(name="total_amount", data_type="NUMERIC(10,2)", nullable=False),
            ColumnSchema(name="status", data_type="VARCHAR(20)", nullable=False),
            ColumnSchema(name="created_at", data_type="TIMESTAMP", nullable=False),
        ],
    )

    return DatabaseSchema(
        database_name="test_db", tables={"users": users_table, "orders": orders_table}
    )


@pytest.fixture
def prompt_builder():
    """Prompt Builder fixture。"""
    return PromptBuilder()


def test_build_system_prompt(prompt_builder):
    """测试系统提示词生成。"""
    system_prompt = prompt_builder.build_system_prompt()

    assert "PostgreSQL SQL 查询专家" in system_prompt
    assert "SELECT" in system_prompt
    assert "INSERT" not in system_prompt or "不允许" in system_prompt.lower()
    assert "LIMIT" in system_prompt


def test_build_user_prompt_simple(prompt_builder, sample_schema):
    """测试简单用户提示词生成。"""
    user_prompt = prompt_builder.build_user_prompt(
        natural_language="显示所有用户", schema=sample_schema
    )

    # 检查 DDL 格式
    assert "CREATE TABLE users" in user_prompt
    assert "id INTEGER" in user_prompt
    assert "username VARCHAR(50)" in user_prompt

    # 检查查询包含
    assert "显示所有用户" in user_prompt


def test_build_user_prompt_with_examples(prompt_builder, sample_schema):
    """测试包含示例的用户提示词生成。"""
    examples = [
        {"nl": "查找活跃用户", "sql": "SELECT * FROM users WHERE is_active = true;"},
        {
            "nl": "统计订单数",
            "sql": "SELECT COUNT(*) FROM orders;",
        },
    ]

    user_prompt = prompt_builder.build_user_prompt(
        natural_language="显示所有订单",
        schema=sample_schema,
        examples=examples,
    )

    # 检查示例包含
    assert "查找活跃用户" in user_prompt
    assert "SELECT * FROM users WHERE is_active = true" in user_prompt
    assert "统计订单数" in user_prompt


def test_schema_to_ddl_format(prompt_builder, sample_schema):
    """测试 Schema 转换为 DDL 格式。"""
    ddl = prompt_builder._schema_to_ddl(sample_schema, relevant_tables=["users"])

    # 检查格式
    assert "CREATE TABLE users (" in ddl
    assert "id INTEGER NOT NULL PRIMARY KEY" in ddl
    assert "username VARCHAR(50) NOT NULL" in ddl
    assert ");" in ddl

    # 确保只包含指定的表
    assert "users" in ddl
    assert "orders" not in ddl


def test_build_retry_prompt(prompt_builder, sample_schema):
    """测试重试提示词生成（验证失败后）。"""
    original_prompt = prompt_builder.build_user_prompt(
        natural_language="删除所有用户", schema=sample_schema
    )

    retry_prompt = prompt_builder.build_retry_prompt(
        original_prompt=original_prompt,
        validation_error="检测到 DELETE 操作，只允许 SELECT 查询",
    )

    assert original_prompt in retry_prompt
    assert "验证失败" in retry_prompt or "重要" in retry_prompt
    assert "DELETE" in retry_prompt or "SELECT" in retry_prompt


def test_select_relevant_tables(prompt_builder, sample_schema):
    """测试选择相关表（基于自然语言）。"""
    # 用户查询提到 "用户"
    relevant = prompt_builder._select_relevant_tables(
        natural_language="显示所有用户的邮箱", schema=sample_schema
    )

    assert "users" in relevant
    # 可能不包含 orders（如果算法足够智能）

    # 用户查询提到 "订单"
    relevant = prompt_builder._select_relevant_tables(
        natural_language="统计每个用户的订单数", schema=sample_schema
    )

    # 应该包含两个表（JOIN 场景）
    assert "users" in relevant
    assert "orders" in relevant


def test_token_optimization(prompt_builder, sample_schema):
    """测试 token 优化（限制表数量）。"""
    # 创建大型 schema（10 个表）
    large_schema = DatabaseSchema(database_name="large_db", tables={})
    for i in range(10):
        table = TableSchema(
            name=f"table_{i}",
            columns=[
                ColumnSchema(name="id", data_type="INTEGER", primary_key=True),
                ColumnSchema(name="data", data_type="TEXT"),
            ],
        )
        large_schema.tables[f"table_{i}"] = table

    user_prompt = prompt_builder.build_user_prompt(
        natural_language="查询 table_0",
        schema=large_schema,
        max_tables=3,  # 限制最多 3 个表
    )

    # 检查只包含相关的表
    assert "table_0" in user_prompt
    # 确保不包含所有 10 个表（token 优化）
    table_count = sum(1 for i in range(10) if f"table_{i}" in user_prompt)
    assert table_count <= 3
