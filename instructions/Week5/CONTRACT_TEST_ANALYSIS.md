# 契约测试结果分析报告

**测试时间**: 2026-01-29 06:18 - 06:32  
**测试用例**: 70 个 (L1-L5 + S1)  
**通过率**: 18/70 (25.7%) ❌

---

## 🔍 问题根因分析

### 主要问题：模式匹配过于严格

**观察到的失败模式**:

1. **L1.2 失败**: 
   - 期望: `SELECT .* FROM products WHERE .* price\s*>\s*100`
   - 生成: `SELECT * FROM products WHERE price > 100 LIMIT 1000;`
   - **问题**: AI 自动添加了 `LIMIT 1000`（这是安全的、好的实践！）

2. **L1.8 失败**:
   - 错误: "Security violation: Dangerous SQL detected: CREATE statement"
   - 生成: `SELECT * FROM customers WHERE created_at >= NOW() - INTERVAL '30 days' LIMIT 100...`
   - **问题**: 误报！`CREATED_AT` 字段名包含 "CREATE" 导致误判

3. **L1.10 失败**:
   - 生成: `SELECT COUNT(*) AS product_count FROM products;`
   - **问题**: AI 添加了有意义的别名 `AS product_count`（这是好的实践！）

### 核心问题总结

| 问题类别 | 影响 | 示例 |
|---------|------|------|
| **LIMIT 子句** | 高 | AI 自动添加 `LIMIT 1000` 保护，但测试期望没有 |
| **别名 (AS)** | 中 | AI 添加有意义的列别名，但测试模式不匹配 |
| **安全验证器误报** | 高 | 字段名 `created_at` 触发 CREATE 关键字检查 |
| **模式匹配太严格** | 高 | 正则表达式不够宽松，无法匹配语义等价的 SQL |

---

## 📊 详细统计

### 按类别统计

| 类别 | 通过 | 失败 | 通过率 |
|------|------|------|--------|
| L1 基础查询 | 6/15 | 9/15 | 40% |
| L2 多表关联 | 6/15 | 9/15 | 40% |
| L3 聚合分析 | 3/12 | 9/12 | 25% |
| L4 复杂逻辑 | 2/10 | 8/10 | 20% |
| L5 高级特性 | 0/8  | 8/8  | 0% |
| S1 安全测试 | 1/10 | 9/10 | 10% |

### 失败原因分类

| 原因 | 数量 | 占比 |
|------|------|------|
| SQL 模式不匹配 | 45 | 86.5% |
| 安全验证误报 | 6 | 11.5% |
| 其他 | 1 | 2% |

---

## ✅ 修复方案

### 1. 修复安全验证器（高优先级）

**问题**: `created_at` 等字段名触发 CREATE 关键字检查

**修复**: 改进 `SQLValidator.validate_security()` 的关键字检测

```python
# 当前实现（太简单）
dangerous_keywords = ["INSERT", "UPDATE", "DELETE", "DROP", "CREATE", ...]
if any(keyword in sql.upper() for keyword in dangerous_keywords):
    return False, f"Dangerous SQL detected: {keyword} statement"

# 改进方案：使用 SQL 解析器
import sqlglot
try:
    parsed = sqlglot.parse_one(sql, dialect="postgres")
    # 检查 AST 的根节点类型
    if not isinstance(parsed, sqlglot.exp.Select):
        return False, "Only SELECT queries are allowed"
except:
    return False, "Invalid SQL syntax"
```

### 2. 放宽模式匹配（高优先级）

**问题**: 正则表达式太严格，无法匹配语义等价的 SQL

**修复选项**:

#### 选项 A: 改进正则表达式（推荐 ⭐）

```python
# L1.2: 显示价格大于 100 的产品
# 当前
expected_sql=r"SELECT .* FROM products WHERE .* price\s*>\s*100"

# 改进（允许 LIMIT 子句）
expected_sql=r"SELECT .* FROM products WHERE .* price\s*>\s*100(\s+LIMIT\s+\d+)?"

# L1.10: 统计产品数量
# 当前
expected_sql=r"SELECT COUNT\(\*\) FROM products"

# 改进（允许别名）
expected_sql=r"SELECT COUNT\(\*\)(\s+AS\s+\w+)? FROM products"
```

#### 选项 B: 改用 SQL 语义验证（最佳，但工作量大）

```python
def validate_sql_semantically(generated_sql: str, expected_elements: dict) -> bool:
    """
    Validate SQL based on semantic elements rather than exact pattern.
    
    expected_elements = {
        "tables": ["products"],
        "where_conditions": ["price > 100"],
        "order_by": None,
        "group_by": None,
        "joins": [],
    }
    """
    parsed = sqlglot.parse_one(generated_sql, dialect="postgres")
    
    # 验证表名
    actual_tables = [t.name for t in parsed.find_all(sqlglot.exp.Table)]
    if set(expected_elements["tables"]) != set(actual_tables):
        return False
    
    # 验证 WHERE 条件（简化版）
    # ...
    
    return True
```

#### 选项 C: 使用验证规则而非模式匹配（折中方案）

```python
# 当前测试用例
TestCase(
    id="L1.2",
    natural_language="显示价格大于 100 的产品",
    expected_sql=r"SELECT .* FROM products WHERE .* price\s*>\s*100",
    validation_rules=["has_where_clause", "uses_comparison"],
)

# 改进：移除 expected_sql，只用 validation_rules
TestCase(
    id="L1.2",
    natural_language="显示价格大于 100 的产品",
    validation_rules=[
        "has_where_clause",
        "uses_comparison",
        "references_table:products",
        "references_column:price",
        "uses_operator:>",
        "value_matches:100",
    ],
)
```

### 3. 改进 AI Prompt（中优先级）

**问题**: AI 添加了我们不期望的（但合理的）元素

**修复**: 在 prompt 中明确指定规则

```python
# 在 PromptBuilder 中添加
system_prompt += """
SQL Generation Rules:
1. Do NOT add LIMIT clause unless explicitly requested
2. Do NOT add column aliases unless explicitly requested
3. Use exact column/table names from schema
4. Follow the natural language description exactly
5. Keep the query as simple as possible
"""
```

---

## 🎯 推荐执行顺序

### 短期修复（1-2小时）

1. **修复安全验证器误报** ⭐ 最重要
   - 文件: `src/postgres_mcp/core/sql_validator.py`
   - 改用 SQLGlot AST 验证而非简单字符串匹配

2. **放宽关键模式匹配**
   - 文件: `tests/contract/test_l1_basic.py` 等
   - 在正则表达式中添加 `(\s+LIMIT\s+\d+)?` 等可选项

3. **重新运行测试**
   - 预期提升通过率到 60-70%

### 中期优化（3-4小时）

4. **改进 Prompt 工程**
   - 文件: `src/postgres_mcp/ai/prompt_builder.py`
   - 添加更严格的生成规则

5. **实现语义验证**
   - 新文件: `tests/contract/semantic_validator.py`
   - 使用 SQLGlot 进行 AST 对比

6. **重新运行测试**
   - 预期提升通过率到 80-90%

### 长期改进（可选）

7. **完善测试用例**
   - 根据实际 AI 行为调整期望
   - 添加更多边界情况

8. **建立基准数据集**
   - 记录每次测试的准确率变化
   - 跟踪 prompt 改进效果

---

## 💡 关键洞察

### AI 生成的 SQL 质量实际上不错！

虽然通过率只有 25.7%，但仔细分析发现：

1. **大多数失败是测试问题，不是 AI 问题**
   - AI 添加 `LIMIT 1000` 是安全的好实践
   - AI 添加有意义的别名是可读性好实践
   - AI 生成的 SQL 在语义上通常是正确的

2. **安全验证器过于简单**
   - 字符串匹配导致大量误报
   - 需要改用 AST 级别的验证

3. **测试用例需要更新**
   - 正则表达式太严格
   - 应该允许语义等价的变体

### 真实准确率估算

如果修复上述问题，**真实准确率可能在 70-85%** 之间，这对于 MVP 来说是可接受的。

---

## 📋 下一步行动

请选择：

**选项 1: 快速修复（推荐）**
```bash
# 修复安全验证器 + 放宽模式匹配
# 预计 1-2 小时
# 预期通过率提升到 60-70%
```

**选项 2: 完整优化**
```bash
# 包括 prompt 改进 + 语义验证
# 预计 4-5 小时
# 预期通过率提升到 80-90%
```

**选项 3: 当前状态可接受**
```bash
# 文档化当前测试结果
# 标注为 "已知问题"
# 继续其他功能开发
```

---

**报告生成时间**: 2026-01-29
**下次测试**: 修复后重新运行
