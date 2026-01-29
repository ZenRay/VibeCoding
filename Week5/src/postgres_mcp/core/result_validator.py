"""
Result validator for verifying query result quality and relevance.

Provides two-tier validation:
- Level 1: Basic validation (local, fast, no AI cost)
- Level 2: AI semantic validation (optional, requires OpenAI)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from postgres_mcp.models.result import QueryResult
from postgres_mcp.models.validation import (
    ValidationIssue,
    ValidationLevel,
    ValidationResult,
    ValidationSeverity,
    ValidationSuggestion,
)

if TYPE_CHECKING:
    from postgres_mcp.ai.openai_client import OpenAIClient

logger = structlog.get_logger(__name__)


class ResultValidator:
    """
    Validate query result quality and semantic relevance.

    Provides basic local validation and optional AI semantic validation.
    Supports smart AUTO mode that automatically chooses validation level
    based on result characteristics.
    """

    def __init__(
        self,
        openai_client: OpenAIClient | None = None,
        min_expected_rows: int = 1,
        max_expected_rows: int = 10000,
        semantic_threshold: float = 0.7,
    ) -> None:
        """
        Initialize result validator.

        Args:
            openai_client: Optional OpenAI client for semantic validation.
            min_expected_rows: Minimum expected rows (triggers warning if less).
            max_expected_rows: Maximum reasonable rows (triggers warning if more).
            semantic_threshold: Minimum AI match score to pass semantic validation.
        """
        self._openai_client = openai_client
        self._min_expected_rows = min_expected_rows
        self._max_expected_rows = max_expected_rows
        self._semantic_threshold = semantic_threshold

    async def validate(
        self,
        result: QueryResult,
        natural_language: str,
        level: ValidationLevel = ValidationLevel.AUTO,
    ) -> ValidationResult:
        """
        Validate query result.

        Args:
            result: Query result to validate.
            natural_language: Original natural language query.
            level: Validation level (BASIC, SEMANTIC, AUTO).

        Returns:
            ValidationResult with issues and suggestions.
        """
        logger.info(
            "validating_result",
            row_count=result.row_count,
            level=level.value,
        )

        # Step 1: Always perform basic validation
        validation = await self._basic_validation(result, natural_language)

        # Step 2: Determine if semantic validation is needed
        should_use_semantic = self._should_use_semantic_validation(
            level=level,
            basic_validation=validation,
            result=result,
        )

        # Step 3: Perform semantic validation if needed
        if should_use_semantic and self._openai_client:
            semantic_validation = await self._semantic_validation(result, natural_language)
            validation = self._merge_validations(validation, semantic_validation)
            validation.validation_level_used = ValidationLevel.SEMANTIC
        else:
            validation.validation_level_used = ValidationLevel.BASIC

        logger.info(
            "validation_complete",
            valid=validation.valid,
            issues_count=len(validation.issues),
            suggestions_count=len(validation.suggestions),
            level_used=validation.validation_level_used.value,
        )

        return validation

    def _should_use_semantic_validation(
        self,
        level: ValidationLevel,
        basic_validation: ValidationResult,
        result: QueryResult,
    ) -> bool:
        """
        智能决策: 是否需要 AI 语义验证.

        策略:
        1. 用户明确请求 SEMANTIC → 总是验证
        2. 用户请求 BASIC → 从不验证
        3. 用户请求 AUTO → 根据结果质量智能决策:
           - 空结果 → 验证 (找出原因)
           - 结果过少 → 验证 (可能查询过严格)
           - 列名严重不匹配 → 验证 (可能查询错表)
           - 结果正常 → 跳过验证 (节省成本)

        Args:
            level: 用户请求的验证级别.
            basic_validation: 基础验证结果.
            result: 查询结果.

        Returns:
            是否需要执行 AI 语义验证.
        """
        # 用户明确请求
        if level == ValidationLevel.SEMANTIC:
            logger.debug("semantic_validation_forced", reason="user_requested")
            return True
        if level == ValidationLevel.BASIC:
            logger.debug("semantic_validation_skipped", reason="basic_only_requested")
            return False

        # AUTO 模式: 智能决策
        if not self._openai_client:
            logger.debug("semantic_validation_skipped", reason="no_openai_client")
            return False

        # 场景 1: 空结果 → 必须验证
        if result.row_count == 0:
            logger.info("semantic_validation_triggered", reason="empty_result")
            return True

        # 场景 2: 结果过少 → 可能需要验证
        if result.row_count < self._min_expected_rows:
            logger.info("semantic_validation_triggered", reason="too_few_rows")
            return True

        # 场景 3: 列名严重不匹配 → 可能查询错表
        if ValidationIssue.COLUMN_MISMATCH in basic_validation.issues:
            logger.info("semantic_validation_triggered", reason="column_mismatch")
            return True

        # 场景 4: 基础验证发现其他严重问题
        if not basic_validation.valid or basic_validation.has_errors:
            logger.info("semantic_validation_triggered", reason="basic_validation_failed")
            return True

        # 场景 5: 结果正常 → 跳过 AI 验证，节省成本
        logger.debug(
            "semantic_validation_skipped",
            reason="result_looks_good",
            row_count=result.row_count,
        )
        return False

    async def _basic_validation(
        self, result: QueryResult, natural_language: str
    ) -> ValidationResult:
        """基础验证 (本地, 无 AI 调用)."""
        issues: list[ValidationIssue] = []
        suggestions: list[ValidationSuggestion] = []

        # 检查 1: 空结果
        if result.row_count == 0:
            issues.append(ValidationIssue.EMPTY_RESULT)
            suggestions.append(
                ValidationSuggestion(
                    issue=ValidationIssue.EMPTY_RESULT,
                    severity=ValidationSeverity.ERROR,
                    message=(
                        "查询返回空结果。可能原因:\n"
                        "  1) 数据库中没有匹配的数据\n"
                        "  2) 过滤条件过于严格\n"
                        "  3) 表名或列名错误\n"
                        "建议: 检查查询条件或使用 list_databases 查看可用表"
                    ),
                    confidence=0.9,
                )
            )

        # 检查 2: 结果过少 (可能查询过于严格)
        elif result.row_count < self._min_expected_rows:
            issues.append(ValidationIssue.TOO_FEW_ROWS)
            suggestions.append(
                ValidationSuggestion(
                    issue=ValidationIssue.TOO_FEW_ROWS,
                    severity=ValidationSeverity.WARNING,
                    message=(
                        f"仅返回 {result.row_count} 行结果。"
                        "考虑放宽过滤条件或检查数据是否完整。"
                    ),
                    confidence=0.6,
                )
            )

        # 检查 3: 结果过多 (可能需要更精确的查询)
        if result.row_count >= self._max_expected_rows or result.truncated:
            issues.append(ValidationIssue.TOO_MANY_ROWS)
            truncation_note = " (结果已截断)" if result.truncated else ""
            suggestions.append(
                ValidationSuggestion(
                    issue=ValidationIssue.TOO_MANY_ROWS,
                    severity=ValidationSeverity.WARNING,
                    message=(
                        f"返回大量结果 ({result.row_count} 行){truncation_note}。\n"
                        "建议: 添加更具体的过滤条件 (如 WHERE, 日期范围) 或减少 LIMIT 值。"
                    ),
                    confidence=0.7,
                )
            )

        # 检查 4: 列名匹配度 (简单关键词检查)
        if result.row_count > 0:  # 仅在有结果时检查
            nl_keywords = self._extract_keywords(natural_language)
            column_names = {col.name.lower() for col in result.columns}

            if nl_keywords:
                matched_keywords = sum(1 for kw in nl_keywords if kw in column_names)
                match_ratio = matched_keywords / len(nl_keywords) if nl_keywords else 1.0

                if match_ratio == 0:  # 没有任何关键词匹配
                    issues.append(ValidationIssue.COLUMN_MISMATCH)
                    suggestions.append(
                        ValidationSuggestion(
                            issue=ValidationIssue.COLUMN_MISMATCH,
                            severity=ValidationSeverity.WARNING,
                            message=(
                                f"查询关键词 ({', '.join(nl_keywords)}) "
                                f"未在结果列名中出现 ({', '.join(column_names)})。\n"
                                "可能查询了错误的表或列。"
                            ),
                            confidence=0.5,
                        )
                    )

        # 验证通过条件: 无严重错误
        valid = ValidationIssue.EMPTY_RESULT not in issues

        return ValidationResult(
            valid=valid,
            issues=issues,
            suggestions=suggestions,
            details={
                "row_count": result.row_count,
                "column_count": len(result.columns),
                "truncated": result.truncated,
                "execution_time_ms": result.execution_time_ms,
            },
        )

    async def _semantic_validation(
        self, result: QueryResult, natural_language: str
    ) -> ValidationResult:
        """AI 语义验证 (需要 OpenAI)."""
        if not self._openai_client:
            logger.warning("semantic_validation_skipped_no_client")
            return ValidationResult(valid=True)

        try:
            logger.info("calling_ai_semantic_validation")

            # 调用 AI 验证
            ai_response = await self._openai_client.validate_result_relevance(
                natural_language=natural_language,
                sql=result.sql or "",
                columns=[col.name for col in result.columns],
                sample_rows=result.rows[:5],  # 只发送前 5 行作为样本
            )

            # 解析 AI 响应
            match_score = ai_response.match_score
            is_relevant = ai_response.is_relevant
            ai_suggestion = ai_response.suggestion
            ai_reason = ai_response.reason

            issues = []
            suggestions = []

            if match_score < self._semantic_threshold:
                issues.append(ValidationIssue.SEMANTIC_MISMATCH)
                suggestions.append(
                    ValidationSuggestion(
                        issue=ValidationIssue.SEMANTIC_MISMATCH,
                        severity=(
                            ValidationSeverity.ERROR
                            if match_score < 0.5
                            else ValidationSeverity.WARNING
                        ),
                        message=(
                            f"AI 检测到查询结果与用户意图匹配度较低 "
                            f"(得分: {match_score:.2f})。"
                        ),
                        suggested_query=ai_suggestion,
                        confidence=1.0 - match_score,  # 低匹配分数 = 高建议置信度
                        reasoning=ai_reason,
                    )
                )

            logger.info(
                "ai_semantic_validation_complete",
                is_relevant=is_relevant,
                match_score=match_score,
            )

            return ValidationResult(
                valid=is_relevant,
                issues=issues,
                suggestions=suggestions,
                semantic_match_score=match_score,
            )

        except Exception as e:
            logger.warning("semantic_validation_failed", error=str(e))
            # AI 验证失败不应阻止查询，返回通过
            return ValidationResult(
                valid=True,
                details={"ai_validation_error": str(e)},
            )

    def _extract_keywords(self, text: str) -> list[str]:
        """
        从自然语言中提取关键词.

        简单实现: 提取长度 > 2 的单词，排除常见停用词.
        中文需要逐字分割处理.
        """
        stopwords = {
            # 中文停用词
            "显示",
            "查看",
            "列出",
            "所有",
            "查询",
            "获取",
            "的",
            "和",
            "或",
            "从",
            "在",
            "中",
            # 英文停用词
            "show",
            "list",
            "get",
            "all",
            "select",
            "from",
            "where",
            "the",
            "and",
            "or",
            "in",
            "on",
            "at",
            "to",
            "of",
        }

        # 先按空格分词
        words = text.lower().replace(",", " ").replace(".", " ").split()

        keywords = []
        for word in words:
            # 处理中文（检测是否包含中文字符）
            if any("\u4e00" <= char <= "\u9fff" for char in word):
                # 中文词，直接添加（如果不在停用词中）
                if word not in stopwords and len(word) > 1:
                    keywords.append(word)
            else:
                # 英文词，过滤长度和停用词
                if len(word) > 2 and word not in stopwords:
                    keywords.append(word)

        return keywords

    def _merge_validations(
        self, basic: ValidationResult, semantic: ValidationResult
    ) -> ValidationResult:
        """合并基础验证和语义验证结果."""
        # 合并详情
        merged_details = {**basic.details, **semantic.details}
        if semantic.semantic_match_score is not None:
            merged_details["ai_semantic_score"] = semantic.semantic_match_score

        return ValidationResult(
            valid=basic.valid and semantic.valid,
            issues=basic.issues + semantic.issues,
            suggestions=basic.suggestions + semantic.suggestions,
            semantic_match_score=semantic.semantic_match_score,
            details=merged_details,
        )
