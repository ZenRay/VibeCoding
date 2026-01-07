# Project Alpha 测试指南

**文档版本**: v1.0  
**创建时间**: 2026-01-08  
**最后更新**: 2026-01-08

## 📋 测试概述

项目包含两种类型的测试：
1. **单元测试**：测试 Service 层的业务逻辑
2. **集成测试**：测试 API 端点的完整流程

## 🚀 快速开始

### 运行所有测试

```bash
cd backend

# 激活虚拟环境
source .venv/bin/activate

# 运行所有测试
pytest

# 或使用脚本
./scripts/run_tests.sh
```

### 运行特定测试

```bash
# 运行单元测试
pytest tests/test_services/

# 运行集成测试
pytest tests/test_api/

# 运行特定测试文件
pytest tests/test_services/test_ticket_service.py

# 运行特定测试类
pytest tests/test_services/test_ticket_service.py::TestTicketService

# 运行特定测试方法
pytest tests/test_services/test_ticket_service.py::TestTicketService::test_create_ticket
```

### 查看测试覆盖率

```bash
# 运行测试并生成覆盖率报告
pytest --cov=app --cov-report=html

# 查看 HTML 报告
open htmlcov/index.html  # macOS
# 或
xdg-open htmlcov/index.html  # Linux
```

## 📊 测试结构

```
tests/
├── conftest.py                    # pytest 配置和 fixtures
├── test_services/                 # Service 层单元测试
│   ├── test_ticket_service.py    # Ticket Service 测试
│   └── test_tag_service.py       # Tag Service 测试
└── test_api/                      # API 层集成测试
    ├── test_tickets.py            # Ticket API 测试
    └── test_tags.py               # Tag API 测试
```

## 🔧 测试配置

### conftest.py

提供以下 fixtures：
- `db`: 数据库会话（每个测试函数一个）
- `client`: FastAPI 测试客户端

### 测试数据库

- 使用 SQLite 内存数据库（`:memory:`）
- 每个测试函数都会创建和清理数据库
- 不支持 PostgreSQL 特定特性（如全文搜索）

## 📝 编写测试

### 单元测试示例

```python
def test_create_ticket(self, db):
    """测试创建 Ticket"""
    ticket_data = TicketCreate(
        title="测试 Ticket",
        description="这是一个测试",
    )
    ticket = TicketService.create_ticket(db, ticket_data)

    assert ticket.id is not None
    assert ticket.title == "测试 Ticket"
    assert ticket.status == "pending"
```

### 集成测试示例

```python
def test_create_ticket(self, client, db):
    """测试创建 Ticket"""
    response = client.post(
        "/api/v1/tickets",
        json={
            "title": "API 测试 Ticket",
            "description": "通过 API 创建的测试 Ticket",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "API 测试 Ticket"
```

## 🐛 常见问题

### 问题 1：测试数据库连接失败

**错误**: `sqlalchemy.exc.OperationalError`

**解决方案**：
- 确保使用 SQLite 内存数据库
- 检查 `conftest.py` 中的数据库配置

### 问题 2：外键约束错误

**错误**: `FOREIGN KEY constraint failed`

**解决方案**：
- SQLite 需要启用外键支持
- `conftest.py` 中已配置 `PRAGMA foreign_keys=ON`

### 问题 3：测试数据污染

**错误**: 测试之间相互影响

**解决方案**：
- 每个测试函数使用独立的数据库会话
- 测试结束后自动清理数据库

## 📈 测试覆盖率目标

- **目标覆盖率**: ≥ 70%
- **当前覆盖率**: 运行 `pytest --cov=app` 查看

## 🔍 测试最佳实践

1. **测试独立性**：每个测试应该独立运行
2. **测试清理**：测试后清理数据，避免影响其他测试
3. **断言明确**：使用清晰的断言消息
4. **测试命名**：使用描述性的测试名称
5. **测试组织**：按功能模块组织测试文件

## 📚 相关资源

- [pytest 文档](https://docs.pytest.org/)
- [FastAPI 测试文档](https://fastapi.tiangolo.com/tutorial/testing/)
- [SQLAlchemy 测试文档](https://docs.sqlalchemy.org/en/20/core/testing.html)

---

**状态**: ✅ 测试框架已配置完成
