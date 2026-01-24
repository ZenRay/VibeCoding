# VibeCoding Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-01-24

**Repository Root**: `~/Documents/VibeCoding`
**Current Branch**: `001-scribeflow-voice-system`

---

## Project Structure

This repository contains multiple projects organized by week:

```text
~/Documents/VibeCoding/
├── Week1/                      # Ticket 管理系统 (FastAPI + React)
├── Week2/                      # 数据库查询工具 (已完成)
├── Week3/                      # 🔥 ScribeFlow 语音听写系统 (活跃)
│   ├── .specify/               # 项目工具和模板
│   ├── docs/                   # 项目文档
│   ├── src-tauri/              # Rust 后端 (待创建)
│   ├── src/                    # React 前端 (待创建)
│   ├── CLAUDE.md               # Week3 本地 Agent 配置
│   └── PROJECT_STRUCTURE.md    # 详细路径指南
├── specs/                      # 所有功能的规范文档
│   ├── 001-scribeflow-voice-system/  # Week3 功能规范
│   ├── 002-mysql-support/
│   └── 003-export-query-results/
└── archive/                    # 归档文件
```

---

## Active Project: Week3 - ScribeFlow

**Project Root**: `~/Documents/VibeCoding/Week3`
**Feature Branch**: `001-scribeflow-voice-system`
**Description**: 基于 Tauri v2 和 ElevenLabs Scribe v2 API 的桌面实时语音听写工具

### Active Technologies

**Backend (Rust 2024 edition)**:
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

- **Constitution**: `Week3/.specify/memory/constitution.md`
- **Specification**: `specs/001-scribeflow-voice-system/spec.md`
- **Design**: `specs/001-scribeflow-voice-system/design.md`
- **Implementation Plan**: `specs/001-scribeflow-voice-system/plan.md`
- **Research**: `specs/001-scribeflow-voice-system/research.md`
- **Data Model**: `specs/001-scribeflow-voice-system/data-model.md`
- **QuickStart**: `specs/001-scribeflow-voice-system/quickstart.md`

### Project-Specific Guidelines

详见 `Week3/CLAUDE.md` 获取 Week3 项目的详细开发指南。

---

## Common Commands

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

### Rust 2024 Edition (Week3)

- **Never** use `unsafe` code
- **Never** use `.unwrap()` or `.expect()` - properly handle or propagate errors
- Prefer `mpsc` channels over shared memory
- Use `ArcSwap` for rarely-modified data, `DashMap` for concurrent HashMap
- Use Rust's native `async trait` support (not `async_trait` crate)

### TypeScript (All Projects)

- Follow standard conventions
- Use strict mode
- Prefer functional components (React)
- Use proper typing (no `any`)

---

## Recent Changes

- **2026-01-24**: 001-scribeflow-voice-system - Added Rust 2024 + TypeScript 5.3, Linux platform support
- **2026-01-20**: Week2 - Database query tool features (MySQL support, export)
- **2026-01-18**: Week1 - Ticket management system

---

## Navigation

| 项目 | 路径 | 状态 |
|------|------|------|
| Week1 - Ticket System | `./Week1` | ✅ 开发中 |
| Week2 - DB Query Tool | `./Week2` | ✅ 完成 |
| Week3 - ScribeFlow | `./Week3` | 🔥 活跃开发 |

**当前活跃**: Week3 - ScribeFlow (Branch: `001-scribeflow-voice-system`)

---

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
