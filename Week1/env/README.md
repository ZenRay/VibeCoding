# Docker 开发环境

Project Alpha 完全基于 Docker 的开发环境配置。

## 🚀 快速开始

### 启动服务

```bash
cd env
./start.sh

# 或手动启动
docker-compose up -d
```

**访问地址：**
- 🌐 前端：http://localhost:5173
- 🔌 后端 API：http://localhost:8000/docs
- 📊 数据库管理：http://localhost:5050 (可选，使用 `docker-compose --profile tools up -d` 启动)

### 停止服务

```bash
./stop.sh

# 或手动停止
docker-compose down
```

---

## 🔍 代码质量检查（提交前必做）

### 方式 1：在运行中的容器内检查（推荐）⭐⭐⭐⭐⭐

**适用场景**：服务已启动（`./start.sh` 执行后）

```bash
./check-running.sh
```

**优势：**
- ✅ 最快（复用运行中的容器）
- ✅ 实时查看服务日志
- ✅ 自动修复格式问题

### 方式 2：使用临时容器检查

**适用场景**：独立运行检查，不依赖服务状态

```bash
./check.sh
```

**优势：**
- ✅ 独立运行，不需要启动服务
- ✅ 与 CI 环境 100% 一致
- ✅ 自动修复格式问题

---

## 📦 服务管理

### 查看日志

```bash
# 所有服务
docker-compose logs -f

# 特定服务
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f postgres
```

### 重启服务

```bash
# 重启单个服务
docker-compose restart backend
docker-compose restart frontend

# 重建并重启
docker-compose up -d --build backend
docker-compose up -d --build frontend
```

### 进入容器

```bash
# 后端容器
docker exec -it project-alpha-backend bash

# 前端容器
docker exec -it project-alpha-frontend sh

# 数据库容器
docker exec -it project-alpha-db psql -U ticketuser -d ticketdb
```

### 查看状态

```bash
docker-compose ps
docker stats
```

---

## 🛠️ 开发工作流

### 完整流程

```bash
# 1. 启动服务
cd env && ./start.sh && cd ..

# 2. 修改代码（本地编辑器）
# Docker volume 自动同步，支持热重载

# 3. 实时预览
# 前端：http://localhost:5173 （自动刷新）
# 后端：http://localhost:8000/docs （自动重载）

# 4. 提交前检查（在 Docker 中）
cd env && ./check-running.sh && cd ..

# 5. 如有问题自动修复，重新检查
cd env && ./check-running.sh && cd ..

# 6. 提交推送
git add -A
git commit -m "feat: 你的功能"
git push origin main

# 7. GitHub Actions 自动运行 CI 检查
# 应该全部通过！✅
```

### 快速检查命令

在容器内直接执行：

```bash
# 后端格式化
docker exec project-alpha-backend bash -c \
  "source .venv/bin/activate && black . && isort . && ruff check --fix ."

# 后端测试
docker exec project-alpha-backend bash -c \
  "source .venv/bin/activate && pytest -v"

# 前端格式化
docker exec project-alpha-frontend sh -c \
  "npx prettier --write 'src/**/*.{ts,tsx,css}'"

# 前端检查
docker exec project-alpha-frontend sh -c \
  "npm run lint && npm run type-check && npm run build"
```

---

## 📂 目录结构

```
env/
├── docker-compose.yml      # Docker Compose 配置
├── Dockerfile.backend      # 后端镜像构建
├── Dockerfile.frontend     # 前端镜像构建
├── start.sh               # 启动服务
├── stop.sh                # 停止服务
├── check.sh               # 代码检查（临时容器）
├── check-running.sh       # 代码检查（运行中容器）
├── init-scripts/          # 数据库初始化脚本
│   └── 01-init.sql
├── .dockerignore.backend  # 后端 Docker 忽略文件
├── .dockerignore.frontend # 前端 Docker 忽略文件
├── env.example            # 环境变量示例
├── DOCKER_SETUP.md        # Docker 安装配置说明
├── DOCKER_CN_OPTIMIZATION.md  # 中国网络优化说明
├── WORKFLOW.md            # 完整工作流文档
└── README.md              # 本文档
```

---

## 🔧 配置说明

### 环境变量

复制 `env.example` 为 `.env` 并修改：

```bash
cp env.example .env
```

主要配置项：
- `DATABASE_URL`: PostgreSQL 连接字符串
- `CORS_ORIGINS`: 允许的跨域源
- `LOG_LEVEL`: 日志级别
- `VITE_API_URL`: 前端 API 地址

### Volume 说明

| Volume | 用途 | 说明 |
|--------|------|------|
| `postgres_data` | 数据库数据 | 持久化数据库 |
| `backend_venv` | Python 虚拟环境 | 避免重复安装依赖 |
| `frontend_node_modules` | Node 依赖 | 避免重复安装依赖 |
| `../backend:/app` | 后端代码 | 实时同步，热重载 |
| `../frontend:/app` | 前端代码 | 实时同步，热重载 |

### 网络配置

所有服务在同一网络 `project-alpha-network` 中，可以通过服务名互相访问：
- 后端访问数据库：`postgres:5432`
- 前端访问后端：`backend:8000`（Vite proxy 配置）

---

## 🌏 中国网络优化

已优化所有 Dockerfile 使用国内镜像源：
- Python 包：清华大学镜像
- npm 包：npmmirror.com
- apt 包：阿里云镜像

详见：[DOCKER_CN_OPTIMIZATION.md](./DOCKER_CN_OPTIMIZATION.md)

---

## 🐛 故障排查

### 服务无法启动

```bash
# 查看日志
docker-compose logs backend
docker-compose logs frontend

# 重建服务
docker-compose down
docker-compose up -d --build
```

### 依赖安装失败

```bash
# 清理 volume 重新安装
docker-compose down -v
docker-compose up -d
```

### 端口冲突

修改 `docker-compose.yml` 中的端口映射：
```yaml
ports:
  - "8001:8000"  # 改为其他端口
```

### 热重载不工作

确保 volume 挂载正确：
```bash
docker-compose config | grep volumes -A 5
```

---

## 📚 相关文档

- [WORKFLOW.md](./WORKFLOW.md) - 完整 Docker 工作流程
- [DOCKER_SETUP.md](./DOCKER_SETUP.md) - Docker 安装配置
- [DOCKER_CN_OPTIMIZATION.md](./DOCKER_CN_OPTIMIZATION.md) - 网络优化
- [../specs/0009-troubleshooting.md](../specs/0009-troubleshooting.md) - 问题排查

---

## 🎯 核心优势

✅ **环境一致性**：本地 = CI = 生产环境  
✅ **零配置**：无需安装 Node/Python/PostgreSQL  
✅ **自动修复**：代码质量问题自动修复  
✅ **热重载**：修改代码实时生效  
✅ **团队协作**：所有人环境完全相同

**使用 Docker 开发，彻底告别环境问题！** 🚀
