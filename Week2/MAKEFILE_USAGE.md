# Makefile 使用指南

本项目提供了完整的 Makefile，用于简化常用的开发任务。

## 快速开始

### 查看所有可用命令

```bash
make help
```

### 首次设置项目

```bash
make setup
```

这将：
1. 安装后端依赖（创建虚拟环境并安装 Python 包）
2. 安装前端依赖（npm install）
3. 初始化数据库（运行 Alembic 迁移）

### 启动开发环境

```bash
make dev
```

这将启动：
- 测试数据库（PostgreSQL + MySQL）
- 后端服务（http://localhost:8000）
- 前端服务（http://localhost:3000）

所有服务在后台运行，日志保存在 `/tmp/backend.log` 和 `/tmp/frontend.log`。

## 常用命令

### 安装和设置

| 命令 | 说明 |
|------|------|
| `make install` | 安装所有依赖（后端 + 前端） |
| `make install-backend` | 仅安装后端依赖 |
| `make install-frontend` | 仅安装前端依赖 |
| `make init-db` | 初始化数据库（运行迁移） |
| `make setup` | 完整设置（安装 + 初始化） |

### 启动和停止服务

| 命令 | 说明 |
|------|------|
| `make start` | 启动所有服务（前台运行） |
| `make start-backend` | 启动后端服务（端口 8000） |
| `make start-frontend` | 启动前端服务（端口 3000） |
| `make start-db` | 启动测试数据库 |
| `make stop` | 停止所有服务 |
| `make stop-backend` | 停止后端服务 |
| `make stop-frontend` | 停止前端服务 |
| `make stop-db` | 停止测试数据库 |
| `make restart` | 重启所有服务 |
| `make dev` | 启动开发环境（后台运行） |

### 数据库迁移

| 命令 | 说明 |
|------|------|
| `make migrate` | 升级数据库到最新版本 |
| `make migrate-create MESSAGE="描述"` | 创建新的迁移文件 |
| `make migrate-upgrade` | 升级数据库 |
| `make migrate-downgrade REVISION="-1"` | 降级数据库 |
| `make migrate-history` | 查看迁移历史 |

**示例：**

```bash
# 创建新的迁移
make migrate-create MESSAGE="添加用户表"

# 降级一个版本
make migrate-downgrade REVISION="-1"

# 降级到初始状态
make migrate-downgrade REVISION="base"
```

### 测试

| 命令 | 说明 |
|------|------|
| `make test` | 运行所有测试 |
| `make test-backend` | 运行后端测试 |
| `make test-frontend` | 运行前端测试 |

### 代码质量

| 命令 | 说明 |
|------|------|
| `make lint` | 运行所有代码检查 |
| `make lint-backend` | 检查后端代码（ruff + mypy） |
| `make lint-frontend` | 检查前端代码（eslint + tsc） |
| `make format` | 格式化所有代码 |
| `make format-backend` | 格式化后端代码（black + ruff） |
| `make format-frontend` | 格式化前端代码（prettier） |
| `make check` | 运行完整的代码检查和测试 |

### 清理

| 命令 | 说明 |
|------|------|
| `make clean` | 清理构建文件和缓存 |
| `make clean-backend` | 清理后端文件（__pycache__, .pytest_cache 等） |
| `make clean-frontend` | 清理前端文件（dist, .vite 等） |
| `make clean-all` | 完全清理（包括虚拟环境和 node_modules） |

### 实用工具

| 命令 | 说明 |
|------|------|
| `make status` | 查看所有服务状态 |
| `make logs-backend` | 查看后端日志（如果使用 make dev 启动） |
| `make logs-frontend` | 查看前端日志（如果使用 make dev 启动） |
| `make logs-db` | 查看数据库日志 |

## 典型工作流程

### 1. 新项目设置

```bash
# 克隆项目后
make setup
make start-db
make dev
```

### 2. 日常开发

```bash
# 启动开发环境
make dev

# 在另一个终端查看日志
make logs-backend
make logs-frontend

# 停止服务
make stop
```

### 3. 代码提交前

```bash
# 格式化代码
make format

# 运行代码检查
make lint

# 运行测试
make test

# 或者一次性运行所有检查
make check
```

### 4. 数据库变更

```bash
# 修改模型后创建迁移
make migrate-create MESSAGE="添加新字段"

# 应用迁移
make migrate

# 如果需要回滚
make migrate-downgrade REVISION="-1"
```

### 5. 清理和重置

```bash
# 清理构建文件
make clean

# 完全重置（删除依赖）
make clean-all
make setup
```

## 注意事项

1. **虚拟环境**: 后端使用 `uv` 管理虚拟环境，位置在 `backend/.venv`
2. **端口占用**: 
   - 后端: 8000
   - 前端: 3000
   - PostgreSQL: 5432
   - MySQL: 3306
3. **日志文件**: 使用 `make dev` 启动时，日志保存在 `/tmp/backend.log` 和 `/tmp/frontend.log`
4. **Docker**: 确保 Docker 和 Docker Compose 已安装并运行

## 故障排除

### 命令找不到

确保在 `Week2` 目录下运行命令：

```bash
cd Week2
make help
```

### 虚拟环境不存在

```bash
make install-backend
```

### 端口被占用

```bash
# 检查端口占用
lsof -i :8000
lsof -i :3000

# 停止服务
make stop
```

### Docker 服务无法启动

```bash
# 检查 Docker 状态
docker ps

# 查看数据库日志
make logs-db
```

## 高级用法

### 自定义变量

可以在命令行覆盖默认值：

```bash
# 使用不同的端口启动后端
cd backend && .venv/bin/uvicorn app.main:app --port 8080
```

### 组合命令

```bash
# 清理并重新设置
make clean-all && make setup

# 停止服务并清理
make stop && make clean
```
