# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- 支持 OpenRouter 的 `ANTHROPIC_AUTH_TOKEN` 和 `OPENROUTER_API_KEY` 环境变量
- 环境变量优先级机制 (ANTHROPIC_API_KEY > CLAUDE_API_KEY > ANTHROPIC_AUTH_TOKEN > OPENROUTER_API_KEY)
- 更新文档说明 OpenRouter 环境变量配置
- 新增 5 个单元测试验证环境变量优先级和 OpenRouter 支持

### Changed
- `Config::load_api_key()` 支持 4 种环境变量名
- `Config::detect_agent_type()` 支持 OpenRouter 环境变量自动检测
- `AgentType::env_var_names()` 返回完整的环境变量列表

## [0.1.0] - 2026-02-10

### Added
- Initial project structure with Cargo Workspace
- `ca-core` crate - Core execution engine
  - Agent trait and ClaudeAgent implementation
  - Repository management with .gitignore support
  - Executor for task coordination
- `ca-pm` crate - Prompt Manager
  - Template system based on MiniJinja
  - Template rendering and context management
- `ca-cli` app - Command Line Interface
  - `init` command for configuration
  - `run` command for task execution
  - `templates` command for template management
  - `tui` command for interactive terminal UI
- Configuration management (~/.code-agent/config.toml)
- Default template system

### Dependencies
- tokio 1.43 - Async runtime
- claude-agent-sdk-rs 0.6 - Claude Agent SDK
- clap 4.5 - CLI argument parsing
- ratatui 0.30 - TUI framework
- minijinja 2.6 - Template engine
- crossterm 0.28 - Terminal manipulation
