"""SQL Generator implementation.

Core SQL generator integrating OpenAI, Schema Cache, and SQL Validator.
"""

from enum import Enum
from typing import Any

import structlog

from postgres_mcp.ai.openai_client import AIServiceUnavailableError, OpenAIClient
from postgres_mcp.ai.prompt_builder import PromptBuilder
from postgres_mcp.models.query import GeneratedQuery

logger = structlog.get_logger(__name__)


class GenerationMethod(str, Enum):
    """SQL 生成方法。"""

    AI_GENERATED = "ai_generated"
    TEMPLATE_MATCHED = "template_matched"
    CACHED = "cached"


class SQLGenerationError(Exception):
    """SQL 生成错误。"""

    pass


class SQLGenerator:
    """SQL 生成器。

    负责将自然语言转换为 SQL 查询。

    Attributes:
        schema_cache: Schema 缓存
        openai_client: OpenAI 客户端
        sql_validator: SQL 验证器
        prompt_builder: Prompt 构建器
    """

    def __init__(
        self,
        schema_cache: Any,
        openai_client: OpenAIClient,
        sql_validator: Any,
        prompt_builder: PromptBuilder | None = None,
    ):
        """初始化 SQL Generator。

        Args:
            schema_cache: Schema 缓存实例
            openai_client: OpenAI 客户端实例
            sql_validator: SQL 验证器实例
            prompt_builder: Prompt 构建器（可选）
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
        """生成 SQL 查询。

        Args:
            natural_language: 自然语言查询
            database: 目标数据库名称
            max_retries: 最大重试次数

        Returns:
            GeneratedQuery: 生成的查询

        Raises:
            SQLGenerationError: 生成失败
        """
        # 1. 获取 schema
        schema = await self._schema_cache.get_schema(database)
        if not schema:
            raise SQLGenerationError(f"数据库 '{database}' 未找到或 schema 未缓存")

        # 2. 尝试生成 SQL
        for attempt in range(max_retries):
            try:
                # 构建 prompts
                system_prompt = self._prompt_builder.build_system_prompt()
                user_prompt = self._prompt_builder.build_user_prompt(
                    natural_language=natural_language, schema=schema
                )

                # 如果是重试，增强 prompt
                if attempt > 0:
                    user_prompt = self._prompt_builder.build_retry_prompt(
                        original_prompt=user_prompt,
                        validation_error="上次验证失败，请重新生成",
                    )

                # 调用 OpenAI
                ai_response = await self._openai_client.generate(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    temperature=0.0 if attempt == 0 else 0.1,  # 重试时增加随机性
                )

                # 验证 SQL
                validation = self._sql_validator.validate(ai_response.sql)

                if validation.valid:
                    # 验证通过
                    return GeneratedQuery(
                        sql=ai_response.sql,
                        validated=True,
                        warnings=validation.warnings if hasattr(validation, 'warnings') else [],
                        explanation=ai_response.explanation,
                        assumptions=ai_response.assumptions,
                        generation_method=GenerationMethod.AI_GENERATED,
                    )
                else:
                    # 验证失败
                    logger.warning(
                        "sql_validation_failed",
                        attempt=attempt + 1,
                        error=validation.error if hasattr(validation, 'error') else "Unknown",
                        sql=ai_response.sql[:100],
                    )

                    if attempt < max_retries - 1:
                        continue  # 重试
                    else:
                        raise SQLGenerationError(
                            f"无法生成有效 SQL: {getattr(validation, 'error', 'Validation failed')}"
                        )

            except AIServiceUnavailableError as e:
                logger.error("ai_service_unavailable", attempt=attempt + 1, error=str(e))
                # TODO: 降级到模板匹配（Phase 4）
                raise SQLGenerationError(f"AI 服务不可用: {e}") from e

            except Exception as e:
                logger.error("unexpected_generation_error", attempt=attempt + 1, error=str(e))
                if attempt < max_retries - 1:
                    continue
                raise SQLGenerationError(f"生成 SQL 时发生错误: {e}") from e

        raise SQLGenerationError(f"达到最大重试次数 ({max_retries})，无法生成有效 SQL")
