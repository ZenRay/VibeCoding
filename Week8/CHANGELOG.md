# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-02-11

### Added

- 🎉 初始发布! Code Agent v0.1.0
- ✅ 核心功能完整 (85% 完成度)

#### 核心功能

- **多 Agent 支持**
  - ✅ Claude Agent SDK 完整集成
  - 🚧 Copilot Agent (实验性，Phase 5 计划)
  - 🚧 Cursor Agent (实验性，Phase 5 计划)

- **命令**
  - `init` - 项目初始化 (环境验证 + CLAUDE.md 生成)
  - `plan` - 功能规划 (specs 文档生成)
  - `run` - 执行开发 (7 Phase 自动编排)
  - `list` - 列出所有功能
  - `status` - 查看功能状态
  - `clean` - 清理 worktree
  - `templates` - 列出可用模板

- **7 Phase 执行流程**
  - Phase 1: Observer (项目分析)
  - Phase 2: Planning (制定计划)
  - Phase 3-4: Execute (执行实施)
  - Phase 5: Review (代码审查 + 自动 Fix 循环)
  - Phase 6: Fix (应用修复)
  - Phase 7: Verification (验证测试)

- **智能 Review 机制**
  - KeywordMatcher (4 种匹配模式)
  - 自动 Review/Fix 循环 (最多 3 次迭代)
  - 关键词: APPROVED, NEEDS_CHANGES, VERIFIED, FAILED

- **状态管理**
  - state.yml (机器可读)
  - status.md (人类可读，中文)
  - 断点恢复支持
  - StatusDocumentHook (自动更新)

- **Prompt 管理**
  - 3 文件模板结构 (config.yml + system.jinja + user.jinja)
  - 12 个 Prompt 模板
  - Phase 配置 (工具/权限/预算)
  - MiniJinja 模板引擎

- **EventHandler**
  - 流式输出支持
  - CLI 实现 (零开销 ZST)
  - TUI 实现 (mpsc channel)

#### 技术栈

- Rust 2024 edition
- Claude Agent SDK 0.6.4
- MiniJinja 2.6 (模板引擎)
- Clap 4.5 (CLI 框架)
- Tokio 1.43 (异步运行时)
- Serde YAML (配置解析)

#### 质量保证

- 72 个单元测试 (100% 通过)
- 4 个集成测试
- 0 Clippy 警告
- 完整文档

### Architecture

- **ca-core** (90% 完成)
  - Agent 抽象和适配器
  - ExecutionEngine (支持 PhaseConfig)
  - StateManager + HookRegistry
  - EventHandler trait
  - KeywordMatcher

- **ca-pm** (85% 完成)
  - PromptManager (3 文件结构支持)
  - ContextBuilder
  - TaskConfig/TaskTemplate

- **ca-cli** (90% 完成)
  - 7 个命令完整实现
  - 配置管理 (零配置文件)
  - UI 模块 (保留，Phase 4 使用)

### Security

- 零配置文件策略 (避免 API Key 泄露)
- 环境变量优先
- 符合 12-Factor App 最佳实践

### Documentation

- README.md (快速开始指南)
- design.md (完整设计文档, 4,849 行)
- GAP_ANALYSIS.md (开发状态分析)
- PROGRESS_REPORT.md (进展报告)
- 多个实施报告和指南

## [Unreleased]

### Planned for v0.2.0

- TUI 界面 (Phase 4)
  - 交互式 Plan 命令
  - 流式响应显示
  - 实时统计

### Planned for v0.3.0

- 多 SDK 支持 (Phase 5)
  - Copilot Agent 完整集成
  - Cursor Agent 完整集成
  - 自动 Agent 检测和切换

[0.1.0]: https://github.com/your-repo/code-agent/releases/tag/v0.1.0
