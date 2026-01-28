"""
Query executor orchestrating SQL generation, validation, and execution.

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
import uuid

from postgres_mcp.core.sql_generator import SQLGenerator
from postgres_mcp.db.connection_pool import PoolManager
from postgres_mcp.db.query_runner import QueryRunner
from postgres_mcp.models.log_entry import LogStatus, QueryLogEntry
from postgres_mcp.models.result import QueryResult
from postgres_mcp.utils.jsonl_writer import JSONLWriter


class QueryExecutionError(Exception):
    """
    Base exception for query execution errors.

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


class QueryExecutor:
    """
    Execute natural language queries end-to-end.

    Orchestrates SQL generation, validation, and database execution.

    Args:
    ----------
        sql_generator: SQL generator instance.
        pool_manager: Connection pool manager.
        query_runner: Query runner instance.

    Returns:
    ----------
        None

    Raises:
    ----------
        None

    Example:
    ----------
        >>> executor = QueryExecutor(generator, pool_manager, runner)
        >>> result = await executor.execute("Show all active users", "main_db")
        >>> print(f"Found {result.row_count} users")
    """

    def __init__(
        self,
        sql_generator: SQLGenerator,
        pool_manager: PoolManager,
        query_runner: QueryRunner,
        jsonl_writer: JSONLWriter | None = None,
    ) -> None:
        self._sql_generator = sql_generator
        self._pool_manager = pool_manager
        self._query_runner = query_runner
        self._jsonl_writer = jsonl_writer

    async def execute(self, natural_language: str, database: str, limit: int = 1000) -> QueryResult:
        """
        Execute a natural language query and return results.

        Args:
        ----------
            natural_language: User's natural language query.
            database: Target database name.
            limit: Maximum rows to return (default: 1000).

        Returns:
        ----------
            QueryResult with SQL, columns, rows, and metadata.

        Raises:
        ----------
            QueryExecutionError: If any step fails (generation, validation, execution).

        Example:
        ----------
            >>> result = await executor.execute("List recent orders", "ecommerce")
            >>> assert result.row_count > 0
            >>> assert "SELECT" in result.sql
        """
        request_id = str(uuid.uuid4())
        start_time = time.perf_counter()
        generated_sql: str | None = None
        status = LogStatus.SUCCESS
        error_message: str | None = None
        row_count: int | None = None
        generation_method: str | None = None

        try:
            # Step 1: Generate SQL
            generated_query = await self._sql_generator.generate(natural_language, database)
            generated_sql = generated_query.sql
            generation_method = generated_query.generation_method

            # Step 2: Validate SQL
            if not generated_query.validated:
                status = LogStatus.VALIDATION_FAILED
                error_message = (
                    f"Generated SQL failed validation: {', '.join(generated_query.warnings)}"
                )
                raise QueryExecutionError(error_message)

            # Step 3: Get database connection
            async with self._pool_manager.get_connection(database) as connection:
                # Step 4: Execute query
                query_result = await self._query_runner.execute(
                    sql=generated_query.sql, connection=connection, limit=limit
                )

            # Step 5: Add SQL to result
            query_result.sql = generated_query.sql
            row_count = query_result.row_count

            return query_result

        except QueryExecutionError:
            # Re-raise our own exceptions
            raise

        except Exception as exc:
            # Wrap all other exceptions
            error_message_lower = str(exc).lower()
            if "ai service" in error_message_lower or "openai" in error_message_lower:
                status = LogStatus.AI_FAILED
                error_message = f"AI service unavailable: {exc}"
            elif "connection" in error_message_lower:
                status = LogStatus.EXECUTION_FAILED
                error_message = f"Database connection failed: {exc}"
            elif "validation" in error_message_lower:
                status = LogStatus.VALIDATION_FAILED
                error_message = f"SQL validation failed: {exc}"
            else:
                status = LogStatus.EXECUTION_FAILED
                error_message = f"Query execution failed: {exc}"

            raise QueryExecutionError(error_message) from exc

        finally:
            # Log query execution
            execution_time_ms = (time.perf_counter() - start_time) * 1000

            if self._jsonl_writer:
                log_entry = QueryLogEntry(
                    request_id=request_id,
                    database=database,
                    natural_language=natural_language,
                    sql=generated_sql,
                    status=status,
                    execution_time_ms=execution_time_ms,
                    row_count=row_count,
                    error_message=error_message,
                    generation_method=generation_method,
                )
                await self._jsonl_writer.write(log_entry)
