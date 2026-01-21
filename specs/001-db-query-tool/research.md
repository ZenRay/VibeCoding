# Research: 数据库查询工具

**Date**: 2026-01-10  
**Phase**: 0 - Outline & Research  
**Status**: Complete

## Research Summary

本文档记录了实施计划中所有技术决策的研究结果，包括技术选择、最佳实践和替代方案评估。

---

## 1. SQL 解析与验证

### Decision: sqlglot

**选择**: sqlglot 作为 SQL 解析和验证工具

**Rationale**:
- 纯 Python 实现，无外部依赖
- 支持多种数据库方言（PostgreSQL, MySQL, SQLite）
- 可以解析、验证和转换 SQL
- 提供 AST（抽象语法树）访问，便于分析 SQL 类型
- 活跃的社区和持续更新

**Alternatives Considered**:

| 方案 | 优点 | 缺点 | 排除原因 |
|------|------|------|----------|
| sqlparse | 简单易用 | 只能分词，不做语法验证 | 无法验证语法正确性 |
| antlr4 | 强大的解析器生成器 | 需要单独的语法文件，复杂 | 过于复杂 |
| python-sqlparser | 基于 libpg_query | 仅支持 PostgreSQL | 不支持多数据库 |

**Implementation Notes**:
```python
import sqlglot

def validate_sql(sql: str, dialect: str) -> tuple[bool, str | None]:
    """验证 SQL 语法并检查是否为 SELECT 语句"""
    try:
        parsed = sqlglot.parse(sql, dialect=dialect)
        if not parsed:
            return False, "无法解析 SQL"
        
        # 检查是否为 SELECT 语句
        for statement in parsed:
            if statement.key != "select":
                return False, "仅允许 SELECT 查询"
        
        return True, None
    except sqlglot.errors.ParseError as e:
        return False, f"语法错误：{e}"
```

---

## 2. 数据库连接管理

### Decision: 异步数据库驱动

**选择**:
- PostgreSQL: `asyncpg`（高性能异步驱动）
- MySQL: `aiomysql`（异步 MySQL 驱动）
- SQLite: `aiosqlite`（异步 SQLite 包装器）

**Rationale**:
- 与 FastAPI 的异步模型完美配合
- 支持查询取消（通过 asyncio.timeout）
- 更好的并发性能
- 统一的异步接口设计

**Alternatives Considered**:

| 方案 | 优点 | 缺点 | 排除原因 |
|------|------|------|----------|
| psycopg2 + mysql-connector | 成熟稳定 | 同步阻塞 | 与 FastAPI 异步模型不匹配 |
| SQLAlchemy async | 统一接口 | 增加复杂性 | 仅需要简单查询，不需要 ORM |
| databases | 多数据库支持 | 额外抽象层 | 直接使用驱动更灵活 |

**Implementation Notes**:

```python
from abc import ABC, abstractmethod
from typing import Any

class DatabaseAdapter(ABC):
    """数据库适配器基类"""
    
    @abstractmethod
    async def connect(self, url: str) -> None:
        """建立连接"""
        pass
    
    @abstractmethod
    async def execute(self, sql: str, timeout: float = 30.0) -> list[dict[str, Any]]:
        """执行查询"""
        pass
    
    @abstractmethod
    async def get_metadata(self) -> dict[str, Any]:
        """获取元数据"""
        pass
    
    @abstractmethod
    async def close(self) -> None:
        """关闭连接"""
        pass
```

---

## 3. 元数据提取策略

### Decision: 数据库系统表查询

**选择**: 直接查询数据库系统表/视图

**Rationale**:
- 标准化方法，各数据库都有系统表
- 可以获取详细的元数据信息
- 无需额外依赖
- 可以精确控制提取哪些信息

**数据库特定查询**:

**PostgreSQL** (information_schema + pg_catalog):
```sql
-- 获取所有表和视图
SELECT table_name, table_type
FROM information_schema.tables
WHERE table_schema = 'public';

-- 获取列信息
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_schema = 'public' AND table_name = :table_name;
```

**MySQL** (information_schema):
```sql
-- 获取所有表和视图
SELECT table_name, table_type
FROM information_schema.tables
WHERE table_schema = :database;

-- 获取列信息
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_schema = :database AND table_name = :table_name;
```

**SQLite** (sqlite_master + PRAGMA):
```sql
-- 获取所有表和视图
SELECT name, type FROM sqlite_master
WHERE type IN ('table', 'view') AND name NOT LIKE 'sqlite_%';

-- 获取列信息
PRAGMA table_info(:table_name);
```

---

## 4. 本地存储设计

### Decision: SQLite + SQLAlchemy

**选择**: SQLite 作为本地存储，SQLAlchemy 作为 ORM

**Rationale**:
- SQLite 是零配置的嵌入式数据库
- 无需额外服务进程
- 文件存储便于备份和迁移
- SQLAlchemy 提供类型安全和迁移支持

**Storage Location**: `Week2/data/meta.db`

**Schema Design**:
```sql
-- 数据库连接表
CREATE TABLE database_connections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    db_type TEXT NOT NULL,  -- 'postgresql', 'mysql', 'sqlite'
    url TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 元数据缓存表
CREATE TABLE metadata_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    connection_id INTEGER REFERENCES database_connections(id) ON DELETE CASCADE,
    metadata_json TEXT NOT NULL,  -- JSON 格式的元数据
    version_hash TEXT,  -- 用于检测变化
    cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    size_bytes INTEGER DEFAULT 0
);

-- 索引
CREATE INDEX idx_metadata_connection ON metadata_cache(connection_id);
```

---

## 5. AI SQL 生成

### Decision: OpenAI GPT-4 API

**选择**: OpenAI GPT-4 (或 GPT-3.5-turbo) + 结构化提示词

**Rationale**:
- 用户指定使用 OpenAI SDK
- GPT-4 对 SQL 生成有优秀的表现
- 可以通过元数据上下文提高准确性
- API 调用简单，错误处理容易

**Implementation Notes**:

```python
from openai import AsyncOpenAI

async def generate_sql(
    client: AsyncOpenAI,
    prompt: str,
    metadata: dict[str, Any],
    dialect: str
) -> str:
    """使用 OpenAI 生成 SQL"""
    
    system_prompt = f"""你是一个 SQL 专家。根据用户的自然语言描述生成 {dialect} SQL 查询。

数据库结构:
{format_metadata(metadata)}

规则:
1. 只生成 SELECT 语句
2. 不要包含 LIMIT 子句（系统会自动添加）
3. 使用正确的表名和列名
4. 只返回 SQL 语句，不要解释
"""
    
    response = await client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        temperature=0.1,
        max_tokens=500
    )
    
    return response.choices[0].message.content.strip()
```

**Error Handling**:
- 网络错误：显示"AI 服务不可用"
- API 配额：显示"API 配额已用尽"
- 无效响应：显示"无法生成有效 SQL"

---

## 6. 前端技术栈

### Decision: Refine 5 + Ant Design + Monaco Editor

**选择**:
- **Refine 5**: React 数据管理框架
- **Ant Design 5**: UI 组件库
- **Monaco Editor**: SQL 编辑器
- **Tailwind CSS**: 样式框架

**Rationale**:
- Refine 提供数据获取和状态管理的最佳实践
- Ant Design 提供丰富的企业级组件（Table、Form、Tree 等）
- Monaco Editor 是 VS Code 的编辑器核心，功能强大
- Tailwind 提供快速的样式开发

**Alternatives Considered**:

| 组件 | 选择 | 替代方案 | 排除原因 |
|------|------|----------|----------|
| 数据管理 | Refine 5 | React Query, SWR | 用户指定 Refine |
| UI 组件 | Ant Design | MUI, Chakra | 用户指定 Ant Design |
| SQL 编辑器 | Monaco | CodeMirror, Ace | 用户指定 Monaco |
| 样式 | Tailwind | CSS Modules, styled-components | 用户指定 Tailwind |

**Monaco Editor Configuration**:
```typescript
import { Editor } from '@monaco-editor/react';

const SqlEditor: React.FC<Props> = ({ value, onChange, dialect }) => {
  return (
    <Editor
      height="200px"
      language="sql"
      value={value}
      onChange={onChange}
      options={{
        minimap: { enabled: false },
        lineNumbers: 'on',
        scrollBeyondLastLine: false,
        wordWrap: 'on',
        automaticLayout: true,
      }}
    />
  );
};
```

---

## 7. API 设计

### Decision: RESTful API with FastAPI

**选择**: 基于用户提供的 API 设计，使用 FastAPI 实现

**API Endpoints** (from instructions02.md):

```yaml
# 数据库连接管理
GET  /api/v1/dbs          # 获取所有已存储的数据库
PUT  /api/v1/dbs/{name}   # 添加/更新一个数据库
GET  /api/v1/dbs/{name}   # 获取一个数据库的元数据
DELETE /api/v1/dbs/{name} # 删除一个数据库连接

# 查询执行
POST /api/v1/dbs/{name}/query          # 执行 SQL 查询
POST /api/v1/dbs/{name}/query/natural  # 自然语言生成 SQL
```

**CORS Configuration**:
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 8. 错误处理策略

### Decision: 结构化错误响应

**Error Response Format**:
```python
from pydantic import BaseModel
from enum import Enum

class ErrorCode(str, Enum):
    CONNECTION_FAILED = "CONNECTION_FAILED"
    AUTHENTICATION_FAILED = "AUTHENTICATION_FAILED"
    DATABASE_NOT_FOUND = "DATABASE_NOT_FOUND"
    NETWORK_UNREACHABLE = "NETWORK_UNREACHABLE"
    QUERY_TIMEOUT = "QUERY_TIMEOUT"
    SYNTAX_ERROR = "SYNTAX_ERROR"
    INVALID_STATEMENT = "INVALID_STATEMENT"
    AI_SERVICE_ERROR = "AI_SERVICE_ERROR"
    STORAGE_ERROR = "STORAGE_ERROR"

class ErrorResponse(BaseModel):
    code: ErrorCode
    message: str
    details: dict[str, Any] | None = None
```

---

## 9. 测试数据准备

### Decision: Docker Compose + 初始化脚本

**测试数据库**:
- PostgreSQL 测试实例（Docker）
- MySQL 测试实例（Docker）
- SQLite 测试文件

**测试数据内容**:
```sql
-- 用户表
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(255) UNIQUE,
    age INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 订单表
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    total DECIMAL(10, 2),
    status VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 产品表
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200),
    price DECIMAL(10, 2),
    description TEXT,
    category VARCHAR(100)
);

-- 插入示例数据
INSERT INTO users (name, email, age) VALUES
    ('Alice', 'alice@example.com', 30),
    ('Bob', 'bob@example.com', 25),
    ('Charlie', 'charlie@example.com', 35);
```

---

## 10. 性能优化考虑

### Metadata Caching Strategy

```python
async def get_metadata(self, connection_id: int, force_refresh: bool = False) -> Metadata:
    """获取元数据，支持缓存和强制刷新"""
    
    if not force_refresh:
        cached = await self.storage.get_cached_metadata(connection_id)
        if cached:
            # 检查版本变化
            current_hash = await self.calculate_version_hash(connection_id)
            if cached.version_hash == current_hash:
                return cached.metadata
            # 版本变化，返回缓存但标记需要刷新
            cached.needs_refresh = True
            return cached
    
    # 重新提取元数据
    metadata = await self.extract_metadata(connection_id)
    await self.storage.cache_metadata(connection_id, metadata)
    return metadata
```

### Query Result Pagination

虽然当前版本使用 LIMIT 1000，但数据结构设计支持未来分页：

```python
class QueryResult(BaseModel):
    columns: list[ColumnInfo]
    rows: list[dict[str, Any]]
    total_rows: int  # 实际返回行数
    execution_time_ms: int
    truncated: bool  # 是否因 LIMIT 被截断
```

---

## Summary of Decisions

| 领域 | 选择 | 关键理由 |
|------|------|----------|
| SQL 解析 | sqlglot | 多数据库支持，纯 Python |
| 数据库驱动 | asyncpg/aiomysql/aiosqlite | 异步支持，性能优异 |
| 本地存储 | SQLite + SQLAlchemy | 零配置，类型安全 |
| AI 服务 | OpenAI GPT-4 | 用户指定，SQL 生成效果好 |
| 前端框架 | Refine + Ant Design | 用户指定，企业级组件 |
| SQL 编辑器 | Monaco Editor | 用户指定，功能强大 |
| 样式框架 | Tailwind CSS | 用户指定，快速开发 |

---

**Phase 0 Complete**: 所有技术决策已确定，无 NEEDS CLARIFICATION 遗留。
