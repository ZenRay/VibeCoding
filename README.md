# Project Alpha - Ticket 管理系统

一个基于标签的轻量级 Ticket 管理系统，使用 FastAPI + React + TypeScript 构建。

## 🚀 快速开始

### 使用 Docker（推荐）

```bash
# 进入环境目录
cd env

# 启动所有服务
./start.sh

# 访问应用
# 前端: http://localhost:5173
# 后端 API 文档: http://localhost:8000/docs
```

### 本地开发

详细说明请查看：[快速开始指南](./specs/0006-quick-start.md)

### 代码检查方式（三选一）

#### 方式 1：Docker 检查（推荐）⭐⭐⭐⭐⭐

**适用场景**：本地 Node/Python 版本不匹配，或希望与 CI 环境 100% 一致

```bash
# 方案 A：在运行中的容器内检查（最快）
./scripts/docker-exec-check.sh

# 方案 B：使用临时容器检查（独立运行）
./scripts/docker-check.sh
```

**优势：**
- ✅ 环境 100% 一致（Python 3.12 + Node 20）
- ✅ 无需本地安装任何工具
- ✅ 自动修复格式问题
- ✅ 本地通过 = CI 必通过

#### 方式 2：本地检查

**适用场景**：本地环境正确（Python 3.12 + Node 14+）

```bash
# 检查所有
./scripts/check-local.sh all

# 只检查后端/前端
./scripts/check-local.sh backend
./scripts/check-local.sh frontend
```

#### 方式 3：手动检查

```bash
# 后端
cd backend
black . && isort . && ruff check --fix . && pytest

# 前端（需要 Node 14+）
cd frontend
npx prettier --write "src/**/*.{ts,tsx,css}"
npm run lint && npm run type-check
```

---

### 快速修复脚本

```bash
# 一键修复所有格式问题
bash 一键修复.sh

# 使用 Docker 修复前端格式
bash fix_prettier_docker.sh
```

---

### 完整开发流程（Docker 方式）

```bash
# 1. 启动开发环境
cd env && ./start.sh && cd ..

# 2. 修改代码（本地编辑器）

# 3. 提交前检查
./scripts/docker-exec-check.sh

# 4. 提交推送
git add -A
git commit -m "feat: 你的功能"
git push origin main
```

详细文档：[Docker 工作流程](./DOCKER_WORKFLOW.md)

## 📋 项目结构

```
Week1/
├── backend/          # 后端代码（Python + FastAPI）
├── frontend/         # 前端代码（React + TypeScript）
├── env/              # Docker 环境配置
├── specs/            # 项目文档
└── ticket/           # 项目说明和进度跟踪
```

## ✨ 功能特性

- ✅ **Ticket 管理**：创建、编辑、删除（软删除）、状态切换
- ✅ **标签管理**：创建、编辑、删除标签，自动转大写
- ✅ **搜索功能**：实时搜索 Ticket 标题
- ✅ **过滤功能**：按状态、标签过滤
- ✅ **批量操作**：批量选择和删除
- ✅ **排序功能**：按创建时间、更新时间、标题排序

## 🛠️ 技术栈

### 后端
- Python 3.12
- FastAPI 0.109+
- PostgreSQL 16
- SQLAlchemy 2.0+
- Alembic（数据库迁移）
- UV（包管理）

### 前端
- React 18.2+
- TypeScript 5.3+
- Vite 5.0+
- Tailwind CSS 3.4+
- Shadcn UI
- Zustand（状态管理）

### 开发环境
- Docker + Docker Compose
- GitHub Actions（CI/CD）
- Pre-commit hooks

## 📚 文档

所有项目文档位于 `specs/` 目录：

- [0001-spec.md](./specs/0001-spec.md) - 需求规格说明
- [0002-implementation-plan.md](./specs/0002-implementation-plan.md) - 实施计划
- [0003-features.md](./specs/0003-features.md) - 功能说明
- [0004-verification.md](./specs/0004-verification.md) - 验证指南
- [0005-testing.md](./specs/0005-testing.md) - 测试指南
- [0006-quick-start.md](./specs/0006-quick-start.md) - 快速开始
- [0007-git-workflow.md](./specs/0007-git-workflow.md) - Git 工作流
- [0008-documentation-structure.md](./specs/0008-documentation-structure.md) - 文档结构

## 📊 项目进度

**当前进度：60.8%** (76/125 任务完成)

### 已完成阶段
- ✅ 阶段 0：环境准备（100%）
- ✅ 阶段 1：数据库与后端基础（100%）
- ✅ 阶段 2：后端 API 实现（100%）
- ✅ 阶段 3：前端基础设施（100%）
- ✅ 阶段 4：前端核心功能（85%）

### 待完成阶段
- ⚪ 阶段 5：前端扩展功能
- ⚪ 阶段 6：测试与优化
- ⚪ 阶段 7：部署与上线

## 🔧 开发

### 安装 Pre-commit Hooks

```bash
pip install pre-commit
pre-commit install
```

### 运行测试

**后端测试**：
```bash
cd backend
pytest
```

**前端类型检查**：
```bash
cd frontend
npm run type-check
npm run lint
```

## 📝 许可证

MIT License

## 👥 贡献

欢迎提交 Issue 和 Pull Request！

---

**项目地址**: https://github.com/ZenRay/VibeCoding
