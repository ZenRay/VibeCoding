"""OpenAI client implementation.

Provides integration with OpenAI API for SQL query generation.
"""

import asyncio
import json
import re
from dataclasses import dataclass

import structlog
from openai import APIError, APITimeoutError, AsyncOpenAI, RateLimitError

logger = structlog.get_logger(__name__)


class AIServiceUnavailableError(Exception):
    """AI service unavailable error."""

    pass


@dataclass
class AIResponse:
    """
    AI response data structure.

    Attributes:
    ----------
        sql: Generated SQL query
        explanation: Brief explanation of the query
        assumptions: List of assumptions made during generation
    """

    sql: str
    explanation: str
    assumptions: list[str]


class OpenAIClient:
    """
    OpenAI API client wrapper.

    Provides SQL generation functionality with retry logic and error handling.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o-mini-2024-07-18",
        temperature: float = 0.0,
        max_tokens: int = 2000,
        timeout: float = 10.0,
        base_url: str | None = None,
    ):
        """
        Initialize OpenAI client.

        Args:
        ----------
            api_key: OpenAI API key
            model: Model name
            temperature: Generation temperature (0.0 = deterministic)
            max_tokens: Maximum number of tokens
            timeout: Request timeout in seconds
            base_url: Optional custom API base URL (for compatible services)
        """
        if base_url:
            self._client = AsyncOpenAI(api_key=api_key, base_url=base_url, timeout=timeout)
        else:
            self._client = AsyncOpenAI(api_key=api_key, timeout=timeout)
        self._model = model
        self._temperature = temperature
        self._max_tokens = max_tokens
        self._timeout = timeout

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float | None = None,
        max_retries: int = 2,
    ) -> AIResponse:
        """
        Generate SQL query using OpenAI API.

        Args:
        ----------
            system_prompt: System prompt
            user_prompt: User prompt
            temperature: Temperature override (optional)
            max_retries: Maximum number of retries

        Returns:
        ----------
            AIResponse object containing SQL, explanation, and assumptions

        Raises:
        ----------
            AIServiceUnavailableError: When AI service is unavailable
        """
        temp = temperature if temperature is not None else self._temperature

        for attempt in range(max_retries):
            try:
                response = await self._client.chat.completions.create(
                    model=self._model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=temp,
                    max_tokens=self._max_tokens,
                )

                content = response.choices[0].message.content
                if not content:
                    raise AIServiceUnavailableError("OpenAI returned empty response")

                # Parse JSON response
                try:
                    data = json.loads(content)
                    sql_value = data.get("sql")
                    if isinstance(sql_value, str) and sql_value.strip():
                        return AIResponse(
                            sql=sql_value,
                            explanation=data.get("explanation", ""),
                            assumptions=data.get("assumptions", []),
                        )

                    logger.warning(
                        "json_sql_missing_or_invalid",
                        attempt=attempt + 1,
                        sql_type=type(sql_value).__name__,
                    )
                    # If JSON parsed but sql is not a valid string, fail fast.
                    # Do not try to extract SQL from JSON text to avoid false matches.
                    raise AIServiceUnavailableError("OpenAI returned JSON without valid SQL")
                except json.JSONDecodeError as e:
                    logger.warning(
                        "json_parse_failed",
                        attempt=attempt + 1,
                        content=content[:200],
                        error=str(e),
                    )
                    extracted_sql = self._extract_sql_from_text(content)
                    if extracted_sql:
                        logger.warning(
                            "non_json_response_parsed",
                            attempt=attempt + 1,
                            sql_preview=extracted_sql[:200],
                        )
                        return AIResponse(
                            sql=extracted_sql,
                            explanation="Generated from non-JSON response.",
                            assumptions=[],
                        )
                    if attempt < max_retries - 1:
                        await asyncio.sleep(0.5 * (attempt + 1))
                        continue
                    raise AIServiceUnavailableError(f"Failed to parse OpenAI response: {e}") from e

            except APITimeoutError as e:
                logger.warning("openai_timeout", attempt=attempt + 1, timeout=self._timeout)
                if attempt < max_retries - 1:
                    await asyncio.sleep(1.0 * (attempt + 1))
                    continue
                raise AIServiceUnavailableError(f"OpenAI API timeout ({self._timeout}s)") from e

            except RateLimitError as e:
                logger.warning("openai_rate_limit", attempt=attempt + 1)
                if attempt < max_retries - 1:
                    await asyncio.sleep(2.0 * (attempt + 1))
                    continue
                raise AIServiceUnavailableError("OpenAI API rate limit exceeded") from e

            except APIError as e:
                logger.error("openai_api_error", attempt=attempt + 1, error=str(e))
                if attempt < max_retries - 1 and e.status_code >= 500:
                    # Only retry on server errors
                    await asyncio.sleep(1.0 * (attempt + 1))
                    continue
                raise AIServiceUnavailableError(f"OpenAI API error: {e}") from e

            except TimeoutError as e:
                logger.warning("request_timeout", attempt=attempt + 1, timeout=self._timeout)
                if attempt < max_retries - 1:
                    await asyncio.sleep(1.0 * (attempt + 1))
                    continue
                raise AIServiceUnavailableError(f"OpenAI API timeout ({self._timeout}s)") from e

            except Exception as e:
                logger.error("unexpected_error", attempt=attempt + 1, error=str(e))
                raise AIServiceUnavailableError(f"Unexpected error: {e}") from e

        raise AIServiceUnavailableError(f"Reached max retries ({max_retries})")

    @staticmethod
    def _extract_sql_from_text(content: str) -> str | None:
        """Extract SQL from non-JSON model output."""
        if not content:
            return None

        fence_sql = re.search(r"```sql\s*(.*?)```", content, re.IGNORECASE | re.DOTALL)
        if fence_sql:
            sql = fence_sql.group(1).strip()
            if sql:
                return sql

        fence_any = re.search(r"```\s*(.*?)```", content, re.DOTALL)
        if fence_any:
            sql = fence_any.group(1).strip()
            if sql and re.search(r"\b(select|with)\b", sql, re.IGNORECASE):
                return sql

        stmt_match = re.search(r"(?is)\b(select|with)\b.*?(;|$)", content)
        if stmt_match:
            sql = stmt_match.group(0).strip()
            if sql:
                return sql

        return None
