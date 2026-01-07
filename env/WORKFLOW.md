# Docker 工作流程 - 完全避免环境问题

## 为什么使用 Docker？

✅ **环境一致性 100%** - 本地、CI、生产环境完全相同  
✅ **无需安装工具** - 不需要本地 Node/Python 版本匹配  
✅ **自动修复问题** - 格式化、代码质量自动修复  
✅ **隔离依赖** - 不污染本地环境

## 🚀 完整工作流程

### 1. 启动开发环境

```bash
cd env
./start.sh

# 或使用 docker-compose
docker-compose up -d
```

访问：
- 前端: http://localhost:5173
- 后端 API: http://localhost:8000/docs
- 数据库管理: http://localhost:5050 (可选)

---

### 2. 修改代码（在本地编辑器）

Docker 使用 volume 挂载，修改会实时同步：
- `backend/` → 后端容器
- `frontend/` → 前端容器

支持**热重载**，无需重启容器。

---

### 3. 提交前检查（关键！）

#### 方案 A：使用专用检查脚本（推荐）⭐⭐⭐⭐⭐

```bash
# 在 Docker 中运行所有检查
./scripts/docker-check.sh
```

**优势：**
- 使用与 CI 完全相同的环境（Python 3.12 + Node 20）
- 自动修复格式问题
- 一键执行所有检查

#### 方案 B：在运行中的容器内检查 ⭐⭐⭐⭐

```bash
# 适用于已启动 docker-compose 的情况
./scripts/docker-exec-check.sh
```

**优势：**
- 复用已运行的容器
- 更快（不需要启动新容器）
- 可以实时查看日志

#### 方案 C：单独运行某个检查

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
  "npm run lint && npm run type-check"
```

---

### 4. 提交和推送

```bash
# 检查通过后提交
git add -A
git commit -m "feat: 你的功能描述"
git push origin main
```

---

## 📦 Docker 服务管理

### 启动服务

```bash
cd env

# 启动所有服务
./start.sh

# 或指定服务
docker-compose up -d backend frontend postgres

# 启动包含 PgAdmin
docker-compose --profile tools up -d
```

### 查看日志

```bash
# 查看所有服务日志
docker-compose logs -f

# 查看特定服务
docker-compose logs -f backend
docker-compose logs -f frontend
```

### 停止服务

```bash
cd env
./stop.sh

# 或
docker-compose down

# 清理所有数据（谨慎！）
docker-compose down -v
```

---

## 🔧 常用 Docker 命令

### 进入容器调试

```bash
# 进入后端容器
docker exec -it project-alpha-backend bash

# 进入前端容器
docker exec -it project-alpha-frontend sh

# 在容器内：
source .venv/bin/activate  # 后端
pytest -v                   # 运行测试
black .                     # 格式化
npm run lint               # 前端检查
```

### 重启服务

```bash
# 重启单个服务
docker-compose restart backend
docker-compose restart frontend

# 重建并重启（代码改动后）
docker-compose up -d --build backend
```

### 查看容器状态

```bash
docker-compose ps
docker stats  # 资源使用情况
```

---

## 🎯 完整示例：修改代码并提交

```bash
# 1. 启动环境
cd env && ./start.sh && cd ..

# 2. 修改代码（在本地编辑器）
# 编辑 backend/app/... 或 frontend/src/...

# 3. 实时查看效果
# 前端: http://localhost:5173 （自动刷新）
# 后端: http://localhost:8000/docs （自动重载）

# 4. 提交前检查
./scripts/docker-exec-check.sh

# 5. 如有问题，脚本会自动修复
# 重新运行检查确认
./scripts/docker-exec-check.sh

# 6. 提交
git add -A
git commit -m "feat: 新功能"
git push origin main

# 7. 停止服务（可选）
cd env && ./stop.sh
```

---

## 📊 对比：三种检查方式

| 方式 | 本地检查 | Docker 检查 | Docker Exec 检查 |
|------|---------|------------|-----------------|
| **命令** | `./scripts/check-local.sh` | `./scripts/docker-check.sh` | `./scripts/docker-exec-check.sh` |
| **Node 版本要求** | 需要 14+ | 无要求 | 无要求 |
| **Python 版本要求** | 需要 3.12 | 无要求 | 无要求 |
| **执行速度** | 快（已安装依赖） | 慢（需拉取镜像） | 快（复用容器） |
| **环境一致性** | 取决于本地 | 100% | 100% |
| **适用场景** | 本地环境正确 | 本地环境不匹配 | 容器已运行 |

**推荐：**
- 日常开发：`docker-exec-check.sh`（容器已启动）
- 独立检查：`docker-check.sh`（不依赖运行中容器）
- 快速检查：`check-local.sh`（本地环境匹配时）

---

## 🎉 总结

使用 Docker 工作流可以：
1. **彻底避免环境不一致问题**（本次所有问题的根源）
2. **提交前自动检查和修复**（避免 CI 反复失败）
3. **与 CI 环境 100% 一致**（本地通过 = CI 通过）
4. **支持团队协作**（所有人环境相同）

**下次提交只需运行：**
```bash
./scripts/docker-exec-check.sh && git add -A && git commit -m "你的消息" && git push
```

就这么简单！🚀
