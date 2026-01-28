"""
Query result models for executed SQL.

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

import csv
import io

from pydantic import BaseModel, Field, computed_field


class ColumnInfo(BaseModel, frozen=True):
    """
    Column metadata for query results.

    Args:
    ----------
        name: Column name.
        type: Column data type.
        table: Optional source table name.

    Returns:
    ----------
        None

    Raises:
    ----------
        None
    """

    name: str
    type: str
    table: str | None = None


class QueryResult(BaseModel):
    """
    Query execution result model.

    Args:
    ----------
        columns: Column metadata.
        rows: Result rows.
        row_count: Number of rows returned.
        execution_time_ms: Execution duration in milliseconds.
        truncated: Whether results were truncated.
        errors: Error messages if any.

    Returns:
    ----------
        None

    Raises:
    ----------
        None
    """

    columns: list[ColumnInfo]
    rows: list[dict[str, object]] = Field(default_factory=list)
    row_count: int = Field(ge=0)
    execution_time_ms: float = Field(ge=0)
    truncated: bool = False
    errors: list[str] = Field(default_factory=list)

    @computed_field
    @property
    def has_data(self) -> bool:
        """
        Indicate whether the result has data rows.

        Args:
        ----------
            None

        Returns:
        ----------
            True if row_count is greater than zero.

        Raises:
        ----------
            None
        """

        return self.row_count > 0

    def to_csv(self) -> str:
        """
        Convert results to CSV string.

        Args:
        ----------
            None

        Returns:
        ----------
            CSV representation of rows.

        Raises:
        ----------
            None
        """

        if not self.columns:
            return ""

        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=[col.name for col in self.columns])
        writer.writeheader()
        writer.writerows(self.rows)
        return output.getvalue()
