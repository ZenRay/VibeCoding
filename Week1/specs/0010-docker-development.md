# Docker 开发环境完整指南

**文档版本**: v1.0  
**创建时间**: 2026-01-08  
**最后更新**: 2026-01-08

## 📋 目录

1. [概述](#概述)
2. [环境架构](#环境架构)
3. [Docker 配置详解](#docker-配置详解)
4. [开发工作流](#开发工作流)
5. [代码质量检查](#代码质量检查)
6. [常用操作](#常用操作)
7. [故障排查](#故障排查)

---

## 概述

### 为什么使用 Docker

Project Alpha 完全基于 Docker 开发，原因：

✅ **环境一致性 100%**
- 本地开发环境 = CI 环境 = 生产环境
- 避免 "在我机器上可以运行" 的问题

✅ **零配置要求**
- 无需安装 Node.js、Python、PostgreSQL
- 不污染宿主机环境

✅ **团队协作友好**
- 所有开发者使用完全相同的环境
- 新成员 1 分钟即可开始开发

✅ **与 CI/CD 完美对接**
- 本地检查 = CI 检查
- 本地通过 = CI 必通过

### 核心原则

> **所有开发和测试都在 Docker 环境中进行，不使用宿主机环境。**

---

## 环境架构

### 服务组成

```
Docker Network: project-alpha-network
├── postgres (PostgreSQL 16)
│   ├── 端口: 5432
│   ├── Volume: postgres_data
│   └── 健康检查: pg_isready
│
├── backend (FastAPI + Python 3.12)
│   ├── 端口: 8000
│   ├── Volume: backend/ + backend_venv
│   ├── 依赖: postgres
│   └── 热重载: ✅
│
├── frontend (Vite + Node 20)
│   ├── 端口: 5173
│   ├── Volume: frontend/ + frontend_node_modules
│   ├── 依赖: backend
│   └── 热重载: ✅
│
└── pgadmin (可选)
    ├── 端口: 5050
    ├── Profile: tools
    └── 用途: 数据库管理
```

### Volume 说明

| Volume | 用途 | 持久化 |
|--------|------|-------|
| `postgres_data` | 数据库数据 | ✅ 是 |
| `backend_venv` | Python 虚拟环境 | ✅ 是 |
| `frontend_node_modules` | Node 依赖 | ✅ 是 |
| `../backend:/app` | 后端代码挂载 | ❌ 否（实时同步）|
| `../frontend:/app` | 前端代码挂载 | ❌ 否（实时同步）|

**关键点**：
- 代码目录使用 bind mount，修改实时同步
- 依赖目录使用 named volume，避免重复安装

---

## Docker 配置详解

### docker-compose.yml

位置：`env/docker-compose.yml`

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: ticketdb
      POSTGRES_USER: ticketuser
      POSTGRES_PASSWORD: ticketpass123
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready"]
      interval: 10s

  backend:
    build:
      context: ../backend
      dockerfile: ../env/Dockerfile.backend
    volumes:
      - ../backend:/app              # 代码实时同步
      - backend_venv:/app/.venv      # 依赖持久化
    depends_on:
      postgres:
        condition: service_healthy   # 等待数据库就绪
    command: .venv/bin/uvicorn app.main:app --reload

  frontend:
    build:
      context: ../frontend
      dockerfile: ../env/Dockerfile.frontend
    volumes:
      - ../frontend:/app                        # 代码实时同步
      - frontend_node_modules:/app/node_modules # 依赖持久化
    command: npm run dev -- --host 0.0.0.0
```

### Dockerfile.backend

位置：`env/Dockerfile.backend`

**关键配置**：
```dockerfile
FROM python:3.12-slim

# 国内镜像优化
ENV PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple

# 虚拟环境
RUN python -m venv .venv
RUN . .venv/bin/activate && pip install -e ".[dev]"

# 热重载支持
CMD [".venv/bin/uvicorn", "app.main:app", "--reload"]
```

### Dockerfile.frontend

位置：`env/Dockerfile.frontend`

**关键配置**：
```dockerfile
FROM node:20-alpine

# 国内镜像优化
RUN npm config set registry https://registry.npmmirror.com

# 安装依赖
RUN npm install

# 热重载支持
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
```

---

## 开发工作流

### 完整流程

```bash
# === 第一步：启动开发环境 ===
cd env
./start.sh

# 等待服务启动（约 10-30 秒）
# 查看日志确认启动成功：
docker-compose logs -f

# === 第二步：开发 ===
# 在本地编辑器修改代码
# - backend/ 目录 → 后端容器自动重载
# - frontend/ 目录 → 前端容器自动重载

# 实时预览：
# - 前端: http://localhost:5173
# - 后端 API: http://localhost:8000/docs

# === 第三步：提交前检查 ===
cd env
./check-running.sh

# 如果检查失败，会自动修复格式问题
# 重新运行检查确认通过
./check-running.sh

# === 第四步：提交推送 ===
cd ..
git add -A
git commit -m "feat: 你的功能描述"
git push origin main

# === 第五步：验证 ===
# GitHub Actions 自动运行 CI 检查
# 应该全部通过！✅

# === 第六步：停止服务（可选）===
cd env
./stop.sh
```

### 快捷命令

```bash
# 启动
cd env && ./start.sh

# 检查
cd env && ./check-running.sh

# 停止
cd env && ./stop.sh
```

---

## 代码质量检查

### 检查脚本

#### check-running.sh（推荐）

在运行中的容器内执行检查，最快。

```bash
cd env
./check-running.sh
```

**执行内容**：
1. 后端检查（在 `project-alpha-backend` 容器内）
   - Black 格式化检查 + 自动修复
   - isort 导入排序 + 自动修复
   - Ruff 代码检查 + 自动修复
   - pytest 测试

2. 前端检查（在 `project-alpha-frontend` 容器内）
   - Prettier 格式化 + 自动修复
   - ESLint 检查
   - TypeScript 类型检查
   - 构建检查

#### check.sh

使用临时容器检查，不依赖服务状态。

```bash
cd env
./check.sh
```

**优势**：
- 独立运行，不需要先启动服务
- 使用官方镜像（python:3.12-slim、node:20-alpine）
- 与 CI 环境完全一致

### 手动检查命令

#### 后端

```bash
# 进入后端容器
docker exec -it project-alpha-backend bash

# 在容器内执行
source .venv/bin/activate

# 格式化
black .
isort .
ruff check --fix .

# 测试
pytest -v
pytest --cov=app --cov-report=term
```

#### 前端

```bash
# 进入前端容器
docker exec -it project-alpha-frontend sh

# 在容器内执行
npx prettier --write "src/**/*.{ts,tsx,css}"
npm run lint
npm run type-check
npm run build
```

---

## 常用操作

### 服务管理

```bash
# 启动所有服务
docker-compose up -d

# 启动特定服务
docker-compose up -d backend frontend

# 停止所有服务
docker-compose down

# 停止并删除数据
docker-compose down -v

# 重启服务
docker-compose restart backend
docker-compose restart frontend

# 重建服务
docker-compose up -d --build backend
```

### 日志查看

```bash
# 所有服务日志
docker-compose logs -f

# 特定服务日志
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f postgres

# 查看最近 100 行
docker-compose logs --tail=100 backend
```

### 容器操作

```bash
# 列出运行中的容器
docker-compose ps

# 查看资源使用
docker stats

# 进入容器
docker exec -it project-alpha-backend bash
docker exec -it project-alpha-frontend sh
docker exec -it project-alpha-db psql -U ticketuser -d ticketdb
```

### 数据库操作

```bash
# 进入数据库
docker exec -it project-alpha-db psql -U ticketuser -d ticketdb

# 备份数据库
docker exec project-alpha-db pg_dump -U ticketuser ticketdb > backup.sql

# 恢复数据库
docker exec -i project-alpha-db psql -U ticketuser -d ticketdb < backup.sql

# 查看数据库日志
docker-compose logs postgres
```

---

## 故障排查

### 服务无法启动

```bash
# 1. 查看日志
docker-compose logs backend | tail -50
docker-compose logs frontend | tail -50

# 2. 检查端口占用
lsof -i :5173
lsof -i :8000
lsof -i :5432

# 3. 重建服务
docker-compose down
docker-compose up -d --build

# 4. 清理并重建
docker-compose down -v
docker volume prune
docker-compose up -d --build
```

### 热重载不工作

```bash
# 1. 检查 volume 挂载
docker-compose config | grep volumes -A 5

# 2. 检查容器日志
docker-compose logs -f backend

# 3. 重启服务
docker-compose restart backend
docker-compose restart frontend
```

### 依赖安装失败

```bash
# 1. 清理 volume
docker-compose down -v

# 2. 重新构建
docker-compose build --no-cache backend
docker-compose build --no-cache frontend

# 3. 启动服务
docker-compose up -d
```

### 数据库连接失败

```bash
# 1. 检查数据库健康状态
docker-compose ps postgres

# 2. 查看数据库日志
docker-compose logs postgres

# 3. 手动连接测试
docker exec -it project-alpha-db psql -U ticketuser -d ticketdb

# 4. 重启数据库
docker-compose restart postgres
```

### 端口冲突

修改 `docker-compose.yml` 中的端口映射：

```yaml
services:
  backend:
    ports:
      - "8001:8000"  # 改为其他端口
  
  frontend:
    ports:
      - "5174:5173"  # 改为其他端口
```

---

## 性能优化

### 构建优化

```bash
# 使用构建缓存
docker-compose build

# 并行构建
docker-compose build --parallel

# 清理构建缓存
docker builder prune
```

### 运行优化

```bash
# 限制资源使用
docker-compose up -d --scale backend=1 --scale frontend=1

# 查看资源使用
docker stats
```

---

## CI/CD 集成

### GitHub Actions 配置

**所有 CI 检查都在 Docker 中执行**，确保与本地环境完全一致。

```yaml
# .github/workflows/ci.yml
jobs:
  backend-check:
    runs-on: ubuntu-latest
    steps:
      - name: Run checks in Docker
        run: |
          docker run --rm \
            -v "${{ github.workspace }}/backend:/app" \
            -w /app \
            python:3.12-slim \
            bash -c "pip install -q -e '.[dev]' && black --check . && pytest"
```

### 本地复现 CI 环境

```bash
# 完全复现 GitHub Actions 的检查
cd env
./check.sh

# 与 CI 使用相同的 Docker 镜像和命令
```

---

## 最佳实践

### 1. 提交前必做

```bash
cd env && ./check-running.sh
```

### 2. 定期清理

```bash
# 清理未使用的镜像
docker image prune

# 清理未使用的 volume
docker volume prune

# 清理所有（谨慎！）
docker system prune -a
```

### 3. 监控日志

```bash
# 实时查看日志
docker-compose logs -f

# 配合 grep 过滤
docker-compose logs -f backend | grep ERROR
```

### 4. 数据备份

```bash
# 定期备份数据库
docker exec project-alpha-db pg_dump -U ticketuser ticketdb > backup_$(date +%Y%m%d).sql
```

---

## 快速参考

### 一键命令

```bash
# 启动
cd env && ./start.sh

# 检查
cd env && ./check-running.sh

# 停止
cd env && ./stop.sh
```

### 容器操作

```bash
# 进入容器
docker exec -it project-alpha-backend bash
docker exec -it project-alpha-frontend sh

# 查看日志
docker-compose logs -f backend

# 重启服务
docker-compose restart backend
```

### 代码检查

```bash
# 后端
docker exec project-alpha-backend bash -c \
  "source .venv/bin/activate && black . && pytest"

# 前端
docker exec project-alpha-frontend sh -c \
  "npx prettier --write 'src/**/*.{ts,tsx,css}' && npm run lint"
```

---

## 相关文档

- [快速参考](../env/快速参考.md) - 常用命令速查
- [完整工作流](../env/WORKFLOW.md) - 详细工作流程
- [问题排查](./0009-troubleshooting.md) - 常见问题解决
- [Docker 配置](../env/README.md) - 环境配置说明

---

## 总结

**使用 Docker 开发的核心优势：**

1. **环境一致性** - 本地 = CI = 生产
2. **零配置** - 无需安装工具
3. **自动修复** - 代码质量问题自动修复
4. **热重载** - 修改代码实时生效
5. **团队友好** - 所有人环境相同

**记住**：提交前运行 `cd env && ./check-running.sh`，确保代码质量！🚀
