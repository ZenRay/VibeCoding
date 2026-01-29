"""
Security tests for QueryTemplate SQL injection prevention.

This module contains comprehensive security tests to ensure QueryTemplate
properly validates and sanitizes inputs to prevent SQL injection attacks.
"""

from __future__ import annotations

import pytest

from postgres_mcp.models.template import ParameterType, QueryTemplate, TemplateParameter


def test_template_rejects_sql_injection_in_identifier() -> None:
    """
    Test that template rejects SQL injection attempts in identifier parameters.

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
        name="select_from_table",
        description="Select from table",
        priority=100,
        keywords=["select"],
        parameters=[
            TemplateParameter(
                name="table_name",
                type=ParameterType.IDENTIFIER,
                description="Table name",
                required=True,
            )
        ],
        sql_template="SELECT * FROM {table_name}",
    )

    # SQL injection attempts that should be rejected
    malicious_inputs = [
        "users; DROP TABLE users--",
        "users' OR '1'='1",
        "users UNION SELECT * FROM passwords",
        "users/*comment*/",
        "users; DELETE FROM users WHERE 1=1--",
    ]

    for malicious_input in malicious_inputs:
        with pytest.raises(ValueError, match="invalid.*identifier"):
            template.generate_sql({"table_name": malicious_input})


def test_template_rejects_sql_injection_in_expression() -> None:
    """
    Test that template properly handles expression parameters.

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
        name="select_where",
        description="Select with where clause",
        priority=100,
        keywords=["where"],
        parameters=[
            TemplateParameter(
                name="condition",
                type=ParameterType.EXPRESSION,
                description="Where condition",
                required=True,
            )
        ],
        sql_template="SELECT * FROM users WHERE {condition}",
    )

    # SQL injection attempts in expressions
    malicious_inputs = [
        "1=1; DROP TABLE users--",
        "1=1' OR '1'='1",
        "id > 0 UNION SELECT * FROM passwords",
    ]

    for malicious_input in malicious_inputs:
        with pytest.raises(ValueError, match="invalid.*expression"):
            template.generate_sql({"condition": malicious_input})


def test_template_validates_identifier_format() -> None:
    """
    Test that identifiers follow PostgreSQL naming rules.

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
        name="select_column",
        description="Select specific column",
        priority=100,
        keywords=["column"],
        parameters=[
            TemplateParameter(
                name="column_name",
                type=ParameterType.IDENTIFIER,
                description="Column name",
                required=True,
            )
        ],
        sql_template="SELECT {column_name} FROM users",
    )

    # Valid identifiers should work
    valid_identifiers = ["user_id", "firstName", "user123", "_internal"]

    for valid_id in valid_identifiers:
        sql, params = template.generate_sql({"column_name": valid_id})
        # Identifier will be quoted, so check for quoted version
        assert f'"{valid_id}"' in sql
        assert params == []  # Identifiers don't use parameters

    # Invalid identifiers should be rejected
    invalid_identifiers = [
        "123user",  # starts with number
        "user-name",  # contains hyphen
        "user name",  # contains space
        "user@domain",  # contains special char
    ]

    for invalid_id in invalid_identifiers:
        with pytest.raises(ValueError):
            template.generate_sql({"column_name": invalid_id})


def test_template_with_parameterized_values() -> None:
    """
    Test that literal values are properly parameterized.

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
        name="select_by_name",
        description="Select by name",
        priority=100,
        keywords=["name"],
        parameters=[
            TemplateParameter(
                name="name_value",
                type=ParameterType.LITERAL,
                description="Name to search",
                required=True,
            )
        ],
        sql_template="SELECT * FROM users WHERE name = {name_value}",
    )

    # generate_sql should now return tuple[str, list[Any]]
    sql, params = template.generate_sql({"name_value": "John'; DROP TABLE users--"})

    # SQL should use parameterized placeholder, not direct interpolation
    assert "$1" in sql or "?" in sql  # Depending on implementation
    assert "John'; DROP TABLE users--" in params  # Value should be in params list
    assert "John'; DROP TABLE users--" not in sql  # Value should NOT be in SQL string


def test_template_empty_identifier_rejected() -> None:
    """
    Test that empty identifiers are rejected.

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
        name="select_table",
        description="Select from table",
        priority=100,
        keywords=["table"],
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
        template.generate_sql({"table_name": ""})

    with pytest.raises(ValueError):
        template.generate_sql({"table_name": "   "})


def test_template_keyword_injection_rejected() -> None:
    """
    Test that SQL keywords in identifiers are handled correctly.

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
        name="select_column",
        description="Select column",
        priority=100,
        keywords=["column"],
        parameters=[
            TemplateParameter(
                name="col",
                type=ParameterType.IDENTIFIER,
                description="Column name",
                required=True,
            )
        ],
        sql_template="SELECT {col} FROM users",
    )

    # SQL keywords used as identifiers should be quoted/escaped
    sql, _ = template.generate_sql({"col": "select"})
    # Should be properly quoted: "select" or `select`
    assert '"select"' in sql or "`select`" in sql or sql == "SELECT select FROM users"

    # But SQL injection attempts disguised as keywords should fail
    with pytest.raises(ValueError):
        template.generate_sql({"col": "id; DROP TABLE users"})
