"""SQL Generator implementation.

Core SQL generator integrating OpenAI, Schema Cache, and SQL Validator.
"""

from enum import Enum
from typing import Any

import structlog

from postgres_mcp.ai.openai_client import AIServiceUnavailableError, OpenAIClient
from postgres_mcp.ai.prompt_builder import PromptBuilder
from postgres_mcp.core.sql_validator import SQLValidator
from postgres_mcp.models.query import GeneratedQuery

logger = structlog.get_logger(__name__)


class GenerationMethod(str, Enum):
    """SQL generation method."""

    AI_GENERATED = "ai_generated"
    TEMPLATE_MATCHED = "template_matched"
    CACHED = "cached"


class SQLGenerationError(Exception):
    """SQL generation error."""

    pass


class SQLGenerator:
    """
    SQL Generator for converting natural language to SQL queries.

    Orchestrates OpenAI client, schema cache, and SQL validator to
    generate safe and validated SQL queries.
    """

    def __init__(
        self,
        schema_cache: Any,
        openai_client: OpenAIClient,
        sql_validator: SQLValidator,
        prompt_builder: PromptBuilder | None = None,
    ):
        """
        Initialize SQL Generator.

        Args:
        ----------
            schema_cache: Schema cache instance
            openai_client: OpenAI client instance
            sql_validator: SQL validator instance
            prompt_builder: Prompt builder (optional)
        """
        self._schema_cache = schema_cache
        self._openai_client = openai_client
        self._sql_validator = sql_validator
        self._prompt_builder = prompt_builder or PromptBuilder()

    async def generate(
        self,
        natural_language: str,
        database: str,
        max_retries: int = 2,
    ) -> GeneratedQuery:
        """
        Generate SQL query from natural language.

        Args:
        ----------
            natural_language: Natural language query
            database: Target database name
            max_retries: Maximum number of retries on validation failure

        Returns:
        ----------
            GeneratedQuery with validated SQL

        Raises:
        ----------
            SQLGenerationError: When generation fails after all retries

        Example:
        ----------
            >>> generator = SQLGenerator(cache, client, validator)
            >>> query = await generator.generate("show all users", "mydb")
            >>> assert query.validated is True
        """
        # 1. Fetch schema from cache
        schema = await self._schema_cache.get_schema(database)
        if not schema:
            raise SQLGenerationError(f"Database '{database}' not found or schema not cached")

        # Track validation errors for retry prompts
        previous_validation_errors: list[str] = []

        # 2. Attempt to generate and validate SQL
        for attempt in range(max_retries):
            try:
                # Build prompts
                system_prompt = self._prompt_builder.build_system_prompt()
                user_prompt = self._prompt_builder.build_user_prompt(
                    natural_language=natural_language, schema=schema
                )

                # Enhance prompt with validation errors on retry
                if attempt > 0 and previous_validation_errors:
                    error_summary = "; ".join(previous_validation_errors[:3])
                    user_prompt = self._prompt_builder.build_retry_prompt(
                        original_prompt=user_prompt,
                        validation_error=f"Previous SQL failed validation: {error_summary}",
                    )

                # Call OpenAI API
                ai_response = await self._openai_client.generate(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    temperature=0.0 if attempt == 0 else 0.1,  # Add randomness on retry
                )

                # Validate generated SQL
                validation = self._sql_validator.validate(ai_response.sql)

                if validation.valid:
                    # Validation passed - return successful query
                    logger.info(
                        "sql_generation_success",
                        attempt=attempt + 1,
                        sql_length=len(ai_response.sql),
                        warnings_count=len(validation.warnings),
                    )
                    return GeneratedQuery(
                        sql=validation.cleaned_sql or ai_response.sql,
                        validated=True,
                        warnings=validation.warnings,
                        explanation=ai_response.explanation,
                        assumptions=ai_response.assumptions,
                        generation_method=GenerationMethod.AI_GENERATED,
                    )
                else:
                    # Validation failed - log and retry
                    logger.warning(
                        "sql_validation_failed",
                        attempt=attempt + 1,
                        errors=validation.errors,
                        sql_preview=ai_response.sql[:100],
                    )

                    # Store errors for next retry
                    previous_validation_errors.extend(validation.errors)

                    if attempt < max_retries - 1:
                        continue  # Retry generation
                    else:
                        # Max retries reached - return failed query
                        error_summary = "; ".join(validation.errors[:3])
                        raise SQLGenerationError(
                            f"Failed to generate valid SQL after {max_retries} attempts. "
                            f"Validation errors: {error_summary}"
                        )

            except AIServiceUnavailableError as e:
                logger.error("ai_service_unavailable", attempt=attempt + 1, error=str(e))
                # TODO: Fallback to template matching (Phase 4)
                raise SQLGenerationError(f"AI service unavailable: {e}") from e

            except SQLGenerationError:
                # Re-raise SQLGenerationError without wrapping
                raise

            except Exception as e:
                logger.error("unexpected_generation_error", attempt=attempt + 1, error=str(e))
                if attempt < max_retries - 1:
                    continue
                raise SQLGenerationError(f"Unexpected error during SQL generation: {e}") from e

        # Should not reach here, but just in case
        raise SQLGenerationError(f"Failed to generate valid SQL after {max_retries} attempts")
