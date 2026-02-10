# Code Agent

> 统一的 AI Agent SDK 封装工具，让 AI 帮你写代码

[![Rust Version](https://img.shields.io/badge/rust-2024%20edition-blue)](https://www.rust-lang.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Code Agent 是一个命令行工具，封装了多种 AI Agent SDK (Claude, Copilot, Cursor)，提供统一的接口来帮助你在代码仓库中添加新功能、重构代码、修复 Bug。

## ✨ 特性

- 🤖 **多 Agent 支持**: Claude (✅), Copilot (🚧), Cursor (🚧)
- 📋 **智能规划**: 自动分析项目结构，生成详细的实施计划
- 🔄 **7 Phase 执行**: Observer → Planning → Execute → Review → Fix → Verification → PR
- 🔍 **智能 Review**: 自动代码审查 + Fix 循环 (最多 3 次)
- 💾 **断点恢复**: 支持中断后继续执行
- 📊 **状态追踪**: 自动生成 status.md 和 state.yml
- 🎯 **零配置**: 直接使用环境变量，无需配置文件

## 🚀 快速开始

### 安装

```bash
# 从源码构建
git clone https://github.com/your-repo/code-agent.git
cd code-agent/Week8
cargo build --release

# 安装到系统
cargo install --path apps/ca-cli
```

### 配置

设置环境变量:

```bash
# Claude (推荐)
export ANTHROPIC_API_KEY='sk-ant-xxx'

# Copilot (实验性)
export COPILOT_GITHUB_TOKEN='ghp_xxx'

# Cursor (实验性)
export CURSOR_API_KEY='cursor_xxx'
```

### 使用流程

```bash
# 1. 初始化项目
code-agent init

# 2. 规划新功能
code-agent plan user-authentication --description "添加 OAuth2 用户认证"

# 3. 执行开发
code-agent run user-authentication

# 4. 查看状态
code-agent status user-authentication

# 5. 列出所有功能
code-agent list
```

## 📖 详细文档

### 命令

#### `init` - 初始化项目

```bash
code-agent init [OPTIONS]

选项:
  --api-key <KEY>    API 密钥 (覆盖环境变量)
  --agent <TYPE>     Agent 类型 (claude, copilot, cursor)
  --interactive      交互式配置向导
  --force            强制重新初始化
```

#### `plan` - 规划功能

```bash
code-agent plan <FEATURE_SLUG> [OPTIONS]

参数:
  <FEATURE_SLUG>    功能名称 (slug 格式, 如: user-auth)

选项:
  -d, --description <DESC>    功能描述
  -i, --interactive           交互式规划
  -r, --repo <PATH>          工作目录
```

#### `run` - 执行任务

```bash
code-agent run <FEATURE_SLUG> [OPTIONS]

参数:
  <FEATURE_SLUG>    功能名称

选项:
  --phase <N>           执行特定阶段 (1-7)
  --resume              从中断处恢复
  --dry-run             模拟执行
  --skip-review         跳过代码审查
  --skip-test           跳过测试验证
  -r, --repo <PATH>    工作目录
```

#### `list` - 列出功能

```bash
code-agent list [OPTIONS]

选项:
  --all                 显示所有功能 (包括已完成)
  --status <STATUS>     按状态筛选 (planned, in_progress, completed)
```

#### `status` - 查看状态

```bash
code-agent status <FEATURE_SLUG>
```

#### `clean` - 清理 worktree

```bash
code-agent clean [OPTIONS]

选项:
  --dry-run    试运行
  --all        显示所有功能
```

#### `templates` - 列出模板

```bash
code-agent templates [OPTIONS]

选项:
  -v, --verbose    显示详细信息
```

### 执行阶段

Code Agent 使用 7 个阶段来执行功能开发:

1. **Observer** - 分析项目结构
2. **Planning** - 制定实施计划
3. **Execute (1)** - 执行实施 (前半部分)
4. **Execute (2)** - 执行实施 (后半部分)
5. **Review** - 代码审查 (自动 Fix 循环)
6. **Fix** - 应用修复
7. **Verification** - 验证测试

### Review/Fix 循环

Phase 5 (Review) 会自动检测以下关键词:

- **APPROVED** → 通过，继续下一阶段
- **NEEDS_CHANGES** → 需要修复，自动执行 Fix (最多 3 次)

Phase 7 (Verification) 类似:

- **VERIFIED** → 验证通过，生成 PR
- **FAILED** → 验证失败，再次 Fix

## 🏗️ 架构

```
code-agent/
├── crates/
│   ├── ca-core/       # 核心执行引擎
│   │   ├── agent/     # Agent SDK 适配器
│   │   ├── engine/    # 执行引擎
│   │   ├── state/     # 状态管理
│   │   ├── event/     # EventHandler (流式输出)
│   │   └── review/    # KeywordMatcher (Review 循环)
│   └── ca-pm/         # Prompt 管理器
│       ├── templates/ # Prompt 模板 (3 文件结构)
│       └── manager.rs # 模板加载和渲染
└── apps/
    └── ca-cli/        # 命令行界面
        └── commands/  # 命令实现
```

## 🤝 贡献

欢迎贡献! 请查看 [CONTRIBUTING.md](CONTRIBUTING.md)

## 📄 许可证

MIT License - 查看 [LICENSE](LICENSE) 文件

## 🙏 致谢

感谢 [GBA 项目](https://github.com/tyrchen/gba) 提供的优秀设计参考。
