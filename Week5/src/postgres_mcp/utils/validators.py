"""
SQL validation utilities for preventing injection attacks.

This module provides functions for validating and sanitizing SQL identifiers
and expressions to prevent SQL injection vulnerabilities.
"""

from __future__ import annotations

import re
from typing import Any

# PostgreSQL identifier rules: must start with letter or underscore,
# can contain letters, digits, underscores, max 63 characters
_IDENTIFIER_PATTERN = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]{0,62}$")

# Dangerous SQL keywords and patterns that should not appear in identifiers
_DANGEROUS_PATTERNS = [
    r";",  # Statement separator
    r"--",  # Comment
    r"/\*",  # Block comment start
    r"\*/",  # Block comment end
    r"'",  # String delimiter
    r'"(?![a-zA-Z0-9_]+")'  # Quote not used for identifier quoting
    r"\bDROP\b",
    r"\bDELETE\b",
    r"\bINSERT\b",
    r"\bUPDATE\b",
    r"\bUNION\b",
    r"\bEXEC\b",
    r"\bEXECUTE\b",
    r"\bOR\b.*=.*=",  # OR with equality (common injection)
]


def validate_sql_identifier(identifier: str | None) -> str:
    """
    Validate SQL identifier follows PostgreSQL naming rules.

    Args:
    ----------
        identifier: The identifier to validate

    Returns:
    ----------
        The validated identifier

    Raises:
    ----------
        ValueError: If identifier is invalid or contains dangerous patterns

    Example:
    ----------
        >>> validate_sql_identifier("user_id")
        'user_id'
        >>> validate_sql_identifier("users; DROP TABLE users--")
        Traceback (most recent call last):
        ...
        ValueError: invalid SQL identifier: contains dangerous pattern
    """
    if not identifier or not identifier.strip():
        raise ValueError("SQL identifier cannot be empty")

    identifier = identifier.strip()

    # Check for dangerous patterns first
    for pattern in _DANGEROUS_PATTERNS:
        if re.search(pattern, identifier, re.IGNORECASE):
            raise ValueError(f"invalid SQL identifier: contains dangerous pattern '{pattern}'")

    # Validate identifier format
    if not _IDENTIFIER_PATTERN.match(identifier):
        raise ValueError(
            f"invalid SQL identifier format: '{identifier}' "
            f"(must start with letter/underscore, contain only alphanumerics/underscores)"
        )

    return f'"{identifier}"'


def validate_sql_expression(expression: str | None) -> str:
    """
    Validate SQL expression for dangerous patterns.

    This is more permissive than identifier validation but still checks
    for common injection attempts.

    Args:
    ----------
        expression: The SQL expression to validate

    Returns:
    ----------
        The validated expression

    Raises:
    ----------
        ValueError: If expression contains dangerous patterns

    Example:
    ----------
        >>> validate_sql_expression("id > 5")
        'id > 5'
        >>> validate_sql_expression("1=1; DROP TABLE users--")
        Traceback (most recent call last):
        ...
        ValueError: invalid SQL expression: contains dangerous pattern
    """
    if not expression or not expression.strip():
        raise ValueError("SQL expression cannot be empty")

    expression = expression.strip()

    # Check for statement separators, comments, and string delimiters
    dangerous_in_expressions = [r";", r"--", r"/\*", r"\*/", r"'"]

    for pattern in dangerous_in_expressions:
        if re.search(pattern, expression):
            raise ValueError(f"invalid SQL expression: contains dangerous pattern '{pattern}'")

    # Check for UNION attacks
    if re.search(r"\bUNION\b", expression, re.IGNORECASE):
        raise ValueError("invalid SQL expression: UNION not allowed in expressions")

    # Check for nested SELECT (subqueries might be legitimate, but risky in templates)
    if re.search(r"\b(SELECT|INSERT|UPDATE|DELETE|DROP)\b", expression, re.IGNORECASE):
        raise ValueError("invalid SQL expression: nested SQL statements not allowed in expressions")

    return expression


def quote_identifier(identifier: str) -> str:
    """
    Quote SQL identifier for safe use in queries.

    Args:
    ----------
        identifier: The identifier to quote

    Returns:
    ----------
        Quoted identifier safe for use in SQL

    Example:
    ----------
        >>> quote_identifier("user_id")
        '"user_id"'
        >>> quote_identifier("select")
        '"select"'
    """
    # First validate
    validated = validate_sql_identifier(identifier)

    # PostgreSQL uses double quotes for identifiers
    # Escape any existing double quotes by doubling them
    escaped = validated.replace('"', '""')

    return f'"{escaped}"'


def parameterize_value(value: Any) -> tuple[str, Any]:
    """
    Prepare a value for parameterized query.

    Args:
    ----------
        value: The value to parameterize

    Returns:
    ----------
        Tuple of (placeholder, value) where placeholder is like $1, $2, etc.

    Example:
    ----------
        >>> parameterize_value("user input")
        ('$', 'user input')
    """
    # Return a marker and the value
    # The actual placeholder number will be assigned by the caller
    return ("$", value)
