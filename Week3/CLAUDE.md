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

**Tech Stack**:
- Backend: Rust 2024 edition (Tauri v2.9, cpal 0.16, rubato 0.16.2, tokio-tungstenite 0.28)
- Frontend: TypeScript 5.3 (React 19.2, Zustand 5.0.8, TailwindCSS 4.1)
- Platform: macOS 10.15+ (Tier 1), Linux X11 (Tier 1), Linux Wayland (Tier 2)

**Key Documents**:
- Constitution: `.specify/memory/constitution.md`
- Specification: `../specs/001-scribeflow-voice-system/spec.md`
- Design: `../specs/001-scribeflow-voice-system/design.md`
- Plan: `../specs/001-scribeflow-voice-system/plan.md`
- Research: `../specs/001-scribeflow-voice-system/research.md`

## Rust Development Guidelines

### Version and Dependencies
- Always use Rust 2024 edition
- Manage dependencies using workspace configuration
- Verify crate APIs by visiting their documentation pages
- Always use the latest stable versions of dependencies

### Concurrency Patterns
- Prefer `mpsc` channels over shared memory for communication
- For rarely-modified data (e.g., configuration): use `ArcSwap` instead of `Arc<Mutex<T>>`
- For concurrent HashMap access: use `DashMap` instead of `Mutex<HashMap>` or `RwLock<HashMap>`

### Code Safety and Quality
- **Never** use `unsafe` code
- **Never** use `.unwrap()` or `.expect()` - properly handle or propagate errors
- For tests requiring environment variables: use the `dotenv` library
- Use Rust's native `async trait` support (not the `async_trait` crate)

## Common Commands

Since this is a new project, specific build/test commands will be added as the project develops.

For Rust projects, typical commands include:
```bash
cargo build          # Build the project
cargo test           # Run all tests
cargo test test_name # Run a specific test
cargo clippy         # Lint code
cargo fmt            # Format code
```
