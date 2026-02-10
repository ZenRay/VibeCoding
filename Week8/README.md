# Code Agent

一个强大的代码 Agent CLI 工具,封装了多种 AI Agent SDK (Claude Agent, GitHub Copilot Agent, Cursor Agent),让你能够轻松地在代码仓库中添加新功能。

## 特性

- 🤖 **多 Agent 支持**: Claude Agent (已实现), GitHub Copilot, Cursor (规划中)
- 📝 **模板系统**: 基于 MiniJinja 的灵活 Prompt 模板管理
- 🎯 **智能执行**: 自动处理文件读取、修改和验证
- 🖥️ **交互式 TUI**: 基于 Ratatui 的终端用户界面
- ⚡ **异步执行**: 基于 Tokio 的高性能异步运行时

## 架构

本项目采用 Cargo Workspace 架构:

```
Week8/
├── Cargo.toml              # Workspace 配置
├── crates/
│   ├── ca-core/           # 核心执行引擎
│   │   ├── src/
│   │   │   ├── agent/     # Agent 抽象和实现
│   │   │   ├── executor/  # 任务执行器
│   │   │   ├── repository/# 代码仓库管理
│   │   │   ├── config.rs  # 配置
│   │   │   └── error.rs   # 错误处理
│   │   └── Cargo.toml
│   └── ca-pm/             # Prompt Manager
│       ├── src/
│       │   ├── manager.rs # Prompt 管理器
│       │   ├── template.rs# 模板渲染
│       │   └── error.rs   # 错误处理
│       └── Cargo.toml
└── apps/
    └── ca-cli/            # CLI 应用
        ├── src/
        │   ├── commands/  # 命令实现
        │   ├── ui/        # TUI 界面
        │   ├── config/    # 配置管理
        │   └── main.rs
        └── Cargo.toml
```

## 安装

### 前置要求

- Rust 1.75+ (2021 edition)
- Cargo

### 从源码构建

```bash
cd ~/Documents/VibeCoding/Week8
cargo build --release
```

生成的二进制文件位于 `target/release/code-agent`

## 快速开始

### 1. 初始化配置

```bash
code-agent init --api-key YOUR_CLAUDE_API_KEY
```

配置文件会保存到 `~/.code-agent/config.toml`

### 2. 执行任务

```bash
# 在当前目录执行任务
code-agent run "添加一个新的 README 文件"

# 指定工作目录
code-agent run "重构 main.rs" --repo /path/to/repo

# 指定相关文件
code-agent run "优化性能" --files src/main.rs --files src/lib.rs
```

### 3. 查看可用模板

```bash
# 列出所有模板
code-agent templates

# 显示详细信息
code-agent templates --verbose
```

### 4. 启动交互式 TUI

```bash
# 在当前目录启动 TUI
code-agent tui

# 指定工作目录
code-agent tui --repo /path/to/repo
```

## 配置

配置文件位于 `~/.code-agent/config.toml`:

```toml
[agent]
agent_type = "claude"
api_key = "your-api-key"
model = "claude-3-5-sonnet-20241022"

[prompt]
template_dir = "/home/user/.code-agent/templates"
default_template = "default"

# 可选: 默认工作目录
default_repo = "/path/to/your/repo"
```

## Prompt 模板

模板使用 MiniJinja 语法,位于 `~/.code-agent/templates/`:

```jinja
# Task: {{ task }}

## Context
{% if context_files %}
The following files are relevant:
{% for file in context_files %}
- {{ file }}
{% endfor %}
{% endif %}

## Instructions
{{ instructions }}

## Output Format
Please provide:
1. A summary of the changes
2. The implementation details
3. Any potential issues or considerations
```

## 开发

### 构建

```bash
# 构建所有 crates
cargo build

# 构建特定 crate
cargo build -p ca-core
cargo build -p ca-pm
cargo build -p ca-cli
```

### 测试

```bash
# 运行所有测试
cargo test

# 运行特定 crate 的测试
cargo test -p ca-pm
```

### 代码格式化

```bash
cargo fmt --all
```

### Lint

```bash
cargo clippy --all-targets --all-features
```

## Crates 说明

### ca-core

核心执行引擎,提供:

- `Agent` trait 和实现 (ClaudeAgent, 未来支持 CopilotAgent, CursorAgent)
- `Repository` - 代码仓库管理,支持 .gitignore
- `Executor` - 任务执行器,协调 Agent 和 Repository

### ca-pm

Prompt Manager,提供:

- `PromptManager` - 模板管理
- `TemplateRenderer` - 基于 MiniJinja 的模板渲染
- `TemplateContext` - 模板上下文数据

### ca-cli

命令行应用,提供:

- `init` - 初始化配置
- `run` - 执行任务
- `templates` - 管理模板
- `tui` - 交互式终端界面

## 依赖

主要依赖包括:

- **tokio** - 异步运行时
- **claude-agent-sdk-rs 0.6** - Claude Agent SDK
- **clap** - 命令行参数解析
- **ratatui** - TUI 界面
- **minijinja** - 模板引擎
- **serde/serde_json** - 序列化
- **anyhow/thiserror** - 错误处理

完整依赖列表见根目录 `Cargo.toml`

## 路线图

- [x] 核心架构和 Workspace 设置
- [x] Claude Agent 集成
- [x] Prompt 模板系统
- [x] 基础 CLI 命令
- [x] TUI 界面
- [ ] GitHub Copilot Agent 支持
- [ ] Cursor Agent 支持
- [ ] 任务历史记录
- [ ] 配置向导
- [ ] 插件系统

## 许可证

MIT License

## 作者

Ray
