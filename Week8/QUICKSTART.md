# 快速开始指南

本指南将帮助你快速上手 Code Agent。

## 安装

### 1. 构建项目

```bash
cd ~/Documents/VibeCoding/Week8
cargo build --release
```

### 2. 安装到系统 (可选)

```bash
cargo install --path apps/ca-cli
```

或者直接使用:

```bash
alias code-agent="~/Documents/VibeCoding/Week8/target/release/code-agent"
```

## 配置

### 1. 初始化配置

```bash
code-agent init --api-key YOUR_CLAUDE_API_KEY
```

这将创建 `~/.code-agent/config.toml` 文件。

### 2. 自定义配置 (可选)

编辑 `~/.code-agent/config.toml`:

```toml
[agent]
agent_type = "claude"
api_key = "your-key-here"
model = "claude-3-5-sonnet-20241022"

[prompt]
template_dir = "/home/user/.code-agent/templates"
default_template = "default"

# 设置默认工作目录
default_repo = "/home/user/projects/my-project"
```

## 基本使用

### 执行简单任务

```bash
# 在当前目录执行
code-agent run "添加 MIT 许可证文件"

# 指定工作目录
code-agent run "重构代码" --repo /path/to/project
```

### 使用上下文文件

```bash
code-agent run "优化这个函数" \
  --files src/main.rs \
  --files src/utils.rs
```

### 查看模板

```bash
# 列出所有模板
code-agent templates

# 显示详细信息
code-agent templates --verbose
```

## 交互式 TUI

启动终端用户界面:

```bash
code-agent tui
```

在 TUI 中:
- 输入任务描述
- 按 Enter 执行
- 按 Esc 退出

## 自定义模板

### 1. 创建模板文件

在 `~/.code-agent/templates/` 目录下创建 `.jinja` 文件:

```bash
mkdir -p ~/.code-agent/templates
nano ~/.code-agent/templates/my-template.jinja
```

### 2. 编写模板

```jinja
# Task: {{ task }}

## Context Files
{% for file in context_files %}
- {{ file }}
{% endfor %}

## Instructions
{{ instructions }}

Please implement this carefully.
```

### 3. 使用模板

在配置文件中设置 `default_template = "my-template"`

## 示例场景

### 场景 1: 添加新功能

```bash
code-agent run "添加用户认证功能" \
  --repo ~/projects/webapp \
  --files src/auth.rs \
  --files src/models/user.rs
```

### 场景 2: 修复 Bug

```bash
code-agent run "修复登录时的内存泄漏问题" \
  --files src/auth/login.rs
```

### 场景 3: 重构代码

```bash
code-agent run "将数据库代码重构为 repository 模式" \
  --repo ~/projects/api \
  --files src/db.rs
```

## 故障排除

### 问题: API 密钥错误

```bash
# 重新配置
code-agent init --api-key NEW_API_KEY
```

### 问题: 找不到模板

```bash
# 检查模板目录
ls -la ~/.code-agent/templates/

# 查看可用模板
code-agent templates
```

### 问题: 权限错误

```bash
# 确保配置目录权限正确
chmod 700 ~/.code-agent
chmod 600 ~/.code-agent/config.toml
```

## 开发模式

如果你想修改代码:

```bash
cd ~/Documents/VibeCoding/Week8

# 构建
cargo build

# 运行测试
cargo test

# 运行 (无需 install)
cargo run --bin code-agent -- run "your task"
```

## 下一步

- 阅读 [README.md](README.md) 了解完整功能
- 查看 [CHANGELOG.md](CHANGELOG.md) 了解更新历史
- 探索 `crates/` 目录了解内部实现

## 获取帮助

```bash
# 查看帮助
code-agent --help

# 查看子命令帮助
code-agent run --help
code-agent init --help
```
