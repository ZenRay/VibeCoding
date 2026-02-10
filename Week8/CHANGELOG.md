# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

## [0.1.0] - 2026-02-10

Initial release with basic functionality.
