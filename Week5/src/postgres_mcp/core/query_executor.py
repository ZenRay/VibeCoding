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

from postgres_mcp.core.sql_generator import SQLGenerator
from postgres_mcp.db.connection_pool import PoolManager
from postgres_mcp.db.query_runner import QueryRunner
from postgres_mcp.models.result import QueryResult


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
    ) -> None:
        self._sql_generator = sql_generator
        self._pool_manager = pool_manager
        self._query_runner = query_runner

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
        try:
            # Step 1: Generate SQL
            generated_query = await self._sql_generator.generate(natural_language, database)

            # Step 2: Validate SQL
            if not generated_query.validated:
                raise QueryExecutionError(
                    f"Generated SQL failed validation: {', '.join(generated_query.warnings)}"
                )

            # Step 3: Get database connection
            async with self._pool_manager.get_connection(database) as connection:
                # Step 4: Execute query
                query_result = await self._query_runner.execute(
                    sql=generated_query.sql, connection=connection, limit=limit
                )

            # Step 5: Add SQL to result
            query_result.sql = generated_query.sql

            return query_result

        except QueryExecutionError:
            # Re-raise our own exceptions
            raise

        except Exception as exc:
            # Wrap all other exceptions
            error_message = str(exc).lower()
            if "ai service" in error_message or "openai" in error_message:
                raise QueryExecutionError(f"AI service unavailable: {exc}") from exc
            elif "connection" in error_message:
                raise QueryExecutionError(f"Database connection failed: {exc}") from exc
            elif "validation" in error_message:
                raise QueryExecutionError(f"SQL validation failed: {exc}") from exc
            else:
                raise QueryExecutionError(f"Query execution failed: {exc}") from exc
