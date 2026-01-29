"""SQL Generator implementation.

Core SQL generator integrating OpenAI, Schema Cache, Template Matcher, and SQL Validator.
"""

from typing import Any

import structlog

from postgres_mcp.ai.openai_client import AIServiceUnavailableError, OpenAIClient
from postgres_mcp.ai.prompt_builder import PromptBuilder
from postgres_mcp.core.sql_validator import SQLValidator
from postgres_mcp.core.template_matcher import TemplateMatcher
from postgres_mcp.models.query import GeneratedQuery, GenerationMethod

logger = structlog.get_logger(__name__)


class SQLGenerationError(Exception):
    """SQL generation error."""

    pass


class SQLGenerator:
    """
    SQL Generator for converting natural language to SQL queries.

    Orchestrates OpenAI client, template matcher (fallback), schema cache,
    and SQL validator to generate safe and validated SQL queries.
    """

    def __init__(
        self,
        schema_cache: Any,
        openai_client: OpenAIClient,
        sql_validator: SQLValidator,
        prompt_builder: PromptBuilder | None = None,
        template_matcher: TemplateMatcher | None = None,
    ):
        """
        Initialize SQL Generator.

        Args:
        ----------
            schema_cache: Schema cache instance
            openai_client: OpenAI client instance
            sql_validator: SQL validator instance
            prompt_builder: Prompt builder (optional)
            template_matcher: Template matcher for fallback (optional)
        """
        self._schema_cache = schema_cache
        self._openai_client = openai_client
        self._sql_validator = sql_validator
        self._prompt_builder = prompt_builder or PromptBuilder()
        self._template_matcher = template_matcher

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

                # Fallback to template matching if available
                if self._template_matcher:
                    logger.info("attempting_template_fallback", natural_language=natural_language)
                    try:
                        template_query = await self._generate_from_template(
                            natural_language=natural_language,
                            schema=schema,
                        )
                        if template_query:
                            logger.info(
                                "template_fallback_success",
                                template=template_query.generation_method,
                            )
                            return template_query
                    except Exception as template_error:
                        logger.warning(
                            "template_fallback_failed",
                            error=str(template_error),
                            exc_info=True,
                        )

                # No template fallback available or failed
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

    async def _generate_from_template(
        self,
        natural_language: str,
        schema: Any,
    ) -> GeneratedQuery | None:
        """
        Generate SQL from template matching (fallback method).

        Args:
        ----------
            natural_language: Natural language query
            schema: Database schema

        Returns:
        ----------
            GeneratedQuery if template matched, None otherwise

        Raises:
        ----------
            SQLGenerationError: When template matching fails
        """
        if not self._template_matcher:
            return None

        # Convert schema to dict format expected by template matcher
        schema_dict = {table.name: table for table in schema.tables}

        # Match query to template
        match = self._template_matcher.match(natural_language, schema_dict)

        if not match:
            logger.warning("no_template_match_found", query=natural_language)
            return None

        # Generate SQL from template
        try:
            sql, params = match["template"].generate_sql(match["entities"])

            # Validate generated SQL
            validation = self._sql_validator.validate(sql)

            if not validation.valid:
                error_summary = "; ".join(validation.errors[:3])
                logger.warning(
                    "template_sql_validation_failed",
                    template=match["template"].name,
                    errors=error_summary,
                )
                raise SQLGenerationError(
                    f"Template-generated SQL failed validation: {error_summary}"
                )

            logger.info(
                "template_sql_generated",
                template=match["template"].name,
                score=match["score"],
                entities=match["entities"],
            )

            return GeneratedQuery(
                sql=validation.cleaned_sql or sql,
                validated=True,
                warnings=validation.warnings,
                explanation=f"Generated from template: {match['template'].description}",
                assumptions=[f"Matched template: {match['template'].name}"],
                generation_method=GenerationMethod.TEMPLATE_MATCHED,
            )

        except Exception as e:
            logger.error("template_sql_generation_failed", error=str(e), exc_info=True)
            raise SQLGenerationError(f"Template SQL generation failed: {e}") from e
