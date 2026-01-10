# 数据库查询工具 - 快速开始指南

**日期**: 2026-01-11  
**版本**: v1.0 (包含 P0/P1 安全增强)  
**状态**: ✅ 生产就绪

---

## 📖 概述

这是一个支持多数据库（PostgreSQL、MySQL、SQLite）的查询工具，具有以下特性：

- ✅ **多层安全防护**: 5 层 SQL 注入防护
- ✅ **AI 智能查询**: 自然语言转 SQL (OpenAI GPT-4)
- ✅ **智能查询限制**: 聚合查询自动豁免 LIMIT
- ✅ **并发安全**: 元数据刷新与查询执行互斥
- ✅ **元数据缓存**: 本地 SQLite 存储，自动版本检测
- ✅ **现代化界面**: React + Ant Design + Monaco Editor

---

## 🚀 快速启动 (5 分钟)

### 前置要求

| 软件 | 最低版本 | 用途 |
|------|---------|------|
| Docker | 24.0+ | 容器化运行 |
| Docker Compose | 2.20+ | 服务编排 |
| Make | 任意版本 | 构建工具 (可选) |

### 步骤 1: 克隆项目

```bash
cd Week2
```

### 步骤 2: 环境配置

```bash
# 复制环境变量模板
cp env/.env.example env/.env

# 编辑 .env 文件，设置 OpenAI API Key (自然语言查询功能需要)
nano env/.env
```

**最小配置** (env/.env):
```bash
# OpenAI API 配置 (可选 - 不设置则禁用 AI 功能)
OPENAI_API_KEY=sk-your-api-key-here

# 其他配置已预设默认值
```

### 步骤 3: 启动服务

```bash
# 使用 Makefile (推荐)
make start

# 或使用 Docker Compose
cd env && docker compose up -d
```

### 步骤 4: 验证服务

访问以下地址确认服务启动：

| 服务 | 地址 | 说明 |
|------|------|------|
| **前端应用** | http://localhost:5173 | React 用户界面 |
| **后端 API** | http://localhost:8000 | FastAPI 服务 |
| **API 文档** | http://localhost:8000/docs | Swagger UI |
| **健康检查** | http://localhost:8000/health | 返回 `{"status": "ok"}` |

### 步骤 5: 测试数据库连接

系统已自动启动测试数据库：

| 数据库 | 连接字符串 | 说明 |
|--------|-----------|------|
| PostgreSQL | `postgresql://testuser:testpass@localhost:5433/testdb` | 端口 5433 |
| MySQL | `mysql://testuser:testpass@localhost:3307/testdb` | 端口 3307 |
| SQLite | `sqlite:///data/test.db` | 本地文件 |

**在前端界面添加连接**:
1. 打开 http://localhost:5173
2. 点击 "添加数据库连接"
3. 填写连接名称和 URL
4. 点击 "保存" 并 "刷新元数据"

---

## 📚 核心功能使用

### 1. 添加数据库连接

#### 方式 1: 前端界面 (推荐)

1. 访问 http://localhost:5173
2. 点击 "添加数据库连接"
3. 填写信息：
   - **连接名称**: `my-postgres` (唯一标识)
   - **数据库 URL**: `postgresql://testuser:testpass@localhost:5433/testdb`
4. 保存并刷新元数据

#### 方式 2: API 调用

```bash
# 添加 PostgreSQL 连接
curl -X PUT http://localhost:8000/api/v1/dbs/my-postgres \
  -H "Content-Type: application/json" \
  -d '{
    "url": "postgresql://testuser:testpass@localhost:5433/testdb"
  }'

# 添加 MySQL 连接
curl -X PUT http://localhost:8000/api/v1/dbs/my-mysql \
  -H "Content-Type: application/json" \
  -d '{
    "url": "mysql://testuser:testpass@localhost:3307/testdb"
  }'
```

### 2. 查看数据库元数据

```bash
# 获取缓存的元数据
curl http://localhost:8000/api/v1/dbs/my-postgres

# 强制刷新元数据 (会触发并发互斥锁)
curl "http://localhost:8000/api/v1/dbs/my-postgres?refresh=true"
```

**响应示例**:
```json
{
  "name": "my-postgres",
  "dbType": "postgresql",
  "tables": [
    {
      "name": "users",
      "tableType": "table",
      "columns": [
        {"name": "id", "dataType": "integer", "isPrimaryKey": true},
        {"name": "name", "dataType": "varchar(100)"},
        {"name": "email", "dataType": "varchar(255)"}
      ],
      "rowCount": 1250
    }
  ],
  "versionHash": "a7f3b8...",
  "cachedAt": "2026-01-11T00:30:15.123Z",
  "needsRefresh": false
}
```

### 3. 执行 SQL 查询

#### 方式 1: 前端界面 (推荐)

1. 选择数据库连接
2. 在 SQL 编辑器输入查询
3. 按 `Ctrl+Enter` 或点击 "执行"
4. 查看结果表格

#### 方式 2: API 调用

```bash
# 基础查询
curl -X POST http://localhost:8000/api/v1/dbs/my-postgres/query \
  -H "Content-Type: application/json" \
  -d '{
    "sql": "SELECT * FROM users WHERE age > 18"
  }'

# 聚合查询 (自动豁免 LIMIT)
curl -X POST http://localhost:8000/api/v1/dbs/my-postgres/query \
  -H "Content-Type: application/json" \
  -d '{
    "sql": "SELECT COUNT(*) FROM users"
  }'
```

**智能 LIMIT 行为**:
```sql
-- 普通查询: 自动添加 LIMIT 1000
SELECT * FROM users
→ SELECT * FROM users LIMIT 1000

-- 聚合查询 (无 GROUP BY): 不添加 LIMIT
SELECT COUNT(*), AVG(age) FROM users
→ 保持原样 (返回单行结果)

-- 分组聚合: 添加 LIMIT
SELECT city, COUNT(*) FROM users GROUP BY city
→ SELECT city, COUNT(*) FROM users GROUP BY city LIMIT 1000

-- 超大 LIMIT: 自动限制为 10000
SELECT * FROM users LIMIT 50000
→ SELECT * FROM users LIMIT 10000
```

### 4. 自然语言查询 (AI 功能)

**前提**: 需要在 `env/.env` 中配置 `OPENAI_API_KEY`

```bash
# API 调用
curl -X POST http://localhost:8000/api/v1/dbs/my-postgres/query/natural \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "查询所有年龄大于 18 岁的用户姓名和邮箱"
  }'
```

**AI 生成的 SQL 会经过 5 层安全验证**:
1. ✅ 输出清洗 (移除注释、代码块标记)
2. ✅ 白名单验证 (仅允许 `SELECT`, `FROM`, `WHERE` 等安全关键字)
3. ✅ 禁止子查询 (拒绝嵌套 SELECT)
4. ✅ 禁止系统函数 (`VERSION()`, `SLEEP()` 等)
5. ✅ 表名验证 (检查表是否存在于元数据中)

**被拒绝的示例**:
```json
// AI 尝试生成包含子查询的 SQL
{
  "error": "AI 生成的 SQL 包含不安全模式: 不允许子查询"
}
// 审计日志已记录该事件
```

---

## 🛡️ 安全特性说明

### SQL 注入防护 (5 层防御)

系统对所有 SQL 查询执行多层验证：

```python
# 示例: 被拒绝的注入攻击
❌ "SELECT * FROM users -- WHERE role='admin'"
   → "检测到不安全的 SQL 模式: 注释"

❌ "SELECT * FROM users; DROP TABLE users"
   → "检测到不安全的 SQL 模式: 多语句"

❌ "SELECT * FROM users UNION SELECT * FROM passwords"
   → "检测到不安全的 SQL 模式: UNION"

❌ "SELECT * FROM information_schema.tables"
   → "检测到不安全的 SQL 模式: 访问系统表 information_schema"

✅ "SELECT * FROM users WHERE age > 18"
   → 通过验证，安全执行
```

### 并发控制 (互斥锁)

防止数据不一致：

```bash
# 场景 1: 查询执行中，刷新被阻止
$ curl "http://localhost:8000/api/v1/dbs/my-postgres?refresh=true"
{
  "code": "CONFLICT",
  "message": "查询执行中,无法刷新元数据"
}

# 场景 2: 刷新中，查询被阻止
$ curl -X POST http://localhost:8000/api/v1/dbs/my-postgres/query ...
{
  "code": "CONFLICT",
  "message": "元数据刷新中,请稍候..."
}
```

---

## 🔧 本地开发

### 后端开发

```bash
# 进入后端目录
cd backend

# 安装依赖 (使用 uv - 更快的包管理器)
make install-backend
# 或
uv sync

# 激活虚拟环境
source .venv/bin/activate

# 启动开发服务器 (热重载)
make start-backend
# 或
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 运行测试 (21 个测试用例)
make test-backend
# 或
pytest -v

# 代码格式化
make format-backend
# 或
black app tests && ruff check --fix app tests

# 类型检查
make lint-backend
# 或
mypy app
```

### 前端开发

```bash
# 进入前端目录
cd frontend

# 安装依赖
make install-frontend
# 或
npm install

# 启动开发服务器
make start-frontend
# 或
npm run dev

# 运行测试
make test-frontend
# 或
npm run test

# 代码格式化
make format-frontend
# 或
npm run lint:fix
```

### Makefile 快捷命令

```bash
make help              # 显示所有可用命令
make install           # 安装所有依赖
make start             # 启动所有服务 (Docker)
make stop              # 停止所有服务
make test              # 运行所有测试
make format            # 格式化所有代码
make clean             # 清理临时文件
make migrate-upgrade   # 运行数据库迁移
```

完整命令列表见 [MAKEFILE_USAGE.md](./MAKEFILE_USAGE.md)

---

## 📂 项目结构

```
Week2/
├── backend/                     # FastAPI 后端
│   ├── app/
│   │   ├── main.py             # 应用入口
│   │   ├── config.py           # 配置管理
│   │   ├── api/v1/             # API 路由
│   │   │   ├── dbs.py          # 数据库连接管理
│   │   │   └── query.py        # 查询执行 API
│   │   ├── models/             # Pydantic 模型
│   │   │   ├── database.py     # 数据库连接模型
│   │   │   ├── metadata.py     # 元数据模型
│   │   │   └── query.py        # 查询模型
│   │   ├── services/           # 业务逻辑
│   │   │   ├── ai_service.py   # AI SQL 生成 (含 5 层验证)
│   │   │   ├── db_service.py   # 数据库适配器管理
│   │   │   ├── metadata_service.py  # 元数据提取 (含互斥锁)
│   │   │   └── query_service.py     # 查询执行 (含互斥锁)
│   │   ├── db/                 # 数据库适配器
│   │   │   ├── base.py         # 基类
│   │   │   ├── postgres.py     # PostgreSQL 适配器
│   │   │   ├── mysql.py        # MySQL 适配器
│   │   │   └── sqlite.py       # SQLite 适配器
│   │   ├── storage/            # 本地存储
│   │   │   ├── models.py       # SQLAlchemy 模型 (UTC 时间)
│   │   │   └── local_db.py     # 存储操作层
│   │   └── utils/              # 工具函数
│   │       ├── error_handler.py # 错误处理
│   │       ├── locks.py        # 并发互斥锁 (新增)
│   │       └── sql_validator.py # SQL 验证 (5 层防护 + 智能限制)
│   ├── tests/                  # 测试套件
│   │   ├── test_api/           # API 测试
│   │   ├── test_services/      # 服务层测试
│   │   └── test_utils/         # 工具测试 (21 个用例)
│   ├── alembic/                # 数据库迁移
│   ├── pyproject.toml          # Python 项目配置
│   └── py.typed                # 类型标记
│
├── frontend/                    # React + TypeScript 前端
│   ├── src/
│   │   ├── App.tsx             # 应用入口
│   │   ├── components/         # React 组件
│   │   │   ├── DatabaseForm.tsx      # 数据库连接表单
│   │   │   ├── DatabaseList.tsx      # 连接列表
│   │   │   ├── DatabaseSelector.tsx  # 连接选择器
│   │   │   ├── SqlEditor.tsx         # Monaco SQL 编辑器
│   │   │   ├── QueryResult.tsx       # 查询结果表格
│   │   │   ├── NaturalLanguageInput.tsx  # AI 查询输入
│   │   │   ├── MetadataTree.tsx      # 元数据树形展示
│   │   │   └── QueryHistory.tsx      # 查询历史
│   │   ├── pages/              # 页面组件
│   │   │   ├── HomePage.tsx    # 主页
│   │   │   └── DatabasePage.tsx # 数据库查询页
│   │   ├── services/           # API 服务
│   │   │   ├── api.ts          # axios 实例
│   │   │   ├── databaseService.ts  # 数据库 API
│   │   │   └── queryService.ts     # 查询 API
│   │   ├── types/              # TypeScript 类型
│   │   └── hooks/              # 自定义 Hooks
│   ├── package.json
│   └── vite.config.ts
│
├── env/                         # Docker 环境配置
│   ├── docker-compose.yml      # 服务编排
│   ├── .env.example            # 环境变量模板
│   ├── Dockerfile.backend      # 后端镜像
│   ├── Dockerfile.frontend     # 前端镜像
│   └── init-scripts/           # 数据库初始化脚本
│       ├── postgres-init.sql
│       └── mysql-init.sql
│
├── data/                        # 运行时数据目录
│   └── meta.db                 # SQLite 元数据存储 (自动创建)
│
├── Makefile                    # 构建工具
├── README.md                   # 项目说明
├── TEST_REPORT.md              # P0/P1 测试报告
└── NEXT_STEPS.md               # 开发指南
```

---

## 🧪 测试

### 运行所有测试

```bash
# 使用 Makefile
make test

# 或分别运行
make test-backend
make test-frontend
```

### 后端测试详情

```bash
cd backend

# 运行所有测试 (21 个用例)
pytest -v

# 运行特定测试文件
pytest tests/test_utils/test_sql_validator.py -v

# 生成覆盖率报告
pytest --cov=app --cov-report=html
```

**测试覆盖**:
- ✅ SQL 注入防护: 9/9 测试通过
- ✅ 智能查询限制: 5/5 测试通过
- ✅ 基础验证: 7/7 测试通过
- 总覆盖率: 65.12% (核心模块)

详细报告见 [TEST_REPORT.md](./TEST_REPORT.md)

---

## 🐛 故障排查

### 问题 1: 后端启动失败 - 数据库连接错误

**症状**:
```
sqlalchemy.exc.OperationalError: could not connect to server
```

**解决方案**:
```bash
# 检查测试数据库是否启动
docker compose ps

# 如果未启动，启动测试数据库
cd env && docker compose up -d postgres mysql

# 查看日志
docker compose logs postgres
```

### 问题 2: AI 查询返回 "AI 服务不可用"

**症状**:
```json
{
  "code": "AI_SERVICE_UNAVAILABLE",
  "message": "AI 服务未配置，请设置 OPENAI_API_KEY 环境变量"
}
```

**解决方案**:
```bash
# 检查环境变量
cat env/.env | grep OPENAI_API_KEY

# 如果未设置，编辑 .env 文件
nano env/.env
# 添加: OPENAI_API_KEY=sk-your-api-key-here

# 重启后端服务
make restart
```

### 问题 3: 前端无法连接后端 API

**症状**: 前端显示 "Network Error" 或 CORS 错误

**解决方案**:
```bash
# 1. 检查后端服务状态
curl http://localhost:8000/health

# 2. 检查 CORS 配置 (backend/app/main.py)
# 应包含: allow_origins=["http://localhost:5173"]

# 3. 重启服务
make restart
```

### 问题 4: 查询返回 409 CONFLICT

**症状**:
```json
{
  "code": "CONFLICT",
  "message": "元数据刷新中,请稍候..."
}
```

**说明**: 这是正常的并发控制行为，表示元数据正在刷新，请稍后重试。

**解决方案**: 等待 2-3 秒后重试，或在前端界面等待刷新完成。

### 问题 5: Docker 容器启动很慢

**原因**: 首次启动需要下载镜像

**解决方案**:
```bash
# 预先拉取镜像
docker compose pull

# 查看下载进度
docker compose pull --progress=plain
```

---

## 📊 性能优化建议

### 1. 元数据缓存

元数据默认缓存在本地 SQLite (`data/meta.db`)，无需频繁刷新。

**推荐频率**:
- 数据库结构变更后: 立即刷新
- 日常使用: 每天刷新 1 次
- 仅查看数据: 无需刷新

### 2. 查询限制

系统默认添加 `LIMIT 1000`，防止大表查询耗尽资源。

**优化建议**:
```sql
-- ❌ 避免全表扫描
SELECT * FROM large_table

-- ✅ 使用索引列过滤
SELECT * FROM large_table WHERE id > 1000 AND id < 2000

-- ✅ 使用聚合代替明细
SELECT COUNT(*), AVG(amount) FROM large_table
```

### 3. 并发控制

避免同时刷新多个数据库的元数据，顺序操作以提高响应速度。

---

## 🔐 安全最佳实践

### 1. 数据库连接 URL 安全

- ❌ 不要在前端代码中硬编码密码
- ✅ 使用环境变量或配置文件
- ✅ 生产环境使用 Secret 管理工具

### 2. OpenAI API Key 保护

- ❌ 不要提交 `.env` 文件到 Git
- ✅ 使用 `.env.example` 作为模板
- ✅ 定期轮换 API Key

### 3. SQL 注入防护

系统已内置 5 层防护，但仍需注意：
- ✅ 使用参数化查询 (系统自动处理)
- ✅ 避免拼接用户输入到 SQL
- ✅ 定期查看审计日志 (AI 拒绝记录)

---

## 📝 下一步

### 基础使用
1. ✅ 添加数据库连接
2. ✅ 刷新元数据
3. ✅ 执行 SQL 查询
4. ✅ 尝试 AI 自然语言查询

### 进阶功能
5. 查看 [API 文档](http://localhost:8000/docs) 了解完整接口
6. 阅读 [TEST_REPORT.md](./TEST_REPORT.md) 了解安全特性
7. 查看 [NEXT_STEPS.md](./NEXT_STEPS.md) 了解开发指南

### 开发贡献
8. Fork 项目并创建功能分支
9. 运行 `make test` 确保测试通过
10. 提交 Pull Request

---

## 📞 支持和反馈

- **文档**: 查看 `Week2/README.md` 和 `specs/001-db-query-tool/`
- **问题**: 提交 GitHub Issue
- **测试报告**: [TEST_REPORT.md](./TEST_REPORT.md)

---

**快速开始指南完成** ✅  
**版本**: v1.0 (包含 P0/P1 安全增强)  
**最后更新**: 2026-01-11
