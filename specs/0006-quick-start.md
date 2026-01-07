# Project Alpha 快速开始指南

**文档版本**: v1.0  
**创建时间**: 2026-01-08  
**最后更新**: 2026-01-08

## 🚀 方式 1：Docker（推荐，最简单）

### 一键启动

```bash
# 进入 env 目录
cd env

# 启动所有服务
./start.sh
```

就这么简单！所有服务会自动启动：
- ✅ PostgreSQL 数据库
- ✅ FastAPI 后端（自动运行数据库迁移）
- ✅ React 前端
- ✅ 代码热重载支持

### 访问应用

启动后访问：
- **前端页面**: http://localhost:5173
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **健康检查**: http://localhost:8000/health

### 停止服务

```bash
cd env
./stop.sh
```

### 查看日志

```bash
cd env
docker compose logs -f backend
docker compose logs -f frontend
```

---

## 🛠️ 方式 2：本地开发

### 后端设置

#### 1. 启动数据库（使用 Docker）

```bash
cd env
docker compose up -d postgres
```

#### 2. 设置后端环境

```bash
cd backend

# 安装 UV（如果还没有）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 创建虚拟环境
uv venv
source .venv/bin/activate  # Linux/macOS
# 或 .venv\Scripts\activate  # Windows

# 安装依赖
uv pip install -e ".[dev]"
```

#### 3. 配置环境变量

创建 `.env` 文件：

```bash
cat > .env << EOF
DATABASE_URL=postgresql://ticketuser:ticketpass123@localhost:5432/ticketdb
ENVIRONMENT=development
API_V1_PREFIX=/api/v1
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
LOG_LEVEL=info
EOF
```

#### 4. 运行数据库迁移

```bash
alembic upgrade head
```

#### 5. 启动开发服务器

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 前端设置

#### 1. 安装依赖

```bash
cd frontend

# 使用国内镜像源加速（推荐）
npm config set registry https://registry.npmmirror.com

# 安装依赖
npm install
```

#### 2. 配置环境变量

创建 `.env.local` 文件：

```bash
cat > .env.local << EOF
VITE_API_URL=http://localhost:8000/api/v1
VITE_APP_TITLE=Project Alpha
VITE_APP_DESCRIPTION=Ticket 管理系统
EOF
```

#### 3. 启动开发服务器

```bash
npm run dev
```

访问 http://localhost:5173

---

## ✅ 验证安装

### 使用验证脚本

```bash
cd backend
python verify_phase2.py
```

### 手动验证

1. **健康检查**
   ```bash
   curl http://localhost:8000/health
   ```
   应该返回: `{"status":"healthy","version":"1.0.0"}`

2. **访问 Swagger UI**
   打开浏览器: http://localhost:8000/docs

3. **检查数据库**
   ```bash
   # Docker 方式
   docker compose exec postgres psql -U ticketuser -d ticketdb -c "\dt"
   
   # 本地方式
   psql -U ticketuser -d ticketdb -c "\dt"
   ```

4. **访问前端页面**
   打开浏览器: http://localhost:5173
   应该看到 "Project Alpha - Ticket 管理系统" 页面

---

## 🆘 遇到问题？

### Docker 端口被占用

```bash
# 检查端口占用
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# 修改端口（编辑 docker-compose.yml）
ports:
  - "8001:8000"  # 改为其他端口
```

### 数据库连接失败

```bash
# 检查数据库容器状态
docker compose ps postgres

# 查看数据库日志
docker compose logs postgres

# 等待数据库启动（通常需要 10-30 秒）
```

### 模块导入错误

```bash
# 确保虚拟环境已激活
source .venv/bin/activate

# 重新安装依赖
uv pip install -e ".[dev]"
```

### 前端依赖安装慢

```bash
# 使用国内镜像源
npm config set registry https://registry.npmmirror.com
npm install
```

### API 连接失败

1. 确保后端服务已启动（http://localhost:8000）
2. 检查 `.env.local` 中的 `VITE_API_URL`
3. 查看浏览器控制台的网络请求

---

## 📚 更多文档

- [功能说明](./0003-features.md)
- [验证指南](./0004-verification.md)
- [测试指南](./0005-testing.md)
- [实施计划](./0002-implementation-plan.md)

---

**推荐使用 Docker 方式，更简单、更可靠！** 🐳
