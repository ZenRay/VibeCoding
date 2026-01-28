# 快速开始：PostgreSQL 自然语言查询 MCP 服务器

**版本**: 0.1.0
**更新日期**: 2026-01-28

本指南将帮助您在 5 分钟内启动并运行 PostgreSQL MCP 服务器。

---

## 前置要求

- Python 3.12+
- UV 包管理器
- PostgreSQL 12.0+ 数据库（至少一个）
- OpenAI API 密钥
- Docker 2.x（可选，用于容器化部署）

---

## 1. 安装（2 分钟）

```bash
# 克隆仓库
cd ~/Documents/VibeCoding/Week5

# 创建虚拟环境
uv venv
source .venv/bin/activate

# 安装依赖
uv pip install -e ".[dev]"

# 验证安装
python -m postgres_mcp --version
```

---

## 2. 配置（2 分钟）

### 创建配置文件

```bash
# 复制示例配置
cp config/config.example.yaml config/config.yaml
```

### 编辑配置

```yaml
# config/config.yaml
server:
  name: "postgres-mcp"
  version: "0.1.0"

databases:
  - name: "mydb"
    host: "localhost"
    port: 5432
    database: "myapp_db"
    user: "readonly_user"
    password_env_var: "MYDB_PASSWORD"  # 密码从环境变量读取
    ssl_mode: "prefer"

default_database: "mydb"

openai:
  api_key_env_var: "OPENAI_API_KEY"
  model: "gpt-4o-mini-2024-07-18"
```

### 设置环境变量

```bash
# 方法 1: 导出环境变量
export MYDB_PASSWORD="your_database_password"
export OPENAI_API_KEY="sk-..."

# 方法 2: 使用 .env 文件
cat > .env << EOF
MYDB_PASSWORD=your_database_password
OPENAI_API_KEY=sk-...
EOF

# 加载 .env
source .env
```

---

## 3. 启动服务器（1 分钟）

```bash
# 启动 MCP 服务器（stdio 模式）
python -m postgres_mcp

# 或使用 UV 运行
uv run python -m postgres_mcp

# 带调试日志
POSTGRES_MCP_LOG_LEVEL=DEBUG python -m postgres_mcp
```

服务器启动后会：
1. 加载配置文件
2. 连接所有数据库
3. 缓存 database schemas
4. 等待 MCP 客户端连接（通过 stdio）

---

## 4. 配置 MCP 客户端

### Claude Desktop

编辑 `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "postgres-mcp": {
      "command": "uv",
      "args": [
        "--directory",
        "/Users/你的用户名/Documents/VibeCoding/Week5",
        "run",
        "python",
        "-m",
        "postgres_mcp"
      ],
      "env": {
        "MYDB_PASSWORD": "your_database_password",
        "OPENAI_API_KEY": "sk-..."
      }
    }
  }
}
```

### Cursor/其他 MCP 客户端

参考各客户端的 MCP 服务器配置文档。

---

## 5. 使用示例

### 示例 1: 生成 SQL（不执行）

**MCP 工具调用**:

```json
{
  "tool": "generate_sql",
  "arguments": {
    "natural_language": "显示所有活跃的用户"
  }
}
```

**响应**:

```json
{
  "sql": "SELECT id, username, email, created_at FROM users WHERE active = true LIMIT 1000;",
  "validated": true,
  "warnings": [],
  "explanation": "查询 users 表中 active 字段为 true 的所有记录",
  "generation_method": "ai_generated"
}
```

### 示例 2: 执行查询

**MCP 工具调用**:

```json
{
  "tool": "execute_query",
  "arguments": {
    "natural_language": "统计每个类别的产品数量",
    "database": "mydb"
  }
}
```

**响应**:

```json
{
  "sql": "SELECT category, COUNT(*) as product_count FROM products GROUP BY category ORDER BY product_count DESC LIMIT 1000;",
  "columns": [
    {"name": "category", "type": "text"},
    {"name": "product_count", "type": "bigint"}
  ],
  "rows": [
    {"category": "Electronics", "product_count": 245},
    {"category": "Books", "product_count": 189},
    {"category": "Clothing", "product_count": 156}
  ],
  "row_count": 3,
  "execution_time_ms": 45.2,
  "truncated": false
}
```

### 示例 3: 列出数据库

**MCP 工具调用**:

```json
{
  "tool": "list_databases",
  "arguments": {}
}
```

**响应**:

```json
{
  "databases": [
    {
      "name": "mydb",
      "host": "localhost",
      "database": "myapp_db",
      "status": "connected",
      "table_count": 45,
      "last_updated": "2026-01-28T10:30:00Z"
    }
  ]
}
```

### 示例 4: 查看 Schema（资源）

**MCP 资源访问**:

```
URI: schema://mydb
```

**响应**: JSON 格式的完整 database schema

### 示例 5: 查询历史

**MCP 工具调用**:

```json
{
  "tool": "query_history",
  "arguments": {
    "limit": 10,
    "status": "success"
  }
}
```

**响应**: 最近 10 条成功的查询记录

---

## 常见使用场景

### 场景 1: 探索数据库结构

```text
1. 调用 list_databases 查看可用数据库
2. 调用 schema://mydb 资源查看完整 schema
3. 调用 schema://mydb/users 查看特定表详情
```

### 场景 2: 生成并调试 SQL

```text
1. 调用 generate_sql 生成 SQL
2. 检查返回的 warnings（如缺少 LIMIT）
3. 如果需要，调整自然语言描述重新生成
4. 满意后使用 execute_query 执行
```

### 场景 3: AI 服务不可用时

```text
1. generate_sql 返回 AI_SERVICE_UNAVAILABLE 错误
2. 服务器自动尝试模板库匹配
3. 如果匹配成功，返回 generation_method="template_matched"
4. 如果未匹配，返回错误建议稍后重试
```

### 场景 4: 审计查询历史

```text
1. 调用 query_history 获取历史记录
2. 使用 jq 查询日志文件进行深度分析
3. 识别常见查询模式优化模板库
```

---

## 故障排查

### 问题 1: 服务器无法启动

**症状**: 启动时报错

**可能原因**:
- 配置文件格式错误
- 环境变量未设置
- 数据库连接失败

**解决方法**:

```bash
# 验证配置文件语法
python -c "import yaml; yaml.safe_load(open('config/config.yaml'))"

# 检查环境变量
echo $MYDB_PASSWORD
echo $OPENAI_API_KEY

# 测试数据库连接
psql -h localhost -U readonly_user -d myapp_db -c "SELECT 1"

# 查看详细日志
POSTGRES_MCP_LOG_LEVEL=DEBUG python -m postgres_mcp
```

### 问题 2: SQL 生成失败

**症状**: generate_sql 返回错误

**可能原因**:
- OpenAI API 密钥无效
- 自然语言描述过于模糊
- Schema 缓存未初始化

**解决方法**:

```bash
# 验证 OpenAI API 密钥
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"

# 检查 schema 缓存
# 调用 list_databases 查看 table_count

# 刷新 schema
# 调用 refresh_schema 工具

# 尝试更简单的查询
# "显示所有用户" 而非 "显示上周活跃且购买超过 100 元的用户"
```

### 问题 3: 查询执行超时

**症状**: execute_query 返回 QUERY_TIMEOUT

**可能原因**:
- 查询过于复杂（多表 JOIN）
- 数据库性能问题
- 表数据量过大

**解决方法**:

```bash
# 1. 先用 generate_sql 检查生成的 SQL
# 2. 手动在数据库中测试 SQL 性能
# 3. 添加索引或优化数据库
# 4. 调整超时配置（config.yaml）

query:
  max_timeout_seconds: 60  # 增加到 60 秒
```

### 问题 4: 内存使用过高

**症状**: 服务器内存占用超过 500MB

**可能原因**:
- 数据库表数量过多（1000+）
- Sample 数据过多

**解决方法**:

```yaml
# 在 config.yaml 中禁用示例数据
schema_cache:
  load_sample_data: false  # 禁用
  max_sample_rows: 0

# 或使用懒加载（仅缓存常用表）
schema_cache:
  lazy_load: true
  preload_tables: ["users", "products", "orders"]  # 仅预加载关键表
```

---

## 高级配置

### 多数据库配置

```yaml
databases:
  - name: "production"
    host: "prod-db.example.com"
    port: 5432
    database: "app"
    user: "app_readonly"
    password_env_var: "PROD_DB_PASSWORD"
    ssl_mode: "require"
    max_pool_size: 30  # 生产环境更大池

  - name: "staging"
    host: "staging-db.example.com"
    port: 5432
    database: "app"
    user: "app_readonly"
    password_env_var: "STAGING_DB_PASSWORD"
    ssl_mode: "prefer"

  - name: "analytics"
    host: "analytics-db.example.com"
    port: 5433
    database: "warehouse"
    user: "analyst"
    password_env_var: "ANALYTICS_DB_PASSWORD"
    ssl_mode: "prefer"
    min_pool_size: 2
    max_pool_size: 10

default_database: "production"
```

### 性能调优

```yaml
query:
  default_limit: 1000      # 默认返回行数限制
  max_timeout_seconds: 30  # 查询超时
  enable_query_cache: true # 启用查询缓存（可选）
  cache_ttl_seconds: 3600  # 缓存 1 小时

schema_cache:
  poll_interval_minutes: 5  # Schema 刷新间隔
  load_sample_data: true    # 加载示例数据
  max_sample_rows: 3        # 每表最多 3 行

pools:
  min_size: 5
  max_size: 20
  command_timeout: 60.0
  max_inactive_lifetime: 300.0

logging:
  level: "INFO"           # DEBUG/INFO/WARNING/ERROR
  buffer_size: 100        # 日志缓冲大小
  flush_interval_seconds: 5.0
```

### 模板库自定义

```bash
# 添加自定义模板
cat > src/postgres_mcp/templates/queries/custom_report.yaml << EOF
name: "custom_report"
description: "自定义报表查询"
priority: 90
keywords:
  - "报表"
  - "统计"
  - "汇总"
patterns:
  - "生成.*报表"
parameters:
  - name: "table_name"
    type: "identifier"
    required: true
  - name: "group_column"
    type: "identifier"
    required: true
sql_template: |
  SELECT {group_column}, COUNT(*) as count
  FROM {table_name}
  GROUP BY {group_column}
  ORDER BY count DESC
  LIMIT 100;
examples:
  - input: "生成按地区的用户统计报表"
    parameters:
      table_name: "users"
      group_column: "region"
EOF
```

---

## 测试

### 单元测试

```bash
# 运行所有测试
pytest

# 运行特定模块测试
pytest tests/unit/test_sql_validator.py -v

# 查看覆盖率
pytest --cov=src/postgres_mcp --cov-report=html
open htmlcov/index.html
```

### 集成测试

```bash
# 需要真实 PostgreSQL 数据库
export TEST_DB_HOST=localhost
export TEST_DB_PASSWORD=test

pytest tests/integration/ -v
```

### 手动测试

```python
# 在 Python REPL 中测试
from postgres_mcp.server import create_server
import asyncio

async def test():
    async with create_server() as mcp:
        # 测试 generate_sql 工具
        result = await mcp.call_tool("generate_sql", {
            "natural_language": "显示所有用户"
        })
        print(result)

asyncio.run(test())
```

---

## 监控和日志

### 查看实时日志

```bash
# 应用日志（console）
tail -f logs/application.log

# 查询历史日志（JSONL）
tail -f logs/queries/$(date +%Y-%m-%d).jsonl | jq '.'
```

### 查询日志分析

```bash
# 今天的成功查询数
jq 'select(.status == "success")' logs/queries/$(date +%Y-%m-%d).jsonl | wc -l

# 平均执行时间
jq -s 'map(select(.execution_time_ms != null) | .execution_time_ms) | add / length' logs/queries/$(date +%Y-%m-% d).jsonl

# 最慢的 10 个查询
jq -s 'sort_by(.execution_time_ms) | reverse | .[0:10] | .[] | {sql, execution_time_ms}' logs/queries/$(date +%Y-%m-%d).jsonl

# 失败原因分布
jq -s 'map(select(.status != "success")) | group_by(.error_message) | map({error: .[0].error_message, count: length})' logs/queries/$(date +%Y-%m-%d).jsonl
```

---

## Docker 部署（可选）

**Docker 版本要求**: Docker 2.x（Docker Compose V2）

### Dockerfile

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# 安装 UV
RUN pip install uv

# 复制项目文件
COPY pyproject.toml uv.lock ./
COPY src/ ./src/
COPY config/ ./config/

# 安装依赖
RUN uv pip install -e .

# 创建日志目录
RUN mkdir -p /app/logs/queries

# 运行服务器
CMD ["python", "-m", "postgres_mcp"]
```

### Docker Compose

```yaml
# Docker Compose 2.x 配置（不需要 version 字段）
services:
  postgres-mcp:
    build: .
    environment:
      - MYDB_PASSWORD=${MYDB_PASSWORD}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - POSTGRES_MCP_LOG_LEVEL=INFO
    volumes:
      - ./config:/app/config:ro
      - ./logs:/app/logs
    networks:
      - app-network
    restart: unless-stopped

networks:
  app-network:
    driver: bridge
```

### 启动

```bash
# 注意: 使用 Docker Compose V2 命令（docker compose，无连字符）

# 构建
docker compose build

# 启动
docker compose up -d

# 查看日志
docker compose logs -f postgres-mcp

# 停止
docker compose down

# 注意: 如果仍在使用旧版 docker-compose（V1），请升级到 Docker 2.x
# 升级命令: sudo apt-get update && sudo apt-get install docker-compose-plugin
```

---

## 下一步

- 📖 阅读 [完整文档](./README.md)
- 🔧 查看 [数据模型定义](./data-model.md)
- 📋 查看 [MCP 契约](./contracts/)
- 🧪 运行 [测试套件](../Week5/tests/)
- 🚀 查看 [实现计划](./plan.md)

---

## 获取帮助

- **文档**: `/specs/001-postgres-mcp/` 目录下的所有 Markdown 文件
- **示例**: `/Week5/examples/` 目录
- **问题**: 查看 logs 目录下的日志文件
- **配置**: 参考 `config/config.example.yaml`

---

**预计启动时间**: 5 分钟
**核心功能**: ✅ 自然语言 → SQL | ✅ 查询执行 | ✅ Schema 缓存 | ✅ 安全验证
