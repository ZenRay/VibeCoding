"""
Tests for core data models.

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

import json

import pytest

from postgres_mcp.models.connection import DatabaseConnection
from postgres_mcp.models.log_entry import LogStatus, QueryLogEntry
from postgres_mcp.models.query import GeneratedQuery, QueryRequest
from postgres_mcp.models.result import ColumnInfo, QueryResult
from postgres_mcp.models.schema import ColumnSchema, DatabaseSchema, IndexSchema, TableSchema
from postgres_mcp.models.template import ParameterType, QueryTemplate, TemplateParameter


def test_database_connection_name_validation() -> None:
    """
    Ensure invalid database connection names are rejected.

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

    with pytest.raises(ValueError):
        DatabaseConnection(
            name="invalid name",
            host="localhost",
            port=5432,
            database="db",
            user="user",
            password_env_var="DB_PASSWORD",
            ssl_mode="prefer",
            min_pool_size=1,
            max_pool_size=2,
        )


def test_schema_computed_fields_and_ddl() -> None:
    """
    Validate schema computed fields and DDL rendering.

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

    columns = [
        ColumnSchema(name="id", data_type="uuid", nullable=False, primary_key=True),
        ColumnSchema(
            name="user_id",
            data_type="uuid",
            foreign_key_table="users",
            foreign_key_column="id",
        ),
    ]
    table = TableSchema(
        name="orders",
        columns=columns,
        indexes=[IndexSchema(name="idx_orders_user", columns=["user_id"])],
        sample_data=[{"id": "1", "user_id": "2"}],
    )
    schema = DatabaseSchema(database_name="app", tables={"orders": table})

    assert schema.table_count == 1
    assert table.primary_keys == ["id"]
    assert table.foreign_keys[0]["ref_table"] == "users"

    ddl = schema.to_ddl()
    assert "CREATE TABLE orders" in ddl
    assert "FOREIGN KEY" in ddl


def test_query_models_validation() -> None:
    """
    Validate request and generated query models.

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

    request = QueryRequest(natural_language="List all users")
    assert request.natural_language == "List all users"

    with pytest.raises(ValueError):
        GeneratedQuery(sql=" ", validated=True)


def test_query_result_has_data_and_csv() -> None:
    """
    Validate query result helpers.

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

    result = QueryResult(
        columns=[ColumnInfo(name="id", type="int")],
        rows=[{"id": 1}],
        row_count=1,
        execution_time_ms=5.0,
    )
    assert result.has_data is True
    csv_content = result.to_csv()
    assert "id" in csv_content


def test_log_entry_to_jsonl() -> None:
    """
    Ensure log entries serialize to JSONL strings.

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

    entry = QueryLogEntry(
        request_id="req-1",
        natural_language="List users",
        status=LogStatus.SUCCESS,
        sql="SELECT 1",
    )
    payload = json.loads(entry.to_jsonl())
    assert payload["status"] == "success"


def test_template_generate_sql_missing_required() -> None:
    """
    Ensure template raises on missing required parameter.

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

    template = QueryTemplate(
        name="select_all",
        description="Select all",
        priority=100,
        keywords=["all"],
        parameters=[
            TemplateParameter(
                name="table_name",
                type=ParameterType.IDENTIFIER,
                description="Table",
                required=True,
            )
        ],
        sql_template="SELECT * FROM {table_name}",
    )

    with pytest.raises(ValueError):
        template.generate_sql({})
