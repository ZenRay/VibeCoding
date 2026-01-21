# Implementation Plan: 数据库查询工具

**Branch**: `001-db-query-tool` | **Date**: 2026-01-10 | **Spec**: [spec.md](./spec.md)  
**Input**: Feature specification from `/specs/001-db-query-tool/spec.md`

## Summary

构建一个数据库查询工具，支持用户添加多种类型的数据库连接（PostgreSQL、MySQL、SQLite），自动提取并展示数据库元数据（表、视图、列信息），提供 SQL 编辑器用于执行只读查询，并集成 AI 服务支持自然语言生成 SQL。

**技术方案**:
- **后端**: Python 3.12 + FastAPI + sqlglot（SQL 解析）+ OpenAI SDK
- **前端**: React + Refine 5 + Ant Design + Monaco Editor（SQL 编辑器）+ Tailwind CSS
- **本地存储**: SQLite（存储数据库连接和元数据）
- **环境管理**: Docker + Docker Compose

## Technical Context

**Language/Version**:
- Backend: Python 3.12+
- Frontend: TypeScript 5.x (strict mode)

**Primary Dependencies**:
- Backend: FastAPI, Pydantic v2, sqlglot, openai, asyncpg (PostgreSQL), aiomysql (MySQL), aiosqlite
- Frontend: React 18+, Refine 5, Ant Design 5, Monaco Editor, Tailwind CSS, axios

**Storage**:
- 本地元数据存储: SQLite (`Week2/data/meta.db`)
- 目标数据库: PostgreSQL 10+ / MySQL 5.7+ / SQLite 3.8+

**Testing**:
- Backend: pytest, pytest-asyncio, httpx
- Frontend: Vitest, React Testing Library

**Target Platform**:
- Desktop browsers (Chrome, Firefox, Safari, Edge)
- Minimum resolution: 1280x720

**Project Type**: Web Application (frontend + backend)

**Performance Goals**:
- 应用启动: < 3 秒
- 元数据提取（100 表）: < 5 秒
- 简单查询执行: < 3 秒
- AI SQL 生成: < 10 秒

**Constraints**:
- 查询超时: 30 秒
- 本地存储: < 100MB
- 元数据缓存: < 50MB
- 查询结果限制: 1000 行

**Scale/Scope**:
- 单用户场景
- 中小型数据库（< 100 表）
- 开发/调试工具定位

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. 人体工程学代码风格 (Ergonomic Code Style) ✅

- **后端**: 使用 Ergonomic Python 风格
  - ✅ 清晰命名和简洁结构
  - ✅ 避免过度抽象
  - ✅ 明确优于隐晦
- **前端**: TypeScript + React 最佳实践
  - ✅ 函数组件 + Hooks
  - ✅ 组件职责单一

### II. 严格类型标注 (Strict Type Annotations - NON-NEGOTIABLE) ✅

- **后端**:
  - ✅ 所有函数参数和返回值类型标注
  - ✅ mypy strict 模式
  - ✅ Pydantic v2 数据模型
- **前端**:
  - ✅ TypeScript strict 模式
  - ✅ 明确的接口定义
  - ✅ 禁止 any 类型

### III. 数据模型与序列化标准 (Data Model & Serialization Standards) ✅

- ✅ 所有 API 请求/响应使用 Pydantic 模型
- ✅ JSON 使用 camelCase 格式
- ✅ 数据库字段使用 snake_case
- ✅ 配置 `alias_generator=to_camel`

### IV. 无认证访问原则 (No Authentication Required) ✅

- ✅ 无登录/注册
- ✅ 无权限控制
- ✅ 适用于开发环境

### V. Docker 容器化开发 (Docker-Based Development) ✅

- ✅ `Week2/env/` 目录管理所有 Docker 配置
- ✅ docker-compose.yml 一键启动
- ✅ pydantic-settings 管理配置
- ✅ .env.example 模板

**GATE RESULT**: ✅ 通过 - 所有原则符合

## Project Structure

### Documentation (this feature)

```text
specs/001-db-query-tool/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (OpenAPI specs)
│   └── api.yaml
├── checklists/          # Quality checklists
│   ├── requirements.md
│   └── comprehensive-review.md
└── tasks.md             # Phase 2 output (by /speckit.tasks)
```

### Source Code (repository root)

```text
Week2/
├── backend/                        # FastAPI 后端
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI 应用入口
│   │   ├── config.py               # pydantic-settings 配置
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   └── v1/
│   │   │       ├── __init__.py
│   │   │       ├── dbs.py          # 数据库连接 API
│   │   │       └── query.py        # 查询执行 API
│   │   ├── models/                 # Pydantic 模型（API 请求/响应）
│   │   │   ├── __init__.py
│   │   │   ├── database.py         # DatabaseConnection, Metadata
│   │   │   └── query.py            # QueryRequest, QueryResult
│   │   ├── services/               # 业务逻辑层
│   │   │   ├── __init__.py
│   │   │   ├── db_service.py       # 数据库连接管理
│   │   │   ├── metadata_service.py # 元数据提取
│   │   │   ├── query_service.py    # 查询执行
│   │   │   └── ai_service.py       # OpenAI SQL 生成
│   │   ├── db/                     # 数据库适配器
│   │   │   ├── __init__.py
│   │   │   ├── base.py             # 抽象基类
│   │   │   ├── postgres.py         # PostgreSQL 适配器
│   │   │   ├── mysql.py            # MySQL 适配器
│   │   │   └── sqlite.py           # SQLite 适配器
│   │   ├── storage/                # 本地存储（SQLite）
│   │   │   ├── __init__.py
│   │   │   ├── local_db.py         # 本地 SQLite 操作
│   │   │   └── models.py           # SQLAlchemy 模型
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── sql_validator.py    # sqlglot SQL 验证
│   │       └── error_handler.py    # 错误处理
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── conftest.py
│   │   ├── test_api/
│   │   │   ├── test_dbs.py
│   │   │   └── test_query.py
│   │   └── test_services/
│   │       ├── test_db_service.py
│   │       └── test_query_service.py
│   ├── pyproject.toml
│   └── py.typed
├── frontend/                       # React + Refine 前端
│   ├── src/
│   │   ├── App.tsx                 # 应用入口
│   │   ├── main.tsx
│   │   ├── components/
│   │   │   ├── DatabaseForm.tsx    # 添加/编辑连接表单
│   │   │   ├── DatabaseList.tsx    # 连接列表
│   │   │   ├── DatabaseSelector.tsx # 数据库选择器
│   │   │   ├── MetadataTree.tsx    # 元数据树形展示
│   │   │   ├── SqlEditor.tsx       # Monaco Editor 封装
│   │   │   ├── QueryResult.tsx     # 查询结果表格
│   │   │   ├── QueryHistory.tsx    # 查询历史
│   │   │   └── NaturalLanguageInput.tsx # 自然语言输入
│   │   ├── pages/
│   │   │   ├── HomePage.tsx        # 主页
│   │   │   └── DatabasePage.tsx    # 数据库详情页
│   │   ├── services/
│   │   │   ├── api.ts              # API 客户端
│   │   │   ├── databaseService.ts  # 数据库 API
│   │   │   └── queryService.ts     # 查询 API
│   │   ├── types/
│   │   │   ├── database.ts         # 数据库类型定义
│   │   │   └── query.ts            # 查询类型定义
│   │   ├── hooks/
│   │   │   ├── useDatabases.ts     # 数据库列表 Hook
│   │   │   └── useQuery.ts         # 查询执行 Hook
│   │   └── styles/
│   │       └── globals.css         # Tailwind 全局样式
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   └── tailwind.config.js
├── data/                           # 本地数据存储
│   └── meta.db                     # SQLite 元数据存储（运行时生成）
└── env/                            # Docker 环境配置
    ├── docker-compose.yml
    ├── .env.example
    ├── Dockerfile.backend
    ├── Dockerfile.frontend
    └── init-scripts/
        ├── postgres-init.sql       # PostgreSQL 测试数据
        └── mysql-init.sql          # MySQL 测试数据
```

**Structure Decision**: 采用 Web Application 结构（frontend + backend），符合 Constitution 的项目结构规范。所有代码位于 `Week2/` 目录，Docker 配置位于 `Week2/env/`。

## Complexity Tracking

> 无 Constitution 违规需要记录
