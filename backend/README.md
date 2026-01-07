# Project Alpha Backend

Project Alpha Ticket 管理系统的后端服务。

## 技术栈

- Python 3.12
- FastAPI 0.109+
- PostgreSQL 16
- SQLAlchemy 2.0+
- Alembic 1.13+
- Pydantic 2.5+
- UV（包管理器）

## 快速开始

### 前置要求

- Python 3.12+
- UV 包管理器
- PostgreSQL 16+

### 安装依赖

```bash
# 安装 UV（如果还没有）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 创建虚拟环境
uv venv

# 激活虚拟环境
source .venv/bin/activate  # Linux/macOS
# 或 .venv\Scripts\activate  # Windows

# 安装依赖
uv pip install -e ".[dev]"
```

### 配置环境变量

```bash
# 复制环境变量示例文件
cp .env.example .env

# 编辑 .env 文件，配置数据库连接等
```

### 运行数据库迁移

```bash
# 初始化数据库（如果还没有）
alembic upgrade head
```

### 启动开发服务器

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 访问 API 文档

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI JSON: http://localhost:8000/openapi.json

## 项目结构

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI 应用入口
│   ├── config.py            # 配置管理
│   ├── database.py          # 数据库连接
│   ├── models/              # SQLAlchemy 模型
│   ├── schemas/             # Pydantic 模式
│   ├── api/                 # API 路由
│   ├── services/            # 业务逻辑
│   └── utils/               # 工具函数
├── alembic/                 # 数据库迁移
├── tests/                   # 测试
├── pyproject.toml           # 项目配置
└── .env.example             # 环境变量示例
```

## 开发命令

```bash
# 运行测试
pytest

# 代码格式化
black app/
isort app/

# 代码检查
ruff check app/

# 数据库迁移
alembic revision --autogenerate -m "message"
alembic upgrade head
```
