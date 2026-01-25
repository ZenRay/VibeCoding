# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Location

- **Root directory**: `~/Documents/VibeCoding/Week3`
- **Active Feature**: ScribeFlow 桌面实时语音听写系统 (Branch: `001-scribeflow-voice-system`)
- **Source code location**: `~/Documents/VibeCoding/Week3/` (Tauri 项目将在此创建)
- **Specification location**: `~/Documents/VibeCoding/specs/001-scribeflow-voice-system/`
- **Documentation files**: Place all `*.md` files (except user-requested ones) in `./docs/` directory
- **Shared tools**: `.specify/` directory contains project templates and scripts
- Avoid creating redundant markdown files - keep document checks, checklists, and summaries in the same file

## Active Feature: ScribeFlow

**Description**: 基于 Tauri v2 和 ElevenLabs Scribe v2 API 的桌面实时语音听写工具

**Current Status**: Phase 4 Complete (4/7 tasks, 57%) - Ready for Phase 5

**Tech Stack**:
- Backend: Rust 2021 edition (Tauri v2.9, cpal 0.16, rubato 0.16.2, tokio-tungstenite 0.28, enigo 0.6.1)
- Frontend: TypeScript 5.3 (React 19.2, Zustand 5.0.8, TailwindCSS 4.1)
- Platform: macOS 10.15+ (Tier 1), Linux X11 (Tier 1), Linux Wayland (Tier 2)

**Key Documents**:
- **Current Status**: `../specs/001-scribeflow-voice-system/CURRENT_STATUS.md` ← Start here!
- Constitution: `.specify/memory/constitution.md`
- Specification: `../specs/001-scribeflow-voice-system/spec.md`
- Design: `../specs/001-scribeflow-voice-system/design.md`
- Plan: `../specs/001-scribeflow-voice-system/plan.md`
- Tasks: `../specs/001-scribeflow-voice-system/tasks.md`
- Research: `../specs/001-scribeflow-voice-system/research.md`

## Rust Development Guidelines

### Version and Dependencies
- **Use Rust 2021 edition** (not 2024, requires Rust 1.85+)
- Manage dependencies using workspace configuration
- Verify crate APIs by visiting their documentation pages
- Always use the latest stable versions of dependencies
- **Important**: enigo 0.6.1 requires `Settings::default()` and `Keyboard` trait

### Concurrency Patterns
- Prefer `mpsc` channels over shared memory for communication
- For rarely-modified data (e.g., configuration): use `ArcSwap` instead of `Arc<Mutex<T>>`
- For concurrent HashMap access: use `DashMap` instead of `Mutex<HashMap>` or `RwLock<HashMap>`

### Code Safety and Quality
- **Never** use `unsafe` code
- **Never** use `.unwrap()` or `.expect()` - properly handle or propagate errors
- For tests requiring environment variables: use the `dotenv` library
- Use Rust's native `async trait` support (not the `async_trait` crate)

## Implemented Modules (Phase 1-4)

### Audio System (Phase 2)
- `audio/capture.rs` - cpal 音频采集 (立体声→单声道)
- `audio/buffer.rs` - 无锁环形缓冲 (crossbeam ArrayQueue)
- `audio/resampler.rs` - FFT 重采样 48kHz→16kHz (rubato)

### Network System (Phase 3)
- `network/protocol.rs` - ElevenLabs Scribe v2 协议定义
- `network/client.rs` - WebSocket 客户端 (tokio-tungstenite)
- `network/state_machine.rs` - 连接状态机 + 指数退避重连

### Text Injection System (Phase 4)
- `input/keyboard.rs` - 键盘模拟 (enigo, UTF-8, 5ms/char)
- `input/clipboard.rs` - 剪贴板注入 (保存/恢复, Cmd+V/Ctrl+V)
- `input/injector.rs` - 智能策略选择 (10字符阈值, 密码框检测)
- `system/hotkey.rs` - 全局热键管理 (Cmd+Shift+\)
- `system/permissions.rs` - 权限管理 (macOS Accessibility + 麦克风)

## Common Commands

```bash
# Full test path required
~/.cargo/bin/cargo test --manifest-path ~/Documents/VibeCoding/Week3/src-tauri/Cargo.toml

# Build
~/.cargo/bin/cargo build --manifest-path ~/Documents/VibeCoding/Week3/src-tauri/Cargo.toml

# Lint
~/.cargo/bin/cargo clippy --manifest-path ~/Documents/VibeCoding/Week3/src-tauri/Cargo.toml

# Format
~/.cargo/bin/cargo fmt --manifest-path ~/Documents/VibeCoding/Week3/src-tauri/Cargo.toml
```

**Note**: `cargo` is not in PATH, use `~/.cargo/bin/cargo` explicitly
