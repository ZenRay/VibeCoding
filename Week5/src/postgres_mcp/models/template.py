"""
Query template models for fallback SQL generation.

This module provides Pydantic models for defining and using SQL query templates
with parameter validation and SQL injection prevention.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from postgres_mcp.utils.validators import (
    validate_sql_expression,
    validate_sql_identifier,
)


class ParameterType(str, Enum):
    """Template parameter types for SQL generation."""

    IDENTIFIER = "identifier"
    EXPRESSION = "expression"
    KEYWORD = "keyword"
    LITERAL = "literal"


class TemplateParameter(BaseModel, frozen=True):
    """
    Template parameter definition.

    Args:
    ----------
        name: Parameter name.
        type: Parameter type.
        description: Parameter description.
        required: Whether the parameter is required.
        default: Default value if optional.
        validation_pattern: Optional regex validation pattern.

    Returns:
    ----------
        None

    Raises:
    ----------
        None
    """

    name: str
    type: ParameterType
    description: str
    required: bool = True
    default: str | None = None
    validation_pattern: str | None = None


class QueryTemplate(BaseModel, frozen=True):
    """
    Query template definition.

    Args:
    ----------
        name: Template name.
        description: Template description.
        priority: Template priority score.
        keywords: Keywords to trigger the template.
        patterns: Regex patterns to trigger the template.
        parameters: Template parameter definitions.
        sql_template: SQL template with placeholders.
        examples: Example inputs and parameters.

    Returns:
    ----------
        None

    Raises:
    ----------
        ValueError: If required parameters are missing.
    """

    name: str = Field(..., pattern="^[a-z_]+$")
    description: str
    priority: int = Field(..., ge=0, le=100)
    keywords: list[str] = Field(..., min_length=1)
    patterns: list[str] = Field(default_factory=list)
    parameters: list[TemplateParameter]
    sql_template: str = Field(..., min_length=1)
    examples: list[dict[str, object]] = Field(default_factory=list)

    def generate_sql(self, params: dict[str, str]) -> tuple[str, list[Any]]:
        """
        Generate SQL by filling template parameters with proper validation.

        Args:
        ----------
            params: Parameter values keyed by name.

        Returns:
        ----------
            Tuple of (SQL string with placeholders, list of parameter values)

        Raises:
        ----------
            ValueError: If a required parameter is missing or validation fails.
        """
        sql = self.sql_template
        param_values: list[Any] = []
        param_index = 1

        for parameter in self.parameters:
            # Check required parameters
            if parameter.required and parameter.name not in params:
                if parameter.default is not None:
                    params[parameter.name] = parameter.default
                else:
                    raise ValueError(f"missing required parameter: {parameter.name}")

            value = params.get(parameter.name, parameter.default)
            if value is None:
                continue

            # Validate based on parameter type
            if parameter.type == ParameterType.IDENTIFIER:
                validated_value = validate_sql_identifier(value)
                # Identifiers are directly replaced (after validation)
                sql = sql.replace(f"{{{parameter.name}}}", validated_value)

            elif parameter.type == ParameterType.EXPRESSION:
                validated_value = validate_sql_expression(value)
                # Expressions are also directly replaced (after validation)
                sql = sql.replace(f"{{{parameter.name}}}", validated_value)

            elif parameter.type == ParameterType.LITERAL:
                # Literals use parameterized placeholders
                sql = sql.replace(f"{{{parameter.name}}}", f"${param_index}")
                param_values.append(value)
                param_index += 1

            elif parameter.type == ParameterType.KEYWORD:
                # Keywords are validated against a whitelist
                validated_value = value.upper()
                if validated_value not in {"ASC", "DESC", "AND", "OR", "NOT"}:
                    raise ValueError(f"invalid keyword: {value}")
                sql = sql.replace(f"{{{parameter.name}}}", validated_value)

        return sql, param_values
