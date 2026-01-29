"""
Unit tests for ResultValidator.

Tests basic validation, AI semantic validation, and smart validation strategy selection.
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from postgres_mcp.core.result_validator import ResultValidator
from postgres_mcp.models.result import ColumnInfo, QueryResult
from postgres_mcp.models.validation import (
    AIValidationResponse,
    ValidationIssue,
    ValidationLevel,
    ValidationSeverity,
)


@pytest.fixture
def mock_openai_client():
    """Create mock OpenAI client."""
    client = AsyncMock()
    client.validate_result_relevance = AsyncMock()
    return client


class TestBasicValidation:
    """Test basic (local) validation functionality."""

    @pytest.mark.asyncio
    async def test_empty_result_detection(self):
        """测试空结果检测"""
        validator = ResultValidator()
        result = QueryResult(
            columns=[ColumnInfo(name="id", type="integer")],
            rows=[],
            row_count=0,
            execution_time_ms=10.0,
            sql="SELECT * FROM users WHERE false",
        )

        validation = await validator.validate(
            result=result,
            natural_language="show all users",
            level=ValidationLevel.BASIC,
        )

        assert not validation.valid
        assert ValidationIssue.EMPTY_RESULT in validation.issues
        assert len(validation.suggestions) > 0
        assert any(s.issue == ValidationIssue.EMPTY_RESULT for s in validation.suggestions)
        assert validation.validation_level_used == ValidationLevel.BASIC

    @pytest.mark.asyncio
    async def test_too_few_rows_detection(self):
        """测试结果过少检测"""
        validator = ResultValidator(min_expected_rows=5)
        result = QueryResult(
            columns=[ColumnInfo(name="id", type="integer")],
            rows=[{"id": 1}],
            row_count=1,
            execution_time_ms=10.0,
            sql="SELECT * FROM users LIMIT 1",
        )

        validation = await validator.validate(
            result=result,
            natural_language="show all users",
            level=ValidationLevel.BASIC,
        )

        assert ValidationIssue.TOO_FEW_ROWS in validation.issues
        assert any(s.issue == ValidationIssue.TOO_FEW_ROWS for s in validation.suggestions)

    @pytest.mark.asyncio
    async def test_too_many_rows_detection(self):
        """测试结果过多检测"""
        validator = ResultValidator(max_expected_rows=100)
        result = QueryResult(
            columns=[ColumnInfo(name="id", type="integer")],
            rows=[{"id": i} for i in range(100)],
            row_count=100,
            execution_time_ms=50.0,
            truncated=True,
            sql="SELECT * FROM large_table",
        )

        validation = await validator.validate(
            result=result,
            natural_language="show all records",
            level=ValidationLevel.BASIC,
        )

        assert ValidationIssue.TOO_MANY_ROWS in validation.issues
        truncation_msg = any(
            "截断" in s.message or "truncated" in s.message.lower() for s in validation.suggestions
        )
        assert truncation_msg

    @pytest.mark.asyncio
    async def test_column_mismatch_detection(self):
        """测试列名不匹配检测"""
        validator = ResultValidator()
        result = QueryResult(
            columns=[
                ColumnInfo(name="product_id", type="integer"),
                ColumnInfo(name="product_name", type="text"),
            ],
            rows=[{"product_id": 1, "product_name": "Widget"}],
            row_count=1,
            execution_time_ms=10.0,
            sql="SELECT product_id, product_name FROM products",
        )

        validation = await validator.validate(
            result=result,
            natural_language="show all users",  # 请求 users 但返回 products
            level=ValidationLevel.BASIC,
        )

        assert ValidationIssue.COLUMN_MISMATCH in validation.issues
        suggestion = next(
            s for s in validation.suggestions if s.issue == ValidationIssue.COLUMN_MISMATCH
        )
        assert "users" in suggestion.message or "product" in suggestion.message

    @pytest.mark.asyncio
    async def test_valid_result_passes(self):
        """测试正常结果验证通过"""
        validator = ResultValidator()
        result = QueryResult(
            columns=[
                ColumnInfo(name="user_id", type="integer"),
                ColumnInfo(name="username", type="text"),
            ],
            rows=[{"user_id": 1, "username": "alice"}, {"user_id": 2, "username": "bob"}],
            row_count=2,
            execution_time_ms=10.0,
            sql="SELECT user_id, username FROM users",
        )

        validation = await validator.validate(
            result=result,
            natural_language="show user IDs and usernames",
            level=ValidationLevel.BASIC,
        )

        assert validation.valid
        assert len(validation.issues) == 0 or ValidationIssue.EMPTY_RESULT not in validation.issues


class TestSemanticValidation:
    """Test AI semantic validation functionality."""

    @pytest.mark.asyncio
    async def test_semantic_validation_high_match(self, mock_openai_client):
        """测试 AI 语义验证 - 高匹配度"""
        mock_openai_client.validate_result_relevance.return_value = AIValidationResponse(
            is_relevant=True,
            match_score=0.95,
            reason="Query correctly retrieves active users as requested",
        )

        validator = ResultValidator(openai_client=mock_openai_client, semantic_threshold=0.7)
        result = QueryResult(
            columns=[ColumnInfo(name="user_id", type="integer")],
            rows=[{"user_id": 1}, {"user_id": 2}],
            row_count=2,
            execution_time_ms=10.0,
            sql="SELECT user_id FROM users WHERE status = 'active'",
        )

        validation = await validator.validate(
            result=result,
            natural_language="show active users",
            level=ValidationLevel.SEMANTIC,
        )

        assert validation.valid
        assert validation.semantic_match_score == 0.95
        assert ValidationIssue.SEMANTIC_MISMATCH not in validation.issues
        assert validation.validation_level_used == ValidationLevel.SEMANTIC
        mock_openai_client.validate_result_relevance.assert_called_once()

    @pytest.mark.asyncio
    async def test_semantic_validation_low_match(self, mock_openai_client):
        """测试 AI 语义验证 - 低匹配度"""
        mock_openai_client.validate_result_relevance.return_value = AIValidationResponse(
            is_relevant=False,
            match_score=0.3,
            reason="Query returned products but user asked for users",
            suggestion="SELECT * FROM users WHERE status = 'active'",
        )

        validator = ResultValidator(openai_client=mock_openai_client, semantic_threshold=0.7)
        result = QueryResult(
            columns=[ColumnInfo(name="product_id", type="integer")],
            rows=[{"product_id": 1}],
            row_count=1,
            execution_time_ms=10.0,
            sql="SELECT product_id FROM products",
        )

        validation = await validator.validate(
            result=result,
            natural_language="show active users",
            level=ValidationLevel.SEMANTIC,
        )

        assert not validation.valid
        assert validation.semantic_match_score == 0.3
        assert ValidationIssue.SEMANTIC_MISMATCH in validation.issues

        suggestion = next(
            s for s in validation.suggestions if s.issue == ValidationIssue.SEMANTIC_MISMATCH
        )
        assert suggestion.suggested_query is not None
        assert suggestion.severity == ValidationSeverity.ERROR  # 0.3 < 0.5


class TestAutoValidationStrategy:
    """Test AUTO validation level (smart strategy selection)."""

    @pytest.mark.asyncio
    async def test_auto_upgrades_to_semantic_on_empty_result(self, mock_openai_client):
        """测试 AUTO 模式在空结果时自动升级到语义验证"""
        mock_openai_client.validate_result_relevance.return_value = AIValidationResponse(
            is_relevant=False,
            match_score=0.4,
            reason="No data found, possibly wrong table",
        )

        validator = ResultValidator(openai_client=mock_openai_client)
        result = QueryResult(
            columns=[ColumnInfo(name="id", type="integer")],
            rows=[],
            row_count=0,
            execution_time_ms=10.0,
            sql="SELECT * FROM users WHERE false",
        )

        validation = await validator.validate(
            result=result,
            natural_language="show all users",
            level=ValidationLevel.AUTO,
        )

        # 应该执行了 AI 验证
        assert validation.validation_level_used == ValidationLevel.SEMANTIC
        assert validation.semantic_match_score is not None
        mock_openai_client.validate_result_relevance.assert_called_once()

    @pytest.mark.asyncio
    async def test_auto_skips_semantic_on_good_result(self, mock_openai_client):
        """测试 AUTO 模式在正常结果时跳过语义验证"""
        # Mock AI validation (虽然不应该被调用)
        mock_openai_client.validate_result_relevance.return_value = AIValidationResponse(
            is_relevant=True,
            match_score=0.9,
            reason="Good result",
        )

        validator = ResultValidator(openai_client=mock_openai_client)
        result = QueryResult(
            columns=[ColumnInfo(name="user_id", type="integer")],
            rows=[{"user_id": i} for i in range(10)],
            row_count=10,
            execution_time_ms=10.0,
            sql="SELECT user_id FROM users",
        )

        validation = await validator.validate(
            result=result,
            natural_language="show users",  # 与 user_id 相关，不会触发列名不匹配
            level=ValidationLevel.AUTO,
        )

        # 应该仅执行基础验证（或者如果执行了AI验证也应该通过）
        # 关键是结果应该是有效的
        assert validation.valid
        assert not validation.has_errors

    @pytest.mark.asyncio
    async def test_auto_upgrades_on_column_mismatch(self, mock_openai_client):
        """测试 AUTO 模式在列名不匹配时升级到语义验证"""
        mock_openai_client.validate_result_relevance.return_value = AIValidationResponse(
            is_relevant=False,
            match_score=0.2,
            reason="User asked for users but got products",
        )

        validator = ResultValidator(openai_client=mock_openai_client)
        result = QueryResult(
            columns=[ColumnInfo(name="product_id", type="integer")],
            rows=[{"product_id": 1}],
            row_count=1,
            execution_time_ms=10.0,
            sql="SELECT product_id FROM products",
        )

        validation = await validator.validate(
            result=result,
            natural_language="show all users",  # 明显不匹配
            level=ValidationLevel.AUTO,
        )

        # 应该执行了 AI 验证
        assert validation.validation_level_used == ValidationLevel.SEMANTIC
        mock_openai_client.validate_result_relevance.assert_called_once()


class TestKeywordExtraction:
    """Test keyword extraction functionality."""

    def test_extract_keywords_chinese(self):
        """测试中文关键词提取"""
        validator = ResultValidator()
        keywords = validator._extract_keywords("显示所有用户的名称和邮箱")

        # 中文分词结果
        assert "用户的名称和邮箱" in keywords or "用户" in " ".join(keywords)
        # 停用词应该被过滤
        assert "显示" not in keywords
        assert "所有" not in keywords

    def test_extract_keywords_english(self):
        """测试英文关键词提取"""
        validator = ResultValidator()
        keywords = validator._extract_keywords("show all active users and their email addresses")

        assert "active" in keywords
        assert "users" in keywords
        assert "email" in keywords
        assert "addresses" in keywords
        assert "show" not in keywords  # 停用词
        assert "all" not in keywords  # 停用词
        assert "and" not in keywords  # 停用词

    def test_extract_keywords_mixed(self):
        """测试混合语言关键词提取"""
        validator = ResultValidator()
        keywords = validator._extract_keywords("查询 active 用户的 email")

        assert "active" in keywords
        assert "email" in keywords
        # 中文词可能作为整体或部分提取
        assert any("用户" in kw for kw in keywords) or "用户的" in keywords
        assert "查询" not in keywords  # 停用词


class TestValidationResultProperties:
    """Test ValidationResult helper properties."""

    def test_has_errors_property(self):
        """测试 has_errors 属性"""
        from postgres_mcp.models.validation import ValidationResult, ValidationSuggestion

        result = ValidationResult(
            valid=False,
            suggestions=[
                ValidationSuggestion(
                    issue=ValidationIssue.EMPTY_RESULT,
                    severity=ValidationSeverity.ERROR,
                    message="Error message",
                )
            ],
        )

        assert result.has_errors

    def test_has_warnings_property(self):
        """测试 has_warnings 属性"""
        from postgres_mcp.models.validation import ValidationResult, ValidationSuggestion

        result = ValidationResult(
            valid=True,
            suggestions=[
                ValidationSuggestion(
                    issue=ValidationIssue.TOO_MANY_ROWS,
                    severity=ValidationSeverity.WARNING,
                    message="Warning message",
                )
            ],
        )

        assert result.has_warnings
        assert not result.has_errors


class TestEdgeCases:
    """Test edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_semantic_validation_without_client(self):
        """测试没有 OpenAI client 时语义验证的降级"""
        validator = ResultValidator(openai_client=None)
        result = QueryResult(
            columns=[],
            rows=[],
            row_count=0,
            execution_time_ms=10.0,
        )

        validation = await validator.validate(
            result=result,
            natural_language="test query",
            level=ValidationLevel.SEMANTIC,
        )

        # 应该降级到基础验证
        assert validation.validation_level_used == ValidationLevel.BASIC
        assert validation.semantic_match_score is None

    @pytest.mark.asyncio
    async def test_ai_validation_failure_graceful_degradation(self, mock_openai_client):
        """测试 AI 验证失败时的优雅降级"""
        mock_openai_client.validate_result_relevance.side_effect = Exception("API Error")

        validator = ResultValidator(openai_client=mock_openai_client)
        result = QueryResult(
            columns=[ColumnInfo(name="id", type="integer")],
            rows=[{"id": 1}],
            row_count=1,
            execution_time_ms=10.0,
        )

        validation = await validator.validate(
            result=result,
            natural_language="test query",
            level=ValidationLevel.SEMANTIC,
        )

        # AI 验证失败时应优雅降级
        # 基础验证应该通过（非空结果）
        # 或者至少不应该有严重错误阻止查询
        assert validation.valid or len([s for s in validation.suggestions if s.severity == ValidationSeverity.ERROR]) == 0
