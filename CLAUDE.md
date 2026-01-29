# VibeCoding Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-01-25

**Repository Root**: `~/Documents/VibeCoding`
**Current Branch**: `001-scribeflow-voice-system`

---

## Project Structure

This repository contains multiple projects organized by week:

```text
~/Documents/VibeCoding/
├── Week1/                      # Ticket 管理系统 (FastAPI + React)
├── Week2/                      # 数据库查询工具 (已完成)
├── Week3/                      # ScribeFlow 语音听写系统 (v0.1.0 完成)
│   ├── .specify/               # 项目工具和模板
│   ├── docs/                   # 项目文档
│   ├── src-tauri/              # Rust 后端
│   ├── src/                    # React 前端
│   ├── CLAUDE.md               # Week3 本地 Agent 配置
│   └── PROJECT_STRUCTURE.md    # 详细路径指南
├── Week5/                      # 🔥 PostgreSQL MCP Server (v1.0.0 生产就绪)
│   ├── src/postgres_mcp/       # Python 主包
│   ├── tests/                  # 测试套件 (141 unit + 80 contract)
│   ├── config/                 # 配置文件
│   └── README.md               # 项目文档
├── specs/                      # 所有功能的规范文档
│   ├── 001-postgres-mcp/       # Week5 功能规范 ✨ NEW
│   ├── 001-scribeflow-voice-system/  # Week3 功能规范
│   ├── 002-mysql-support/
│   └── 003-export-query-results/
└── archive/                    # 归档文件
```

---

## Active Project: Week5 - PostgreSQL MCP Server

**Project Root**: `~/Documents/VibeCoding/Week5`
**Feature Branch**: `001-postgres-mcp`
**Status**: ✅ **v1.0.0 Production Ready (97%) - 生产就绪**
**Description**: 基于 Python 3.12 和 FastMCP 的自然语言到 SQL 查询服务器

### Active Technologies

**Backend (Python 3.12)**:
- FastMCP 0.3+ (MCP 服务器框架)
- Asyncpg 0.29+ (异步 PostgreSQL 客户端)
- SQLGlot 25.29+ (SQL 解析和验证)
- Pydantic 2.10+ (数据验证)
- OpenAI SDK 1.59+ (GPT-4o-mini 或 阿里百炼)
- Structlog 24+ (结构化日志)

**Database**:
- PostgreSQL 12.0+

**AI Services**:
- OpenAI GPT-4o-mini (默认)
- 阿里百炼通义千问 (国内推荐)

### Key Documents

- **🔥 Current Status**: `specs/001-postgres-mcp/CURRENT_STATUS.md` ← **Start here!**
- **Specification**: `specs/001-postgres-mcp/spec.md`
- **Implementation Plan**: `specs/001-postgres-mcp/plan.md`
- **Tasks**: `specs/001-postgres-mcp/tasks.md`
- **Research**: `specs/001-postgres-mcp/research.md`
- **Data Model**: `specs/001-postgres-mcp/data-model.md`
- **QuickStart**: `specs/001-postgres-mcp/quickstart.md`
- **README**: `Week5/README.md`

### Project-Specific Guidelines

详见 `Week5/CLAUDE.md` 获取 Week5 项目的详细开发指南。

---

## Previous Project: Week3 - ScribeFlow

**Project Root**: `~/Documents/VibeCoding/Week3`
**Feature Branch**: `001-scribeflow-voice-system`
**Status**: ✅ **v0.1.0 Complete (100%) - Ready for Release**
**Description**: 基于 Tauri v2 和 ElevenLabs Scribe v2 API 的桌面实时语音听写工具

### Active Technologies

**Backend (Rust 2021 edition)**:
- Tauri v2.9 (桌面应用框架)
- cpal 0.16 (音频采集)
- rubato 0.16.2 (音频重采样)
- tokio-tungstenite 0.28 (WebSocket)
- enigo 0.6.1 (键盘模拟)
- keyring 2.3 (密钥存储)

**Frontend (TypeScript 5.3)**:
- React 19.2
- Zustand 5.0.8 (状态管理)
- TailwindCSS 4.1
- Vite (构建工具)

**Platform Support**:
- ✅ Tier 1: macOS 10.15+, Linux X11 (Ubuntu 22.04+)
- ⚠️ Tier 2: Linux Wayland (功能降级)

### Key Documents

- **🔥 Current Status**: `specs/001-scribeflow-voice-system/CURRENT_STATUS.md` ← **Start here!**
- **Constitution**: `Week3/.specify/memory/constitution.md`
- **Specification**: `specs/001-scribeflow-voice-system/spec.md`
- **Design**: `specs/001-scribeflow-voice-system/design.md`
- **Implementation Plan**: `specs/001-scribeflow-voice-system/plan.md`
- **Tasks**: `specs/001-scribeflow-voice-system/tasks.md`
- **Research**: `specs/001-scribeflow-voice-system/research.md`
- **Data Model**: `specs/001-scribeflow-voice-system/data-model.md`
- **QuickStart**: `specs/001-scribeflow-voice-system/quickstart.md`

### Project-Specific Guidelines

详见 `Week3/CLAUDE.md` 获取 Week3 项目的详细开发指南。

---

## Common Commands

### Week5 (PostgreSQL MCP Server)

```bash
# 进入项目目录
cd ~/Documents/VibeCoding/Week5

# 安装依赖
source .venv/bin/activate
pip install -e .

# 配置
cp config/config.example.yaml config/config.yaml
# 编辑 config.yaml 填入数据库和 API 配置

# 开发
python -m postgres_mcp

# 测试
pytest tests/unit/ -v                           # 单元测试 (141个)
pytest tests/contract/test_mcp_protocol.py -v   # MCP 协议测试 (10个)
cd tests/contract && ./run_contract_tests.sh sample  # 契约测试快速验证

# 覆盖率
pytest tests/unit/ --cov=src/postgres_mcp --cov-report=term-missing

# Lint
ruff format src/ tests/
ruff check src/ tests/ --fix

# 类型检查
mypy src/
```

### Week3 (ScribeFlow)

```bash
# 进入项目目录
cd ~/Documents/VibeCoding/Week3

# 开发
npm run tauri dev

# 测试
cargo test --manifest-path src-tauri/Cargo.toml
npm run test

# 构建
npm run tauri build

# Lint
cargo clippy --manifest-path src-tauri/Cargo.toml
npm run lint

# 格式化
cargo fmt --manifest-path src-tauri/Cargo.toml
npm run format
```

### Week2 (数据库查询工具)

```bash
cd ~/Documents/VibeCoding/Week2
npm run dev
```

### Week1 (Ticket 系统)

```bash
cd ~/Documents/VibeCoding/Week1/env
./start.sh
```

---

## Code Style

### Rust 2021 Edition (Week3)

- **Never** use `unsafe` code
- **Never** use `.unwrap()` or `.expect()` - properly handle or propagate errors (except in Default impl)
- Prefer `mpsc` channels over shared memory
- Use `ArcSwap` for rarely-modified data, `DashMap` for concurrent HashMap
- Use Rust's native `async trait` support (not `async_trait` crate)
- **Note**: Using Rust 2021 (not 2024) - Rust 2024 requires Rust 1.85+

### TypeScript (All Projects)

- Follow standard conventions
- Use strict mode
- Prefer functional components (React)
- Use proper typing (no `any`)

---

## Recent Changes

- **2026-01-30**: 🎉 001-postgres-mcp **v1.0.0 生产就绪** - 完整功能集完成 (221 tests, 97% tasks)
  - US5 结果验证器完成 (基础验证 + AI 语义验证 + 智能 AUTO 策略) - 1,050 LOC, 17 tests
  - MCP 协议契约测试完成 (5个工具全覆盖) - 10 tests
  - 文档全面更新 (README, tasks, CURRENT_STATUS)
  - **项目完成度**: 102/105 tasks (97%), 221 tests (100% pass), 92% coverage
- **2026-01-25**: 🎉 001-scribeflow-voice-system **v0.1.0 COMPLETE** - All 7 phases done (5,520 LOC, 62 tests)
 - Phase 6: Frontend UI (悬浮窗, 波形, Toast, 设置面板) - 850 LOC
 - Phase 7: Error Handling & Logging (日志轮转, 完整文档) - 200 LOC
 - **Status**: Production build ready, recommended to complete plugin integration before public release
- **2026-01-25**: 001-scribeflow-voice-system Phase 5 完成 - Tauri Commands & Integration (5 commands, Event system, 650 LOC)

---

## Navigation

| 项目 | 路径 | 状态 |
|------|------|------|
| Week1 - Ticket System | `./Week1` | ✅ 开发中 |
| Week2 - DB Query Tool | `./Week2` | ✅ 完成 |
| Week3 - ScribeFlow | `./Week3` | 🎉 v0.1.0 完成 |
| Week5 - PostgreSQL MCP | `./Week5` | 🔥 v1.0.0 生产就绪 |

**当前活跃**: Week5 - PostgreSQL MCP Server (Branch: `001-postgres-mcp`)

---

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
