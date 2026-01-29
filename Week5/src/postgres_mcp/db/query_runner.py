"""
Query runner for executing SQL queries against PostgreSQL.

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

import time
from typing import Any

import asyncpg

from postgres_mcp.models.result import ColumnInfo, QueryResult


class QueryRunnerError(Exception):
    """
    Base exception for query runner errors.

    Args:
    ----------
        message: Error message.

    Returns:
    ----------
        None

    Raises:
    ----------
        None
    """


class QueryTimeoutError(QueryRunnerError):
    """
    Raised when query execution times out.

    Args:
    ----------
        message: Error message.

    Returns:
    ----------
        None

    Raises:
    ----------
        None
    """


class QueryExecutionError(QueryRunnerError):
    """
    Raised when query execution fails.

    Args:
    ----------
        message: Error message.

    Returns:
    ----------
        None

    Raises:
    ----------
        None
    """


class QueryRunner:
    """
    Execute SQL queries against PostgreSQL with timeout and result limiting.

    Args:
    ----------
        timeout_seconds: Query execution timeout in seconds.

    Returns:
    ----------
        None

    Raises:
    ----------
        None

    Example:
    ----------
        >>> runner = QueryRunner(timeout_seconds=30.0)
        >>> async with pool.acquire() as conn:
        ...     result = await runner.execute("SELECT * FROM users", conn)
        ...     print(f"Returned {result.row_count} rows")
    """

    def __init__(self, timeout_seconds: float = 30.0) -> None:
        self._timeout = timeout_seconds

    async def execute(
        self, sql: str, connection: asyncpg.Connection, limit: int = 1000
    ) -> QueryResult:
        """
        Execute a SQL query and return formatted results.

        Args:
        ----------
            sql: SQL query to execute.
            connection: Active asyncpg connection.
            limit: Maximum number of rows to return.

        Returns:
        ----------
            QueryResult with columns, rows, and metadata.

        Raises:
        ----------
            QueryTimeoutError: If query exceeds timeout.
            QueryExecutionError: If query execution fails.

        Example:
        ----------
            >>> result = await runner.execute("SELECT * FROM users", conn, limit=100)
            >>> assert result.row_count <= 100
        """
        start_time = time.perf_counter()

        try:
            # Execute query with timeout
            records = await connection.fetch(sql)

            # Extract column information
            columns: list[ColumnInfo] = []
            if records:
                for key in records[0].keys():
                    # Get column type from record
                    value = records[0][key]
                    type_name = type(value).__name__ if value is not None else "unknown"
                    columns.append(ColumnInfo(name=key, type=type_name))

            # Convert records to dictionaries
            rows: list[dict[str, Any]] = [dict(record) for record in records]

            # Apply limit
            truncated = len(rows) > limit
            if truncated:
                rows = rows[:limit]

            execution_time_ms = (time.perf_counter() - start_time) * 1000

            return QueryResult(
                columns=columns,
                rows=rows,
                row_count=len(rows),
                execution_time_ms=execution_time_ms,
                truncated=truncated,
            )

        except asyncpg.QueryCanceledError as exc:
            raise QueryTimeoutError(f"Query execution timed out after {self._timeout}s") from exc

        except (
            asyncpg.PostgresSyntaxError,
            asyncpg.UndefinedTableError,
            asyncpg.UndefinedColumnError,
        ) as exc:
            raise QueryExecutionError(f"SQL syntax error: {exc}") from exc

        except asyncpg.InsufficientPrivilegeError as exc:
            raise QueryExecutionError(f"Permission denied: {exc}") from exc

        except (asyncpg.ConnectionDoesNotExistError, asyncpg.InterfaceError) as exc:
            raise QueryExecutionError(f"Database connection error: {exc}") from exc

        except asyncpg.PostgresError as exc:
            raise QueryExecutionError(f"Database error: {exc}") from exc

        except Exception as exc:
            raise QueryExecutionError(f"Unexpected query execution error: {exc}") from exc
