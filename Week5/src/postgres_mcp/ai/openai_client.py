"""OpenAI client implementation.

Provides integration with OpenAI API for SQL query generation and result validation.
"""

import asyncio
import json
import re
from dataclasses import dataclass

import structlog
from openai import (
    APIConnectionError,
    APIError,
    APITimeoutError,
    AsyncOpenAI,
    RateLimitError,
)

from postgres_mcp.models.validation import AIValidationResponse

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

            except APIConnectionError as e:
                logger.error("openai_connection_error", attempt=attempt + 1, error=str(e))
                if attempt < max_retries - 1:
                    await asyncio.sleep(2.0 * (attempt + 1))
                    continue
                raise AIServiceUnavailableError(f"OpenAI API connection error: {e}") from e

            except APIError as e:
                logger.error("openai_api_error", attempt=attempt + 1, error=str(e))
                # Only retry on server errors (status_code >= 500)
                if attempt < max_retries - 1 and hasattr(e, "status_code") and e.status_code >= 500:
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

    async def validate_result_relevance(
        self,
        natural_language: str,
        sql: str,
        columns: list[str],
        sample_rows: list[dict[str, object]],
    ) -> AIValidationResponse:
        """
        使用 AI 验证查询结果与用户意图的相关性.

        Args:
            natural_language: 用户原始查询.
            sql: 执行的 SQL 查询.
            columns: 结果列名列表.
            sample_rows: 样本数据行 (通常前 3-5 行).

        Returns:
            AIValidationResponse 包含相关性评分和建议.

        Raises:
            AIServiceUnavailableError: AI 服务不可用时.
        """
        logger.info(
            "validating_result_relevance",
            natural_language_length=len(natural_language),
            columns_count=len(columns),
            sample_rows_count=len(sample_rows),
        )

        # 构建验证 prompt
        prompt = self._build_validation_prompt(
            natural_language=natural_language,
            sql=sql,
            columns=columns,
            sample_rows=sample_rows,
        )

        try:
            response = await self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a database query result validator. "
                            "Evaluate if SQL query results semantically match the user's intent. "
                            "Respond ONLY with valid JSON."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,  # 低温度保证一致性
                max_tokens=800,
                response_format={"type": "json_object"},
            )

            content = response.choices[0].message.content
            if not content:
                raise AIServiceUnavailableError("Empty response from AI")

            # 解析 JSON 响应
            data = json.loads(content)

            # 验证必需字段
            if "is_relevant" not in data or "match_score" not in data:
                logger.warning("invalid_ai_response_format", data=data)
                # 默认认为有效，避免阻止查询
                return AIValidationResponse(
                    is_relevant=True,
                    match_score=1.0,
                    reason="AI response format invalid, assuming valid",
                )

            logger.info(
                "result_validation_complete",
                is_relevant=data["is_relevant"],
                match_score=data["match_score"],
            )

            return AIValidationResponse(
                is_relevant=data["is_relevant"],
                match_score=float(data["match_score"]),
                reason=data.get("reason", "No reason provided"),
                suggestion=data.get("suggestion"),
                issues=data.get("issues", []),
            )

        except (APIConnectionError, APITimeoutError, RateLimitError) as e:
            logger.error("ai_validation_api_error", error=str(e))
            raise AIServiceUnavailableError(f"AI validation failed: {e}") from e

        except json.JSONDecodeError as e:
            logger.error("ai_validation_json_error", error=str(e))
            # 默认认为有效
            return AIValidationResponse(
                is_relevant=True,
                match_score=1.0,
                reason=f"Failed to parse AI response: {e}",
            )

        except Exception as e:
            logger.error("ai_validation_unexpected_error", error=str(e))
            # 默认认为有效，避免阻止查询
            return AIValidationResponse(
                is_relevant=True,
                match_score=1.0,
                reason=f"Validation error: {e}",
            )

    @staticmethod
    def _build_validation_prompt(
        natural_language: str,
        sql: str,
        columns: list[str],
        sample_rows: list[dict[str, object]],
    ) -> str:
        """
        构建 AI 验证 prompt.

        Args:
            natural_language: 用户原始查询.
            sql: 执行的 SQL.
            columns: 结果列名.
            sample_rows: 样本数据行.

        Returns:
            完整的验证 prompt.
        """
        # 格式化样本数据 (限制长度)
        sample_data_str = (
            "No data returned" if not sample_rows else json.dumps(sample_rows, indent=2)
        )
        if len(sample_data_str) > 1000:
            sample_data_str = sample_data_str[:1000] + "\n... (truncated)"

        prompt = f"""Evaluate if the SQL query result semantically matches the user's intent.

**User Request**: "{natural_language}"

**SQL Executed**:
```sql
{sql}
```

**Result Columns**: {', '.join(columns) if columns else 'No columns'}

**Sample Data** (first {len(sample_rows)} rows):
```json
{sample_data_str}
```

**Your Task**:
1. Does the result semantically answer the user's question?
2. Are the returned columns relevant to the request?
3. Does the sample data look correct based on the query intent?

**Evaluation Criteria**:
- **High match (0.9-1.0)**: Perfect semantic match, answers the question directly
- **Good match (0.7-0.8)**: Mostly relevant, minor column naming differences
- **Partial match (0.5-0.6)**: Some relevance, but may be missing key info
- **Poor match (0.0-0.4)**: Wrong table, wrong columns, or completely irrelevant

**Output Format** (MUST be valid JSON):
{{
    "is_relevant": true/false,
    "match_score": 0.0-1.0,
    "reason": "Brief explanation of the score",
    "suggestion": "Improved SQL query (if match_score < 0.7, otherwise null)",
    "issues": ["List of specific issues detected, if any"]
}}

**Important**:
- If user asked for "users" but got "products", match_score should be very low
- If column names differ slightly (e.g., "user_name" vs "username"), still acceptable
- Empty result should be flagged with low match_score if data is expected
- Respond ONLY with valid JSON, no markdown formatting
"""
        return prompt
