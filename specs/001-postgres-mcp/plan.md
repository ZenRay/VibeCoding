# 实现计划：PostgreSQL 自然语言查询 MCP 服务器

**分支**: `001-postgres-mcp` | **日期**: 2026-01-28 | **规格**: [spec.md](./spec.md)
**输入**: 功能规格来自 `/specs/001-postgres-mcp/spec.md`

## 摘要

构建一个基于 MCP (Model Context Protocol) 的 PostgreSQL 查询服务器，允许用户通过自然语言查询数据库。系统使用 OpenAI GPT-4o-mini 将自然语言转换为 SQL，通过 SQLGlot 进行 SQL 验证和安全检查，使用 Asyncpg 执行查询，并通过 FastMCP 暴露标准 MCP 接口。核心技术栈：FastMCP (MCP 服务器框架)、Asyncpg (异步 PostgreSQL 客户端)、SQLGlot (SQL 解析器)、Pydantic (数据验证)、OpenAI (AI 模型)。

## 技术上下文

**语言/版本**: Python 3.12 (最新稳定版，支持最新 typing 特性和性能优化)
**主要依赖**:
- FastMCP 0.3+ (MCP 服务器框架，支持工具/资源/提示)
- Asyncpg 0.29+ (高性能异步 PostgreSQL 驱动)
- SQLGlot 25.29+ (SQL 解析、验证、转换库)
- Pydantic 2.10+ (数据验证，v2 性能优化)
- OpenAI Python SDK 1.59+ (GPT-4o-mini API 客户端)
- Structlog 24+ (结构化日志)

**存储**:
- Schema 缓存：内存存储（Python dict + asyncio.Lock）
- 查询历史：JSONL 日志文件（按日期轮转）
- 配置：YAML 文件 + 环境变量覆盖

**测试**:
- Pytest 8+ (测试框架)
- Pytest-asyncio 0.24+ (异步测试)
- Pytest-cov 6+ (覆盖率)
- Pytest-mock 3+ (模拟)
- Hypothesis 6+ (属性测试，用于 SQL 验证)

**目标平台**: Linux/macOS (Python 3.12+)，Docker 2.x 容器化部署
**项目类型**: 单一 Python 包（MCP 服务器应用）
**性能目标**:
- SQL 生成：95% 请求 <5 秒（不含 OpenAI 延迟）
- Schema 缓存：100 表 <60 秒加载
- 并发：10+ 并发请求无降级

**约束**:
- 仅只读查询（SELECT），阻止所有 DML/DDL
- 内存使用：Schema 缓存 <500MB（100 表场景）
- 响应时间：P95 <15 秒（含重试）

**规模/范围**:
- 支持 1-100 个数据库连接
- Schema 缓存：每数据库 100-1000 表
- 查询模板库：10-15 个常见模式

## 宪章检查

*门控：必须在 Phase 0 研究前通过。Phase 1 设计后重新检查。*

由于项目尚无 constitution.md，采用标准 Python 项目最佳实践：

### ✅ 测试优先（非协商）
- **要求**: TDD 流程 - 先写测试，红-绿-重构循环
- **状态**: ✅ 已规划 - 每个模块先定义测试契约

### ✅ 代码质量
- **要求**:
  - Ruff 代码检查（无错误）
  - 90%+ 测试覆盖率
  - Mypy 类型检查（严格模式）
- **状态**: ✅ 已规划

### ✅ SOLID 原则
- **单一职责**: 每个模块职责明确（schema_cache, sql_generator, query_executor 等）
- **开闭原则**: 使用 Protocol 定义接口，易于扩展
- **依赖倒置**: 核心逻辑依赖抽象接口，不依赖具体实现

### ✅ 安全性
- **要求**: SQL 注入防护、凭据安全存储、只读强制
- **状态**: ✅ 已规划 - SQLGlot 解析验证 + Asyncpg 参数化

### ⚠️ 性能要求
- **挑战**: OpenAI API 延迟不可控，可能影响响应时间目标
- **缓解**: 本地模板库降级、查询缓存（Phase 2 可选）

## 项目结构

### 文档（本功能）

```text
specs/001-postgres-mcp/
├── spec.md              # 功能规格（已完成）
├── plan.md              # 本文件（/speckit.plan 输出）
├── research.md          # Phase 0 输出
├── data-model.md        # Phase 1 输出
├── quickstart.md        # Phase 1 输出
├── contracts/           # Phase 1 输出（MCP 工具定义）
│   ├── mcp_tools.json   # MCP 工具规范
│   └── mcp_resources.json # MCP 资源规范
└── tasks.md             # Phase 2 输出（/speckit.tasks 创建）
```

### 源代码（仓库根目录 Week5/）

```text
src/
└── postgres_mcp/           # 主包
    ├── __init__.py         # 包初始化
    ├── server.py           # FastMCP 服务器入口
    ├── config.py           # 配置管理（Pydantic Settings）
    │
    ├── core/               # 核心业务逻辑
    │   ├── __init__.py
    │   ├── schema_cache.py     # Schema 缓存管理
    │   ├── sql_generator.py    # AI SQL 生成器
    │   ├── sql_validator.py    # SQL 安全验证（SQLGlot）
    │   ├── query_executor.py   # 查询执行器（Asyncpg）
    │   └── template_matcher.py # 模板库降级
    │
    ├── models/             # 数据模型（Pydantic）
    │   ├── __init__.py
    │   ├── connection.py       # DatabaseConnection
    │   ├── schema.py           # SchemaCache 数据结构
    │   ├── query.py            # QueryRequest, GeneratedQuery
    │   ├── result.py           # QueryResult
    │   └── log_entry.py        # QueryLogEntry
    │
    ├── mcp/                # MCP 接口层
    │   ├── __init__.py
    │   ├── tools.py            # MCP 工具实现
    │   ├── resources.py        # MCP 资源实现
    │   └── prompts.py          # MCP 提示定义（可选）
    │
    ├── db/                 # 数据库层
    │   ├── __init__.py
    │   ├── connection_pool.py  # Asyncpg 连接池管理
    │   ├── schema_inspector.py # Schema 元数据提取
    │   └── query_runner.py     # 查询执行封装
    │
    ├── ai/                 # AI 集成
    │   ├── __init__.py
    │   ├── openai_client.py    # OpenAI API 客户端
    │   ├── prompt_builder.py   # 提示词构建
    │   └── response_parser.py  # AI 响应解析
    │
    ├── utils/              # 工具函数
    │   ├── __init__.py
    │   ├── logging.py          # Structlog 配置
    │   ├── template_loader.py  # 模板加载
    │   └── jsonl_writer.py     # JSONL 日志写入
    │
    └── templates/          # SQL 模板库
        └── queries/            # 常见查询模板（YAML）
            ├── select_all.yaml
            ├── group_by.yaml
            └── join_basic.yaml

tests/
├── conftest.py             # Pytest 配置和固件
├── unit/                   # 单元测试
│   ├── test_schema_cache.py
│   ├── test_sql_generator.py
│   ├── test_sql_validator.py
│   ├── test_query_executor.py
│   └── test_template_matcher.py
├── integration/            # 集成测试
│   ├── test_mcp_tools.py
│   ├── test_db_operations.py
│   └── test_openai_integration.py
└── contract/               # 契约测试
    ├── test_mcp_protocol.py
    └── test_api_contracts.py

config/
├── config.yaml             # 默认配置
└── config.example.yaml     # 配置示例

logs/                       # 查询历史日志（运行时创建）
└── queries/
    └── 2026-01-28.jsonl

pyproject.toml              # 项目配置（UV）
uv.lock                     # 依赖锁定
README.md                   # 项目文档
CLAUDE.md                   # AI Agent 指南（已存在）
```

**结构决策**: 选择单一项目结构（Option 1），因为这是一个纯后端 MCP 服务器应用。采用分层架构：
- `mcp/`: MCP 协议接口层（FastMCP）
- `core/`: 核心业务逻辑（架构中立）
- `db/`: 数据库访问层（Asyncpg）
- `ai/`: AI 服务集成层（OpenAI）
- `models/`: 数据模型（Pydantic）
- `utils/`: 通用工具

这种分层确保关注点分离，核心逻辑可独立测试，不依赖具体的 MCP 实现或数据库驱动。

## 复杂度跟踪

> **仅在宪章检查有必须论证的违规时填写**

**无需论证** - 项目符合标准 Python 最佳实践，无特殊复杂度。

## Phase 0: 概述与研究

### 研究任务

基于技术上下文中的未知项和技术选择，需要研究以下主题：

#### R1: FastMCP 最佳实践
- **目标**: 了解 FastMCP 0.3+ 的工具/资源/提示实现模式
- **研究点**:
  - 工具（Tools）定义：输入/输出 schema、错误处理
  - 资源（Resources）暴露：动态资源生成模式
  - 上下文管理：连接状态、缓存共享
  - 异步处理：Asyncpg 与 FastMCP 集成
- **输出**: `research.md` 中的 FastMCP 集成模式

#### R2: Asyncpg 连接池最佳实践
- **目标**: 设计高性能、可靠的数据库连接管理
- **研究点**:
  - 连接池大小配置（10 并发 + 动态连接场景）
  - 连接健康检查和重连策略
  - 多数据库连接池管理
  - 事务隔离和超时控制
- **输出**: `research.md` 中的连接池架构

#### R3: SQLGlot SQL 验证策略
- **目标**: 确保 100% 阻止非 SELECT 语句
- **研究点**:
  - AST 解析识别 DML/DDL 语句类型
  - 嵌套查询（子查询、CTE）验证
  - SQL 注释去除和注入检测
  - PostgreSQL 方言特定语法处理
- **输出**: `research.md` 中的 SQL 安全验证方案

#### R4: OpenAI Prompt Engineering
- **目标**: 优化 SQL 生成准确率（目标 90%）
- **研究点**:
  - Schema 上下文组织（表结构、关系、示例数据）
  - Few-shot examples 策略
  - 结构化输出（JSON mode）确保解析成功
  - 重试策略（验证失败时的 prompt 改进）
- **输出**: `research.md` 中的 Prompt 模板和策略

#### R5: Pydantic v2 性能优化
- **目标**: 利用 Pydantic v2 的性能提升
- **研究点**:
  - 模型编译和缓存
  - 严格模式 vs 非严格模式权衡
  - 自定义验证器性能影响
  - Schema 缓存数据结构设计
- **输出**: `research.md` 中的数据模型设计指南

#### R6: 查询模板库设计
- **目标**: 定义 10-15 个常见查询模板
- **研究点**:
  - 模板参数化方案（表名、列名占位符）
  - 模板匹配算法（关键词、模式识别）
  - 模板覆盖率评估方法
  - YAML 模板格式设计
- **输出**: `research.md` 中的模板库规范 + 初始模板列表

#### R7: 日志轮转和 JSONL 格式
- **目标**: 高效的查询历史记录
- **研究点**:
  - JSONL 写入性能（追加、fsync 策略）
  - 日期轮转机制（文件命名、清理策略）
  - 日志查询工具（jq 查询示例）
  - 结构化日志字段定义
- **输出**: `research.md` 中的日志格式规范

### 研究输出结构

所有研究结果将整合到 `research.md`，格式如下：

```markdown
# 技术研究：PostgreSQL MCP 服务器

## 1. FastMCP 集成模式

**决策**: [选择的实现模式]
**理由**: [为什么这样设计]
**替代方案**: [考虑过的其他方案]
**代码示例**: [关键代码片段]

## 2. Asyncpg 连接池架构

...（同样格式）

## 3-7. [其他研究主题]

...
```

## Phase 1: 设计与契约

### 数据模型设计

基于功能规格中的关键实体，将在 `data-model.md` 中详细定义：

#### 核心实体

1. **DatabaseConnection** (连接配置)
   - 字段：name, host, port, database, user, password_env_var, ssl_mode
   - 验证：端口范围、必填字段
   - 状态：connected, disconnected, error

2. **SchemaCache** (Schema 缓存)
   - 字段：database_name, tables, views, types, indexes, last_updated
   - 嵌套：TableSchema (columns, constraints, relationships)
   - 生命周期：startup load → periodic refresh → manual refresh

3. **QueryRequest** (查询请求)
   - 字段：natural_language, database_name, response_mode (sql_only | execute)
   - 验证：非空文本、有效数据库名
   - 元数据：timestamp, request_id

4. **GeneratedQuery** (生成的 SQL)
   - 字段：sql, validation_status, warnings, generated_at
   - 状态：pending, validated, rejected, executed
   - 关联：QueryRequest (1-to-1)

5. **QueryResult** (查询结果)
   - 字段：columns, rows, row_count, execution_time_ms, errors
   - 数据：List[Dict[str, Any]] (动态列)
   - 限制：max_rows (1000 默认)

6. **QueryLogEntry** (审计日志)
   - 字段：timestamp, request_id, user_id, natural_language, sql, status, result_summary
   - 格式：JSONL 单行
   - 索引：timestamp, request_id

### MCP 契约定义

将在 `contracts/` 目录创建 MCP 工具和资源定义：

#### MCP 工具（Tools）

1. **generate_sql**
   - 输入：natural_language (string), database (string, optional)
   - 输出：{sql: string, validated: boolean, warnings: string[]}
   - 错误：InvalidQuery, DatabaseNotFound, AIServiceUnavailable

2. **execute_query**
   - 输入：natural_language (string), database (string, optional)
   - 输出：{sql: string, columns: string[], rows: object[], row_count: int}
   - 错误：QueryTimeout, InvalidSQL, PermissionDenied

3. **list_databases**
   - 输入：无
   - 输出：{databases: [{name: string, table_count: int, status: string}]}

4. **refresh_schema**
   - 输入：database (string, optional)
   - 输出：{refreshed_databases: string[], duration_ms: int}

5. **query_history**
   - 输入：limit (int, default: 100), database (string, optional)
   - 输出：{entries: [{timestamp, natural_language, sql, status}]}

#### MCP 资源（Resources）

1. **schema://{database}**
   - 描述：返回指定数据库的 schema 信息
   - 格式：JSON (tables, views, relationships)

2. **templates://queries**
   - 描述：返回可用查询模板列表
   - 格式：YAML/JSON 模板定义

### QuickStart 文档

将创建 `quickstart.md` 包含：
- 5 分钟快速开始指南
- 配置示例
- 常见 MCP 工具调用示例
- 故障排查

## Phase 2: 任务分解

*注意：Phase 2 由 `/speckit.tasks` 命令执行，不在本计划范围内*

任务分解将包括：
- Phase 2.1: 基础设施（配置、日志、连接池）
- Phase 2.2: Schema 缓存（inspector、缓存管理、刷新）
- Phase 2.3: SQL 生成（OpenAI 集成、prompt 构建、解析）
- Phase 2.4: SQL 验证（SQLGlot 解析、安全检查）
- Phase 2.5: 查询执行（Asyncpg 执行器、结果处理）
- Phase 2.6: 模板库（模板定义、匹配逻辑）
- Phase 2.7: MCP 接口（FastMCP 工具/资源实现）
- Phase 2.8: 测试（单元、集成、契约测试）
- Phase 2.9: 文档和部署

## 架构图

### 系统架构层次

```text
┌─────────────────────────────────────────────────────────────┐
│                      MCP Client                              │
│                 (Claude Desktop, Cursor等)                   │
└────────────────────────┬────────────────────────────────────┘
                         │ MCP Protocol (stdio/JSON-RPC)
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   FastMCP Server Layer                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Tools        │  │ Resources    │  │ Prompts      │      │
│  │ (5 tools)    │  │ (2 resources)│  │ (optional)   │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
└─────────┼──────────────────┼──────────────────┼─────────────┘
          │                  │                  │
          ▼                  ▼                  ▼
┌─────────────────────────────────────────────────────────────┐
│                    Core Business Logic                       │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  SchemaCache        SQLGenerator      QueryExecutor  │   │
│  │  ┌─────────┐       ┌──────────┐      ┌───────────┐  │   │
│  │  │ Cache   │◄──────┤ Prompt   │      │ Executor  │  │   │
│  │  │ Manager │       │ Builder  │      │ Runner    │  │   │
│  │  └─────────┘       └────┬─────┘      └─────┬─────┘  │   │
│  │                          │                  │         │   │
│  │  SQLValidator      TemplateMatch            │         │   │
│  │  ┌──────────┐      ┌──────────┐            │         │   │
│  │  │ SQLGlot  │      │ Template │            │         │   │
│  │  │ Parser   │      │ Matcher  │            │         │   │
│  │  └──────────┘      └──────────┘            │         │   │
│  └──────────────────────────────────────────────┼────────┘   │
└─────────────────────────────────────────────────┼────────────┘
                  │                  │            │
                  ▼                  ▼            ▼
┌──────────────────────┐  ┌───────────────┐  ┌──────────────┐
│   OpenAI Client      │  │ Schema        │  │ Asyncpg      │
│   (GPT-4o-mini)      │  │ Inspector     │  │ Connection   │
│                      │  │               │  │ Pool         │
└──────────────────────┘  └───────┬───────┘  └──────┬───────┘
                                  │                  │
                                  ▼                  ▼
                          ┌─────────────────────────────┐
                          │   PostgreSQL Database(s)    │
                          └─────────────────────────────┘
```

### 数据流

#### 场景 1: SQL 生成（不执行）

```text
1. MCP Client → generate_sql tool
2. FastMCP → SQLGenerator.generate()
3. SQLGenerator → SchemaCache.get_schema(database)
4. SQLGenerator → PromptBuilder.build_prompt(nl, schema)
5. SQLGenerator → OpenAIClient.generate_sql(prompt)
6. SQLGenerator → SQLValidator.validate(sql)
   ├─ 如果失败 → 重试 1 次（增强 prompt）
   └─ 如果成功 → 返回 SQL
7. SQLGenerator → 返回 {sql, validated, warnings}
8. FastMCP → MCP Client
```

#### 场景 2: 执行查询

```text
1. MCP Client → execute_query tool
2. FastMCP → QueryExecutor.execute()
3. QueryExecutor → SQLGenerator.generate() (同场景 1)
4. QueryExecutor → SQLValidator.final_check(sql)
5. QueryExecutor → ConnectionPool.get_connection(database)
6. QueryExecutor → QueryRunner.execute(sql, connection)
7. QueryExecutor → 格式化结果 {sql, columns, rows}
8. QueryExecutor → JSONLWriter.log(entry)
9. FastMCP → MCP Client
```

#### 场景 3: OpenAI 失败降级

```text
1. OpenAI API 不可用/速率限制
2. SQLGenerator → TemplateMatcher.match(natural_language)
3. TemplateMatcher → 加载模板库
4. TemplateMatcher → 关键词匹配/模式识别
5. TemplateMatcher → 填充模板参数（表名、列名）
   ├─ 如果匹配成功 → 返回模板生成的 SQL
   └─ 如果未匹配 → 返回错误 "无法生成 SQL，请稍后重试"
```

## 技术决策

### 1. FastMCP vs 原生 MCP 实现

**决策**: 使用 FastMCP 0.3+
**理由**:
- 简化 MCP 协议实现（工具、资源、提示的声明式定义）
- 内置异步支持（与 Asyncpg 无缝集成）
- 类型安全（基于 Pydantic 的输入验证）
- 活跃维护（2024+ 持续更新）

**替代方案**: 原生 MCP SDK - 需要更多样板代码，不值得额外复杂度

### 2. Asyncpg vs SQLAlchemy (Async)

**决策**: 使用 Asyncpg 直接连接
**理由**:
- 性能：Asyncpg 是最快的 PostgreSQL Python 驱动（比 SQLAlchemy 快 2-3 倍）
- 简单性：不需要 ORM，只需执行 SQL
- 异步原生：从头设计为异步，无同步包袱
- 连接池内置：asyncpg.create_pool() 开箱即用

**替代方案**: SQLAlchemy 2.0 Async - 如果需要复杂查询构建或多数据库支持，但本项目不需要

### 3. SQLGlot vs sqlparse

**决策**: 使用 SQLGlot 25.29+
**理由**:
- 完整的 SQL 解析器（AST，不仅仅是词法分析）
- PostgreSQL 方言支持
- 查询优化和转换功能（未来可用于查询改进）
- 类型识别（准确区分 SELECT/INSERT/UPDATE/DELETE/DDL）

**替代方案**: sqlparse - 仅词法分析，无法可靠识别复杂查询类型

### 4. Pydantic v2 vs v1

**决策**: 使用 Pydantic 2.10+
**理由**:
- 性能：v2 使用 Rust 核心，比 v1 快 5-50 倍
- 严格模式：更好的类型安全
- JSON Schema：自动生成 MCP 工具 schema
- 未来支持：v1 将在 2025 年停止维护

**注意**: 迁移代码需要注意 v1 → v2 的 breaking changes（配置类、验证器语法）

### 5. 日志：Structlog vs Python logging

**决策**: 使用 Structlog 24+
**理由**:
- 结构化日志（JSON 输出，易于解析）
- 上下文绑定（request_id 自动传播）
- 性能（比标准 logging 快）
- 可观测性友好（Prometheus、ELK 集成）

**替代方案**: Python logging - 非结构化，难以查询

### 6. 配置管理：Pydantic Settings vs python-dotenv

**决策**: 使用 Pydantic Settings 2.10+
**理由**:
- 类型验证（配置加载时验证类型）
- 环境变量优先级（文件 < 环境变量）
- Nested 配置支持（数据库连接列表）
- 与 Pydantic 模型无缝集成

**配置格式**: YAML（易读） + 环境变量覆盖（密码等敏感值）

## 风险与缓解

### 风险 1: AI 生成准确率低于 90%

**影响**: 无法满足 SC-001 成功标准
**概率**: 中等（GPT-4o-mini 是较小模型）
**缓解**:
- Phase 0 研究：优化 prompt engineering（few-shot examples）
- 模板库降级：常见查询用模板覆盖
- 用户反馈循环：收集失败案例改进 prompts
- 考虑升级到 GPT-4o（更大模型）如果准确率不足

### 风险 2: Schema 缓存超出内存限制

**影响**: 大型数据库（1000+ 表）可能超过 500MB 限制
**概率**: 低（100 表场景）
**缓解**:
- 懒加载：仅缓存常用表的详细信息
- 压缩：使用 msgpack/pickle 压缩缓存数据
- 分层缓存：表名列表（全部）+ 列详情（按需）

### 风险 3: Asyncpg 连接池耗尽

**影响**: 并发请求超过 10 时性能降级
**概率**: 中等（动态连接场景）
**缓解**:
- 自适应池大小：根据负载动态调整（min=5, max=50）
- 连接超时：30 秒无活动自动释放
- 请求排队：超过池大小时排队（最多等待 5 秒）

### 风险 4: OpenAI API 速率限制

**影响**: 高频使用时触发 429 错误
**概率**: 中等（免费/低级别账户）
**缓解**:
- 模板库降级：FR-016（已规划）
- 查询缓存：相同 NL 查询缓存 1 小时（Phase 2 可选）
- 速率限制监控：记录 429 错误率，提示用户升级

### 风险 5: SQL 注入绕过验证

**影响**: 严重安全问题
**概率**: 极低（SQLGlot + Asyncpg 参数化）
**缓解**:
- 多层防护：SQLGlot 解析 + 正则检测 + Asyncpg 参数化
- 安全测试：Property-based testing（Hypothesis）生成攻击向量
- 代码审查：Phase 2 所有 SQL 相关代码 peer review

## 依赖版本锁定

基于最新稳定版本（2026-01-28）：

### Python 依赖

```toml
[project]
name = "postgres-mcp"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "fastmcp>=0.3.0,<0.4",           # MCP 服务器框架
    "asyncpg>=0.29.0,<0.30",         # PostgreSQL 异步驱动
    "sqlglot>=25.29.0,<26",          # SQL 解析器
    "pydantic>=2.10.0,<3",           # 数据验证
    "pydantic-settings>=2.7.0,<3",   # 配置管理
    "openai>=1.59.0,<2",             # OpenAI SDK
    "structlog>=24.1.0,<25",         # 结构化日志
    "pyyaml>=6.0.1,<7",              # YAML 解析
    "python-dotenv>=1.0.0,<2",       # 环境变量加载
    "pybreaker>=1.2.0,<2",           # 熔断器模式
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0,<9",
    "pytest-asyncio>=0.24.0,<0.25",
    "pytest-cov>=6.0.0,<7",
    "pytest-mock>=3.14.0,<4",
    "hypothesis>=6.98.0,<7",
    "ruff>=0.8.0,<0.9",
    "mypy>=1.13.0,<2",
    "pre-commit>=4.0.0,<5",
]
```

### 系统依赖

**Docker 2.x** (容器化部署，可选):
- Docker Engine 2.0+ (Docker Compose V2 内置)
- 不再需要独立安装 docker-compose V1
- 命令: `docker compose` (无连字符，V2 标准)

**PostgreSQL 12.0+**:
- 推荐使用 PostgreSQL 15+ (更好的性能和 JSON 支持)
- Docker 镜像: `postgres:15-alpine` (生产环境)

## 下一步

1. **立即执行**: 生成 `research.md`（Phase 0）
2. **后续**: 生成 `data-model.md` 和 `contracts/`（Phase 1）
3. **最后**: 执行 `/speckit.tasks` 进行详细任务分解（Phase 2）

---

**计划状态**: Phase 0 待执行
**估计完成时间**: Phase 0-1 约 4-6 小时研究和设计
