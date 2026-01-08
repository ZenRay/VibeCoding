# Project Alpha - Ticket 管理系统

基于标签的 Ticket 管理工具，提供简洁高效的任务跟踪和分类功能。

## 技术栈

- **后端**: Python 3.12 + FastAPI + PostgreSQL 16 + SQLAlchemy 2.0 + Alembic
- **前端**: React 18 + TypeScript 5 + Vite 5 + Tailwind CSS + Shadcn UI
- **状态管理**: Zustand
- **开发环境**: Docker + Docker Compose

## 功能特性

- ✅ 创建、编辑、删除、完成 Ticket
- ✅ 软删除和恢复功能
- ✅ 批量操作（批量完成、批量删除）
- ✅ 基于标签的灵活分类
- ✅ 标签管理（创建、编辑、删除，名称自动大写）
- ✅ 多维度过滤（状态、标签、删除状态）
- ✅ 实时搜索（防抖优化）
- ✅ 排序功能（按创建时间、更新时间、标题）
- ✅ 分页功能
- ✅ Toast 提示系统
- ✅ 骨架屏加载状态
- ✅ 回收站页面
- ✅ 键盘快捷键支持
- ✅ 错误边界处理

## 快速开始

### 前置要求

- Docker Desktop（已安装 Docker Compose）

### 一键启动

```bash
cd env
./start.sh
```

### 访问应用

- 前端: http://localhost:5173
- 后端 API: http://localhost:8000
- API 文档 (Swagger): http://localhost:8000/docs
- API 文档 (ReDoc): http://localhost:8000/redoc

### 停止服务

```bash
cd env
./stop.sh
```

## 项目结构

```
Week1/
├── backend/          # FastAPI 后端
│   ├── app/
│   │   ├── api/      # API 路由
│   │   ├── models/   # 数据模型
│   │   ├── schemas/  # Pydantic 模型
│   │   ├── services/ # 业务逻辑
│   │   └── utils/    # 工具函数
│   ├── alembic/      # 数据库迁移
│   └── tests/        # 测试
├── frontend/         # React 前端
│   └── src/
│       ├── components/   # React 组件
│       ├── hooks/        # 自定义 Hooks
│       ├── pages/        # 页面组件
│       ├── services/     # API 服务
│       ├── store/        # 状态管理
│       └── types/        # TypeScript 类型
├── env/              # Docker 环境配置
├── specs/            # 技术文档（17 个）
└── ticket/           # 项目说明
```

## 开发

### 代码检查（提交前必须）

```bash
cd env
./check-running.sh
```

### 运行测试

```bash
docker exec project-alpha-backend bash -c \
  "source .venv/bin/activate && pytest -v"
```

### 查看日志

```bash
docker compose -f env/docker-compose.yml logs -f backend
docker compose -f env/docker-compose.yml logs -f frontend
```

### 进入容器

```bash
# 后端
docker exec -it project-alpha-backend bash

# 前端
docker exec -it project-alpha-frontend sh
```

## 键盘快捷键

- `N`: 创建新 Ticket
- `Ctrl/Cmd + K`: 聚焦搜索框
- `Esc`: 关闭对话框

## 文档

- [快速开始](../specs/0006-quick-start.md) - 3 分钟上手
- [Docker 环境](../specs/0010-docker-development.md) - 开发环境详解
- [代码质量](../specs/0011-code-quality.md) - 代码规范
- [项目状态](../PROJECT_STATUS.md) - 当前进度
- [文档导航](../文档导航.md) - 所有文档索引

## 许可证

MIT
