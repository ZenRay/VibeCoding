# Project Alpha - Ticket 管理系统

一个基于标签的轻量级 Ticket 管理系统，使用 FastAPI + React + TypeScript 构建。

## 🚀 快速开始

**本项目完全基于 Docker 开发，无需安装 Node.js、Python 或 PostgreSQL。**

### 1. 启动服务

```bash
cd env
./start.sh
```

### 2. 访问应用

- 🌐 前端：http://localhost:5173
- 🔌 后端 API 文档：http://localhost:8000/docs
- 📊 数据库管理：http://localhost:5050 (可选)

### 3. 开发

在本地编辑器修改代码，Docker 自动同步并热重载。

### 4. 提交前检查

```bash
cd env
./check-running.sh  # 在 Docker 中检查代码质量
```

详细说明：[env/README.md](./env/README.md) | [env/WORKFLOW.md](./env/WORKFLOW.md)

### 代码质量检查（提交前必做）

**所有检查都在 Docker 环境中运行，确保与 CI 环境 100% 一致。**

#### 方式 1：在运行中的容器内检查（推荐）⭐⭐⭐⭐⭐

```bash
cd env && ./check-running.sh
```

**优势：** 最快，复用已启动的容器，自动修复格式问题

#### 方式 2：使用临时容器检查

```bash
cd env && ./check.sh
```

**优势：** 独立运行，不依赖服务状态

---

### 完整开发流程

```bash
# 1. 启动开发环境
cd env && ./start.sh

# 2. 修改代码（本地编辑器，支持热重载）

# 3. 实时预览
#    前端: http://localhost:5173
#    后端: http://localhost:8000/docs

# 4. 提交前检查（在 Docker 中）
./check-running.sh

# 5. 如有问题会自动修复，重新检查
./check-running.sh

# 6. 提交推送
cd ..
git add -A
git commit -m "feat: 你的功能"
git push origin main

# 7. GitHub Actions 自动验证（应该全部通过✅）
```

详细文档：[env/WORKFLOW.md](./env/WORKFLOW.md)

## 📋 项目结构

```
Week1/
├── backend/          # 后端代码（Python + FastAPI）
├── frontend/         # 前端代码（React + TypeScript）
├── env/              # Docker 环境配置（所有开发工具）
│   ├── check.sh              # 代码质量检查（临时容器）
│   ├── check-running.sh      # 代码质量检查（运行中容器）
│   ├── start.sh              # 启动服务
│   ├── stop.sh               # 停止服务
│   ├── docker-compose.yml    # Docker 配置
│   ├── Dockerfile.backend    # 后端镜像
│   ├── Dockerfile.frontend   # 前端镜像
│   ├── WORKFLOW.md           # 完整工作流文档
│   └── README.md             # Docker 环境说明
├── specs/            # 项目文档
│   └── 0009-troubleshooting.md  # 问题排查指南
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

## 🔧 开发工具

### 容器内开发

所有开发和测试都在 Docker 容器内进行：

**后端开发**：
```bash
# 进入后端容器
docker exec -it project-alpha-backend bash

# 在容器内
source .venv/bin/activate
pytest -v              # 运行测试
black .                # 格式化
ruff check --fix .     # 代码检查
```

**前端开发**：
```bash
# 进入前端容器
docker exec -it project-alpha-frontend sh

# 在容器内
npm run lint           # ESLint 检查
npm run type-check     # TypeScript 检查
npx prettier --write "src/**/*.{ts,tsx,css}"  # 格式化
```

### 数据库管理

**PgAdmin（图形界面）**：
```bash
docker-compose --profile tools up -d pgadmin
# 访问 http://localhost:5050
# 用户名：admin@example.com
# 密码：admin123
```

**命令行**：
```bash
docker exec -it project-alpha-db psql -U ticketuser -d ticketdb
```

## 📝 许可证

MIT License

## 👥 贡献

欢迎提交 Issue 和 Pull Request！

---

**项目地址**: https://github.com/ZenRay/VibeCoding
