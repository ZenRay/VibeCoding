# Data Model: 数据库查询工具

**Date**: 2026-01-10  
**Phase**: 1 - Design & Contracts  
**Status**: Complete (评审后修订)  
**Last Updated**: 2026-01-10

## Overview

本文档定义了数据库查询工具的数据模型，包括 API 请求/响应模型（Pydantic）和本地存储模型（SQLAlchemy）。

### 设计原则

1. **时区处理**: 所有日期时间字段使用 UTC 时间存储（`datetime.utcnow()`），前端根据用户时区转换显示
2. **JSON 序列化**: API 响应使用 camelCase，内部代码使用 snake_case
3. **空值处理**: API 响应中可选字段为空时返回 `null`，不省略字段
4. **密码安全**: API 响应不返回密码字段，仅在创建/更新请求中接收
5. **数据迁移**: 使用 Alembic 管理模式版本变更

---

## 1. Pydantic Models (API Layer)

### 1.1 Database Connection Models

```python
# app/models/database.py
from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from pydantic.alias_generators import to_camel


class DatabaseType(str, Enum):
    """支持的数据库类型"""
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    SQLITE = "sqlite"


class DatabaseConnectionCreate(BaseModel):
    """创建/更新数据库连接的请求模型"""
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )
    
    url: str = Field(
        ...,
        description="数据库连接 URL",
        examples=["postgresql://user:pass@localhost:5432/mydb"]
    )


class DatabaseConnectionResponse(BaseModel):
    """数据库连接响应模型
    
    注意：此模型不包含密码字段（安全设计决策）。
    密码仅在 DatabaseConnectionCreate 请求中接收，不在响应中返回。
    """
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )
    
    name: str = Field(
        ..., 
        description="连接名称/标识符",
        min_length=1,
        max_length=100,
        pattern=r"^[a-zA-Z0-9_-]+$"
    )
    db_type: DatabaseType = Field(..., description="数据库类型")
    host: str | None = Field(None, description="主机名（SQLite 为 null）")
    port: int | None = Field(None, description="端口（范围 1-65535，SQLite 为 null）", ge=1, le=65535)
    database: str = Field(..., description="数据库名或文件路径")
    created_at: datetime = Field(..., description="创建时间（UTC）")
    updated_at: datetime = Field(..., description="更新时间（UTC）")
    # 注意：不返回 password 字段


class DatabaseListResponse(BaseModel):
    """数据库列表响应模型"""
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )
    
    databases: list[DatabaseConnectionResponse] = Field(
        default_factory=list,
        description="数据库连接列表"
    )
    total: int = Field(..., description="总数")
```

### 1.2 Metadata Models

```python
# app/models/metadata.py
from pydantic import BaseModel, Field, ConfigDict
from pydantic.alias_generators import to_camel


class ColumnInfo(BaseModel):
    """列信息模型"""
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )
    
    name: str = Field(..., description="列名")
    data_type: str = Field(..., description="数据类型")
    is_nullable: bool = Field(True, description="是否可为空")
    is_primary_key: bool = Field(False, description="是否为主键")
    default_value: str | None = Field(None, description="默认值")
    comment: str | None = Field(None, description="列注释")


class TableInfo(BaseModel):
    """表/视图信息模型"""
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )
    
    name: str = Field(..., description="表名")
    table_type: str = Field("table", description="类型: table 或 view")
    columns: list[ColumnInfo] = Field(default_factory=list, description="列列表")
    row_count: int | None = Field(None, description="估计行数")
    comment: str | None = Field(None, description="表注释")


class DatabaseMetadata(BaseModel):
    """数据库元数据模型"""
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )
    
    name: str = Field(..., description="数据库名")
    db_type: str = Field(..., description="数据库类型")
    tables: list[TableInfo] = Field(default_factory=list, description="表列表")
    views: list[TableInfo] = Field(default_factory=list, description="视图列表")
    version_hash: str | None = Field(None, description="元数据版本哈希")
    cached_at: str | None = Field(None, description="缓存时间")
    needs_refresh: bool = Field(False, description="是否需要刷新")
    warnings: list[str] = Field(default_factory=list, description="提取时的警告信息")
```

### 1.3 Query Models

```python
# app/models/query.py
from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from pydantic.alias_generators import to_camel
from typing import Any


class QueryStatus(str, Enum):
    """查询状态"""
    PENDING = "pending"
    EXECUTING = "executing"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class QueryRequest(BaseModel):
    """SQL 查询请求模型"""
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )
    
    sql: str = Field(..., description="SQL 查询语句", min_length=1)


class NaturalLanguageQueryRequest(BaseModel):
    """自然语言查询请求模型"""
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )
    
    prompt: str = Field(
        ...,
        description="自然语言查询描述",
        min_length=1,
        examples=["查询所有用户的姓名和邮箱"]
    )


class QueryResultColumn(BaseModel):
    """查询结果列信息"""
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )
    
    name: str = Field(..., description="列名")
    data_type: str = Field(..., description="数据类型")


class QueryResult(BaseModel):
    """查询结果模型"""
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )
    
    columns: list[QueryResultColumn] = Field(..., description="列信息")
    rows: list[dict[str, Any]] = Field(..., description="行数据")
    row_count: int = Field(..., description="返回行数")
    execution_time_ms: int = Field(..., description="执行时间（毫秒）")
    truncated: bool = Field(False, description="是否因 LIMIT 被截断")
    sql: str = Field(..., description="执行的 SQL（可能被修改添加 LIMIT）")


class NaturalLanguageQueryResult(BaseModel):
    """自然语言查询结果模型"""
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )
    
    generated_sql: str = Field(..., description="生成的 SQL")
    result: QueryResult | None = Field(None, description="查询结果（如果执行）")
    generation_time_ms: int = Field(..., description="SQL 生成时间（毫秒）")
```

### 1.4 Error Models

```python
# app/models/error.py
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict
from pydantic.alias_generators import to_camel
from typing import Any


class ErrorCode(str, Enum):
    """错误代码"""
    # 连接错误
    CONNECTION_FAILED = "CONNECTION_FAILED"
    AUTHENTICATION_FAILED = "AUTHENTICATION_FAILED"
    DATABASE_NOT_FOUND = "DATABASE_NOT_FOUND"
    NETWORK_UNREACHABLE = "NETWORK_UNREACHABLE"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    
    # 查询错误
    QUERY_TIMEOUT = "QUERY_TIMEOUT"
    QUERY_CANCELLED = "QUERY_CANCELLED"
    SYNTAX_ERROR = "SYNTAX_ERROR"
    INVALID_STATEMENT = "INVALID_STATEMENT"
    
    # AI 服务错误
    AI_SERVICE_UNAVAILABLE = "AI_SERVICE_UNAVAILABLE"
    AI_QUOTA_EXCEEDED = "AI_QUOTA_EXCEEDED"
    AI_INVALID_RESPONSE = "AI_INVALID_RESPONSE"
    
    # 存储错误
    STORAGE_FULL = "STORAGE_FULL"
    STORAGE_CORRUPTED = "STORAGE_CORRUPTED"
    
    # 通用错误
    NOT_FOUND = "NOT_FOUND"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class ErrorResponse(BaseModel):
    """错误响应模型"""
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )
    
    code: ErrorCode = Field(..., description="错误代码")
    message: str = Field(..., description="错误消息")
    details: dict[str, Any] | None = Field(None, description="详细信息")


class ValidationErrorDetail(BaseModel):
    """验证错误详情"""
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )
    
    field: str = Field(..., description="字段名")
    message: str = Field(..., description="错误信息")
    value: Any = Field(None, description="错误值")
```

---

## 2. SQLAlchemy Models (Storage Layer)

### 2.1 Database Connection Storage

```python
# app/storage/models.py
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship, DeclarativeBase


class Base(DeclarativeBase):
    pass


class DatabaseConnection(Base):
    """数据库连接存储模型"""
    __tablename__ = "database_connections"
    
    id: int = Column(Integer, primary_key=True, autoincrement=True)
    name: str = Column(String(255), unique=True, nullable=False, index=True)
    db_type: str = Column(String(50), nullable=False)  # postgresql, mysql, sqlite
    url: str = Column(Text, nullable=False)  # 完整连接 URL（明文存储）
    host: str | None = Column(String(255), nullable=True)
    port: int | None = Column(Integer, nullable=True)
    database: str = Column(String(255), nullable=False)
    created_at: datetime = Column(DateTime, default=datetime.utcnow)
    updated_at: datetime = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联元数据缓存
    metadata_cache = relationship(
        "MetadataCache",
        back_populates="connection",
        cascade="all, delete-orphan",
        uselist=False
    )


class MetadataCache(Base):
    """元数据缓存存储模型"""
    __tablename__ = "metadata_cache"
    
    id: int = Column(Integer, primary_key=True, autoincrement=True)
    connection_id: int = Column(
        Integer,
        ForeignKey("database_connections.id", ondelete="CASCADE"),
        nullable=False,
        unique=True
    )
    metadata_json: str = Column(Text, nullable=False)  # JSON 序列化的元数据
    version_hash: str | None = Column(String(64), nullable=True)  # SHA-256 哈希
    size_bytes: int = Column(Integer, default=0)
    cached_at: datetime = Column(DateTime, default=datetime.utcnow)
    
    # 关联数据库连接
    connection = relationship("DatabaseConnection", back_populates="metadata_cache")
    
    __table_args__ = (
        Index("idx_metadata_connection", "connection_id"),
    )
```

---

## 3. Entity Relationships

```
┌─────────────────────────────────────────────────────────────────┐
│                         API Layer                                │
├─────────────────────────────────────────────────────────────────┤
│  DatabaseConnectionCreate    ──┐                                │
│  DatabaseConnectionResponse  ←─┼── API 请求/响应                  │
│  DatabaseListResponse        ──┘                                │
│                                                                 │
│  DatabaseMetadata ◄──────────────── 包含 ──┐                     │
│       │                                    │                    │
│       ├── TableInfo[]                      │                    │
│       │      └── ColumnInfo[]              │                    │
│       └── views: TableInfo[]               │                    │
│                                            │                    │
│  QueryRequest / NaturalLanguageQueryRequest │                   │
│       └──► QueryResult                      │                   │
│               ├── columns: QueryResultColumn[]                  │
│               └── rows: dict[]                                  │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                       Storage Layer                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  DatabaseConnection ─────────────1:1─────────── MetadataCache   │
│       │                                              │          │
│       ├── id (PK)                                    ├── id (PK)│
│       ├── name (UNIQUE)                              ├── connection_id (FK)│
│       ├── db_type                                    ├── metadata_json    │
│       ├── url                                        ├── version_hash     │
│       ├── host/port/database                         ├── size_bytes       │
│       └── created_at/updated_at                      └── cached_at        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 4. State Transitions

### 4.1 Query Execution State Machine

```
                    ┌─────────────┐
                    │   PENDING   │
                    └──────┬──────┘
                           │ execute()
                           ▼
                    ┌─────────────┐
         ┌──────────│  EXECUTING  │──────────┐
         │          └──────┬──────┘          │
         │ cancel()        │                 │ timeout
         ▼                 │                 ▼
  ┌─────────────┐          │          ┌─────────────┐
  │  CANCELLED  │          │          │   TIMEOUT   │
  └─────────────┘          │          └─────────────┘
                           │
              ┌────────────┴────────────┐
              │                         │
              ▼ success                 ▼ error
       ┌─────────────┐           ┌─────────────┐
       │   SUCCESS   │           │   FAILED    │
       └─────────────┘           └─────────────┘
```

**状态转换规则**:

| 当前状态 | 允许转换到 | 触发条件 |
|----------|------------|----------|
| PENDING | EXECUTING | 调用 execute() |
| EXECUTING | SUCCESS | 查询成功完成 |
| EXECUTING | FAILED | 查询执行出错 |
| EXECUTING | CANCELLED | 用户点击取消 |
| EXECUTING | TIMEOUT | 超过 30 秒 |

**并发处理**: 当取消和超时同时发生时，优先处理先到达的事件。如果无法确定顺序，优先标记为 CANCELLED（用户主动操作优先）。

**非法转换处理**: 任何从终态（SUCCESS、FAILED、CANCELLED、TIMEOUT）的状态转换尝试都应被忽略并记录警告日志，不抛出异常。

### 4.2 Database Connection State

```
                    ┌─────────────┐
                    │  NOT_SAVED  │
                    └──────┬──────┘
                           │ PUT /api/v1/dbs/{name}
                           ▼
                    ┌─────────────┐
    ┌───────────────│    SAVED    │───────────────┐
    │               └──────┬──────┘               │
    │ refresh()            │                      │ delete()
    ▼                      │ connect()            ▼
┌─────────────┐            │              ┌─────────────┐
│  REFRESHING │            ▼              │   DELETED   │
└──────┬──────┘     ┌─────────────┐       └─────────────┘
       │            │  CONNECTED  │
       └───────────►└─────────────┘
```

---

## 5. Validation Rules

### 5.1 Database Connection URL Validation

```python
import re
from urllib.parse import urlparse

def validate_connection_url(url: str) -> tuple[bool, str | None, dict[str, Any]]:
    """验证数据库连接 URL"""
    
    # PostgreSQL: postgresql://user:password@host:port/database
    # MySQL: mysql://user:password@host:port/database
    # SQLite: sqlite:///path/to/database.db
    
    parsed = urlparse(url)
    
    if parsed.scheme == "sqlite":
        if not parsed.path:
            return False, "SQLite URL 必须包含文件路径", {}
        return True, None, {
            "db_type": "sqlite",
            "database": parsed.path,
        }
    
    if parsed.scheme in ("postgresql", "postgres"):
        if not parsed.hostname:
            return False, "PostgreSQL URL 必须包含主机名", {}
        return True, None, {
            "db_type": "postgresql",
            "host": parsed.hostname,
            "port": parsed.port or 5432,
            "database": parsed.path.lstrip("/"),
        }
    
    if parsed.scheme == "mysql":
        if not parsed.hostname:
            return False, "MySQL URL 必须包含主机名", {}
        return True, None, {
            "db_type": "mysql",
            "host": parsed.hostname,
            "port": parsed.port or 3306,
            "database": parsed.path.lstrip("/"),
        }
    
    return False, f"不支持的数据库类型: {parsed.scheme}", {}
```

### 5.2 SQL Validation Rules

```python
# SQL 验证规则
SQL_VALIDATION_RULES = {
    "allowed_statements": ["SELECT"],
    "forbidden_statements": [
        "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE",
        "TRUNCATE", "GRANT", "REVOKE", "EXECUTE", "CALL"
    ],
    "max_query_length": 10000,  # 字符
    "default_limit": 1000,
    "max_limit": 10000,
    "timeout_seconds": 30,
}

# 连接名称验证规则
CONNECTION_NAME_RULES = {
    "pattern": r"^[a-zA-Z0-9_-]+$",
    "min_length": 1,
    "max_length": 100,
}

# 端口号验证规则
PORT_RULES = {
    "min": 1,
    "max": 65535,
    "default_postgresql": 5432,
    "default_mysql": 3306,
}
```

**注意**: 所有 SQL 验证规则同时适用于手动输入的 SQL 和 AI 生成的 SQL。

---

## 6. Index Strategy

```sql
-- 主要索引
CREATE UNIQUE INDEX idx_db_connections_name ON database_connections(name);
CREATE INDEX idx_metadata_cache_connection ON metadata_cache(connection_id);

-- 查询优化索引
CREATE INDEX idx_db_connections_type ON database_connections(db_type);
CREATE INDEX idx_metadata_cache_cached_at ON metadata_cache(cached_at);
```

---

## 7. Data Migration Strategy

### 7.1 Migration Tool

使用 **Alembic** 管理数据库模式迁移：

```python
# alembic.ini 配置
[alembic]
script_location = alembic
sqlalchemy.url = sqlite:///%(here)s/../data/meta.db

# 迁移脚本命名约定
file_template = %%(year)d%%(month).2d%%(day).2d_%%(hour).2d%%(minute).2d_%%(rev)s_%%(slug)s
```

### 7.2 Migration Rules

1. **向前兼容**: 每次迁移必须包含 `upgrade()` 和 `downgrade()` 函数
2. **数据保留**: 迁移不应删除用户数据，仅修改模式
3. **版本追踪**: 在 `alembic_version` 表中记录当前版本
4. **自动应用**: 应用启动时自动检查并应用待执行的迁移

### 7.3 Example Migration

```python
"""add_version_hash_to_metadata_cache

Revision ID: 001
Create Date: 2026-01-10
"""

def upgrade():
    op.add_column('metadata_cache', 
        sa.Column('version_hash', sa.String(64), nullable=True))

def downgrade():
    op.drop_column('metadata_cache', 'version_hash')
```

---

## Summary

本数据模型设计遵循以下原则：

1. **严格类型标注**: 所有 Pydantic 模型使用完整的类型标注
2. **camelCase JSON**: API 响应使用 `alias_generator=to_camel`
3. **snake_case 内部**: Python 代码和数据库字段使用 snake_case
4. **关系明确**: 一对一关系（Connection ↔ MetadataCache）
5. **状态清晰**: 使用枚举定义所有状态，定义状态转换规则
6. **验证完整**: 包含 URL 验证、SQL 验证、连接名称验证规则
7. **时区一致**: 所有时间使用 UTC 存储
8. **密码安全**: API 响应不返回密码字段
9. **空值明确**: 可选字段为空时返回 null，不省略
10. **迁移支持**: 使用 Alembic 管理模式版本变更

**Phase 1 Data Model Complete** ✅ (评审后修订)
