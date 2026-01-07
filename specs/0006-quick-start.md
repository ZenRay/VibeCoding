# Project Alpha 快速开始指南

**文档版本**: v2.0  
**创建时间**: 2026-01-08  
**最后更新**: 2026-01-08

**🎯 3 分钟即可开始开发！**

---

## 📋 前置要求

- ✅ Docker Desktop 已安装并运行
- ✅ Git 已配置
- ✅ 代码编辑器（VS Code 推荐）

**仅此而已！** 无需安装 Node.js、Python 或 PostgreSQL。

---

## 🚀 三步开始

### 第一步：启动服务（30 秒）

```bash
cd env
./start.sh
```

等待服务启动，看到：
```
✅ 所有服务已启动
前端: http://localhost:5173
后端: http://localhost:8000/docs
```

### 第二步：开始开发（立即）

在编辑器中打开项目：
- 修改 `backend/` → 后端自动重载
- 修改 `frontend/` → 前端自动刷新

**实时预览**：
- 🌐 前端：http://localhost:5173
- 🔌 后端 API：http://localhost:8000/docs
- 📊 数据库管理：http://localhost:5050 (可选)

### 第三步：提交代码（1 分钟）

```bash
cd env
./check-running.sh  # 自动检查和修复

cd ..
git add -A
git commit -m "feat: 你的功能"
git push origin main
```

**就这么简单！** ✨

---

## 📖 常用命令

```bash
# 启动服务
cd env && ./start.sh

# 检查代码（提交前必做）
cd env && ./check-running.sh

# 停止服务
cd env && ./stop.sh

# 查看日志
docker-compose -f env/docker-compose.yml logs -f backend
docker-compose -f env/docker-compose.yml logs -f frontend
```

---

## 🛠️ 进阶操作

### 查看日志

```bash
cd env
docker-compose logs -f backend  # 后端日志
docker-compose logs -f frontend # 前端日志
docker-compose logs -f postgres # 数据库日志
```

### 进入容器

```bash
# 后端容器（调试）
docker exec -it project-alpha-backend bash
source .venv/bin/activate
pytest -v

# 前端容器
docker exec -it project-alpha-frontend sh
npm run lint

# 数据库容器
docker exec -it project-alpha-db psql -U ticketuser -d ticketdb
```

### 重启服务

```bash
cd env
docker-compose restart backend
docker-compose restart frontend

# 重建并重启
docker-compose up -d --build backend
```

---

## 🐛 遇到问题？

### 服务无法启动

```bash
cd env
docker-compose logs backend  # 查看错误日志
docker-compose down && docker-compose up -d --build  # 重建
```

### 端口被占用

修改 `env/docker-compose.yml` 中的端口：
```yaml
ports:
  - "8001:8000"  # 改为其他端口
```

### 依赖安装失败

```bash
cd env
docker-compose down -v  # 清理 volume
docker-compose up -d --build  # 重建
```

### 更多问题

查看 [0009-troubleshooting.md](./0009-troubleshooting.md)

---

## 🎯 开发提示

### DO（应该做）✅

- ✅ 提交前运行 `cd env && ./check-running.sh`
- ✅ 在 Docker 容器内测试（环境一致）
- ✅ 查看日志排查问题
- ✅ 定期 `git pull` 同步代码

### DON'T（不要做）❌

- ❌ 在宿主机安装 Node/Python（使用 Docker）
- ❌ 手动调整格式化输出（让工具处理）
- ❌ 跳过代码检查直接提交（会导致 CI 失败）
- ❌ 忽略 TypeScript 错误

---

## 📚 学习资源

### 必读文档

1. [Docker 开发环境](./0010-docker-development.md) - 完整指南
2. [代码质量规范](./0011-code-quality.md) - 代码规范
3. [快速参考](../env/快速参考.md) - 常用命令

### 技术文档

- [数据库设计](./0012-database-design.md) - 后端开发
- [前端架构](./0013-frontend-architecture.md) - 前端开发
- [经验教训](./0014-lessons-learned.md) - 最佳实践

### 完整索引

查看 [specs/README.md](./README.md)

---

## 🎉 开始享受开发吧！

有问题随时查看文档，或提交 Issue。

**Happy Coding!** 🚀

---

## 🛠️ 备选方式：本地开发（不推荐）

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
