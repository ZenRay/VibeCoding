# PostgreSQL MCP Server - 配置指南

本文档详细说明如何配置和扩展 PostgreSQL MCP Server 的各个组件。

---

## 📋 目录

1. [基础配置](#基础配置)
2. [查询模板](#查询模板)
3. [安全规则](#安全规则)
4. [AI Prompt 规则](#ai-prompt-规则)
5. [契约测试](#契约测试)
6. [扩展开发](#扩展开发)

---

## 基础配置

### 配置文件: `config/config.yaml`

```yaml
# 数据库配置
databases:
  my_database:                    # 数据库标识符
    host: localhost              # 数据库主机
    port: 5432                   # 端口
    database: mydb               # 数据库名
    user: postgres               # 用户名
    password_env_var: DB_PASSWORD  # 密码环境变量
    min_pool_size: 2             # 最小连接池大小
    max_pool_size: 10            # 最大连接池大小

# OpenAI 配置
openai:
  # 方式 1: 直接配置 API Key (开发推荐)
  api_key: "sk-your-key"
  
  # 方式 2: 使用环境变量 (生产推荐)
  # api_key: null
  # api_key_env_var: "OPENAI_API_KEY"
  
  # AI 服务选择
  
  # OpenAI (默认)
  model: "gpt-4o-mini-2024-07-18"
  base_url: null
  
  # 阿里百炼 / 通义千问 (国内推荐)
  # model: "qwen-turbo-latest"
  # base_url: "https://dashscope.aliyuncs.com/compatible-mode/v1"
  
  temperature: 0.0              # 生成温度 (0=确定性, 1=随机性)
  max_tokens: 2000              # 最大token数
  timeout: 30.0                 # 请求超时 (秒)

# 代理配置 (可选)
# proxy:
#   http: "http://localhost:7890"
#   https: "http://localhost:7890"

# 日志配置
logging:
  level: INFO                   # 日志级别: DEBUG, INFO, WARNING, ERROR
  history_dir: "logs/history"   # 查询历史目录
  max_file_size_mb: 100         # 单个日志文件最大大小
  retention_days: 30            # 日志保留天数
```

### 环境变量

```bash
# 必需
export DB_PASSWORD="your_database_password"

# 如果使用环境变量方式配置 API Key
export OPENAI_API_KEY="sk-your-openai-key"

# 代理 (可选)
export HTTP_PROXY="http://localhost:7890"
export HTTPS_PROXY="http://localhost:7890"
```

---

## 查询模板

查询模板提供 AI 服务不可用时的降级方案。模板位于 `src/postgres_mcp/templates/queries/`。

### 模板结构

每个模板是一个 YAML 文件，包含：

```yaml
# src/postgres_mcp/templates/queries/my_query.yaml

name: "my_query"                 # 模板名称 (必需)
description: "查询描述"           # 描述 (必需)
category: "basic"                # 类别: basic, aggregate, join, filter
tags:                            # 标签列表 (用于匹配)
  - "select"
  - "all"
  - "显示"
  - "所有"
patterns:                        # 匹配模式 (正则表达式)
  - "^显示所有.*"
  - "^查询.*所有记录"
  - "^list all.*"
sql_template: |                  # SQL 模板 (支持变量)
  SELECT * FROM {table_name}
  LIMIT {limit};
variables:                       # 变量定义
  table_name:
    type: "identifier"           # 类型: identifier, integer, string
    required: true               # 是否必需
    description: "表名"
  limit:
    type: "integer"
    required: false
    default: 100                 # 默认值
    description: "返回行数限制"
examples:                        # 示例
  - natural_language: "显示所有用户"
    database: "mydb"
    result_sql: "SELECT * FROM users LIMIT 100;"
  - natural_language: "list all products"
    database: "mydb"
    result_sql: "SELECT * FROM products LIMIT 100;"
```

### 现有模板

系统内置 15 个模板，涵盖常见查询场景：

| 模板文件 | 类别 | 说明 |
|---------|------|------|
| `select_all.yaml` | basic | 查询所有记录 |
| `count_records.yaml` | aggregate | 统计记录数 |
| `filter_by_condition.yaml` | filter | 条件筛选 |
| `sort_records.yaml` | basic | 排序查询 |
| `aggregate_sum.yaml` | aggregate | 求和聚合 |
| `aggregate_avg.yaml` | aggregate | 平均值聚合 |
| `aggregate_max_min.yaml` | aggregate | 最大/最小值 |
| `group_by.yaml` | aggregate | 分组聚合 |
| `simple_join.yaml` | join | 简单 JOIN |
| `left_join.yaml` | join | LEFT JOIN |
| `filter_null.yaml` | filter | NULL 值筛选 |
| `filter_range.yaml` | filter | 范围筛选 |
| `filter_like.yaml` | filter | 模糊匹配 |
| `distinct_values.yaml` | basic | 去重查询 |
| `top_n_records.yaml` | basic | TOP N 查询 |

### 添加新模板

1. **创建 YAML 文件**:
   ```bash
   touch src/postgres_mcp/templates/queries/my_custom_query.yaml
   ```

2. **填写模板内容** (参考上面的结构)

3. **测试模板**:
   ```bash
   pytest tests/unit/test_template_loader.py -v
   pytest tests/unit/test_template_matcher.py -v
   ```

4. **验证匹配**:
   ```python
   from postgres_mcp.core.template_matcher import TemplateMatcher
   from postgres_mcp.utils.template_loader import TemplateLoader
   
   loader = TemplateLoader()
   templates = loader.load_all()
   matcher = TemplateMatcher(templates)
   
   # 测试匹配
   result = matcher.match("显示所有用户", "mydb", {})
   print(result.sql if result else "未匹配")
   ```

---

## 安全规则

安全验证确保只允许安全的只读查询。配置位于 `src/postgres_mcp/core/sql_validator.py`。

### 当前规则

#### 1. 允许的语句类型

```python
allowed_types = (
    exp.Select,      # SELECT 查询
    exp.Union,       # UNION 集合操作
    exp.Intersect,   # INTERSECT 交集
    exp.Except,      # EXCEPT 差集
)
```

#### 2. 禁止的操作

```python
dangerous_operations = (
    exp.Insert,      # INSERT - 插入数据
    exp.Update,      # UPDATE - 更新数据
    exp.Delete,      # DELETE - 删除数据
    exp.Drop,        # DROP - 删除对象
    exp.Create,      # CREATE - 创建对象
    exp.Alter,       # ALTER - 修改对象
    exp.Command,     # 命令 (如 COPY)
    exp.Merge,       # MERGE - 合并操作
)
```

#### 3. 危险函数

```python
dangerous_functions = [
    "pg_read_file",      # 读取文件
    "pg_ls_dir",         # 列出目录
    "pg_read_binary_file",  # 读取二进制文件
    "copy_from",         # 从文件导入
    "copy_to",           # 导出到文件
]
```

### 自定义安全规则

如果需要调整安全策略（例如允许 CTEs 或窗口函数）：

1. **修改 `sql_validator.py`**:
   ```python
   # 允许新的语句类型
   allowed_types = (
       exp.Select,
       exp.Union,
       exp.Intersect,
       exp.Except,
       exp.With,  # 新增: 允许 WITH CTE
   )
   ```

2. **添加新的检查**:
   ```python
   # 在 validate_security() 中添加
   if has_excessive_complexity(statement):
       return False, "Query too complex"
   ```

3. **测试验证**:
   ```bash
   pytest tests/unit/test_sql_validator.py -v
   ```

### 测试安全规则

```python
from postgres_mcp.core.sql_validator import SQLValidator

validator = SQLValidator()

# 测试 SELECT (应该通过)
is_safe, error = validator.validate_security("SELECT * FROM users")
assert is_safe

# 测试 UNION (应该通过)
is_safe, error = validator.validate_security(
    "SELECT id FROM users UNION SELECT id FROM orders"
)
assert is_safe

# 测试 INSERT (应该拒绝)
is_safe, error = validator.validate_security(
    "INSERT INTO users VALUES (1, 'test')"
)
assert not is_safe
assert "Insert" in error
```

---

## AI Prompt 规则

AI Prompt 构建器控制如何指导 AI 生成 SQL。配置位于 `src/postgres_mcp/ai/prompt_builder.py`。

### 当前 Prompt 结构

```python
system_prompt = """
You are a PostgreSQL SQL query expert...

RULES:
1. Generate ONLY valid PostgreSQL SQL queries
2. Use ONLY SELECT statements (read-only)
3. Reference ONLY tables and columns from the provided schema
4. ALWAYS add LIMIT clause (default 1000) unless user specifies
5. Use explicit JOIN syntax (INNER JOIN, LEFT JOIN, etc.)
6. Prefer column aliases with AS for clarity
7. Return SQL in a single line without extra formatting

SECURITY:
- NO INSERT, UPDATE, DELETE, DROP, CREATE, ALTER
- NO dangerous functions: pg_read_file, pg_ls_dir, copy_from
- UNION, INTERSECT, EXCEPT are ALLOWED (read-only set operations)
"""
```

### 自定义 Prompt

修改 `PromptBuilder` 类以添加新规则：

```python
class PromptBuilder:
    def build_system_prompt(self) -> str:
        base_rules = """
        You are a PostgreSQL expert...
        """
        
        # 添加自定义规则
        custom_rules = """
        CUSTOM RULES:
        - Prefer window functions for ranking queries
        - Use CTEs for complex subqueries
        - Add DISTINCT when appropriate
        """
        
        return base_rules + custom_rules
```

### Few-Shot 示例

添加示例可以提高生成质量：

```python
examples = """
EXAMPLES:
1. Natural: "显示销量最高的10个产品"
   SQL: SELECT product_id, name, SUM(quantity) as total_sales 
        FROM order_items 
        GROUP BY product_id, name 
        ORDER BY total_sales DESC 
        LIMIT 10;

2. Natural: "查询从未下单的客户"
   SQL: SELECT c.customer_id, c.name 
        FROM customers c 
        LEFT JOIN orders o ON c.customer_id = o.customer_id 
        WHERE o.order_id IS NULL 
        LIMIT 1000;
"""
```

---

## 契约测试

契约测试验证自然语言到 SQL 转换的准确性。测试位于 `tests/contract/`。

### 测试结构

```
tests/contract/
├── test_framework.py          # 测试框架
├── test_l1_basic.py           # L1 基础查询 (15个)
├── test_l2_join.py            # L2 多表JOIN (15个)
├── test_l3_aggregate.py       # L3 聚合分析 (12个)
├── test_l4_complex.py         # L4 复杂逻辑 (10个)
├── test_l5_advanced.py        # L5 高级特性 (8个)
├── test_s1_security.py        # S1 安全测试 (10个)
├── run_tests.py               # 主测试执行器
└── run_contract_tests.sh      # 测试脚本
```

### 添加新测试用例

1. **选择测试类别**:
   - L1: 基础查询 (单表, WHERE, ORDER BY, LIMIT)
   - L2: 多表 JOIN
   - L3: 聚合 (GROUP BY, HAVING, 聚合函数)
   - L4: 复杂逻辑 (子查询, CASE, UNION)
   - L5: 高级特性 (窗口函数, CTE, JSON)
   - S1: 安全测试 (SQL 注入防护)

2. **添加测试用例**:
   ```python
   # tests/contract/test_l1_basic.py
   
   TestCase(
       id="L1.16",
       category=TestCategory.L1_BASIC,
       natural_language="查询用户名包含'admin'的记录",
       database="ecommerce_small",
       expected_sql=r"SELECT .* FROM users WHERE.*?username.*?LIKE.*?'%admin%'",
       validation_rules=["has_where_clause", "uses_like"],
       description="LIKE pattern matching",
   )
   ```

3. **运行测试**:
   ```bash
   cd tests/contract
   ./run_contract_tests.sh sample  # 快速验证
   ./run_contract_tests.sh full    # 完整测试
   ```

### 正则表达式最佳实践

- **使用非贪婪匹配**: `.*?` 而不是 `.*`
- **归一化SQL**: 测试框架会自动将多行SQL压缩为单行
- **允许变体**: 
  ```python
  # 好: 允许多种等价写法
  r"WHERE.*?(price BETWEEN|price.*?>=.*?AND.*?price.*?<=)"
  
  # 差: 过于严格
  r"WHERE price BETWEEN 50 AND 200"
  ```

### 验证规则

可用的验证规则 (`validation_rules`):

```python
validation_rules = [
    "has_where_clause",    # 有 WHERE 子句
    "has_join",            # 有 JOIN
    "has_group_by",        # 有 GROUP BY
    "has_having",          # 有 HAVING
    "has_order_by",        # 有 ORDER BY
    "has_limit",           # 有 LIMIT
    "uses_aggregate",      # 使用聚合函数
    "uses_distinct",       # 使用 DISTINCT
    "uses_and",            # 使用 AND
    "uses_or",             # 使用 OR
    "uses_like",           # 使用 LIKE
    "uses_in",             # 使用 IN
    "uses_between",        # 使用 BETWEEN
    "uses_is_null",        # 使用 IS NULL
    "uses_interval",       # 使用 INTERVAL
]
```

---

## 扩展开发

### 添加新的 MCP Tool

1. **在 `src/postgres_mcp/mcp/tools.py` 中添加**:
   ```python
   @mcp.tool()
   async def my_custom_tool(
       parameter1: str,
       parameter2: int = 10
   ) -> str:
       """
       Tool description here.
       
       Args:
           parameter1: Description
           parameter2: Description (default: 10)
       
       Returns:
           Result description
       """
       # 实现逻辑
       return result
   ```

2. **添加单元测试**:
   ```python
   # tests/unit/test_my_tool.py
   
   @pytest.mark.asyncio
   async def test_my_custom_tool():
       result = await my_custom_tool("test", 20)
       assert result == expected
   ```

3. **更新文档**:
   - 在 `README.md` 的 "MCP Tools" 部分添加说明
   - 更新 `specs/001-postgres-mcp/spec.md`

### 添加新的 MCP Resource

1. **在 `src/postgres_mcp/mcp/resources.py` 中添加**:
   ```python
   @mcp.resource("custom://resource/{param}")
   async def my_custom_resource(
       uri: str,
       param: str
   ) -> str:
       """Resource description"""
       # 实现逻辑
       return content
   ```

2. **测试访问**:
   ```bash
   # 在 Claude Desktop 中测试
   # Resource URI: custom://resource/value
   ```

### 性能优化

1. **Schema 缓存**:
   - 调整 `schema_cache.py` 中的缓存策略
   - 修改自动刷新间隔 (`auto_refresh_interval`)

2. **连接池**:
   - 调整 `config.yaml` 中的 `min_pool_size` 和 `max_pool_size`
   - 监控连接池使用情况

3. **查询超时**:
   - 修改 `openai.timeout` 控制 AI 请求超时
   - 修改 `query_executor.py` 中的数据库查询超时

---

## 常见问题

### Q: 如何添加对新数据库的支持？

A: 在 `config/config.yaml` 中添加新的数据库配置：

```yaml
databases:
  new_database:
    host: newhost
    port: 5432
    database: newdb
    user: newuser
    password_env_var: NEW_DB_PASSWORD
```

### Q: 如何禁用某个查询模板？

A: 删除或重命名对应的 YAML 文件（添加 `.disabled` 后缀）。

### Q: 如何调整 AI 生成的 SQL 风格？

A: 修改 `src/postgres_mcp/ai/prompt_builder.py` 中的 `system_prompt`。

### Q: 契约测试失败怎么办？

A: 
1. 查看详细错误: `cat /tmp/contract_test_results_full.txt`
2. 检查生成的 SQL 是否语义正确
3. 如果 SQL 正确，调整测试用例的 `expected_sql` 正则表达式

---

## 相关文档

- [README.md](./README.md) - 项目概览
- [specs/001-postgres-mcp/CURRENT_STATUS.md](../specs/001-postgres-mcp/CURRENT_STATUS.md) - 项目状态
- [specs/001-postgres-mcp/spec.md](../specs/001-postgres-mcp/spec.md) - 功能规范
- [tests/contract/README.md](./tests/contract/README.md) - 契约测试文档

---

**最后更新**: 2026-01-29  
**维护**: VibeCoding Team
