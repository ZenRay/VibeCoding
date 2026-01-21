# 数据库查询工具项目 Constitution

<!--
Sync Impact Report - Version 1.0.0
=====================================
Version Change: Template → 1.0.0 (Initial Constitution)
Modified Principles:
  - [PRINCIPLE_1_NAME] → I. 人体工程学代码风格 (Ergonomic Code Style)
  - [PRINCIPLE_2_NAME] → II. 严格类型标注 (Strict Type Annotations - NON-NEGOTIABLE)
  - [PRINCIPLE_3_NAME] → III. 数据模型与序列化标准 (Data Model & Serialization Standards)
  - [PRINCIPLE_4_NAME] → IV. 无认证访问原则 (No Authentication Required)
  - [PRINCIPLE_5_NAME] → V. Docker 容器化开发 (Docker-Based Development)

Added Sections:
  - Core Principles (5 具体原则)
  - Technology Stack Standards (后端/前端技术栈)
  - Development Environment (项目结构、Docker 管理、代码质量门禁)
  - Governance (修订流程、版本策略、合规审查)

Removed Sections:
  - [SECTION_2_NAME] (合并到 Technology Stack Standards)
  - [SECTION_3_NAME] (合并到 Development Environment)

Templates Alignment Status:
  ✅ plan-template.md (.specify/templates/plan-template.md)
     - Constitution Check 章节与新原则对齐
     - Technical Context 与技术栈标准一致
     - 项目结构支持 Week2/ 组织形式
  
  ✅ spec-template.md (.specify/templates/spec-template.md)
     - 用户场景测试方法与类型安全原则对齐
     - 需求定义支持 Pydantic 数据模型方法
  
  ✅ tasks-template.md (.specify/templates/tasks-template.md)
     - 任务组织与独立测试原则一致
     - 支持 Docker 环境下的开发工作流
  
  ✅ agent-file-template.md (.specify/templates/agent-file-template.md)
     - 技术栈部分将反映实际使用的技术
     - 代码风格章节将包含 Ergonomic Python 和 TypeScript strict 要求

Follow-up TODOs: 无
-->

## Core Principles

### I. 人体工程学代码风格 (Ergonomic Code Style)

**后端**: 必须使用 Ergonomic Python 风格编写代码。这意味着:
- 代码应当易读、直观,符合 Python 社区的最佳实践
- 优先使用清晰的命名和简洁的结构
- 避免过度抽象和不必要的复杂性
- 遵循 "明确优于隐晦" (Explicit is better than implicit) 原则

**前端**: 必须使用 TypeScript 编写,遵循现代 React/TypeScript 最佳实践

**理由**: Ergonomic 代码风格提高代码可维护性,减少认知负担,使团队成员能够快速理解和修改代码。

### II. 严格类型标注 (Strict Type Annotations - NON-NEGOTIABLE)

**后端**: 所有 Python 代码必须包含完整的类型标注:
- 函数参数和返回值必须标注类型
- 变量在需要时应当标注类型(特别是复杂类型)
- 必须通过 mypy strict 模式检查
- 使用 Pydantic 定义所有数据模型,确保运行时类型验证

**前端**: 所有 TypeScript 代码必须:
- 启用 strict 模式
- 避免使用 `any` 类型(除非有充分理由)
- 为 props、state、API 响应等定义明确的接口/类型

**理由**: 严格的类型系统在编译/开发时捕获错误,提供更好的 IDE 支持,作为活文档帮助理解代码意图,减少运行时错误。

### III. 数据模型与序列化标准 (Data Model & Serialization Standards)

**Pydantic 为核心**: 所有数据模型必须使用 Pydantic 定义:
- API 请求/响应模型
- 数据库模型的 schema 表示
- 配置模型
- 内部服务间传递的数据结构

**命名约定**: 后端生成的所有 JSON 数据必须使用 camelCase 格式:
- Pydantic 模型配置 `alias_generator` 为 `to_camel`
- 数据库字段使用 snake_case,序列化时自动转换为 camelCase
- 确保前后端接口命名一致性

**理由**: Pydantic 提供强大的数据验证、序列化和文档生成能力。统一的命名约定(camelCase for JSON)符合前端 JavaScript/TypeScript 惯例,减少命名转换的心智负担。

### IV. 无认证访问原则 (No Authentication Required)

项目不实现用户认证和授权机制:
- 任何用户都可以访问所有功能
- 不需要登录、注册或权限控制
- 简化开发和部署流程
- 适用于内部工具或受信任的网络环境

**理由**: 该项目定位为内部开发工具,运行在受控环境中。移除认证层简化架构,加快开发速度,降低维护复杂度。

### V. Docker 容器化开发 (Docker-Based Development)

**环境管理**: 开发和测试环境必须使用 Docker 管理:
- 所有环境配置统一在 `./Week2/env` 目录管理
- 提供 docker-compose.yml 用于一键启动完整开发环境
- 包含所有必要的服务(数据库、后端、前端等)
- 确保开发环境一致性,避免 "在我机器上能运行" 问题

**配置隔离**: 环境变量和配置文件应当:
- 提供 `.env.example` 作为模板
- 使用 `pydantic-settings` 管理配置
- 支持不同环境的配置切换

**理由**: Docker 确保所有开发者拥有相同的开发环境,简化新成员入职流程,便于 CI/CD 集成,提高开发体验。

## Technology Stack Standards

### Backend Stack

- **语言**: Python 3.12+
- **Web 框架**: FastAPI
- **数据验证**: Pydantic v2
- **数据库**: SQLite / PostgreSQL / MySQL (多数据库支持)
- **ORM**: SQLAlchemy 2.0+
- **类型检查**: mypy (strict mode)
- **代码格式化**: black, isort
- **代码检查**: ruff
- **测试**: pytest, pytest-asyncio

### Frontend Stack

- **语言**: TypeScript (strict mode)
- **框架**: React 18+
- **构建工具**: Vite
- **状态管理**: React Hooks / Context API（兼容 Refine 5 / React Query 等基于 Hooks 的数据管理库）
- **HTTP 客户端**: axios
- **UI 组件库**: Ant Design 5（可选，根据项目需求）
- **代码检查**: ESLint, TypeScript compiler

### Development Tools

- **容器化**: Docker, Docker Compose
- **版本控制**: Git
- **包管理**: 
  - Python: uv（推荐）或 pip，配置文件为 pyproject.toml
  - Node.js: npm

## Development Environment

### Project Structure

```
Week2/
├── backend/                    # FastAPI 后端
│   ├── app/
│   │   ├── api/               # API 路由
│   │   ├── models/            # Pydantic 模型
│   │   ├── schemas/           # 数据库 schema
│   │   ├── services/          # 业务逻辑
│   │   ├── db/                # 数据库连接管理
│   │   └── utils/             # 工具函数
│   ├── tests/                 # 测试
│   └── pyproject.toml         # Python 项目配置
├── frontend/                   # React + TypeScript 前端
│   ├── src/
│   │   ├── components/        # React 组件
│   │   ├── pages/             # 页面组件
│   │   ├── services/          # API 服务
│   │   ├── types/             # TypeScript 类型定义
│   │   └── styles/            # 样式文件
│   └── package.json           # Node.js 项目配置
└── env/                        # Docker 环境配置
    ├── docker-compose.yml      # Docker Compose 配置
    ├── .env.example            # 环境变量模板
    └── init-scripts/           # 数据库初始化脚本
```

### Docker Environment Management

所有 Docker 相关配置必须集中在 `./Week2/env` 目录:
- `docker-compose.yml`: 定义所有服务(数据库、后端、前端)
- 启动脚本和管理脚本
- 数据库初始化脚本
- 监控配置(如果需要)

### Code Quality Gates

在提交代码前,必须通过以下检查:
- **后端**: mypy, ruff, black, isort
- **前端**: TypeScript 编译, ESLint
- **测试**: pytest 测试通过(如果有测试)

## Governance

### Amendment Process

Constitution 修订需要:
1. 提出修订提案,说明理由和影响范围
2. 更新相关模板和文档
3. 更新版本号(遵循语义化版本)
4. 记录修订历史

### Versioning Policy

Constitution 使用语义化版本(Semantic Versioning):
- **MAJOR**: 移除或重新定义核心原则,不向后兼容的治理变更
- **MINOR**: 新增原则、章节或显著扩展指导内容
- **PATCH**: 澄清措辞、修正错别字、非语义性改进

### Compliance Review

- 所有 PR 必须验证是否符合 Constitution 原则
- 代码审查必须检查类型标注完整性
- 复杂性增加必须有充分的理由
- 偏离原则需要在 PR 中明确说明并获得批准

### Guidance Documents

运行时开发指导参见:
- 项目 README: `Week2/README.md`
- 规格文档: `specs/001-db-query-tool/`
- 快速开始: 各子项目的 README

**Version**: 1.0.0 | **Ratified**: 2026-01-10 | **Last Amended**: 2026-01-10
