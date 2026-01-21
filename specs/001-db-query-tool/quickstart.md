# Quick Start: 数据库查询工具

**Date**: 2026-01-11  
**Phase**: 2 - Implementation Complete  
**Status**: ✅ 生产就绪 (包含 P0/P1 安全增强)

> **📌 重要提示**: 本文档是规划阶段的快速开始指南。  
> **实际项目的完整快速开始指南请参考**: [`Week2/QUICK_START.md`](../../Week2/QUICK_START.md)

## 概述

本文档提供数据库查询工具的快速启动指南，包括环境设置、开发启动和测试验证。

---

## ✅ 实现状态更新

本快速开始指南在 **Phase 2 实现阶段**已完成并增强。

### 🚀 已完成的增强功能

#### P0 - 安全关键 (Week 1)
- ✅ **SQL 注入防护**: 5 层防御系统 (注释、多语句、危险关键字、系统表、语法验证)
- ✅ **AI SQL 防护**: 输出清洗、白名单验证、禁止子查询/系统函数、表名验证、审计日志
- ✅ **并发互斥锁**: 元数据刷新与查询执行互斥控制

#### P1 - 数据正确性 (Week 1)
- ✅ **UTC 时间一致性**: 所有时间戳统一使用 UTC
- ✅ **智能查询限制**: 聚合查询豁免、超大 LIMIT 限制、用户可配置

### 📊 测试结果
- **总测试**: 21 个
- **通过率**: 100% ✅
- **覆盖率**: 65.12% (核心模块)

详细信息见 [`Week2/TEST_REPORT.md`](../../Week2/TEST_REPORT.md)

### 📂 实际项目位置

完整的快速开始指南和实现代码位于:
- **快速开始**: [`Week2/QUICK_START.md`](../../Week2/QUICK_START.md) ⭐
- **测试报告**: [`Week2/TEST_REPORT.md`](../../Week2/TEST_REPORT.md)
- **开发指南**: [`Week2/NEXT_STEPS.md`](../../Week2/NEXT_STEPS.md)
- **Makefile 使用**: [`Week2/MAKEFILE_USAGE.md`](../../Week2/MAKEFILE_USAGE.md)

---

## 1. 前置要求

### 1.1 必需软件

| 软件 | 版本要求 | 用途 |
|------|----------|------|
| Docker | 24.0+ | 容器化运行环境 |
| Docker Compose | 2.20+ | 服务编排 |
| Python | 3.12+ | 后端开发（可选，Docker 内运行） |
| Node.js | 20+ | 前端开发（可选，Docker 内运行） |
| uv | 0.4+ | Python 包管理（推荐） |

### 1.2 环境变量

创建 `Week2/env/.env` 文件（从模板复制）：

```bash
cd Week2/env
cp .env.example .env
```

编辑 `.env` 文件，设置 OpenAI API Key：

```bash
# OpenAI API 配置（自然语言生成 SQL 功能必需）
OPENAI_API_KEY=sk-your-api-key-here

# 可选：本地开发端口
BACKEND_PORT=8000
FRONTEND_PORT=5173

# 测试数据库配置（Docker Compose 会自动设置）
POSTGRES_HOST=localhost
POSTGRES_PORT=5433
POSTGRES_USER=testuser
POSTGRES_PASSWORD=testpass
POSTGRES_DB=testdb

MYSQL_HOST=localhost
MYSQL_PORT=3307
MYSQL_USER=testuser
MYSQL_PASSWORD=testpass
MYSQL_DB=testdb
```

---

## 2. 快速启动

### 2.1 一键启动（推荐）

```bash
# 进入环境目录
cd Week2/env

# 启动所有服务（后端、前端、测试数据库）
docker compose up -d

# 查看服务状态
docker compose ps

# 查看日志
docker compose logs -f
```

### 2.2 验证服务

服务启动后，访问以下地址：

| 服务 | 地址 | 说明 |
|------|------|------|
| 前端 | http://localhost:5173 | React 应用 |
| 后端 API | http://localhost:8000 | FastAPI 服务 |
| API 文档 | http://localhost:8000/docs | Swagger UI |
| 健康检查 | http://localhost:8000/health | 服务状态 |

---

## 3. 本地开发

### 3.1 后端开发

```bash
# 进入后端目录
cd Week2/backend

# 使用 uv 安装依赖
uv sync

# 激活虚拟环境
source .venv/bin/activate

# 启动开发服务器（带热重载）
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 运行类型检查
mypy app

# 运行代码格式化
black app tests
isort app tests

# 运行 lint 检查
ruff check app tests

# 运行测试
pytest
```

### 3.2 前端开发

```bash
# 进入前端目录
cd Week2/frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev

# 运行类型检查
npm run typecheck

# 运行 lint 检查
npm run lint

# 运行测试
npm run test
```

---

## 4. 测试数据库

Docker Compose 会自动启动以下测试数据库：

### 4.1 PostgreSQL

```bash
# 连接字符串
postgresql://testuser:testpass@localhost:5433/testdb

# 命令行连接
docker compose exec postgres psql -U testuser -d testdb
```

### 4.2 MySQL

```bash
# 连接字符串
mysql://testuser:testpass@localhost:3307/testdb

# 命令行连接
docker compose exec mysql mysql -u testuser -ptestpass testdb
```

### 4.3 SQLite

```bash
# 连接字符串（使用容器内路径）
sqlite:///data/test.db

# 本地开发（使用相对路径）
sqlite:///Week2/data/test.db
```

---

## 5. API 快速测试

### 5.1 添加数据库连接

```bash
# 添加 PostgreSQL 连接
curl -X PUT http://localhost:8000/api/v1/dbs/my-postgres \
  -H "Content-Type: application/json" \
  -d '{"url": "postgresql://testuser:testpass@postgres:5432/testdb"}'

# 添加 MySQL 连接
curl -X PUT http://localhost:8000/api/v1/dbs/my-mysql \
  -H "Content-Type: application/json" \
  -d '{"url": "mysql://testuser:testpass@mysql:3306/testdb"}'
```

### 5.2 获取元数据

```bash
# 获取 PostgreSQL 元数据
curl http://localhost:8000/api/v1/dbs/my-postgres

# 强制刷新元数据
curl "http://localhost:8000/api/v1/dbs/my-postgres?refresh=true"
```

### 5.3 执行查询

```bash
# 执行 SQL 查询
curl -X POST http://localhost:8000/api/v1/dbs/my-postgres/query \
  -H "Content-Type: application/json" \
  -d '{"sql": "SELECT * FROM users"}'
```

### 5.4 自然语言查询

```bash
# 自然语言生成 SQL
curl -X POST http://localhost:8000/api/v1/dbs/my-postgres/query/natural \
  -H "Content-Type: application/json" \
  -d '{"prompt": "查询所有用户的姓名和邮箱"}'
```

---

## 6. 项目结构

```
Week2/
├── backend/                  # FastAPI 后端
│   ├── app/
│   │   ├── main.py          # 应用入口
│   │   ├── config.py        # 配置管理
│   │   ├── api/v1/          # API 路由
│   │   ├── models/          # Pydantic 模型
│   │   ├── services/        # 业务逻辑
│   │   ├── db/              # 数据库适配器
│   │   ├── storage/         # 本地存储
│   │   └── utils/           # 工具函数
│   ├── tests/               # 测试
│   ├── pyproject.toml       # Python 项目配置
│   └── py.typed             # 类型标记文件
│
├── frontend/                 # React + TypeScript 前端
│   ├── src/
│   │   ├── App.tsx          # 应用入口
│   │   ├── components/      # React 组件
│   │   ├── pages/           # 页面组件
│   │   ├── services/        # API 服务
│   │   ├── types/           # TypeScript 类型
│   │   └── hooks/           # 自定义 Hooks
│   ├── package.json
│   └── vite.config.ts
│
├── data/                     # 本地数据（运行时生成）
│   └── meta.db              # SQLite 元数据存储
│
└── env/                      # Docker 环境配置
    ├── docker-compose.yml
    ├── .env.example
    ├── Dockerfile.backend
    ├── Dockerfile.frontend
    └── init-scripts/        # 数据库初始化
```

---

## 7. 常见问题

### Q1: 后端启动失败，提示数据库连接错误

**A**: 确保测试数据库已启动：

```bash
docker compose up -d postgres mysql
```

### Q2: 自然语言查询返回 AI 服务不可用

**A**: 检查 `OPENAI_API_KEY` 环境变量是否正确设置：

```bash
echo $OPENAI_API_KEY
```

### Q3: 前端无法连接后端 API

**A**: 检查 CORS 配置和后端服务状态：

```bash
curl http://localhost:8000/health
```

### Q4: Docker 容器启动很慢

**A**: 首次启动需要下载镜像，后续启动会快很多。可以预先拉取镜像：

```bash
docker compose pull
```

---

## 8. 下一步

### 生产环境使用
1. 阅读完整的快速开始指南: [`Week2/QUICK_START.md`](../../Week2/QUICK_START.md) ⭐
2. 查看安全特性说明: [`Week2/TEST_REPORT.md`](../../Week2/TEST_REPORT.md)
3. 了解 Makefile 命令: [`Week2/MAKEFILE_USAGE.md`](../../Week2/MAKEFILE_USAGE.md)

### 技术文档
4. 查看 [API 文档](./contracts/api.yaml) 了解完整的 API 接口
5. 查看 [数据模型](./data-model.md) 了解数据结构设计
6. 查看 [研究文档](./research.md) 了解技术决策
7. 查看 [任务列表](./tasks.md) 了解开发任务

---

**Phase 2 实现完成** ✅  
**包含安全增强**: P0 (SQL 注入防护、AI SQL 防护、并发控制) + P1 (UTC 时间、智能限制)  
**测试通过率**: 100% (21/21 测试用例)

→ **请使用 [`Week2/QUICK_START.md`](../../Week2/QUICK_START.md) 进行实际开发和部署**
