"""
Query audit log entry model.

This module provides Pydantic models for logging query execution details
in JSONL format for audit and debugging purposes.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum

from pydantic import BaseModel, Field


class LogStatus(str, Enum):
    """Log status values for query history entries."""

    SUCCESS = "success"
    VALIDATION_FAILED = "validation_failed"
    EXECUTION_FAILED = "execution_failed"
    AI_FAILED = "ai_failed"
    TEMPLATE_MATCHED = "template_matched"


class QueryLogEntry(BaseModel):
    """
    Query audit log entry for JSONL serialization.

    Attributes:
        timestamp: ISO timestamp of the event
        request_id: Unique request identifier
        database: Target database name
        user_id: Optional user identifier
        natural_language: Original natural language query
        sql: Generated SQL statement
        status: Execution status
        execution_time_ms: Query execution duration in milliseconds
        row_count: Number of rows returned
        error_message: Error message if failed
        generation_method: SQL generation method used
    """

    timestamp: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    request_id: str
    database: str | None = None
    user_id: str | None = None
    natural_language: str
    sql: str | None = None
    status: LogStatus
    execution_time_ms: float | None = Field(None, ge=0)
    row_count: int | None = Field(None, ge=0)
    error_message: str | None = None
    generation_method: str | None = None

    def to_jsonl(self) -> str:
        """Serialize the entry to a JSONL string."""
        return self.model_dump_json(exclude_none=True)
