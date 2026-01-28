# Contract Testing Framework

自动化契约测试框架，用于验证 PostgreSQL MCP 服务器的自然语言到 SQL 转换准确性。

## 目录结构

```
tests/contract/
├── __init__.py                 # 模块初始化
├── test_framework.py           # 测试框架基础类
├── test_l1_basic.py           # L1 基础查询测试（15个用例）
├── test_l2_join.py            # L2 多表关联测试（15个用例）
├── test_l3_aggregate.py       # L3 聚合分析测试（12个用例）
├── test_l4_complex.py         # L4 复杂逻辑测试（10个用例）
├── test_l5_advanced.py        # L5 高级特性测试（8个用例）
├── run_tests.py               # 测试执行器
└── README.md                  # 本文档
```

## 测试分类

根据 `specs/001-postgres-mcp/test-plan.md` 定义：

| 分类 | 难度 | 数量 | 状态 |
|------|------|------|------|
| **L1 基础查询** | 简单 | 15 | ✅ 已实现 |
| **L2 多表关联** | 中等 | 15 | ✅ 已实现 |
| **L3 聚合分析** | 中等 | 12 | ✅ 已实现 |
| **L4 复杂逻辑** | 困难 | 10 | ✅ 已实现 |
| **L5 高级特性** | 困难 | 8 | ✅ 已实现 |
| **S1 安全测试** | 安全 | 10 | ⏸️  待实现 |

**当前进度**: 60/70 测试用例已实现 (86%)

## 快速开始

### 前置条件

1. **启动测试数据库**:
```bash
cd ~/Documents/VibeCoding/Week5
make up
```

2. **验证数据库连接**:
```bash
make test-all
```

3. **配置环境**:
```bash
# 设置数据库密码
export TEST_DB_PASSWORD="testpass123"

# 设置 OpenAI API Key
export OPENAI_API_KEY="sk-..."

# 或使用阿里百炼
export DASHSCOPE_API_KEY="sk-..."
```

### 运行测试

#### 方式 1: 使用测试执行器（推荐）

```bash
cd ~/Documents/VibeCoding/Week5
source .venv/bin/activate

# 运行所有契约测试
python -m tests.contract.run_tests
```

#### 方式 2: 使用 Pytest

```bash
cd ~/Documents/VibeCoding/Week5
source .venv/bin/activate

# 运行 L1 基础查询测试
pytest tests/contract/test_l1_basic.py -v

# 运行所有契约测试
pytest tests/contract/ -v

# 生成详细报告
pytest tests/contract/ -v --tb=short
```

## 测试框架说明

### 核心组件

#### 1. `TestCase` 数据类
定义单个测试用例的结构：
- `id`: 测试用例标识符（如 "L1.1"）
- `category`: 测试分类（L1/L2/L3/L4/L5/S1）
- `natural_language`: 自然语言查询输入
- `database`: 目标数据库名称
- `expected_sql`: 期望的 SQL 模式（正则表达式）
- `validation_rules`: 验证规则列表
- `description`: 测试描述

#### 2. `TestResult` 数据类
记录测试执行结果：
- `test_id`: 测试用例 ID
- `status`: 测试状态（PASSED/FAILED/SKIPPED）
- `generated_sql`: 生成的 SQL 查询
- `execution_time_ms`: 执行时间（毫秒）
- `error_message`: 错误信息（如果失败）
- `validation_details`: 详细验证结果

#### 3. `SQLValidator` 类
SQL 验证器，提供：
- `matches_pattern()`: 正则模式匹配
- `validate_security()`: 安全性验证
- `check_validation_rules()`: 自定义规则验证

#### 4. `TestReport` 类
测试报告生成器，支持：
- 结果聚合
- 统计汇总
- 文本格式报告

### 验证规则

支持的验证规则：
- `has_where_clause`: 包含 WHERE 子句
- `has_order_by`: 包含 ORDER BY 子句
- `has_limit`: 包含 LIMIT 子句
- `has_group_by`: 包含 GROUP BY 子句
- `has_join`: 包含 JOIN 子句
- `uses_aggregate`: 使用聚合函数（COUNT/SUM/AVG等）
- 自定义规则：可通过扩展 `SQLValidator.check_validation_rules()` 添加

## L1 基础查询测试

已实现的 15 个测试用例：

1. **L1.1**: 简单查询所有记录
2. **L1.2**: 带条件过滤
3. **L1.3**: 模糊搜索（LIKE/ILIKE）
4. **L1.4**: 排序查询（ORDER BY）
5. **L1.5**: 限制结果数量（LIMIT）
6. **L1.6**: 多条件过滤（AND）
7. **L1.7**: OR 条件或 IN 子句
8. **L1.8**: 日期范围查询（INTERVAL）
9. **L1.9**: NULL 值检查
10. **L1.10**: 计数查询（COUNT）
11. **L1.11**: 去重查询（DISTINCT）
12. **L1.12**: BETWEEN 范围查询
13. **L1.13**: 特定列查询
14. **L1.14**: 布尔字段查询
15. **L1.15**: 枚举类型查询

## L2 多表关联测试

已实现的 15 个测试用例：

1. **L2.1**: 简单内连接（INNER JOIN）
2. **L2.2**: 左连接带计数（LEFT JOIN + COUNT）
3. **L2.3**: 三表关联
4. **L2.4**: 自连接（Self JOIN）
5. **L2.5**: 多对多关系
6. **L2.6**: 带条件的连接
7. **L2.7**: 聚合与连接（SUM + JOIN）
8. **L2.8**: 视图查询
9. **L2.9**: 标量子查询（Scalar Subquery）
10. **L2.10**: IN 子查询或 JOIN
11. **L2.11**: NOT IN 或 LEFT JOIN + NULL
12. **L2.12**: EXISTS 子查询
13. **L2.13**: 笛卡尔积（CROSS JOIN）
14. **L2.14**: 集合并集（UNION）
15. **L2.15**: 复杂四表关联

## L3 聚合分析测试

已实现的 12 个测试用例：

1. **L3.1**: 基础计数（COUNT + GROUP BY）
2. **L3.2**: 求和聚合（SUM + LEFT JOIN）
3. **L3.3**: 平均值（AVG）
4. **L3.4**: 最大最小值（MAX + MIN）
5. **L3.5**: HAVING 过滤
6. **L3.6**: 多重聚合（COUNT + AVG + SUM）
7. **L3.7**: 日期分组（DATE_TRUNC）
8. **L3.8**: 条件聚合（CASE WHEN）
9. **L3.9**: 百分比计算（子查询）
10. **L3.10**: 排名查询（ORDER BY + LIMIT）
11. **L3.11**: 窗口函数排名（ROW_NUMBER + PARTITION BY）
12. **L3.12**: 累计计算（SUM OVER）

## L4 复杂逻辑测试

已实现的 10 个测试用例：

1. **L4.1**: 递归查询（WITH RECURSIVE）- 嵌套评论
2. **L4.2**: JSONB 查询（@> 或 ->> 操作符）
3. **L4.3**: 复杂时间计算（INTERVAL）
4. **L4.4**: 全文搜索（to_tsvector）或 ILIKE
5. **L4.5**: 复杂 CASE 表达式（价格分级）
6. **L4.6**: 数组/多对多关系（HAVING COUNT）
7. **L4.7**: 关联子查询（排名计算）
8. **L4.8**: 集合运算（INTERSECT）
9. **L4.9**: 集合运算（EXCEPT 差集）
10. **L4.10**: 多级聚合（HAVING 子查询）

## L5 高级特性测试

已实现的 8 个测试用例：

1. **L5.1**: CTE 公共表表达式
2. **L5.2**: 多个 CTE + 窗口函数
3. **L5.3**: LAG/LEAD 窗口函数
4. **L5.4**: FILTER 聚合
5. **L5.5**: LATERAL JOIN
6. **L5.6**: GROUPING SETS
7. **L5.7**: generate_series 生成系列
8. **L5.8**: STRING_AGG 字符串聚合

## 测试报告

测试执行后会生成报告文件：`test_reports/contract_test_report.txt`

报告包含：
- 总体统计（通过率、失败率）
- 按分类的测试结果
- 失败用例的详细错误信息

## 扩展测试

### 添加新测试用例

1. 在相应的测试文件中添加 `TestCase` 定义
2. 更新测试列表（如 `L1_TEST_CASES`）
3. 运行测试验证

示例：
```python
from tests.contract.test_framework import TestCase, TestCategory

NEW_TEST = TestCase(
    id="L1.16",
    category=TestCategory.L1_BASIC,
    natural_language="你的自然语言查询",
    database="small",
    expected_sql=r"SELECT .* FROM your_table",
    validation_rules=["has_where_clause"],
    description="测试描述",
)
```

### 添加新测试分类

1. 创建新的测试文件（如 `test_l2_join.py`）
2. 定义测试用例列表
3. 在 `run_tests.py` 中导入并执行
4. 更新本 README

## 成功标准

根据测试计划要求：

| 分类 | 目标准确率 |
|------|------------|
| L1 基础查询 | ≥95% |
| L2 多表关联 | ≥90% |
| L3 聚合分析 | ≥85% |
| L4 复杂逻辑 | ≥75% |
| L5 高级特性 | ≥70% |
| S1 安全测试 | 100% |

**总体目标**: ≥90% 准确率，100% 安全测试通过

## 故障排查

### 常见问题

1. **数据库连接失败**
   - 确认测试数据库已启动：`make up`
   - 检查环境变量：`echo $TEST_DB_PASSWORD`
   - 验证配置文件：`cat config/config.yaml`

2. **OpenAI API 错误**
   - 确认 API Key 有效
   - 检查网络连接
   - 查看 API 配额和限制

3. **SQL 模式不匹配**
   - 检查正则表达式是否正确
   - 查看生成的 SQL（在错误信息中）
   - 调整 `expected_sql` 模式

4. **导入错误**
   - 确认虚拟环境已激活
   - 重新安装依赖：`pip install -e .`

## 下一步计划

- [x] 实现 L1 基础查询测试（15个用例）
- [x] 实现 L2 多表关联测试（15个用例）
- [x] 实现 L3 聚合分析测试（12个用例）
- [x] 实现 L4 复杂逻辑测试（10个用例）
- [x] 实现 L5 高级特性测试（8个用例）
- [ ] 实现 S1 安全测试（10个用例）
- [ ] 添加 HTML/JSON 格式报告
- [ ] 集成到 CI/CD 流程
- [ ] 添加性能基准测试

## 参考文档

- [测试计划](../../specs/001-postgres-mcp/test-plan.md)
- [项目 README](../../Week5/README.md)
- [当前状态](../../specs/001-postgres-mcp/CURRENT_STATUS.md)

---

**创建日期**: 2026-01-29  
**最后更新**: 2026-01-29  
**版本**: 0.1.0
