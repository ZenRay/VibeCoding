"""
Query executor orchestrating SQL generation, validation, and execution.

Supports optional result validation for quality and semantic relevance checking.
"""

from __future__ import annotations

import time
import uuid

import structlog

from postgres_mcp.core.result_validator import ResultValidator
from postgres_mcp.core.sql_generator import SQLGenerator
from postgres_mcp.db.connection_pool import PoolManager
from postgres_mcp.db.query_runner import QueryRunner
from postgres_mcp.models.log_entry import LogStatus, QueryLogEntry
from postgres_mcp.models.result import QueryResult
from postgres_mcp.models.validation import ValidationLevel
from postgres_mcp.utils.jsonl_writer import JSONLWriter

logger = structlog.get_logger(__name__)


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
        result_validator: ResultValidator | None = None,
        enable_validation: bool = False,
    ) -> None:
        """
        Initialize query executor.

        Args:
            sql_generator: SQL generator instance.
            pool_manager: Connection pool manager.
            query_runner: Query runner instance.
            jsonl_writer: Optional JSONL writer for logging.
            result_validator: Optional result validator (for US5).
            enable_validation: Enable result validation by default.
        """
        self._sql_generator = sql_generator
        self._pool_manager = pool_manager
        self._query_runner = query_runner
        self._jsonl_writer = jsonl_writer
        self._result_validator = result_validator
        self._enable_validation = enable_validation

    async def execute(
        self,
        natural_language: str,
        database: str,
        limit: int = 1000,
        validate_result: bool | None = None,
        validation_level: ValidationLevel = ValidationLevel.AUTO,
    ) -> QueryResult:
        """
        Execute a natural language query and return results.

        Args:
            natural_language: User's natural language query.
            database: Target database name.
            limit: Maximum rows to return (default: 1000).
            validate_result: Override default validation setting (None uses default).
            validation_level: Validation level (BASIC, SEMANTIC, AUTO).

        Returns:
            QueryResult with SQL, columns, rows, and metadata.
            If validation is enabled, result.errors may contain validation suggestions.

        Raises:
            QueryExecutionError: If any step fails (generation, validation, execution).

        Example:
            >>> result = await executor.execute("List recent orders", "ecommerce")
            >>> assert result.row_count > 0
            >>> assert "SELECT" in result.sql
            >>> # Check for validation warnings
            >>> if result.errors:
            >>>     for error in result.errors:
            >>>         print(f"⚠️ {error}")
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

            # Step 6: Validate result quality (if enabled) - US5
            should_validate = (
                validate_result if validate_result is not None else self._enable_validation
            )

            if should_validate and self._result_validator:
                try:
                    validation = await self._result_validator.validate(
                        result=query_result,
                        natural_language=natural_language,
                        level=validation_level,
                    )

                    # Add validation suggestions to result errors
                    if not validation.valid or validation.suggestions:
                        logger.info(
                            "result_validation_suggestions",
                            valid=validation.valid,
                            suggestions_count=len(validation.suggestions),
                        )

                        for suggestion in validation.suggestions:
                            # Format suggestion message
                            suggestion_msg = f"⚠️ [{suggestion.issue.value}] {suggestion.message}"
                            if suggestion.suggested_query:
                                suggestion_msg += f"\n   💡 建议查询: {suggestion.suggested_query}"

                            query_result.errors.append(suggestion_msg)

                except Exception as validation_error:
                    # Validation failure should not block query result
                    logger.warning(
                        "result_validation_failed",
                        error=str(validation_error),
                    )
                    query_result.errors.append(f"⚠️ Result validation failed: {validation_error}")

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
