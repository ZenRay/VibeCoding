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

### 1. 配置环境变量

Code Agent 使用**零配置文件**方案,所有配置通过环境变量提供:

```bash
# Claude Agent (官方 Anthropic API)
export ANTHROPIC_API_KEY='sk-ant-xxx'

# 可选: 指定模型
export CLAUDE_MODEL='claude-3-5-sonnet-20241022'
```

### 2. 规划功能

```bash
# 创建功能规划
code-agent plan my-feature --description "添加用户认证功能"

# 或使用交互模式
code-agent plan my-feature --interactive
```

### 3. 执行功能开发

```bash
# 执行完整的 7 个阶段
code-agent run my-feature

# 执行特定阶段
code-agent run my-feature --phase 3

# 从中断处恢复
code-agent run my-feature --resume
```

### 4. 使用 OpenRouter 等第三方服务

Code Agent 支持使用 OpenRouter、Azure OpenAI、AWS Bedrock 等第三方 API 服务。

#### 方法 1: 环境变量

```bash
# 设置 OpenRouter API Key
export ANTHROPIC_API_KEY='sk-or-v1-xxx'
export ANTHROPIC_BASE_URL='https://openrouter.ai/api/v1'

# 运行命令
code-agent plan my-feature
```

#### 方法 2: CLI 参数

```bash
# 使用 --api-url 参数
code-agent plan my-feature \
  --api-url https://openrouter.ai/api/v1 \
  --api-key sk-or-v1-xxx
```

#### 支持的第三方服务

| 服务 | Base URL | 说明 |
|------|----------|------|
| **OpenRouter** | `https://openrouter.ai/api/v1` | 支持多种模型,按使用付费 |
| **Azure OpenAI** | `https://{resource}.openai.azure.com` | 企业级 API |
| **AWS Bedrock** | 需要额外配置 | 通过 AWS SDK |

#### OpenRouter 完整示例

```bash
# 1. 获取 OpenRouter API Key
# 访问 https://openrouter.ai/ 注册并获取 API Key

# 2. 设置环境变量
export ANTHROPIC_API_KEY='sk-or-v1-xxxxxxxxxxxxx'
export ANTHROPIC_BASE_URL='https://openrouter.ai/api/v1'

# 3. (可选) 指定模型
export CLAUDE_MODEL='anthropic/claude-3.5-sonnet'

# 4. 初始化验证
code-agent init --interactive

# 5. 使用
code-agent plan my-feature --description "实现用户登录"
code-agent run my-feature
```

### 5. 查看可用模板

```bash
# 列出所有模板
code-agent templates

# 显示详细信息
code-agent templates --verbose
```

### 6. 启动交互式 TUI (计划中)

```bash
# 在当前目录启动 TUI
code-agent tui

# 指定工作目录
code-agent tui --repo /path/to/repo
```

## 配置

Code Agent 使用**零配置文件**方案,所有配置通过环境变量提供。

### 必需的环境变量

```bash
# Claude Agent (默认)
export ANTHROPIC_API_KEY='sk-ant-xxx'
```

### 可选的环境变量

```bash
# 指定模型
export CLAUDE_MODEL='claude-3-5-sonnet-20241022'

# 使用自定义 API endpoint (OpenRouter, Azure, etc.)
export ANTHROPIC_BASE_URL='https://openrouter.ai/api/v1'

# 其他支持的环境变量
export CLAUDE_BASE_URL='...'        # 等同于 ANTHROPIC_BASE_URL
export OPENROUTER_BASE_URL='...'   # 自动检测
```

### 配置优先级

配置按以下优先级加载:

1. **CLI 参数** (最高优先级)
   ```bash
   code-agent plan my-feature --api-url https://custom.api.com --model custom-model
   ```

2. **环境变量**
   ```bash
   export ANTHROPIC_BASE_URL='https://openrouter.ai/api/v1'
   ```

3. **配置文件** (可选,位于 `~/.code-agent/config.toml`)
   ```toml
   [agent]
   agent_type = "claude"
   api_key = "your-api-key"
   api_url = "https://openrouter.ai/api/v1"
   model = "claude-3-5-sonnet-20241022"
   
   [prompt]
   template_dir = "/home/user/.code-agent/templates"
   default_template = "default"
   ```

### 环境变量持久化

将环境变量添加到 shell 配置文件:

```bash
# Bash
echo 'export ANTHROPIC_API_KEY="sk-ant-xxx"' >> ~/.bashrc
source ~/.bashrc

# Zsh
echo 'export ANTHROPIC_API_KEY="sk-ant-xxx"' >> ~/.zshrc
source ~/.zshrc
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

### 已完成 ✅

- [x] 核心架构和 Workspace 设置
- [x] Claude Agent 集成
- [x] Prompt 模板系统
- [x] 基础 CLI 命令 (init, plan, run, templates)
- [x] 零配置文件方案 (环境变量优先)
- [x] OpenRouter 和第三方 API endpoint 支持
- [x] 状态管理和恢复功能

### 进行中 🚧

- [ ] TUI 界面完善
- [ ] 完整的 7 个执行阶段实现
- [ ] 集成测试套件

### 计划中 📋

- [ ] GitHub Copilot Agent 支持
- [ ] Cursor Agent 支持
- [ ] 任务历史记录
- [ ] 插件系统
- [ ] 多语言 Prompt 模板
- [ ] Web 界面 (可选)

## 许可证

MIT License

## 作者

Ray
