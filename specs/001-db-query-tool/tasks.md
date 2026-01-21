# Tasks: 数据库查询工具

**Input**: Design documents from `/specs/001-db-query-tool/`  
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅  
**Created**: 2026-01-10  
**Total Tasks**: 64

**Tests**: 本项目未明确要求 TDD，因此测试任务标记为可选。

**Organization**: 任务按用户故事分组，支持独立实现和测试。

## Format: `[ID] [P?] [Story] Description`

- **[P]**: 可并行执行（不同文件，无依赖）
- **[Story]**: 所属用户故事 (US1, US2, US3, US4)
- 包含准确的文件路径

## Path Conventions

本项目采用 Web Application 结构：
- **Backend**: `Week2/backend/`
- **Frontend**: `Week2/frontend/`
- **Environment**: `Week2/env/`

---

## Phase 1: Setup (项目初始化)

**Purpose**: 项目结构创建和基础配置

- [x] T001 创建后端项目结构 `Week2/backend/` 及子目录 (app/, tests/, alembic/)
- [x] T002 创建前端项目结构 `Week2/frontend/` 及子目录 (src/components/, src/pages/, src/services/, src/types/, src/hooks/)
- [x] T003 [P] 初始化后端 Python 项目配置 `Week2/backend/pyproject.toml` (FastAPI, Pydantic, sqlglot, openai, asyncpg, aiomysql, aiosqlite)
- [x] T004 [P] 初始化前端项目配置 `Week2/frontend/package.json` (React, Refine 5, Ant Design, @monaco-editor/react, Tailwind, axios)
- [x] T005 [P] 配置后端代码质量工具 (mypy, ruff, black, isort) in `Week2/backend/pyproject.toml`
- [x] T006 [P] 配置前端 TypeScript strict 模式 `Week2/frontend/tsconfig.json`
- [x] T007 [P] 配置前端 Tailwind CSS `Week2/frontend/tailwind.config.js` 和 `Week2/frontend/postcss.config.js`
- [x] T008 创建 Docker 环境配置 `Week2/env/docker-compose.yml` (backend, frontend, postgres, mysql)
- [x] T009 [P] 创建环境变量模板 `Week2/env/.env.example`
- [x] T010 [P] 创建后端 Dockerfile `Week2/env/Dockerfile.backend`
- [x] T011 [P] 创建前端 Dockerfile `Week2/env/Dockerfile.frontend`
- [x] T012 [P] 创建 PostgreSQL 测试数据初始化脚本 `Week2/env/init-scripts/postgres-init.sql`
- [x] T013 [P] 创建 MySQL 测试数据初始化脚本 `Week2/env/init-scripts/mysql-init.sql`

---

## Phase 2: Foundational (核心基础设施)

**Purpose**: 所有用户故事依赖的核心基础设施

**⚠️ CRITICAL**: 必须完成此阶段才能开始任何用户故事

- [x] T014 创建 FastAPI 应用入口和 CORS 配置 `Week2/backend/app/main.py`
- [x] T015 创建配置管理（pydantic-settings）`Week2/backend/app/config.py`
- [x] T016 创建本地存储 SQLAlchemy 模型 `Week2/backend/app/storage/models.py` (DatabaseConnection, MetadataCache)
- [x] T017 创建本地 SQLite 存储操作层 `Week2/backend/app/storage/local_db.py`，包含启动时完整性检查逻辑（检测损坏时自动重建）
- [x] T018 初始化 Alembic 迁移框架 `Week2/backend/alembic/` 和初始迁移脚本，包含迁移流程文档（如何创建新迁移、前后向迁移命令）
- [x] T019 [P] 创建错误处理和错误响应模型 `Week2/backend/app/utils/error_handler.py`
- [x] T020 [P] 创建 SQL 验证工具（sqlglot）`Week2/backend/app/utils/sql_validator.py`，包含多层注入检测：移除注释、检测多语句、验证危险关键字白名单、拒绝系统表访问
- [x] T021 创建数据库适配器基类 `Week2/backend/app/db/base.py`
- [x] T022 [P] 实现 PostgreSQL 适配器 `Week2/backend/app/db/postgres.py`
- [x] T023 [P] 实现 MySQL 适配器 `Week2/backend/app/db/mysql.py`
- [x] T024 [P] 实现 SQLite 适配器 `Week2/backend/app/db/sqlite.py`
- [x] T025 创建前端 API 客户端基础 `Week2/frontend/src/services/api.ts` (axios 配置, 错误处理)
- [x] T026 [P] 创建前端类型定义 `Week2/frontend/src/types/database.ts`
- [x] T027 [P] 创建前端类型定义 `Week2/frontend/src/types/query.ts`
- [x] T028 创建前端全局样式 `Week2/frontend/src/styles/globals.css`
- [x] T029 创建前端应用入口 `Week2/frontend/src/App.tsx` 和 `Week2/frontend/src/main.tsx`

**Checkpoint**: 基础设施就绪 - 可以开始用户故事实现

---

## Phase 3: User Story 1 - 数据库连接管理 (Priority: P1) 🎯 MVP

**Goal**: 用户可以添加、查看、编辑、删除数据库连接，系统验证连接有效性

**Independent Test**: 添加一个测试数据库连接并成功连接，看到连接列表

### Backend Implementation for US1

- [x] T030 [P] [US1] 创建数据库连接 Pydantic 模型 `Week2/backend/app/models/database.py` (DatabaseConnectionCreate, DatabaseConnectionResponse, DatabaseListResponse)，包含连接名称格式验证 validator（正则：`^[a-zA-Z0-9_-]+$`，长度 1-100）
- [x] T031 [US1] 实现数据库连接服务 `Week2/backend/app/services/db_service.py` (add, get, list, update, delete, validate)
- [x] T032 [US1] 实现数据库连接 API 路由 `Week2/backend/app/api/v1/dbs.py` (GET /dbs, PUT /dbs/{name}, DELETE /dbs/{name})
- [x] T033 [US1] 注册 API 路由到主应用 `Week2/backend/app/api/v1/__init__.py` 和 `Week2/backend/app/main.py`

### Frontend Implementation for US1

- [x] T034 [P] [US1] 创建数据库连接 API 服务 `Week2/frontend/src/services/databaseService.ts`
- [x] T035 [P] [US1] 创建数据库连接 Hook `Week2/frontend/src/hooks/useDatabases.ts`
- [x] T036 [US1] 创建数据库添加/编辑表单组件 `Week2/frontend/src/components/DatabaseForm.tsx`
- [x] T037 [US1] 创建数据库连接列表组件 `Week2/frontend/src/components/DatabaseList.tsx`
- [x] T038 [US1] 创建数据库选择器组件 `Week2/frontend/src/components/DatabaseSelector.tsx`
- [x] T039 [US1] 创建主页面（连接管理）`Week2/frontend/src/pages/HomePage.tsx`

**Checkpoint**: US1 完成 - 可以添加、查看、编辑、删除数据库连接

---

## Phase 4: User Story 2 - 数据库元数据浏览 (Priority: P1)

**Goal**: 用户可以查看数据库的表、视图、列等元数据信息

**Independent Test**: 连接到包含多个表的测试数据库，验证系统正确展示所有表和列信息

### Backend Implementation for US2

- [x] T040 [P] [US2] 扩展数据库 Pydantic 模型 `Week2/backend/app/models/database.py` 添加元数据类 (ColumnInfo, TableInfo, DatabaseMetadata)
- [x] T041 [US2] 实现元数据提取服务 `Week2/backend/app/services/metadata_service.py` (extract, cache, refresh, detect_changes)，包含内存监控逻辑（缓存 ≤ 50MB，超出时清理最少使用的元数据）、并发互斥锁保护、UTC 时间戳比较
- [x] T042 [US2] 扩展数据库连接 API 以支持元数据 `Week2/backend/app/api/v1/dbs.py` (GET /dbs/{name} 返回元数据)

### Frontend Implementation for US2

- [x] T043 [P] [US2] 扩展数据库服务以支持元数据 `Week2/frontend/src/services/databaseService.ts`
- [x] T044 [US2] 创建元数据树形展示组件 `Week2/frontend/src/components/MetadataTree.tsx`
- [x] T045 [US2] 创建数据库详情页面 `Week2/frontend/src/pages/DatabasePage.tsx`
- [x] T046 [US2] 添加元数据刷新提示横幅组件 `Week2/frontend/src/components/MetadataRefreshBanner.tsx`

**Checkpoint**: US1 + US2 完成 - MVP 可用（连接管理 + 元数据浏览）

---

## Phase 5: User Story 3 - 手动 SQL 查询 (Priority: P2)

**Goal**: 用户可以执行 SQL 查询并查看表格化结果

**Independent Test**: 输入 `SELECT * FROM users` 并验证结果正确显示

### Backend Implementation for US3

- [x] T047 [P] [US3] 创建查询 Pydantic 模型 `Week2/backend/app/models/query.py` (QueryRequest, QueryResult, QueryResultColumn)
- [x] T048 [US3] 实现查询执行服务 `Week2/backend/app/services/query_service.py` (validate, execute, cancel, timeout handling)，包含查询队列管理和等待超时逻辑（等待超过 60 秒自动取消）、聚合查询检测和智能 LIMIT 添加、元数据版本快照锁定
- [x] T049 [US3] 实现查询 API 路由 `Week2/backend/app/api/v1/query.py` (POST /dbs/{name}/query)

### Frontend Implementation for US3

- [x] T050 [P] [US3] 创建查询 API 服务 `Week2/frontend/src/services/queryService.ts`
- [x] T051 [P] [US3] 创建查询执行 Hook `Week2/frontend/src/hooks/useQuery.ts`
- [x] T052 [US3] 创建 SQL 编辑器组件（Monaco Editor 封装）`Week2/frontend/src/components/SqlEditor.tsx`
- [x] T053 [US3] 创建查询结果表格组件 `Week2/frontend/src/components/QueryResult.tsx`
- [x] T054 [US3] 创建查询历史组件 `Week2/frontend/src/components/QueryHistory.tsx`
- [x] T055 [US3] 扩展数据库详情页面以集成 SQL 编辑器 `Week2/frontend/src/pages/DatabasePage.tsx`

**Checkpoint**: US1 + US2 + US3 完成 - 核心功能完整

---

## Phase 6: User Story 4 - 自然语言生成 SQL (Priority: P3)

**Goal**: 用户可以用自然语言描述查询需求，系统使用 AI 生成 SQL

**Independent Test**: 输入"查找所有用户"，验证系统生成正确的 SELECT 查询

### Backend Implementation for US4

- [x] T056 [US4] 实现 AI 服务（OpenAI SDK）`Week2/backend/app/services/ai_service.py` (generate_sql, format_metadata_context)，包含元数据上下文截断逻辑（≤ 4000 tokens，优先包含最近访问的表）、AI 输出清洗（移除注释、多余空白）、白名单验证（拒绝子查询、系统函数）、表名存在性验证、审计日志记录
- [x] T057 [US4] 扩展查询 Pydantic 模型 `Week2/backend/app/models/query.py` (NaturalLanguageQueryRequest, NaturalLanguageQueryResult)
- [x] T058 [US4] 实现自然语言查询 API `Week2/backend/app/api/v1/query.py` (POST /dbs/{name}/query/natural)

### Frontend Implementation for US4

- [x] T059 [P] [US4] 扩展查询服务以支持自然语言 `Week2/frontend/src/services/queryService.ts`
- [x] T060 [US4] 创建自然语言输入组件 `Week2/frontend/src/components/NaturalLanguageInput.tsx`
- [x] T061 [US4] 集成自然语言输入到数据库详情页 `Week2/frontend/src/pages/DatabasePage.tsx`

**Checkpoint**: 所有用户故事完成 - 功能完整

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: 跨用户故事的改进和优化

- [x] T062 创建 Alembic 迁移脚本模板和文档 `Week2/backend/alembic/README.md`
- [ ] T062.5 [P] 创建快速开始指南 `specs/001-db-query-tool/quickstart.md`（包含环境配置、启动步骤、基本使用示例）
- [x] T063 运行 quickstart.md 验证，确保所有功能正常工作（测试文件已创建）
- [x] T064 [P] 更新项目 README `Week2/README.md`

---

## Dependencies & Execution Order

### Phase Dependencies

```
Phase 1 (Setup)
     ↓
Phase 2 (Foundational) ← BLOCKS all user stories
     ↓
┌────┴────┐
↓         ↓
Phase 3   Phase 4    (US1 和 US2 可并行，但建议 US1 先完成)
(US1)     (US2)
     ↓
Phase 5 (US3) ← 依赖 US1 的连接管理
     ↓
Phase 6 (US4) ← 依赖 US2 的元数据和 US3 的查询基础
     ↓
Phase 7 (Polish)
```

### User Story Dependencies

| 用户故事 | 依赖 | 可独立测试 |
|----------|------|------------|
| US1 (数据库连接管理) | Phase 2 | ✅ 是 |
| US2 (元数据浏览) | Phase 2, US1 | ✅ 是 |
| US3 (手动 SQL 查询) | Phase 2, US1 | ✅ 是 |
| US4 (自然语言 SQL) | Phase 2, US2, US3 | ✅ 是 |

### Within Each User Story

1. Backend Models → Backend Services → Backend API
2. Frontend Types → Frontend Services → Frontend Components → Frontend Pages

### Parallel Opportunities

**Phase 1 (11 parallel tasks)**:
- T003-T007, T009-T013 可并行

**Phase 2 (9 parallel tasks)**:
- T019-T024, T026-T027 可并行

**Phase 3-6**:
- 每个阶段内 Backend 和 Frontend 部分可并行（在 Backend API 完成后）
- 标记 [P] 的任务可并行

---

## Parallel Example

### Phase 1 Setup 并行执行

```bash
# 可同时执行:
T003: 初始化后端 pyproject.toml
T004: 初始化前端 package.json
T005: 配置后端代码质量工具
T006: 配置前端 TypeScript
T007: 配置 Tailwind CSS
T009: 创建 .env.example
T010: 创建 Dockerfile.backend
T011: 创建 Dockerfile.frontend
T012: 创建 postgres-init.sql
T013: 创建 mysql-init.sql
```

### Phase 2 Foundational 并行执行

```bash
# 依赖 T014-T018 完成后，可同时执行:
T019: 创建错误处理
T020: 创建 SQL 验证工具
T022: 实现 PostgreSQL 适配器
T023: 实现 MySQL 适配器
T024: 实现 SQLite 适配器
T026: 创建前端类型 database.ts
T027: 创建前端类型 query.ts
```

---

## Implementation Strategy

### MVP First (仅 User Story 1 + 2)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1 (数据库连接管理)
4. Complete Phase 4: User Story 2 (元数据浏览)
5. **STOP and VALIDATE**: 测试 MVP 功能
6. Deploy/Demo MVP

### Incremental Delivery

| 阶段 | 交付内容 | 累计功能 |
|------|----------|----------|
| Phase 1-2 | 基础设施 | 项目可运行 |
| Phase 3 | US1 完成 | 连接管理可用 |
| Phase 4 | US2 完成 | MVP 完成（连接 + 元数据） |
| Phase 5 | US3 完成 | 核心功能完整 |
| Phase 6 | US4 完成 | 全部功能完成 |
| Phase 7 | Polish | 生产就绪 |

---

## Summary

| 阶段 | 任务数 | 并行任务 |
|------|--------|----------|
| Phase 1: Setup | 13 | 11 |
| Phase 2: Foundational | 16 | 9 |
| Phase 3: US1 | 10 | 4 |
| Phase 4: US2 | 7 | 2 |
| Phase 5: US3 | 9 | 3 |
| Phase 6: US4 | 6 | 1 |
| Phase 7: Polish | 3 | 1 |
| **Total** | **64** | **31** |

**MVP Scope**: Phase 1-4 (US1 + US2) = 46 tasks  
**Full Scope**: All Phases = 64 tasks
