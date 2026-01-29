"""
Query request and SQL generation models.

This module defines models for natural language query requests and
the generated SQL responses with metadata.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator


class ResponseMode(str, Enum):
    """Response modes for query execution."""

    SQL_ONLY = "sql_only"
    EXECUTE = "execute"


class GenerationMethod(str, Enum):
    """SQL generation methods."""

    AI_GENERATED = "ai_generated"
    TEMPLATE_MATCHED = "template_matched"
    RETRY_GENERATED = "retry_generated"


class QueryRequest(BaseModel):
    """
    Natural language query request model.

    Args:
    ----------
        request_id: Unique request ID.
        natural_language: Natural language query.
        database: Optional database name.
        response_mode: Desired response mode.
        user_id: Optional user identifier.
        timestamp: Request timestamp.
        context: Optional extra context.

    Returns:
    ----------
        None

    Raises:
    ----------
        ValueError: If natural language is empty.
    """

    request_id: str = Field(default_factory=lambda: str(uuid4()))
    natural_language: str = Field(..., min_length=1, max_length=2000)
    database: str | None = Field(None, description="Target database name")
    response_mode: ResponseMode = ResponseMode.SQL_ONLY
    user_id: str | None = Field(None, description="User identifier")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    context: dict[str, object] = Field(default_factory=dict)

    @field_validator("natural_language")
    @classmethod
    def validate_natural_language(cls, value: str) -> str:
        """
        Validate natural language input.

        Args:
        ----------
            value: Natural language input string.

        Returns:
        ----------
            Normalized natural language string.

        Raises:
        ----------
            ValueError: If the input is empty.
        """

        stripped = value.strip()
        if not stripped:
            raise ValueError("natural_language must not be empty")
        return stripped


class GeneratedQuery(BaseModel):
    """
    Generated SQL query model.

    Args:
    ----------
        sql: Generated SQL text.
        validated: Whether the SQL passed validation.
        validation_error: Validation error message if any.
        warnings: Warning messages.
        explanation: Optional explanation from AI.
        assumptions: Optional assumptions from AI.
        generated_at: Timestamp of generation.
        generation_method: Method used to generate SQL.

    Returns:
    ----------
        None

    Raises:
    ----------
        ValueError: If SQL is empty.
    """

    sql: str = Field(..., min_length=1)
    validated: bool
    validation_error: str | None = None
    warnings: list[str] = Field(default_factory=list)
    explanation: str | None = None
    assumptions: list[str] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    generation_method: GenerationMethod = GenerationMethod.AI_GENERATED

    @field_validator("sql")
    @classmethod
    def validate_sql_not_empty(cls, value: str) -> str:
        """
        Validate SQL content is not empty.

        Args:
        ----------
            value: SQL string to validate.

        Returns:
        ----------
            Normalized SQL string.

        Raises:
        ----------
            ValueError: If the SQL string is empty.
        """

        if not value.strip():
            raise ValueError("sql must not be empty")
        return value.strip()
