# Project Alpha 开发环境

这个目录包含了 Project Alpha 票据管理系统的 Docker 开发环境配置。

## 目录结构

```
env/
├── docker-compose.yml              # Docker Compose 配置文件
├── Dockerfile.backend              # 后端 Dockerfile（开发环境，Python 3.12 + UV）
├── Dockerfile.frontend             # 前端 Dockerfile（开发环境）
├── init-scripts/                   # 数据库初始化脚本
│   └── 01-init.sql                # 创建表、索引、触发器和示例数据
├── backend-pyproject.toml.example  # 后端 pyproject.toml 示例（UV 配置）
├── .python-version.example         # Python 版本固定文件示例
├── env.example                     # 环境变量示例文件
└── README.md                       # 本文件
```

## 服务说明

### 1. PostgreSQL 数据库 (postgres)
- **端口**：5432
- **数据库名**：ticketdb
- **用户名**：ticketuser
- **密码**：ticketpass123
- **数据持久化**：通过 Docker volume `postgres_data`
- **健康检查**：每 10 秒检查一次数据库可用性

### 2. FastAPI 后端 (backend)
- **端口**：8000
- **Python 版本**：3.12
- **包管理器**：UV（现代化的 Python 包管理工具）
- **开发模式**：支持热重载
- **依赖服务**：postgres（等待数据库健康检查通过后启动）
- **API 文档**：
  - Swagger UI: http://localhost:8000/docs
  - ReDoc: http://localhost:8000/redoc

### 3. Vite 前端 (frontend)
- **端口**：5173
- **开发模式**：支持热模块替换（HMR）
- **依赖服务**：backend

### 4. PgAdmin (pgadmin) - 可选
- **端口**：5050
- **用途**：数据库管理界面
- **默认邮箱**：admin@example.com
- **默认密码**：admin123
- **启动方式**：需要使用 `--profile tools` 参数

## 快速开始

### 前置要求

#### 使用 Docker（推荐）
- Docker (>= 20.10)
- Docker Compose (>= 2.0)

#### 本地开发（不使用 Docker）
- **Python**：3.12 或更高版本
- **UV**：最新版本（Python 包管理器）
- **Node.js**：20.x LTS 或更高版本
- **PostgreSQL**：16 或更高版本

#### 安装 UV
```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# 验证安装
uv --version

# 添加到 PATH（如果需要）
export PATH="$HOME/.cargo/bin:$PATH"
```

### 1. 启动开发环境

#### 启动所有服务（不包括 PgAdmin）
```bash
cd env
docker-compose up -d
```

#### 启动所有服务（包括 PgAdmin）
```bash
cd env
docker-compose --profile tools up -d
```

### 2. 查看日志
```bash
# 查看所有服务日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f backend
docker-compose logs -f postgres
docker-compose logs -f frontend
```

### 3. 停止服务
```bash
# 停止所有服务
docker-compose down

# 停止并删除数据卷（注意：会删除数据库数据）
docker-compose down -v
```

### 4. 重启服务
```bash
# 重启特定服务
docker-compose restart backend

# 重启所有服务
docker-compose restart
```

## 访问地址

启动成功后，可以访问以下地址：

- **前端应用**：http://localhost:5173
- **后端 API**：http://localhost:8000
- **API 文档（Swagger）**：http://localhost:8000/docs
- **API 文档（ReDoc）**：http://localhost:8000/redoc
- **PgAdmin**：http://localhost:5050（需要使用 `--profile tools` 启动）

## 数据库连接信息

### 从主机连接数据库
```
Host: localhost
Port: 5432
Database: ticketdb
Username: ticketuser
Password: ticketpass123
```

### 从后端容器连接数据库
```
DATABASE_URL=postgresql://ticketuser:ticketpass123@postgres:5432/ticketdb
```

## PgAdmin 配置

如果启动了 PgAdmin，首次使用需要添加服务器连接：

1. 访问 http://localhost:5050
2. 使用邮箱 `admin@example.com` 和密码 `admin123` 登录
3. 右键点击"Servers" -> "Register" -> "Server"
4. 在"General"选项卡中输入名称（如"Project Alpha"）
5. 在"Connection"选项卡中输入：
   - Host: `postgres`
   - Port: `5432`
   - Database: `ticketdb`
   - Username: `ticketuser`
   - Password: `ticketpass123`
6. 保存

## 初始化数据

数据库在首次启动时会自动执行 `init-scripts/01-init.sql` 脚本，该脚本会：

1. 创建所有必要的表（tickets, tags, ticket_tags）
2. 创建索引以优化查询性能
3. 创建触发器（自动更新 updated_at 和 completed_at）
4. 插入示例标签数据（后端、前端、数据库、Bug、功能、优化）
5. 插入示例 Ticket 数据和标签关联

## 环境变量配置

1. 复制示例环境变量文件：
```bash
cp env.example .env
```

2. 根据需要修改 `.env` 文件中的配置

## 本地开发（不使用 Docker）

如果您希望在本地直接运行项目而不使用 Docker，请按照以下步骤操作：

### 1. 后端设置

```bash
# 进入后端目录
cd ../backend  # 从 env 目录返回到 Week1，然后进入 backend

# 确保使用 Python 3.12
python --version  # 应显示 Python 3.12.x

# 复制配置文件
cp ../env/backend-pyproject.toml.example pyproject.toml
cp ../env/.python-version.example .python-version

# 使用 UV 创建虚拟环境
uv venv

# 激活虚拟环境
source .venv/bin/activate  # Linux/macOS
# 或 .venv\Scripts\activate  # Windows

# 安装依赖
uv pip install -e .

# 安装开发依赖
uv pip install -e ".[dev]"

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，配置数据库连接等

# 运行数据库迁移（确保 PostgreSQL 已启动）
alembic upgrade head

# 启动开发服务器
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. 前端设置

```bash
# 进入前端目录
cd ../frontend  # 从 backend 目录进入 frontend

# 安装依赖
npm install
# 或使用 pnpm
pnpm install

# 配置环境变量
cp .env.example .env.local
# 编辑 .env.local，配置 VITE_API_URL=http://localhost:8000/api/v1

# 启动开发服务器
npm run dev
```

### 3. 数据库设置（本地）

**选项 1：使用 Docker 运行 PostgreSQL（推荐）**
```bash
docker run -d \
  --name project-alpha-db \
  -e POSTGRES_DB=ticketdb \
  -e POSTGRES_USER=ticketuser \
  -e POSTGRES_PASSWORD=ticketpass123 \
  -p 5432:5432 \
  postgres:16-alpine
```

**选项 2：使用本地安装的 PostgreSQL**
```bash
# 创建数据库
createdb -U postgres ticketdb

# 创建用户
psql -U postgres -c "CREATE USER ticketuser WITH PASSWORD 'ticketpass123';"
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE ticketdb TO ticketuser;"
```

### 4. 验证安装

```bash
# 检查后端
curl http://localhost:8000/docs

# 检查前端
curl http://localhost:5173
```

## UV 使用指南

UV 是一个现代化的 Python 包管理器，比传统的 pip 更快、更可靠。

### 基本命令

```bash
# 创建虚拟环境
uv venv

# 安装依赖（从 pyproject.toml）
uv pip install -e .

# 安装单个包
uv pip install <package-name>

# 安装开发依赖
uv pip install -e ".[dev]"

# 更新包
uv pip install --upgrade <package-name>

# 同步依赖（确保与 pyproject.toml 一致）
uv pip sync

# 导出依赖列表（兼容 pip）
uv pip freeze > requirements.txt

# 卸载包
uv pip uninstall <package-name>

# 列出已安装的包
uv pip list
```

### pyproject.toml 配置

后端项目使用 `pyproject.toml` 管理依赖和配置：

```toml
[project]
name = "project-alpha-backend"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.109.0",
    "uvicorn[standard]>=0.27.0",
    # ... 其他依赖
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "black>=23.0.0",
    # ... 开发依赖
]
```

详细配置示例请参考 `backend-pyproject.toml.example` 文件。

## 常见问题

### 1. 端口冲突
如果端口 5432、8000 或 5173 已被占用，可以修改 `docker-compose.yml` 中的端口映射：

```yaml
ports:
  - "新端口:容器内端口"
```

### 2. 数据库连接失败
- 检查 postgres 容器是否正常运行：`docker-compose ps postgres`
- 查看 postgres 日志：`docker-compose logs postgres`
- 确保健康检查通过：`docker-compose ps` 查看 postgres 的 Status 列

### 3. 前端无法连接后端
- 检查 `VITE_API_URL` 环境变量是否正确
- 确认后端服务正常运行：`curl http://localhost:8000/docs`
- 检查浏览器控制台的 CORS 错误

### 4. 热重载不工作
- 确保代码目录正确挂载到容器
- 检查文件权限
- 尝试重启服务：`docker-compose restart backend`

### 5. 清理并重新开始
```bash
# 停止所有服务并删除容器、网络、数据卷
docker-compose down -v

# 重新构建并启动
docker-compose up -d --build
```

## 生产环境部署

生产环境需要使用不同的 Dockerfile 和配置：

1. 后端使用 Gunicorn + Uvicorn workers
2. 前端构建静态文件，使用 Nginx 服务
3. 使用环境变量管理敏感信息
4. 启用 HTTPS
5. 配置日志收集和监控

详细的生产环境配置请参考主文档。

## 技术支持

如有问题，请查看：
- [需求和设计文档](../specs/0001-spec.md)
- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [Docker 文档](https://docs.docker.com/)
