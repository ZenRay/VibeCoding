# 数据库设计和迁移指南

**文档版本**: v1.0  
**创建时间**: 2026-01-08  
**最后更新**: 2026-01-08

## 📋 目录

1. [概述](#概述)
2. [数据库架构](#数据库架构)
3. [表结构设计](#表结构设计)
4. [索引和约束](#索引和约束)
5. [数据库迁移](#数据库迁移)
6. [测试数据库](#测试数据库)

---

## 概述

### 技术选型

- **生产环境**：PostgreSQL 16
- **测试环境**：SQLite（文件数据库）
- **ORM**：SQLAlchemy 2.0+
- **迁移工具**：Alembic 1.13+

### 设计原则

✅ **数据库无关**：业务逻辑不依赖特定数据库特性  
✅ **软删除**：使用 `deleted_at` 字段，不物理删除  
✅ **时间戳**：所有表包含 `created_at`, `updated_at`  
✅ **索引优化**：为查询字段添加索引

---

## 数据库架构

### ER 图

```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│   Ticket    │────────<│ Ticket_Tags  │>────────│     Tag     │
├─────────────┤         ├──────────────┤         ├─────────────┤
│ id (PK)     │         │ ticket_id FK │         │ id (PK)     │
│ title       │         │ tag_id FK    │         │ name UNIQUE │
│ description │         └──────────────┘         │ color       │
│ status      │                                  │ created_at  │
│ created_at  │                                  └─────────────┘
│ updated_at  │
│ completed_at│
│ deleted_at  │
└─────────────┘
```

### 关系说明

- **Ticket ↔ Tag**：多对多关系
- **中间表**：`ticket_tags`（无额外字段）
- **级联删除**：删除 Tag 时自动删除关联关系

---

## 表结构设计

### tickets 表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PRIMARY KEY | 主键 |
| title | VARCHAR(200) | NOT NULL | 标题 |
| description | TEXT | NULL | 描述 |
| status | VARCHAR(20) | NOT NULL, DEFAULT 'pending' | 状态 |
| created_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | 创建时间 |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | 更新时间 |
| completed_at | TIMESTAMP | NULL | 完成时间 |
| deleted_at | TIMESTAMP | NULL | 删除时间（软删除） |

**约束**：
```sql
CHECK (status IN ('pending', 'completed'))
```

**索引**：
- `ix_tickets_id` - 主键索引
- `ix_tickets_title` - 标题索引
- `ix_tickets_status` - 状态索引
- `ix_tickets_deleted_at` - 软删除索引
- `idx_tickets_created_at` - 创建时间降序索引
- `idx_tickets_active` - 活动 Ticket 索引（WHERE deleted_at IS NULL）
- `idx_tickets_title_gin` - 全文搜索索引（PostgreSQL）

### tags 表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PRIMARY KEY | 主键 |
| name | VARCHAR(50) | NOT NULL, UNIQUE | 标签名（英文大写） |
| color | VARCHAR(7) | NOT NULL, DEFAULT '#6B7280' | 颜色（Hex） |
| created_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | 创建时间 |

**约束**：
```sql
-- PostgreSQL
CHECK (color ~ '^#[0-9A-Fa-f]{6}$')

-- SQLite
CHECK (color LIKE '#______' AND LENGTH(color) = 7)
```

**索引**：
- `ix_tags_id` - 主键索引
- `ix_tags_name` - 名称唯一索引

**重要**：标签名称转大写在 Service 层处理，不依赖数据库触发器。

### ticket_tags 表（中间表）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| ticket_id | INTEGER | PRIMARY KEY, FOREIGN KEY | Ticket ID |
| tag_id | INTEGER | PRIMARY KEY, FOREIGN KEY | Tag ID |

**约束**：
```sql
FOREIGN KEY (ticket_id) REFERENCES tickets(id) ON DELETE CASCADE
FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
PRIMARY KEY (ticket_id, tag_id)
```

**索引**：
- `ix_ticket_tags_ticket_id` - Ticket ID 索引
- `ix_ticket_tags_tag_id` - Tag ID 索引

---

## 索引和约束

### 索引策略

**查询优化索引**：
```python
# 单字段索引
Index('ix_tickets_status', 'status')
Index('ix_tickets_deleted_at', 'deleted_at')

# 复合索引
Index('idx_tickets_status_deleted', 'status', 'deleted_at')

# 部分索引（PostgreSQL）
Index('idx_tickets_active', 'deleted_at',
      postgresql_where=text('deleted_at IS NULL'))

# 全文搜索索引（PostgreSQL）
Index('idx_tickets_title_gin', text("to_tsvector('english', title)"),
      postgresql_using='gin')
```

### 约束设计

**数据库无关约束**：
```python
# ✅ 正确：在 Service 层处理
@staticmethod
def _normalize_tag_name(name: str) -> str:
    """应用层面标准化，数据库无关"""
    return "".join(c.upper() if c.isascii() and c.isalpha() else c 
                   for c in name.strip())

# ❌ 错误：依赖数据库触发器
CREATE TRIGGER normalize_tag_name
  BEFORE INSERT ON tags
  FOR EACH ROW
  SET NEW.name = UPPER(NEW.name);  -- 只在 PostgreSQL 有效
```

---

## 数据库迁移

### Alembic 配置

**位置**：`backend/alembic/`

```
alembic/
├── env.py                    # Alembic 环境配置
├── script.py.mako           # 迁移脚本模板
└── versions/
    └── 20260108_000001_initial_migration.py
```

### 创建迁移

```bash
# 进入后端容器
docker exec -it project-alpha-backend bash

# 激活虚拟环境
source .venv/bin/activate

# 自动生成迁移
alembic revision --autogenerate -m "add new field"

# 手动创建迁移
alembic revision -m "manual migration"
```

### 执行迁移

```bash
# 升级到最新版本
alembic upgrade head

# 升级到特定版本
alembic upgrade <revision>

# 降级
alembic downgrade -1
alembic downgrade <revision>

# 查看历史
alembic history
alembic current
```

### 迁移最佳实践

**1. 数据库兼容性**

```python
# 在迁移中处理数据库差异
def upgrade():
    conn = op.get_bind()
    dialect_name = conn.dialect.name
    
    if dialect_name == "postgresql":
        # PostgreSQL 特定约束
        op.create_check_constraint(
            "color_format",
            "tags",
            "color ~ '^#[0-9A-Fa-f]{6}$'"
        )
    else:
        # SQLite 兼容约束
        op.create_check_constraint(
            "color_format",
            "tags",
            "color LIKE '#______' AND LENGTH(color) = 7"
        )
```

**2. 迁移测试**

```bash
# 测试升级
alembic upgrade head

# 测试降级
alembic downgrade -1

# 测试完整循环
alembic downgrade base
alembic upgrade head
```

---

## 测试数据库

### 配置（conftest.py）

```python
import os
import tempfile
from app.models import Tag, Ticket, TicketTag  # 必须导入！

# 使用文件数据库（避免内存数据库的连接问题）
_temp_db_path = os.path.join(tempfile.gettempdir(), "test_ticket_db.db")
SQLALCHEMY_DATABASE_URL = f"sqlite:///{_temp_db_path}"

engine = create_engine(SQLALCHEMY_DATABASE_URL, 
                      connect_args={"check_same_thread": False})

@pytest.fixture(scope="function", autouse=True)
def setup_database():
    """每个测试前创建表"""
    Base.metadata.create_all(bind=engine)
    yield
    # 清理数据但保留表结构
    with engine.connect() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(table.delete())
        conn.commit()

@pytest.fixture(scope="function")
def db():
    """数据库会话"""
    db = TestingSessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
```

### 关键点

**1. 模型必须导入**
```python
# ❌ 错误：不导入模型
from app.database import Base
Base.metadata.create_all()  # metadata 为空！

# ✅ 正确：导入所有模型
from app.models import Tag, Ticket, TicketTag
Base.metadata.create_all()  # metadata 包含所有表
```

**2. 使用文件数据库**
```python
# ❌ 错误：内存数据库（每个连接创建新数据库）
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

# ✅ 正确：文件数据库（所有连接共享）
SQLALCHEMY_DATABASE_URL = f"sqlite:///{temp_db_path}"
```

**3. 表创建时机**
```python
# ✅ 使用 autouse fixture 确保表创建
@pytest.fixture(scope="function", autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
```

---

## SQLAlchemy 模型

### 模型定义

```python
from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.orm import relationship
from app.database import Base

class Tag(Base):
    __tablename__ = "tags"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False, index=True)
    color = Column(String(7), nullable=False, default="#6B7280")
    created_at = Column(DateTime(timezone=True), 
                       server_default=func.now(), 
                       nullable=False)
    
    # 关系
    tickets = relationship("Ticket", 
                          secondary="ticket_tags", 
                          back_populates="tags")
    
    # SQLite 兼容约束
    __table_args__ = (
        CheckConstraint(
            "color LIKE '#______' AND LENGTH(color) = 7",
            name="color_format",
        ),
    )
```

### 关系定义

```python
# 多对多关系
class Ticket(Base):
    tags = relationship("Tag", 
                       secondary="ticket_tags", 
                       back_populates="tickets")

class Tag(Base):
    tickets = relationship("Ticket", 
                          secondary="ticket_tags", 
                          back_populates="tags")

# 中间表
class TicketTag(Base):
    __tablename__ = "ticket_tags"
    
    ticket_id = Column(Integer, ForeignKey("tickets.id", ondelete="CASCADE"))
    tag_id = Column(Integer, ForeignKey("tags.id", ondelete="CASCADE"))
    
    __table_args__ = (
        PrimaryKeyConstraint('ticket_id', 'tag_id'),
    )
```

---

## 数据库操作

### 在 Docker 中操作

```bash
# 进入数据库容器
docker exec -it project-alpha-db psql -U ticketuser -d ticketdb

# 常用 SQL
\dt              # 列出所有表
\d tickets       # 查看表结构
\di              # 列出所有索引

SELECT * FROM tickets WHERE deleted_at IS NULL;
SELECT * FROM tags ORDER BY name;
```

### 数据库迁移

```bash
# 在后端容器中执行
docker exec -it project-alpha-backend bash
source .venv/bin/activate

# 创建迁移
alembic revision --autogenerate -m "description"

# 执行迁移
alembic upgrade head

# 回滚
alembic downgrade -1
```

---

## 相关文档

- [需求规格](./0001-spec.md) - 数据库需求
- [测试指南](./0005-testing.md) - 数据库测试
- [问题排查](./0009-troubleshooting.md) - 数据库相关问题

---

## 总结

**关键要点**：

1. **业务逻辑独立**：不依赖数据库特性（如触发器）
2. **模型必须导入**：SQLAlchemy 需要显式导入才能注册
3. **测试使用文件数据库**：避免内存数据库的连接问题
4. **迁移兼容性**：处理 PostgreSQL 和 SQLite 的差异

**记住**：在 Service 层处理业务规则，保持数据库无关性！
