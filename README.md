# Project Alpha - Ticket 管理系统

一个基于标签的轻量级 Ticket 管理系统，使用 FastAPI + React + TypeScript 构建。

**🐳 完全基于 Docker 开发，无需安装任何开发工具！**

## 🚀 快速开始

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

在本地编辑器修改 `backend/` 或 `frontend/` 代码，Docker 自动同步并热重载。

### 4. 提交前检查

```bash
cd env
./check-running.sh  # 在 Docker 中检查代码质量
```

---

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
│   ├── Dockerfile.*          # 镜像构建
│   ├── WORKFLOW.md           # 完整工作流文档
│   ├── 快速参考.md           # 常用命令速查
│   └── README.md             # Docker 环境说明
├── specs/            # 项目文档（15 个技术文档）
│   ├── README.md             # 文档索引
│   ├── 0001-spec.md          # 需求规格
│   ├── 0010-docker-development.md  # Docker 指南
│   ├── 0011-code-quality.md        # 代码质量
│   ├── 0014-lessons-learned.md     # 经验教训
│   └── ...
└── 本次开发总结.md    # 开发总结
```

---

## ✨ 功能特性

### Ticket 管理
- ✅ 创建、编辑、删除（软删除）Ticket
- ✅ 状态切换（未完成 ↔ 已完成）
- ✅ 批量操作（批量选择、批量删除）
- ✅ 软删除恢复
- ✅ 实时搜索标题
- ✅ 多维度过滤（状态、标签、删除状态）
- ✅ 排序（创建时间、更新时间、标题）

### 标签管理
- ✅ 创建、编辑、删除标签
- ✅ 颜色选择器（含预设颜色）
- ✅ 英文自动转大写
- ✅ 标签使用统计

### UI/UX
- ✅ 侧边栏过滤
- ✅ 列表布局
- ✅ 响应式设计
- ✅ 删除线显示已删除项
- ✅ 实时热重载

---

## 🛠️ 技术栈

### 后端
- Python 3.12
- FastAPI 0.109+
- PostgreSQL 16
- SQLAlchemy 2.0+
- Alembic（数据库迁移）

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

### 代码质量
- **后端**：Black、isort、Ruff、pytest
- **前端**：Prettier、ESLint、TypeScript

---

## 📚 文档

### 核心文档

**快速入门**：
- [快速开始](./specs/0006-quick-start.md)
- [Docker 环境](./specs/0010-docker-development.md)
- [快速参考](./env/快速参考.md)

**开发指南**：
- [数据库设计](./specs/0012-database-design.md)
- [前端架构](./specs/0013-frontend-architecture.md)
- [代码质量](./specs/0011-code-quality.md)

**工作流程**：
- [Git 工作流](./specs/0007-git-workflow.md)
- [Docker 工作流](./env/WORKFLOW.md)
- [问题排查](./specs/0009-troubleshooting.md)

**完整索引**：[specs/README.md](./specs/README.md)

---

## 🔧 开发工作流

### 完整流程

```bash
# 1. 启动服务
cd env && ./start.sh

# 2. 编辑代码（本地编辑器）
# 自动热重载，实时预览

# 3. 实时预览
# 前端: http://localhost:5173
# 后端: http://localhost:8000/docs

# 4. 提交前检查（在 Docker 中）
./check-running.sh

# 5. 自动修复（如有问题）
# Black/Prettier 自动修复格式

# 6. 提交推送
cd ..
git add -A
git commit -m "feat: 你的功能"
git push origin main

# 7. GitHub Actions 自动验证
# 应该全部通过！✅
```

### 快捷命令

```bash
# 启动开发环境
cd env && ./start.sh

# 检查代码质量
cd env && ./check-running.sh

# 停止服务
cd env && ./stop.sh

# 查看日志
docker-compose -f env/docker-compose.yml logs -f
```

---

## 🐳 Docker 优势

| 方面 | 传统开发 | Docker 开发 |
|------|---------|------------|
| 环境配置 | 需要安装多个工具 | 一键启动 |
| 环境一致性 | 可能不同 | 100% 一致 |
| Node 版本 | 需要 nvm 管理 | 容器内 Node 20 |
| Python 版本 | 需要 pyenv 管理 | 容器内 Python 3.12 |
| 数据库 | 需要安装 PostgreSQL | 容器自带 |
| 依赖隔离 | 可能冲突 | 完全隔离 |
| CI 一致性 | 不确定 | 100% 一致 |
| 团队协作 | 环境差异 | 所有人相同 |

---

## 📊 项目统计

### 代码统计

- **后端**：Python 文件 34 个，约 2,500 行
- **前端**：TypeScript 文件 31 个，约 3,000 行
- **测试**：35 个测试用例，覆盖率 82%+
- **文档**：15 个技术文档，约 50,000 字

### 功能统计

- **API 端点**：15+ 个
- **前端组件**：14 个
- **数据库表**：3 个
- **Docker 服务**：4 个

---

## 🎯 核心优势

1. **完全基于 Docker** - 环境一致性 100%
2. **自动化程度高** - CI/CD + 代码检查自动化
3. **文档完善** - 15 个技术文档覆盖所有方面
4. **代码质量高** - 82% 测试覆盖率，严格代码规范
5. **可复用性强** - 配置和脚本可作为模板

---

## 📝 许可证

MIT License

## 👥 贡献

欢迎提交 Issue 和 Pull Request！

---

**项目地址**: https://github.com/ZenRay/VibeCoding  
**快速开始**: [specs/0006-quick-start.md](./specs/0006-quick-start.md)  
**文档索引**: [specs/README.md](./specs/README.md)  
**开发总结**: [specs/0015-project-summary.md](./specs/0015-project-summary.md)

---

**使用 Docker 开发，彻底告别环境问题！** 🎉
