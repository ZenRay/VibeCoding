# ResultValidator (US5) - 设计方案

**创建日期**: 2026-01-30  
**状态**: 待实现  
**优先级**: P3 (可选增强功能)

---

## 📋 概述

**目标**: 验证查询结果的质量和相关性，在返回给用户前检测并处理常见问题。

**价值**: 
- 提升用户体验（减少空结果和误匹配）
- 增强系统智能（AI 验证结果语义匹配）
- 提供查询改进建议

**范围**: 可选功能，不影响核心 MVP

---

## 🎯 用户故事 (US5)

### 验收场景

1. **给定** 生成的 SQL 查询，**当** 系统测试执行，**那么** 查询成功运行并返回结果或适当的错误消息

2. **给定** 查询结果和原始自然语言请求，**当** 系统验证相关性，**那么** AI 模型确认结果与用户意图匹配或建议查询改进

3. **给定** 返回意外空结果的查询，**当** 验证发生，**那么** 系统建议替代查询或请求澄清

4. **给定** 有语法错误的查询，**当** 系统测试执行，**那么** 在返回给用户之前捕获错误，并且系统尝试修复或重新生成查询

---

## 📐 设计方案

### 核心功能

ResultValidator 提供 **两层验证**：

#### **Level 1: 基础验证 (本地)** ✅ 快速、无 AI 调用
- ✅ 空结果检测
- ✅ 结果数量异常检测（过少/过多）
- ✅ 列名匹配度检查
- ✅ 数据类型一致性验证

#### **Level 2: 语义验证 (AI)** 🤖 可选、需要 OpenAI API
- 🤖 AI 验证结果与用户意图匹配度
- 🤖 生成查询改进建议
- 🤖 提供替代查询方案

---

## 🏗️ 架构设计

### 数据模型 (新增)

```python
# src/postgres_mcp/models/validation.py

from enum import Enum
from pydantic import BaseModel, Field

class ValidationLevel(str, Enum):
    """验证级别"""
    BASIC = "basic"          # 仅基础验证
    SEMANTIC = "semantic"    # 包含 AI 语义验证

class ValidationIssue(str, Enum):
    """验证问题类型"""
    EMPTY_RESULT = "empty_result"              # 空结果
    TOO_FEW_ROWS = "too_few_rows"              # 结果过少
    TOO_MANY_ROWS = "too_many_rows"            # 结果过多（可能需要更精确的查询）
    COLUMN_MISMATCH = "column_mismatch"        # 列名与预期不符
    TYPE_MISMATCH = "type_mismatch"            # 数据类型不一致
    SEMANTIC_MISMATCH = "semantic_mismatch"    # AI 检测到语义不匹配

class ValidationSuggestion(BaseModel):
    """验证改进建议"""
    issue: ValidationIssue
    message: str                               # 问题描述
    suggested_query: str | None = None         # 建议的替代查询
    confidence: float = Field(ge=0.0, le=1.0)  # 建议置信度

class ValidationResult(BaseModel):
    """验证结果"""
    valid: bool                                # 是否通过验证
    issues: list[ValidationIssue] = Field(default_factory=list)
    suggestions: list[ValidationSuggestion] = Field(default_factory=list)
    semantic_match_score: float | None = None  # AI 语义匹配分数 (0-1)
    details: dict[str, object] = Field(default_factory=dict)  # 详细信息
```

---

### 核心组件

#### 1. ResultValidator (主验证器)

```python
# src/postgres_mcp/core/result_validator.py

from __future__ import annotations
from typing import TYPE_CHECKING

import structlog

from postgres_mcp.models.result import QueryResult
from postgres_mcp.models.validation import (
    ValidationIssue,
    ValidationLevel,
    ValidationResult,
    ValidationSuggestion,
)

if TYPE_CHECKING:
    from postgres_mcp.ai.openai_client import OpenAIClient

logger = structlog.get_logger(__name__)


class ResultValidator:
    """
    验证查询结果质量和相关性.
    
    提供两层验证:
    - Level 1: 基础验证 (本地, 快速)
    - Level 2: AI 语义验证 (可选, 需要 OpenAI)
    """
    
    def __init__(
        self,
        openai_client: OpenAIClient | None = None,
        min_expected_rows: int = 1,          # 最少预期行数
        max_expected_rows: int = 10000,      # 最大合理行数
        semantic_threshold: float = 0.7,     # AI 语义匹配阈值
    ) -> None:
        self._openai_client = openai_client
        self._min_expected_rows = min_expected_rows
        self._max_expected_rows = max_expected_rows
        self._semantic_threshold = semantic_threshold
    
    async def validate(
        self,
        result: QueryResult,
        natural_language: str,
        level: ValidationLevel = ValidationLevel.BASIC,
    ) -> ValidationResult:
        """
        验证查询结果.
        
        Args:
            result: 查询结果
            natural_language: 原始自然语言查询
            level: 验证级别 (basic/semantic)
        
        Returns:
            ValidationResult 包含问题和建议
        """
        # Step 1: 基础验证 (总是执行)
        validation = await self._basic_validation(result, natural_language)
        
        # Step 2: 语义验证 (可选)
        if level == ValidationLevel.SEMANTIC and self._openai_client:
            semantic_validation = await self._semantic_validation(
                result, natural_language
            )
            validation = self._merge_validations(validation, semantic_validation)
        
        logger.info(
            "result_validation_complete",
            valid=validation.valid,
            issues=len(validation.issues),
            level=level.value,
        )
        
        return validation
    
    async def _basic_validation(
        self, result: QueryResult, natural_language: str
    ) -> ValidationResult:
        """基础验证 (本地, 无 AI 调用)"""
        issues: list[ValidationIssue] = []
        suggestions: list[ValidationSuggestion] = []
        
        # 检查 1: 空结果
        if result.row_count == 0:
            issues.append(ValidationIssue.EMPTY_RESULT)
            suggestions.append(
                ValidationSuggestion(
                    issue=ValidationIssue.EMPTY_RESULT,
                    message=(
                        "查询返回空结果。可能原因: "
                        "1) 数据库中没有匹配的数据 "
                        "2) 过滤条件过于严格 "
                        "3) 表名或列名错误"
                    ),
                    confidence=0.8,
                )
            )
        
        # 检查 2: 结果过少 (可能查询过于严格)
        elif result.row_count < self._min_expected_rows:
            issues.append(ValidationIssue.TOO_FEW_ROWS)
            suggestions.append(
                ValidationSuggestion(
                    issue=ValidationIssue.TOO_FEW_ROWS,
                    message=f"仅返回 {result.row_count} 行结果。考虑放宽过滤条件。",
                    confidence=0.6,
                )
            )
        
        # 检查 3: 结果过多 (可能需要更精确的查询)
        elif result.row_count >= self._max_expected_rows or result.truncated:
            issues.append(ValidationIssue.TOO_MANY_ROWS)
            suggestions.append(
                ValidationSuggestion(
                    issue=ValidationIssue.TOO_MANY_ROWS,
                    message=(
                        f"返回大量结果 ({result.row_count} 行)。"
                        "考虑添加更具体的过滤条件或限制返回行数。"
                    ),
                    confidence=0.7,
                )
            )
        
        # 检查 4: 列名匹配度 (简单关键词检查)
        # 提取自然语言中的关键词，检查是否出现在列名中
        nl_keywords = self._extract_keywords(natural_language)
        column_names = {col.name.lower() for col in result.columns}
        
        matched_keywords = sum(1 for kw in nl_keywords if kw in column_names)
        if nl_keywords and matched_keywords == 0:
            issues.append(ValidationIssue.COLUMN_MISMATCH)
            suggestions.append(
                ValidationSuggestion(
                    issue=ValidationIssue.COLUMN_MISMATCH,
                    message=(
                        f"查询关键词 ({', '.join(nl_keywords)}) "
                        f"未在结果列名中出现 ({', '.join(column_names)})。"
                        "可能查询的表或列不正确。"
                    ),
                    confidence=0.5,
                )
            )
        
        # 验证通过条件: 无严重问题
        valid = ValidationIssue.EMPTY_RESULT not in issues
        
        return ValidationResult(
            valid=valid,
            issues=issues,
            suggestions=suggestions,
            details={
                "row_count": result.row_count,
                "column_count": len(result.columns),
                "truncated": result.truncated,
            },
        )
    
    async def _semantic_validation(
        self, result: QueryResult, natural_language: str
    ) -> ValidationResult:
        """AI 语义验证 (需要 OpenAI)"""
        if not self._openai_client:
            return ValidationResult(valid=True)
        
        try:
            # 构建验证 prompt
            prompt = self._build_validation_prompt(result, natural_language)
            
            # 调用 AI 验证
            ai_response = await self._openai_client.validate_result_relevance(
                natural_language=natural_language,
                sql=result.sql or "",
                columns=[col.name for col in result.columns],
                sample_rows=result.rows[:5],  # 只发送前 5 行作为样本
            )
            
            # 解析 AI 响应
            match_score = ai_response.get("match_score", 1.0)
            is_relevant = ai_response.get("is_relevant", True)
            ai_suggestion = ai_response.get("suggestion")
            
            issues = []
            suggestions = []
            
            if match_score < self._semantic_threshold:
                issues.append(ValidationIssue.SEMANTIC_MISMATCH)
                suggestions.append(
                    ValidationSuggestion(
                        issue=ValidationIssue.SEMANTIC_MISMATCH,
                        message=(
                            f"AI 检测到查询结果与用户意图匹配度较低 "
                            f"(得分: {match_score:.2f})。"
                        ),
                        suggested_query=ai_suggestion,
                        confidence=match_score,
                    )
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
            return ValidationResult(valid=True)
    
    def _extract_keywords(self, text: str) -> list[str]:
        """从自然语言中提取关键词"""
        # 简单实现: 提取长度 > 3 的单词，排除常见停用词
        stopwords = {
            "显示", "查看", "列出", "所有", "查询", "获取",
            "show", "list", "get", "all", "select", "from",
            "where", "the", "and", "or",
        }
        words = text.lower().split()
        return [w for w in words if len(w) > 3 and w not in stopwords]
    
    def _merge_validations(
        self, basic: ValidationResult, semantic: ValidationResult
    ) -> ValidationResult:
        """合并基础验证和语义验证结果"""
        return ValidationResult(
            valid=basic.valid and semantic.valid,
            issues=basic.issues + semantic.issues,
            suggestions=basic.suggestions + semantic.suggestions,
            semantic_match_score=semantic.semantic_match_score,
            details=basic.details,
        )
    
    def _build_validation_prompt(
        self, result: QueryResult, natural_language: str
    ) -> str:
        """构建验证 prompt"""
        return f"""
Given:
- User request: "{natural_language}"
- SQL executed: {result.sql}
- Columns returned: {', '.join(col.name for col in result.columns)}
- Sample rows: {result.rows[:3]}

Evaluate:
1. Does the result semantically match the user's intent?
2. If not, what query would be more appropriate?

Respond with JSON:
{{
    "is_relevant": true/false,
    "match_score": 0.0-1.0,
    "reason": "explanation",
    "suggestion": "alternative SQL query (optional)"
}}
"""
```

---

#### 2. OpenAI Client 扩展 (新方法)

```python
# src/postgres_mcp/ai/openai_client.py

# 添加新方法到现有的 OpenAIClient 类

async def validate_result_relevance(
    self,
    natural_language: str,
    sql: str,
    columns: list[str],
    sample_rows: list[dict[str, object]],
) -> dict[str, object]:
    """
    使用 AI 验证查询结果与用户意图的相关性.
    
    Args:
        natural_language: 用户原始查询
        sql: 执行的 SQL
        columns: 结果列名
        sample_rows: 样本数据行
    
    Returns:
        包含 is_relevant, match_score, reason, suggestion 的字典
    """
    prompt = f"""
You are a database query validator. Evaluate if the SQL query result matches the user's intent.

User Request: "{natural_language}"
SQL Executed: {sql}
Result Columns: {', '.join(columns)}
Sample Data (first 3 rows): {sample_rows[:3]}

Evaluate:
1. Does the result semantically answer the user's question?
2. Are the columns relevant to the request?
3. Does the data look correct based on the sample?

Provide a match score (0.0-1.0) and explanation.
If score < 0.7, suggest an improved SQL query.

Respond ONLY with valid JSON (no markdown):
{{
    "is_relevant": true,
    "match_score": 0.95,
    "reason": "The query correctly retrieves active users as requested",
    "suggestion": null
}}
"""
    
    try:
        response = await self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": "You are a database query validator."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=500,
            response_format={"type": "json_object"},
        )
        
        result = json.loads(response.choices[0].message.content)
        return result
    
    except Exception as e:
        logger.error("ai_validation_failed", error=str(e))
        # 默认认为有效，不阻止查询
        return {
            "is_relevant": True,
            "match_score": 1.0,
            "reason": "Validation failed, assuming valid",
            "suggestion": None,
        }
```

---

#### 3. QueryExecutor 集成 (可选启用)

```python
# src/postgres_mcp/core/query_executor.py

# 修改 __init__ 方法
def __init__(
    self,
    sql_generator: SQLGenerator,
    pool_manager: PoolManager,
    query_runner: QueryRunner,
    jsonl_writer: JSONLWriter | None = None,
    result_validator: ResultValidator | None = None,  # 新增: 可选
    enable_validation: bool = False,                   # 新增: 默认关闭
) -> None:
    self._sql_generator = sql_generator
    self._pool_manager = pool_manager
    self._query_runner = query_runner
    self._jsonl_writer = jsonl_writer
    self._result_validator = result_validator
    self._enable_validation = enable_validation


# 修改 execute 方法
async def execute(
    self, 
    natural_language: str, 
    database: str, 
    limit: int = 1000,
    validate_result: bool | None = None,  # 新增: 覆盖默认配置
) -> QueryResult:
    """Execute a natural language query and return results."""
    
    # ... 现有的 SQL 生成和执行逻辑 ...
    
    # 查询成功后，执行结果验证 (如果启用)
    should_validate = (
        validate_result 
        if validate_result is not None 
        else self._enable_validation
    )
    
    if should_validate and self._result_validator and result.row_count > 0:
        validation = await self._result_validator.validate(
            result=result,
            natural_language=natural_language,
            level=ValidationLevel.BASIC,  # 默认仅基础验证
        )
        
        # 将验证结果添加到 QueryResult
        if not validation.valid:
            # 将建议添加到结果的 errors 字段
            for suggestion in validation.suggestions:
                result.errors.append(
                    f"⚠️ {suggestion.issue.value}: {suggestion.message}"
                )
        
        logger.info(
            "result_validated",
            valid=validation.valid,
            issues=len(validation.issues),
        )
    
    return result
```

---

## 🧪 测试策略

### T079: 单元测试 ResultValidator

```python
# tests/unit/test_result_validator.py

import pytest
from postgres_mcp.core.result_validator import ResultValidator
from postgres_mcp.models.result import QueryResult, ColumnInfo
from postgres_mcp.models.validation import ValidationLevel, ValidationIssue


@pytest.mark.asyncio
async def test_empty_result_detection():
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


@pytest.mark.asyncio
async def test_column_mismatch_detection():
    """测试列名不匹配检测"""
    validator = ResultValidator()
    result = QueryResult(
        columns=[ColumnInfo(name="product_id", type="integer")],
        rows=[{"product_id": 1}],
        row_count=1,
        execution_time_ms=10.0,
        sql="SELECT product_id FROM products",
    )
    
    validation = await validator.validate(
        result=result,
        natural_language="show all users",  # 请求 users 但返回 products
        level=ValidationLevel.BASIC,
    )
    
    assert ValidationIssue.COLUMN_MISMATCH in validation.issues


@pytest.mark.asyncio
async def test_too_many_rows_detection():
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


@pytest.mark.asyncio
async def test_valid_result():
    """测试正常结果验证通过"""
    validator = ResultValidator()
    result = QueryResult(
        columns=[ColumnInfo(name="user_id", type="integer")],
        rows=[{"user_id": 1}, {"user_id": 2}],
        row_count=2,
        execution_time_ms=10.0,
        sql="SELECT user_id FROM users",
    )
    
    validation = await validator.validate(
        result=result,
        natural_language="show user IDs",
        level=ValidationLevel.BASIC,
    )
    
    assert validation.valid
    assert len(validation.issues) == 0
```

---

### T080: 实现文件

- `src/postgres_mcp/models/validation.py` (新增 - 数据模型)
- `src/postgres_mcp/core/result_validator.py` (新增 - 验证器)
- `src/postgres_mcp/ai/openai_client.py` (修改 - 添加验证方法)

### T081: 集成到 QueryExecutor

- `src/postgres_mcp/core/query_executor.py` (修改 - 添加验证调用)
- `src/postgres_mcp/server.py` (修改 - 初始化 validator)

---

## 📊 实现工作量估算

| 任务 | 文件 | 工作量 | 说明 |
|------|------|--------|------|
| **T079** | 数据模型 | 0.5h | validation.py (5 个类) |
| **T079** | 单元测试 | 1h | test_result_validator.py (8-10 tests) |
| **T080** | ResultValidator | 2h | 基础验证 + AI 验证逻辑 |
| **T080** | OpenAI 扩展 | 0.5h | validate_result_relevance 方法 |
| **T081** | QueryExecutor 集成 | 0.5h | 添加可选验证调用 |
| **T081** | 集成测试 | 1h | 端到端测试 |
| **代码审查** | - | 0.5h | Ruff, Mypy, 文档 |
| **总计** | - | **6h** | 约 1 个工作日 |

---

## 💡 使用示例

### 基础验证 (默认)

```python
# 仅本地检查，无 AI 调用
executor = QueryExecutor(
    sql_generator=generator,
    pool_manager=pool_manager,
    query_runner=runner,
    result_validator=ResultValidator(),
    enable_validation=True,  # 启用验证
)

result = await executor.execute(
    natural_language="show all users",
    database="main_db",
)

# 如果结果有问题，errors 字段包含建议
if result.errors:
    for error in result.errors:
        print(f"⚠️ {error}")
```

### AI 语义验证 (可选)

```python
# 启用 AI 语义验证
validator = ResultValidator(
    openai_client=openai_client,
    semantic_threshold=0.7,
)

executor = QueryExecutor(
    ...,
    result_validator=validator,
)

result = await executor.execute(
    natural_language="show active users",
    database="main_db",
    validate_result=True,  # 显式启用
)
```

---

## 🔧 配置选项

### config.yaml 新增配置

```yaml
# 结果验证配置
result_validation:
  enabled: false                    # 默认关闭 (可选功能)
  level: "basic"                    # basic | semantic
  min_expected_rows: 1              # 最少预期行数
  max_expected_rows: 10000          # 最大合理行数
  semantic_threshold: 0.7           # AI 匹配阈值
  enable_ai_suggestions: false      # 是否启用 AI 改进建议
```

---

## ⚠️ 注意事项

1. **性能影响**:
   - 基础验证: ~1-5ms 额外开销 ✅ 可接受
   - AI 语义验证: ~500-2000ms 额外开销 ⚠️ 仅在需要时启用

2. **成本影响**:
   - AI 验证每次调用消耗 ~200-500 tokens
   - 建议仅在返回空结果或用户明确请求时启用

3. **降级策略**:
   - AI 验证失败时自动降级为通过
   - 不阻止正常查询返回

4. **可选性**:
   - 默认关闭，不影响现有功能
   - 用户可通过配置或参数启用

---

## 🎯 实现优先级建议

### 推荐实现顺序

1. **阶段 1: 基础验证** (T079, T080) - 3h
   - ✅ 数据模型
   - ✅ ResultValidator (仅 basic validation)
   - ✅ 单元测试
   - 💡 **收益**: 立即可用，无额外成本

2. **阶段 2: QueryExecutor 集成** (T081) - 1h
   - ✅ 集成到查询流程
   - ✅ 配置选项
   - 💡 **收益**: 端到端功能

3. **阶段 3: AI 语义验证** (T080 扩展) - 2h
   - 🤖 OpenAI 集成
   - 🤖 Semantic validation
   - 💡 **收益**: 高级功能，可选启用

---

## 📈 价值评估

| 维度 | 评分 | 说明 |
|------|------|------|
| **用户体验提升** | ⭐⭐⭐⭐ | 减少困惑和重复查询 |
| **系统智能化** | ⭐⭐⭐⭐⭐ | AI 验证增强准确性 |
| **实现复杂度** | ⭐⭐⭐ | 中等，约 6 小时 |
| **维护成本** | ⭐⭐ | 低，逻辑清晰 |
| **MVP 必要性** | ⭐ | 非必需，增强功能 |

**结论**: 如果追求更智能的用户体验，建议实现 **阶段 1 + 阶段 2** (基础验证 + 集成)，约 4 小时。AI 语义验证 (阶段 3) 可作为未来增强。

---

## 📚 相关文档

- [spec.md - US5](../001-postgres-mcp/spec.md#用户故事-5)
- [tasks.md - T079-T081](../001-postgres-mcp/tasks.md)
- [plan.md](../001-postgres-mcp/plan.md)

---

**准备好实现了吗？** 如需开始实现，我可以：
1. 创建数据模型 (`validation.py`)
2. 实现 `ResultValidator` (基础验证)
3. 编写单元测试
4. 集成到 `QueryExecutor`
