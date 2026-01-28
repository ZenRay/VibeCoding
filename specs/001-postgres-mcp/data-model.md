# 数据模型：PostgreSQL 自然语言查询 MCP 服务器

**日期**: 2026-01-28
**状态**: Phase 1 完成
**相关文档**: [spec.md](./spec.md) | [plan.md](./plan.md) | [research.md](./research.md)

本文档定义系统中所有数据实体、关系、验证规则和状态转换。所有模型使用 **Pydantic 2.10+** 实现。

---

## 实体关系图

```text
┌─────────────────────┐
│ DatabaseConnection  │
│ (配置实体)          │
└──────────┬──────────┘
           │ 1
           │ has
           │ *
┌──────────▼──────────┐
│  DatabaseSchema     │
│  (缓存实体)         │
└──────────┬──────────┘
           │ contains
           │
           ├────┐
           │    │ *
           │    ▼
           │  ┌──────────────┐
           │  │ TableSchema  │
           │  └──────┬───────┘
           │         │ has
           │         │ *
           │         ▼
           │  ┌──────────────┐
           │  │ ColumnSchema │
           │  └──────────────┘
           │
┌──────────▼──────────┐
│   QueryRequest      │
│   (请求实体)        │
└──────────┬──────────┘
           │ 1
           │ generates
           │ 1
┌──────────▼──────────┐
│  GeneratedQuery     │
│  (SQL 实体)         │
└──────────┬──────────┘
           │ 1
           │ produces
           │ 0..1
┌──────────▼──────────┐
│   QueryResult       │
│   (结果实体)        │
└──────────┬──────────┘
           │
           │ logged as
           │
┌──────────▼──────────┐
│  QueryLogEntry      │
│  (审计实体)         │
└─────────────────────┘
```

---

## 核心实体定义

### 1. DatabaseConnection（数据库连接配置）

**用途**: 存储数据库连接信息和状态

**字段**:

| 字段 | 类型 | 必填 | 默认值 | 验证规则 |
|------|------|------|--------|---------|
| name | str | ✅ | - | 1-64 字符，字母数字下划线 |
| host | str | ✅ | - | 非空字符串 |
| port | int | ✅ | 5432 | 1-65535 |
| database | str | ✅ | - | 非空字符串 |
| user | str | ✅ | - | 非空字符串 |
| password_env_var | str | ✅ | - | 环境变量名（如 DB_PASSWORD） |
| ssl_mode | str | ✅ | "prefer" | disable/allow/prefer/require |
| min_pool_size | int | ✅ | 5 | 1-50 |
| max_pool_size | int | ✅ | 20 | 1-100, >= min_pool_size |
| status | ConnectionStatus | ❌ | DISCONNECTED | Enum 值 |
| connection_type | ConnectionType | ✅ | PRECONFIGURED | Enum 值 |

**状态枚举**:

```python
class ConnectionStatus(str, Enum):
    CONNECTED = "connected"       # 连接池已初始化且可用
    DISCONNECTED = "disconnected" # 未初始化或已关闭
    ERROR = "error"               # 连接失败（配置错误、网络问题）

class ConnectionType(str, Enum):
    PRECONFIGURED = "preconfigured"  # 配置文件预定义
    DYNAMIC = "dynamic"              # MCP 客户端临时传递
```

**Pydantic 模型**:

```python
# models/connection.py
from pydantic import BaseModel, Field, field_validator
from enum import Enum

class DatabaseConnection(BaseModel, frozen=True):
    """数据库连接配置（不可变）"""
    name: str = Field(..., min_length=1, max_length=64)
    host: str = Field(..., min_length=1)
    port: int = Field(5432, ge=1, le=65535)
    database: str = Field(..., min_length=1)
    user: str = Field(..., min_length=1)
    password_env_var: str = Field(..., description="密码的环境变量名")
    ssl_mode: str = Field("prefer", pattern="^(disable|allow|prefer|require)$")
    min_pool_size: int = Field(5, ge=1, le=50)
    max_pool_size: int = Field(20, ge=1, le=100)
    connection_type: ConnectionType = ConnectionType.PRECONFIGURED

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError("名称只能包含字母、数字、下划线和连字符")
        return v

    @field_validator('max_pool_size')
    @classmethod
    def validate_pool_sizes(cls, v: int, info) -> int:
        min_size = info.data.get('min_pool_size', 5)
        if v < min_size:
            raise ValueError(f"max_pool_size ({v}) 必须 >= min_pool_size ({min_size})")
        return v
```

---

### 2. DatabaseSchema（数据库 Schema 缓存）

**用途**: 存储数据库结构元数据，用于 SQL 生成上下文

**字段**:

| 字段 | 类型 | 说明 |
|------|------|------|
| database_name | str | 数据库名称 |
| tables | Dict[str, TableSchema] | 表名 → 表 schema 映射 |
| views | List[str] | 视图名称列表 |
| custom_types | Dict[str, str] | 自定义类型（ENUM 等） |
| last_updated | datetime | 最后更新时间 |
| table_count | int | 表数量（计算属性） |

**Pydantic 模型**:

```python
# models/schema.py
from datetime import datetime, UTC
from typing import Dict, List
from pydantic import BaseModel, Field, computed_field

class ColumnSchema(BaseModel, frozen=True):
    """列 schema"""
    name: str
    data_type: str  # PostgreSQL 类型（text, integer, jsonb 等）
    nullable: bool = True
    primary_key: bool = False
    foreign_key_table: str | None = None
    foreign_key_column: str | None = None
    default_value: str | None = None

class IndexSchema(BaseModel, frozen=True):
    """索引 schema"""
    name: str
    columns: List[str]
    unique: bool = False
    index_type: str = "btree"  # btree, hash, gin, gist

class TableSchema(BaseModel, frozen=True):
    """表 schema"""
    name: str
    columns: List[ColumnSchema]
    indexes: List[IndexSchema] = Field(default_factory=list)
    row_count_estimate: int | None = None  # pg_class.reltuples
    sample_data: List[Dict[str, Any]] = Field(default_factory=list, max_length=3)

    @computed_field
    @property
    def primary_keys(self) -> List[str]:
        """返回主键列名"""
        return [col.name for col in self.columns if col.primary_key]

    @computed_field
    @property
    def foreign_keys(self) -> List[Dict[str, str]]:
        """返回外键关系"""
        fks = []
        for col in self.columns:
            if col.foreign_key_table:
                fks.append({
                    "column": col.name,
                    "ref_table": col.foreign_key_table,
                    "ref_column": col.foreign_key_column
                })
        return fks

class DatabaseSchema(BaseModel):
    """数据库 schema（可变，支持刷新）"""
    database_name: str
    tables: Dict[str, TableSchema] = Field(default_factory=dict)
    views: List[str] = Field(default_factory=list)
    custom_types: Dict[str, str] = Field(default_factory=dict)
    last_updated: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @computed_field
    @property
    def table_count(self) -> int:
        return len(self.tables)

    def to_ddl(self, table_names: List[str] | None = None) -> str:
        """转换为 DDL 格式（用于 AI prompt）"""
        tables_to_export = table_names if table_names else list(self.tables.keys())

        ddl_parts = []
        for table_name in tables_to_export:
            if table_name not in self.tables:
                continue

            table = self.tables[table_name]
            columns = []

            for col in table.columns:
                col_def = f"  {col.name} {col.data_type}"
                if not col.nullable:
                    col_def += " NOT NULL"
                if col.primary_key:
                    col_def += " PRIMARY KEY"
                columns.append(col_def)

            # 外键
            for fk in table.foreign_keys:
                columns.append(
                    f"  FOREIGN KEY ({fk['column']}) REFERENCES {fk['ref_table']}({fk['ref_column']})"
                )

            ddl = f"CREATE TABLE {table_name} (\n" + ",\n".join(columns) + "\n);"

            # 示例数据
            if table.sample_data:
                samples = [f"  {row}" for row in table.sample_data]
                ddl += f"\n-- 示例数据 ({len(samples)} 行):\n" + "\n".join(samples)

            ddl_parts.append(ddl)

        return "\n\n".join(ddl_parts)
```

---

### 3. QueryRequest（查询请求）

**用途**: 封装用户的自然语言查询请求

**字段**:

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| request_id | str (UUID) | ✅ | auto | 唯一请求标识符 |
| natural_language | str | ✅ | - | 用户的自然语言描述 |
| database | str | ❌ | None | 目标数据库名（None = 默认） |
| response_mode | ResponseMode | ✅ | SQL_ONLY | 响应模式 |
| user_id | str | ❌ | None | 用户标识符（审计用） |
| timestamp | datetime | ✅ | auto | 请求时间戳 |
| context | Dict[str, Any] | ❌ | {} | 额外上下文信息 |

**状态枚举**:

```python
class ResponseMode(str, Enum):
    SQL_ONLY = "sql_only"  # 仅返回 SQL
    EXECUTE = "execute"     # 返回 SQL + 执行结果
```

**Pydantic 模型**:

```python
# models/query.py
from uuid import uuid4
from datetime import datetime, UTC
from typing import Dict, Any
from pydantic import BaseModel, Field

class QueryRequest(BaseModel):
    """查询请求"""
    request_id: str = Field(default_factory=lambda: str(uuid4()))
    natural_language: str = Field(..., min_length=1, max_length=2000)
    database: str | None = Field(None, description="目标数据库（None = 默认）")
    response_mode: ResponseMode = ResponseMode.SQL_ONLY
    user_id: str | None = Field(None, description="用户标识符")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    context: Dict[str, Any] = Field(default_factory=dict)

    @field_validator('natural_language')
    @classmethod
    def validate_nl(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("自然语言描述不能为空")
        return v
```

---

### 4. GeneratedQuery（生成的 SQL 查询）

**用途**: 封装 AI 生成的 SQL 及验证结果

**字段**:

| 字段 | 类型 | 说明 |
|------|------|------|
| sql | str | 生成的 SQL 查询 |
| validated | bool | 是否通过安全验证 |
| validation_error | str | None | 验证失败原因 |
| warnings | List[str] | 警告消息（如缺少 LIMIT） |
| explanation | str | None | AI 生成的解释 |
| assumptions | List[str] | AI 的假设说明 |
| generated_at | datetime | 生成时间戳 |
| generation_method | GenerationMethod | 生成方式 |

**状态枚举**:

```python
class GenerationMethod(str, Enum):
    AI_GENERATED = "ai_generated"      # OpenAI 生成
    TEMPLATE_MATCHED = "template_matched"  # 模板库匹配
    RETRY_GENERATED = "retry_generated"    # 重试后生成
```

**Pydantic 模型**:

```python
# models/query.py (续)
class GeneratedQuery(BaseModel):
    """生成的 SQL 查询"""
    sql: str = Field(..., min_length=1)
    validated: bool
    validation_error: str | None = None
    warnings: List[str] = Field(default_factory=list)
    explanation: str | None = None
    assumptions: List[str] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    generation_method: GenerationMethod = GenerationMethod.AI_GENERATED

    @field_validator('sql')
    @classmethod
    def validate_sql_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("SQL 不能为空")
        return v.strip()
```

---

### 5. QueryResult（查询执行结果）

**用途**: 封装查询执行的结果数据

**字段**:

| 字段 | 类型 | 说明 |
|------|------|------|
| columns | List[ColumnInfo] | 列元数据 |
| rows | List[Dict[str, Any]] | 结果行数据 |
| row_count | int | 返回的行数 |
| execution_time_ms | float | 执行耗时（毫秒） |
| truncated | bool | 是否因 LIMIT 截断 |
| errors | List[str] | 执行错误（如有） |

**嵌套模型**:

```python
# models/result.py
from typing import List, Dict, Any
from pydantic import BaseModel, Field

class ColumnInfo(BaseModel, frozen=True):
    """列元数据"""
    name: str
    type: str  # PostgreSQL 类型
    table: str | None = None  # 来源表（JOIN 查询时有用）

class QueryResult(BaseModel):
    """查询执行结果"""
    columns: List[ColumnInfo]
    rows: List[Dict[str, Any]] = Field(default_factory=list)
    row_count: int = Field(ge=0)
    execution_time_ms: float = Field(ge=0)
    truncated: bool = False
    errors: List[str] = Field(default_factory=list)

    @computed_field
    @property
    def has_data(self) -> bool:
        """是否有数据"""
        return self.row_count > 0

    def to_csv(self) -> str:
        """转换为 CSV 格式"""
        import csv
        import io

        output = io.StringIO()
        if not self.columns:
            return ""

        writer = csv.DictWriter(output, fieldnames=[col.name for col in self.columns])
        writer.writeheader()
        writer.writerows(self.rows)

        return output.getvalue()
```

---

### 6. QueryLogEntry（查询审计日志）

**用途**: 记录所有查询尝试，用于审计和分析

**字段**:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| timestamp | str (ISO 8601) | ✅ | 请求时间戳 |
| request_id | str (UUID) | ✅ | 关联 QueryRequest |
| database | str | ❌ | 目标数据库 |
| user_id | str | ❌ | 用户标识符 |
| natural_language | str | ✅ | 原始自然语言查询 |
| sql | str | ❌ | 生成的 SQL（失败时为 null） |
| status | LogStatus | ✅ | 查询状态 |
| execution_time_ms | float | ❌ | 执行耗时 |
| row_count | int | ❌ | 返回行数 |
| error_message | str | ❌ | 错误消息 |
| generation_method | str | ❌ | 生成方式 |

**状态枚举**:

```python
class LogStatus(str, Enum):
    SUCCESS = "success"               # 成功生成并执行
    VALIDATION_FAILED = "validation_failed"  # SQL 验证失败
    EXECUTION_FAILED = "execution_failed"    # 执行失败
    AI_FAILED = "ai_failed"           # AI 服务不可用
    TEMPLATE_MATCHED = "template_matched"    # 使用模板
```

**Pydantic 模型**:

```python
# models/log_entry.py
from pydantic import BaseModel, Field
from datetime import datetime, UTC

class QueryLogEntry(BaseModel):
    """查询审计日志条目"""
    timestamp: str = Field(
        default_factory=lambda: datetime.now(UTC).isoformat()
    )
    request_id: str
    database: str | None = None
    user_id: str | None = None
    natural_language: str
    sql: str | None = None
    status: LogStatus
    execution_time_ms: float | None = Field(None, ge=0)
    row_count: int | None = Field(None, ge=0)
    error_message: str | None = None
    generation_method: str | None = None

    def to_jsonl(self) -> str:
        """转换为 JSONL 格式（单行 JSON）"""
        return self.model_dump_json(exclude_none=True, by_alias=True)
```

---

### 7. QueryTemplate（查询模板）

**用途**: 定义 SQL 模板用于降级方案

**字段**:

| 字段 | 类型 | 说明 |
|------|------|------|
| name | str | 模板名称 |
| description | str | 模板描述 |
| priority | int | 优先级（0-100） |
| keywords | List[str] | 触发关键词 |
| patterns | List[str] | 正则模式 |
| parameters | List[TemplateParameter] | 参数定义 |
| sql_template | str | SQL 模板（带占位符） |
| examples | List[Dict] | 使用示例 |

**Pydantic 模型**:

```python
# models/template.py
from pydantic import BaseModel, Field
from typing import List, Dict, Any
from enum import Enum

class ParameterType(str, Enum):
    IDENTIFIER = "identifier"  # 表名、列名
    EXPRESSION = "expression"  # WHERE 条件表达式
    KEYWORD = "keyword"        # ORDER BY, GROUP BY 等
    LITERAL = "literal"        # 字符串或数字字面量

class TemplateParameter(BaseModel, frozen=True):
    """模板参数定义"""
    name: str
    type: ParameterType
    description: str
    required: bool = True
    default: str | None = None
    validation_pattern: str | None = None

class QueryTemplate(BaseModel, frozen=True):
    """查询模板"""
    name: str = Field(..., pattern="^[a-z_]+$")
    description: str
    priority: int = Field(..., ge=0, le=100)
    keywords: List[str] = Field(..., min_length=1)
    patterns: List[str] = Field(default_factory=list)
    parameters: List[TemplateParameter]
    sql_template: str = Field(..., min_length=1)
    examples: List[Dict[str, Any]] = Field(default_factory=list)

    def generate_sql(self, params: Dict[str, str]) -> str:
        """基于参数生成 SQL"""
        sql = self.sql_template

        for param in self.parameters:
            if param.required and param.name not in params:
                if param.default:
                    params[param.name] = param.default
                else:
                    raise ValueError(f"缺少必需参数: {param.name}")

            value = params.get(param.name, param.default)
            sql = sql.replace(f"{{{param.name}}}", value)

        return sql
```

---

## 实体关系

### 1. DatabaseConnection → DatabaseSchema (1:1)

每个数据库连接对应一个 schema 缓存。

```python
class SchemaCache:
    """Schema 缓存管理器"""

    def __init__(self):
        self._schemas: Dict[str, DatabaseSchema] = {}
        self._lock = asyncio.Lock()

    async def get_schema(self, database_name: str) -> DatabaseSchema | None:
        """获取数据库 schema"""
        async with self._lock:
            return self._schemas.get(database_name)

    async def set_schema(self, database_name: str, schema: DatabaseSchema):
        """更新 schema 缓存"""
        async with self._lock:
            self._schemas[database_name] = schema
```

### 2. QueryRequest → GeneratedQuery (1:1)

每个请求生成一个 SQL 查询。

### 3. GeneratedQuery → QueryResult (1:0..1)

仅当 `response_mode=EXECUTE` 且 SQL 验证通过时，生成查询结果。

### 4. 所有实体 → QueryLogEntry (N:1)

每次查询尝试记录一条日志。

---

## 数据验证规则

### 输入验证

1. **自然语言长度**: 1-2000 字符
2. **数据库名称**: 必须存在于配置中
3. **Response Mode**: 枚举值验证
4. **SQL 长度**: 生成的 SQL 不超过 10,000 字符

### Schema 验证

1. **表名唯一性**: 同一数据库内表名不重复
2. **外键引用**: 引用的表必须存在
3. **数据类型**: 必须是有效的 PostgreSQL 类型
4. **主键**: 每个表至少有一个主键或唯一标识

### SQL 验证

1. **语句类型**: 必须是 SELECT
2. **表名存在性**: 所有引用的表必须在 schema 中
3. **列名存在性**: 所有引用的列必须在对应表中
4. **函数黑名单**: 不允许危险函数

---

## 状态转换

### DatabaseConnection 状态机

```text
     [初始化]
         │
         ▼
   DISCONNECTED ──┐
         │        │
         │ connect()
         ▼        │
    CONNECTED     │
         │        │
         │ error  │
         ▼        │
      ERROR ──────┘
         │
         │ close()
         ▼
   DISCONNECTED
```

### QueryRequest 处理流程

```text
   [用户输入]
         │
         ▼
   QueryRequest (created)
         │
         ├─→ SQLGenerator.generate()
         │        │
         │        ▼
         │   GeneratedQuery (pending)
         │        │
         │        ├─→ SQLValidator.validate()
         │        │        │
         │        │        ├─→ valid → GeneratedQuery (validated)
         │        │        │
         │        │        └─→ invalid → GeneratedQuery (rejected)
         │        │                       │
         │        │                       └─→ retry (max 1 次)
         │        │
         │        └─→ if response_mode=EXECUTE
         │                    │
         │                    ▼
         │             QueryExecutor.execute()
         │                    │
         │                    ├─→ success → QueryResult (with data)
         │                    │
         │                    └─→ error → QueryResult (with errors)
         │
         └─→ JSONLWriter.log(QueryLogEntry)
```

---

## 数据持久化

### 1. Schema 缓存（内存）

**存储**: Python `Dict[str, DatabaseSchema]`
**并发**: `asyncio.Lock` 保护
**刷新**: 周期性（5 分钟）+ 手动触发
**生命周期**: 服务器启动 → 运行时 → 关闭清空

### 2. 查询历史（JSONL 文件）

**位置**: `logs/queries/YYYY-MM-DD.jsonl`
**写入**: 异步缓冲（5 秒或 100 条）
**轮转**: 每日午夜 UTC
**清理**: 30 天后自动删除
**格式**: 每行一个 JSON 对象

### 3. 配置（YAML 文件）

**位置**: `config/config.yaml`
**格式**:

```yaml
# config/config.yaml
server:
  name: "postgres-mcp"
  version: "0.1.0"

databases:
  - name: "production"
    host: "localhost"
    port: 5432
    database: "myapp"
    user: "readonly_user"
    password_env_var: "PROD_DB_PASSWORD"
    ssl_mode: "require"
    min_pool_size: 5
    max_pool_size: 20

  - name: "analytics"
    host: "analytics-db.example.com"
    port: 5432
    database: "analytics"
    user: "analyst"
    password_env_var: "ANALYTICS_DB_PASSWORD"
    ssl_mode: "prefer"

default_database: "production"

openai:
  api_key_env_var: "OPENAI_API_KEY"
  model: "gpt-4o-mini-2024-07-18"
  temperature: 0.0
  max_tokens: 1000

schema_cache:
  poll_interval_minutes: 5
  load_sample_data: true
  max_sample_rows: 3

query:
  default_limit: 1000
  max_timeout_seconds: 30
  enable_result_validation: false  # FR-015 (可选)

templates:
  enabled: true
  directory: "src/postgres_mcp/templates/queries"

logging:
  level: "INFO"
  directory: "logs/queries"
  retention_days: 30
  max_file_size_mb: 100
  buffer_size: 100
  flush_interval_seconds: 5.0
```

---

## 数据约束

### 内存限制

| 实体 | 单实体大小 | 数量 | 总内存 |
|------|----------|------|--------|
| TableSchema | ~5KB | 100 表 | ~500KB |
| DatabaseSchema | ~500KB | 10 数据库 | ~5MB |
| 查询缓存 | ~2KB | 1000 条 | ~2MB |
| **总计** | - | - | **~10MB** |

远低于 500MB 约束，安全余量充足。

### 磁盘限制

| 文件类型 | 单文件大小 | 轮转 | 保留 | 总磁盘 |
|---------|----------|------|------|--------|
| 查询日志 | 100MB | 每日 | 30 天 | ~3GB |
| 配置文件 | <10KB | - | - | <10KB |
| **总计** | - | - | - | **~3GB** |

---

## 性能考虑

### 模型验证性能

| 模型 | 验证时间 | 吞吐量 |
|------|---------|--------|
| QueryRequest | <0.1ms | 10K+ req/s |
| DatabaseSchema | ~1-5ms | 200-1000/s |
| QueryResult | ~0.5-2ms | 500-2000/s |

### Schema 缓存刷新

```python
async def refresh_schema(self, database_name: str) -> DatabaseSchema:
    """刷新单个数据库的 schema"""
    async with self.pool_manager.get_connection(database_name) as conn:
        # 并行查询 schema 元数据
        tables_task = self._load_tables(conn)
        views_task = self._load_views(conn)
        types_task = self._load_custom_types(conn)

        tables, views, custom_types = await asyncio.gather(
            tables_task, views_task, types_task
        )

        schema = DatabaseSchema(
            database_name=database_name,
            tables=tables,
            views=views,
            custom_types=custom_types
        )

        await self.cache.set_schema(database_name, schema)
        return schema
```

---

## 下一步

✅ **Phase 0 完成**: research.md
✅ **Phase 1 进行中**: data-model.md（本文件）
⏳ **待完成**: contracts/, quickstart.md, 更新 CLAUDE.md

