# 数据库查询工具

一个支持多种数据库（PostgreSQL、MySQL、SQLite）的查询工具，提供元数据浏览、SQL 查询和自然语言生成 SQL 功能。

## 功能特性

- ✅ **数据库连接管理**: 添加、查看、编辑、删除数据库连接
- ✅ **元数据浏览**: 自动提取并展示数据库的表、视图、列信息
- ✅ **SQL 查询**: 支持手动输入 SQL 查询并查看结果
- ✅ **自然语言生成 SQL**: 使用 AI 将自然语言转换为 SQL 查询
- ✅ **查询历史**: 保存当前会话的查询历史

## 技术栈

### 后端
- Python 3.12+
- FastAPI
- SQLAlchemy
- sqlglot (SQL 解析)
- OpenAI SDK (AI SQL 生成)
- asyncpg / aiomysql / aiosqlite

### 前端
- React 18+
- TypeScript
- Refine 5
- Ant Design 5
- Monaco Editor
- Tailwind CSS

## 📚 文档导航

| 文档 | 说明 |
|------|------|
| **[QUICK_START.md](./QUICK_START.md)** | ⭐ **完整快速开始指南** - 包含详细的安装、配置、使用说明 |
| [MAKEFILE_USAGE.md](./MAKEFILE_USAGE.md) | Makefile 命令详细说明 |
| [DOCKER_SETUP.md](./DOCKER_SETUP.md) | Docker 数据库配置指南 |
| [TEST_EXECUTION_REPORT.md](./TEST_EXECUTION_REPORT.md) | 最新测试执行报告 |
| [test_api.py](./test_api.py) | API 测试脚本 |

## 快速开始

### 5 分钟启动 🚀

```bash
# 1. 进入项目目录
cd Week2

# 2. 启动所有服务（数据库 + 后端 + 前端）
make start
```

访问：
- **前端应用**: http://localhost:3000
- **后端 API**: http://localhost:8000
- **API 文档**: http://localhost:8000/docs

> 💡 **详细说明**：查看 [QUICK_START.md](./QUICK_START.md) 了解完整的安装、配置和使用指南

### 环境要求

- Docker 24.0+
- Docker Compose 2.20+
- Make (可选，用于快捷命令)

### 常用 Makefile 命令

```bash
make help       # 查看所有可用命令
make start      # 启动所有服务
make stop       # 停止所有服务
make status     # 查看服务状态
make test       # 运行测试
```

> 📖 更多命令请参考 [MAKEFILE_USAGE.md](./MAKEFILE_USAGE.md)

## 核心特性

### 🔒 安全性
- **5 层 SQL 注入防护**: 注释检测、多语句阻止、危险关键字过滤、系统表限制、语法验证
- **AI SQL 安全验证**: 输出清洗、白名单验证、子查询禁止、系统函数限制
- **并发控制**: 元数据刷新与查询执行互斥锁

### 🎯 智能功能
- **智能查询限制**: 自动添加 LIMIT，聚合查询自动豁免
- **元数据缓存**: 本地 SQLite 存储，自动版本检测
- **自然语言转 SQL**: 使用 OpenAI GPT-4 生成 SQL（可选）

### 📊 测试数据库

Docker Compose 会自动启动测试数据库：

| 数据库 | 连接字符串 | 端口 |
|--------|-----------|------|
| PostgreSQL | `postgresql://postgres:postgres@localhost:5432/testdb` | 5432 |
| MySQL | `mysql://testuser:testpass@localhost:3306/testdb` | 3306 |

> 📖 详细配置请参考 [DOCKER_SETUP.md](./DOCKER_SETUP.md)

## API 文档

启动后端服务后，访问 http://localhost:8000/docs 查看 Swagger API 文档。

## 测试

### 运行测试

```bash
# 运行所有测试
make test

# 后端测试 (21 个单元测试)
make test-backend

# 前端 E2E 测试 (7 个测试)
make test-frontend

# API 测试脚本
python test_api.py
```

### 测试覆盖

- ✅ SQL 注入防护: 9/9 通过
- ✅ 智能查询限制: 5/5 通过  
- ✅ 前端 E2E: 7/7 通过
- ✅ API 功能: 16/16 通过

> 📊 查看 [TEST_EXECUTION_REPORT.md](./TEST_EXECUTION_REPORT.md) 了解完整测试结果

### REST API 测试

使用 VS Code REST Client 插件测试 60+ 个 API 用例：
- 打开 `fixtures/test.rest` 文件
- 点击 "Send Request" 执行测试
- 覆盖所有核心功能和安全验证

## 项目结构

```
Week2/
├── backend/          # FastAPI 后端
│   ├── app/         # 应用代码
│   ├── tests/       # 测试代码
│   └── alembic/     # 数据库迁移
├── frontend/         # React 前端
│   └── src/         # 源代码
├── fixtures/         # API 测试文件
│   ├── test.rest    # REST API 测试套件 (60+ 用例)
│   └── README.md    # 测试使用说明
├── data/            # 本地数据存储
└── env/             # Docker 配置
```

## 开发指南

### 代码质量

```bash
make format    # 格式化代码 (Black, Prettier)
make lint      # 代码检查 (Ruff, ESLint, mypy)
make check     # 完整检查 (Lint + Test)
```

### 数据库迁移

```bash
make migrate-create MESSAGE="描述"  # 创建迁移
make migrate                        # 应用迁移
make migrate-history                # 查看历史
```

> 📖 更多开发指南请参考 [MAKEFILE_USAGE.md](./MAKEFILE_USAGE.md) 和 [QUICK_START.md](./QUICK_START.md)

## 许可证

MIT
