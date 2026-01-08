# AI 编程项目

这是一个包含多个独立项目的 monorepo，每个项目按周组织。

## 项目结构

```
Projects/
├── .github/                    # GitHub Actions 工作流
│   └── workflows/
│       ├── ci.yml              # CI 检查（自动检测变更的项目）
│       ├── docker-build.yml    # Docker 镜像构建
│       └── pre-commit.yml      # Pre-commit 检查
├── .pre-commit-config.yaml     # Pre-commit 配置
├── Week1/                      # Week1 项目（Ticket 管理系统）
│   ├── backend/                # FastAPI 后端
│   ├── frontend/               # React 前端
│   ├── env/                    # Docker 环境配置
│   ├── specs/                  # 需求文档
│   └── README.md
├── Week2/                      # Week2 项目（待开发）
│   └── README.md
└── README.md                   # 本文件
```

## 项目列表

| 项目 | 状态 | 描述 |
|------|------|------|
| [Week1](./Week1) | ✅ 开发中 (93%) | Ticket 管理系统 - Project Alpha |
| [Week2](./Week2) | 📋 计划中 | 待定 |

## 快速开始

### Week1 项目

```bash
# 进入项目目录
cd Week1/env

# 启动 Docker 环境
./start.sh

# 访问
# - 前端: http://localhost:5173
# - 后端 API: http://localhost:8000/docs
```

### 代码质量检查

```bash
# 安装 pre-commit
pip install pre-commit

# 安装 git hooks
pre-commit install

# 手动运行所有检查
pre-commit run --all-files
```

## CI/CD

- **CI 检查**: 自动在 PR 和 push 时运行代码质量检查和测试
- **Docker 构建**: 可通过 tag 或手动触发构建 Docker 镜像
- **Pre-commit**: PR 时自动运行 pre-commit 检查

## 开发指南

1. 每个项目独立管理自己的依赖和配置
2. 共享的 GitHub Actions 配置在根目录 `.github/`
3. 使用路径过滤器确保只有相关项目的变更才会触发 CI
