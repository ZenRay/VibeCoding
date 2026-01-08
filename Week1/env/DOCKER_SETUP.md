# Docker 开发环境配置指南

## 📋 概述

本文档说明如何使用 Docker 开发环境运行 Project Alpha 后端服务。

## 🚀 快速开始

### 方法 1：使用启动脚本（推荐）

```bash
# 启动所有服务
cd env
./start.sh

# 停止所有服务
./stop.sh
```

### 方法 2：手动启动

```bash
cd env

# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f backend

# 停止服务
docker-compose down
```

## 🐳 Docker 服务说明

### 1. PostgreSQL 数据库
- **容器名**: `project-alpha-db`
- **端口**: `5432`
- **数据库名**: `ticketdb`
- **用户名**: `ticketuser`
- **密码**: `ticketpass123`
- **数据持久化**: Docker volume `postgres_data`

### 2. FastAPI 后端
- **容器名**: `project-alpha-backend`
- **端口**: `8000`
- **访问地址**:
  - API 文档 (Swagger): http://localhost:8000/docs
  - API 文档 (ReDoc): http://localhost:8000/redoc
  - 健康检查: http://localhost:8000/health

### 3. PgAdmin（可选）
- **容器名**: `project-alpha-pgadmin`
- **端口**: `5050`
- **访问地址**: http://localhost:5050
- **邮箱**: admin@example.com
- **密码**: admin123
- **启动方式**: `docker-compose --profile tools up -d`

## 🔧 环境变量配置

后端服务使用以下环境变量（在 `docker-compose.yml` 中配置）：

```yaml
DATABASE_URL: postgresql://ticketuser:ticketpass123@postgres:5432/ticketdb
ENVIRONMENT: development
API_V1_PREFIX: /api/v1
CORS_ORIGINS: http://localhost:5173,http://localhost:3000
LOG_LEVEL: info
```

## 📝 常用操作

### 运行数据库迁移

```bash
# 在容器内运行迁移
docker-compose exec backend alembic upgrade head

# 创建新迁移
docker-compose exec backend alembic revision --autogenerate -m "描述"
```

### 查看日志

```bash
# 查看所有服务日志
docker-compose logs -f

# 查看后端日志
docker-compose logs -f backend

# 查看数据库日志
docker-compose logs -f postgres
```

### 进入容器

```bash
# 进入后端容器
docker-compose exec backend bash

# 进入数据库容器
docker-compose exec postgres psql -U ticketuser -d ticketdb
```

### 重启服务

```bash
# 重启所有服务
docker-compose restart

# 重启特定服务
docker-compose restart backend
```

### 重建镜像

```bash
# 重建后端镜像
docker-compose build backend

# 重建并启动
docker-compose up -d --build backend
```

## 🌐 大陆网络环境优化

Dockerfile 已针对大陆网络环境进行优化：

- ✅ **apt-get 使用阿里云镜像源**（加速系统包下载）
- ✅ **UV 使用 GitHub 镜像下载**（ghproxy.com 代理）
- ✅ **pip/UV 使用清华大学 PyPI 镜像**（加速 Python 包下载）

**速度提升约 4-5 倍** 🚀

详细说明请参考：[DOCKER_CN_OPTIMIZATION.md](./DOCKER_CN_OPTIMIZATION.md)

## 🐛 故障排除

### 问题 1：端口被占用

**错误**: `Bind for 0.0.0.0:8000 failed: port is already allocated`

**解决方案**:
1. 检查端口占用: `lsof -i :8000` (macOS/Linux) 或 `netstat -ano | findstr :8000` (Windows)
2. 停止占用端口的进程
3. 或修改 `docker-compose.yml` 中的端口映射

### 问题 2：数据库连接失败

**错误**: `could not connect to server`

**解决方案**:
1. 检查 PostgreSQL 容器是否运行: `docker-compose ps postgres`
2. 查看数据库日志: `docker-compose logs postgres`
3. 等待数据库健康检查通过（通常需要 10-30 秒）

### 问题 3：后端启动失败

**错误**: `ModuleNotFoundError` 或 `ImportError`

**解决方案**:
1. 检查依赖是否安装: `docker-compose exec backend uv pip list`
2. 重新构建镜像: `docker-compose build backend`
3. 查看详细错误日志: `docker-compose logs backend`

### 问题 4：数据库迁移失败

**错误**: `Target database is not up to date`

**解决方案**:
```bash
# 查看当前迁移版本
docker-compose exec backend alembic current

# 升级到最新版本
docker-compose exec backend alembic upgrade head

# 如果需要，降级后重新升级
docker-compose exec backend alembic downgrade -1
docker-compose exec backend alembic upgrade head
```

### 问题 5：构建速度慢（大陆网络环境）

**现象**: Docker 构建时间过长，下载依赖缓慢

**解决方案**:
1. ✅ Dockerfile 已配置国内镜像源，应该已经很快
2. 如果仍然慢，检查镜像源是否可访问：
   ```bash
   # 测试镜像源
   curl -I https://pypi.tuna.tsinghua.edu.cn/simple/
   curl -I https://mirrors.aliyun.com/debian/
   ```
3. 如果镜像源不可用，参考 [DOCKER_CN_OPTIMIZATION.md](./DOCKER_CN_OPTIMIZATION.md) 切换其他镜像源
4. 使用 Docker 构建缓存：
   ```bash
   docker-compose build --no-cache backend  # 不使用缓存
   docker-compose build backend              # 使用缓存（推荐）
   ```

## 📊 验证环境

### 1. 检查服务状态

```bash
docker-compose ps
```

应该看到所有服务状态为 `Up`。

### 2. 测试健康检查

```bash
curl http://localhost:8000/health
```

应该返回: `{"status":"healthy","version":"1.0.0"}`

### 3. 访问 API 文档

打开浏览器访问: http://localhost:8000/docs

应该看到 Swagger UI 界面。

### 4. 检查数据库连接

```bash
docker-compose exec backend python -c "from app.database import engine; engine.connect(); print('✅ 数据库连接成功')"
```

## 🔄 开发工作流

### 本地开发（不使用 Docker）

如果你更喜欢在本地开发：

```bash
cd backend

# 创建虚拟环境
uv venv
source .venv/bin/activate

# 安装依赖
uv pip install -e ".[dev]"

# 配置环境变量（创建 .env 文件）
# DATABASE_URL=postgresql://ticketuser:ticketpass123@localhost:5432/ticketdb

# 运行迁移
alembic upgrade head

# 启动开发服务器
uvicorn app.main:app --reload
```

### Docker 开发（推荐）

使用 Docker 的好处：
- ✅ 环境一致性
- ✅ 无需本地安装 PostgreSQL
- ✅ 一键启动所有服务
- ✅ 代码热重载支持

## 📚 相关文档

- [Docker Compose 文档](https://docs.docker.com/compose/)
- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [PostgreSQL Docker 镜像](https://hub.docker.com/_/postgres)
