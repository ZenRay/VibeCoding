# VibeCoding - AI 编程学习项目集

这是一个包含多个独立项目的 monorepo，每个项目按周组织，展示不同技术栈和应用场景。

## 项目结构

```
VibeCoding/
├── .github/                    # GitHub Actions 工作流
│   └── workflows/
│       ├── ci.yml              # CI 检查（自动检测变更的项目）
│       └── pre-commit.yml      # Pre-commit 检查
│
├── Week1/                      # Week1: Ticket 管理系统
│   ├── backend/                # FastAPI 后端
│   ├── frontend/               # React 前端
│   ├── env/                    # Docker 环境配置
│   └── README.md
│
├── Week2/                      # Week2: 数据库查询工具
│   ├── backend/                # FastAPI + SQLAlchemy
│   ├── frontend/               # React + Vite
│   └── README.md
│
├── Week3/                      # Week3: ScribeFlow 语音听写系统 🔥
│   ├── .specify/               # 项目工具和模板
│   │   ├── memory/constitution.md
│   │   ├── scripts/
│   │   └── templates/
│   ├── docs/                   # 项目文档
│   ├── instructions/           # 技术参考资料
│   ├── src-tauri/              # Rust 后端 (Tauri)
│   ├── src/                    # React 前端
│   ├── CLAUDE.md               # Week3 本地 Agent 配置
│   ├── PROJECT_STRUCTURE.md    # 详细路径指南
│   └── README.md
│
├── specs/                      # 所有功能的规范文档
│   ├── 001-scribeflow-voice-system/  # Week3 功能规范
│   │   ├── spec.md
│   │   ├── design.md
│   │   ├── plan.md
│   │   ├── research.md
│   │   ├── data-model.md
│   │   ├── quickstart.md
│   │   └── contracts/
│   ├── 002-mysql-support/
│   └── 003-export-query-results/
│
├── archive/                    # 归档文件
│
├── CLAUDE.md                   # 仓库级 Agent 配置
└── README.md                   # 本文件
```

## 项目列表

| 项目 | 技术栈 | 状态 | 描述 |
|------|--------|------|------|
| **[Week1](./Week1)** | FastAPI + React + Docker | ✅ 完成 | Ticket 管理系统 - Project Alpha |
| **[Week2](./Week2)** | FastAPI + React + MySQL | ✅ 完成 | 数据库查询工具 (支持 MySQL + 导出功能) |
| **[Week3](./Week3)** | Rust + Tauri v2 + React | ✅ 完成 | ScribeFlow 桌面实时语音听写系统 |
| **[Week5](./Week5)** | Python + FastMCP + PostgreSQL | ✅ 完成 | PostgreSQL MCP Server - 自然语言查询数据库 |

## 快速开始

### Week5 - PostgreSQL MCP Server (最新) 🔥

**自然语言到 SQL 查询服务器** - 通过 Model Context Protocol (MCP) 使用中英文自然语言查询 PostgreSQL 数据库。

```bash
cd Week5

# 安装
python -m venv .venv
source .venv/bin/activate
pip install -e .

# 配置
cp config/config.example.yaml config/config.yaml
# 编辑 config.yaml 填入数据库和 API 配置

# 运行
python -m postgres_mcp

# 测试
pytest tests/unit/ -v              # 单元测试 (141个)
cd tests/contract && ./run_contract_tests.sh sample  # 快速验证 (3个用例)
```

**核心特性**:
- 🗣️ 自然语言 → SQL (OpenAI GPT-4o-mini 或 阿里百炼)
- 🔒 安全优先 (AST 验证, 只读操作, UNION 支持)
- 📊 智能 schema 缓存
- 🧪 契约测试 (70个 NL-to-SQL 准确性测试)
- 📜 查询历史记录

**文档**: 见 [Week5/README.md](./Week5/README.md) 和 [specs/001-postgres-mcp/](./specs/001-postgres-mcp/)

---
### Week3 - ScribeFlow (已完成)

```bash
# 进入项目目录
cd Week3

# 查看详细文档
cat PROJECT_STRUCTURE.md
cat ../specs/001-scribeflow-voice-system/quickstart.md

# 安装依赖 (按平台)
# macOS: 按照 quickstart.md 安装 Xcode Tools, Rust, Node.js
# Linux: 按照 quickstart.md 安装系统依赖、Rust、Node.js

# 安装项目依赖
npm install
cargo build --manifest-path src-tauri/Cargo.toml

# 开发
npm run tauri dev

# 测试
cargo test --manifest-path src-tauri/Cargo.toml
```

**详细文档**: 见 [Week3 QuickStart](./specs/001-scribeflow-voice-system/quickstart.md)

---

### Week2 - 数据库查询工具

```bash
cd Week2

# 启动开发服务器
npm run dev

# 后端: http://localhost:8000
# 前端: http://localhost:5173
```

---

### Week1 - Ticket 管理系统

```bash
# 进入项目目录
cd Week1/env

# 启动 Docker 环境
./start.sh

# 访问
# - 前端: http://localhost:5173
# - 后端 API: http://localhost:8000/docs
```

---

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

## Week3 - ScribeFlow 详细信息

### 项目概述

ScribeFlow 是一个类似 [Wispr Flow](https://www.wsprlabs.com/) 的桌面级实时语音听写工具,通过全局热键唤醒,实现"说话即上屏"的流畅体验。

**核心特性**:
- 🎤 实时语音转文本 (端到端延迟 <200ms)
- ⌨️ 全局热键触发 (Cmd+Shift+\ on macOS, Ctrl+Shift+\ on Linux)
- 🪟 透明悬浮窗实时反馈
- 🔒 隐私优先 (音频即用即弃,API 密钥加密存储)
- 💻 跨平台支持 (macOS, Linux X11, Linux Wayland)
- 📦 极低资源占用 (<100MB 内存)

### 技术架构

**后端 (Rust)**:
- Tauri v2 桌面应用框架
- cpal 实时音频采集 (<10ms 延迟)
- rubato 高质量重采样 (48kHz → 16kHz)
- tokio-tungstenite 异步 WebSocket
- ElevenLabs Scribe v2 Realtime API

**前端 (React)**:
- 悬浮窗实时转写显示
- 音量波形可视化
- 设置面板 (API 配置、快捷键)

### 开发状态

| 阶段 | 状态 | 交付物 |
|------|------|--------|
| Phase 0: Research | ✅ Complete | research.md (6 个技术决策) |
| Phase 1: Design & Contracts | ✅ Complete | data-model.md, contracts/, quickstart.md |
| Phase 2: Core Implementation | ✅ Complete | 音频采集、WebSocket、文本注入 |
| Phase 3: UI & Configuration | ✅ Complete | 悬浮窗、托盘、设置面板 |
| Phase 4: Polish | ✅ Complete | 错误处理、性能优化、文档 |

**状态**: v0.1.0 已完成，可发布

### 关键文档

完整的规范和设计文档位于 `specs/001-scribeflow-voice-system/`:

- 📋 [spec.md](./specs/001-scribeflow-voice-system/spec.md) - 功能规范 (25 个需求)
- 🏗️ [design.md](./specs/001-scribeflow-voice-system/design.md) - 详细设计 (22 个图表)
- 📅 [plan.md](./specs/001-scribeflow-voice-system/plan.md) - 实施计划 (4 个阶段)
- 🔬 [research.md](./specs/001-scribeflow-voice-system/research.md) - 技术调研
- 🗃️ [data-model.md](./specs/001-scribeflow-voice-system/data-model.md) - 数据模型 (7 个实体)
- 🚀 [quickstart.md](./specs/001-scribeflow-voice-system/quickstart.md) - 快速开始

---

## 开发指南

### 通用原则

1. 每个项目独立管理自己的依赖和配置
2. 共享的 GitHub Actions 配置在根目录 `.github/`
3. 使用路径过滤器确保只有相关项目的变更才会触发 CI
4. 每个 Week 目录包含独立的 CLAUDE.md 提供项目特定指导

### Week3 特殊说明

- **文档和代码分离**: 代码在 `Week3/`, 规范在 `specs/001-scribeflow-voice-system/`
- **项目工具**: `.specify/` 目录包含 speckit 工具和模板
- **Constitution**: `.specify/memory/constitution.md` 定义项目治理原则
- **详细路径**: 见 `Week3/PROJECT_STRUCTURE.md`

---

## Platform Support (Week3)

| Platform | Support Level | Features | Recommendation |
|----------|---------------|----------|----------------|
| **macOS 10.15+** | ✅ Tier 1 | 100% | ⭐⭐⭐⭐⭐ |
| **Linux X11** | ✅ Tier 1 | 100% | ⭐⭐⭐⭐⭐ |
| **Linux Wayland** | ⚠️ Tier 2 | 75% (降级) | ⭐⭐⭐ |
| **Windows 11** | ⚠️ Tier 3 | 未验证 | Not tested |

**Linux 用户**: 推荐使用 X11 会话以获得完整功能。Wayland 模式下部分功能降级 (键盘模拟 → 剪贴板注入)。
