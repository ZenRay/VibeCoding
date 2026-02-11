# Code Agent

> 统一的 AI Agent SDK 封装工具，让 AI 帮你写代码

[![Rust](https://img.shields.io/badge/rust-1.93%2B-orange.svg)](https://www.rust-lang.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Edition](https://img.shields.io/badge/edition-2024-blue.svg)](https://blog.rust-lang.org/2024/12/19/rust-1.93.html)

Code Agent 是一个命令行工具，封装了多种 AI Agent SDK (Claude, Copilot, Cursor)，提供统一的接口来帮助你在代码仓库中添加新功能、重构代码、修复 Bug。

## ✨ 特性

- 🤖 **多 Agent 支持**: Claude (已实现), Cursor & Copilot (计划中)
- 📋 **零配置**: 通过环境变量配置，无需配置文件
- 🎨 **交互式 TUI**: Plan 和 Run 命令支持 TUI 模式
- 🌳 **Git Worktree**: 自动隔离功能开发环境 (可选)
- 🔄 **断点续传**: 支持从中断处恢复执行
- 📊 **状态追踪**: 自动生成 status.md 和 state.yml
- 🔍 **Review 循环**: 自动 Review → Fix → Review (最多 3 次)
- 📝 **Prompt 模板**: 13 个内置模板，支持自定义

## 📦 安装

### 前置要求

- Rust 1.93+ (使用 Rust 2024 edition)
- Git (可选，用于 worktree 功能)
- Claude API Key (或其他 Agent API Key)

### 从源码构建

```bash
# 克隆仓库
git clone https://github.com/your-repo/code-agent.git
cd code-agent/Week8

# 构建
cargo build --release

# 安装到系统
cargo install --path apps/ca-cli

# 验证安装
code-agent --version
```

### 开发模式

若从源码运行 (未安装)，建议在 Week8 目录下操作，以便正确加载模板:

```bash
cd /path/to/code-agent/Week8
cargo run -- run add-auth --repo /path/to/your-project
```

## 🔧 配置

### 环境变量

Code Agent 使用**零配置文件**策略，所有配置通过环境变量提供。

#### Claude Agent (推荐)

```bash
# 必需: API Key
export ANTHROPIC_API_KEY='sk-ant-xxx'

# 可选: 自定义配置
export CLAUDE_MODEL='claude-3-5-sonnet-20241022'  # 默认模型
export ANTHROPIC_BASE_URL='https://api.anthropic.com'  # API 端点
```

**支持的环境变量** (按优先级):
1. `ANTHROPIC_API_KEY` (Anthropic 官方 / 阿里百炼)
2. `CLAUDE_API_KEY` (别名)
3. `ANTHROPIC_AUTH_TOKEN` (OpenRouter)
4. `OPENROUTER_API_KEY` (OpenRouter 别名)
5. `DASHSCOPE_API_KEY` (阿里百炼)

#### 阿里百炼（国内推荐）⭐

```bash
export DASHSCOPE_API_KEY='sk-...'
export ANTHROPIC_BASE_URL='https://dashscope.aliyuncs.com/compatible-mode/v1'
```

**优势**：
- ✅ 国内直连，无需代理
- ✅ 完全兼容 Anthropic API
- ✅ 支持最新 Claude 模型
- ✅ 价格便宜，速度快

#### OpenRouter / 第三方服务

```bash
export ANTHROPIC_AUTH_TOKEN='sk-or-v1-xxx'
export ANTHROPIC_BASE_URL='https://openrouter.ai/api/v1'

# 使用时指定模型
code-agent plan add-auth --interactive --model "anthropic/claude-3.5-sonnet"
```

**注意**：OpenRouter 需使用 `ANTHROPIC_AUTH_TOKEN`（不是 `ANTHROPIC_API_KEY`）

#### Cursor Agent (即将支持)

```bash
export CURSOR_API_KEY='cursor_xxx'
export CURSOR_MODEL='claude-4-5-sonnet'
```

#### Copilot Agent (即将支持)

```bash
export COPILOT_GITHUB_TOKEN='ghp_xxx'
export COPILOT_MODEL='gpt-4'
```

### 配置优先级

```
CLI 参数 > 环境变量 > 错误提示
```

示例:

```bash
# 使用环境变量
code-agent run add-auth

# 使用 CLI 参数覆盖
code-agent run add-auth --api-key sk-ant-xxx --model claude-3-opus
```

## 🚀 快速开始

### 1. 初始化项目

```bash
# 进入你的项目目录
cd my-project

# 初始化 Code Agent
code-agent init

# 输出:
# 🚀 欢迎使用 Code Agent!
# 🔌 测试 Agent 连接...
# ✅ 连接成功!
# 📁 初始化项目结构...
# ✓ 已创建 specs/ 目录
# ✓ 已更新 .gitignore
# ✓ 已创建 CLAUDE.md
# 🎉 初始化完成!
```

**创建的文件**:
- `specs/` - 功能规格目录
- `.gitignore` - 添加 Code Agent 规则
- `CLAUDE.md` - 项目 AI 文档

### 2. 规划功能

```bash
# 交互式 TUI 模式 (推荐)
code-agent plan add-user-auth --interactive

# 或使用 CLI 模式
code-agent plan add-user-auth --description "添加用户认证功能"
```

**TUI 界面** (Plan):
- 左侧: 对话历史
- 底部: 输入框
- 右侧: 轮次和成本统计
- `Enter` 发送, `Ctrl+C` 退出

**生成的文件** (在 `specs/001-add-user-auth/`):
- `spec.md` - 功能规格
- `design.md` - 设计文档
- `plan.md` - 实施计划
- `tasks.md` - 任务分解
- `status.md` - 进度状态 (中文)
- `state.yml` - 执行状态 (机器可读)

### 3. 执行开发

```bash
# 交互式 TUI 模式 (推荐)
code-agent run add-user-auth --interactive

# 或使用 CLI 模式
code-agent run add-user-auth
```

**TUI 界面** (Run):
- 左侧: Phase 进度列表
- 右侧: 实时日志流
- 底部: 总体统计 (Phase/Turns/Cost)
- `Ctrl+C` 退出

**7 个执行阶段**:
1. **Phase 1: Observer** - 项目分析
2. **Phase 2: Planning** - 制定计划
3. **Phase 3: Execute 1/2** - 执行实施 (前半)
4. **Phase 4: Execute 2/2** - 执行实施 (后半)
5. **Phase 5: Review** - 代码审查 (自动 Fix 循环)
6. **Phase 6: Fix** - 应用修复
7. **Phase 7: Verification** - 验证测试

### 4. 查看状态

```bash
# 查看单个功能状态
code-agent status add-user-auth

# 列出所有功能
code-agent list

# 列出进行中的功能
code-agent list --status in-progress
```

### 5. 清理 Worktree

```bash
# 预览将清理的 worktree
code-agent clean --dry-run

# 实际清理 (需确认)
code-agent clean
```

## 🌳 Git Worktree (可选)

### 什么是 Worktree?

Worktree 为每个功能创建独立的工作目录，实现功能隔离开发。

**目录结构**:

```
my-project/
├── .git/                  # 主仓库
├── specs/                 # 功能规格 (永久保留)
│   ├── 001-add-auth/
│   └── 002-add-export/
├── .trees/                # Worktree 目录 (可清理)
│   ├── 001-add-auth/      # 功能 001 的隔离环境
│   └── 002-add-export/
└── src/                   # 主分支代码
```

### 自动使用

如果在 git 仓库中，Code Agent 会在 `plan` 时自动创建 worktree:

```bash
$ code-agent plan add-auth
📋 规划功能: add-auth
✅ 创建 worktree: /path/.trees/001-add-auth
```

### 清理 Worktree

```bash
# 查看将清理的 worktree
$ code-agent clean --dry-run
🔍 扫描已完成的功能...
  [DRY RUN] 将删除: .trees/001-add-auth
  [DRY RUN] 将删除: .trees/002-fix-bug

# 实际清理
$ code-agent clean
  ✓ 将删除: .trees/001-add-auth
  ...
⚠️  确认删除 2 个 worktree? [y/N] y
✅ 已清理 2 个 worktree
```

**注意**: `specs/` 目录永久保留，是项目的知识库。仅 PR 已合并或关闭的已完成功能才会被清理。

### 非 Git 仓库

如果不是 git 仓库，Code Agent 会使用主目录，功能正常工作。

## 📖 使用指南

### 断点续传

如果执行中断 (Ctrl+C, 错误等)，可以从断点恢复:

```bash
code-agent run add-auth --resume
```

### 跳过特定阶段

```bash
# 跳过代码审查
code-agent run add-auth --skip-review

# 跳过测试验证
code-agent run add-auth --skip-test

# 同时跳过
code-agent run add-auth --skip-review --skip-test
```

### 执行特定阶段

```bash
# 只执行 Phase 3
code-agent run add-auth --phase 3
```

### Dry-run 模式

```bash
# 模拟执行，不修改文件
code-agent run add-auth --dry-run
```

### 自定义工作目录

```bash
# 指定工作目录
code-agent plan add-auth --repo /path/to/project
code-agent run add-auth --repo /path/to/project
```

## 🎨 TUI 快捷键

### Plan TUI

- `Enter` - 发送消息
- `Ctrl+C` - 退出
- `↑` / `↓` - 历史记录导航 / 滚动对话（输入框为空时）
- `PageUp` / `PageDown` - 滚动对话（5 行）
- `Ctrl+Home` - 滚动到对话顶部
- `Ctrl+End` - 滚动到对话底部

**TUI 特性**：
- ✅ 中文字符宽度正确计算（光标位置准确）
- ✅ 对话区域可滚动、可复制内容
- ✅ 实时显示 Agent 状态（空闲 / 思考中 / 执行工具）
- ✅ 动态思考动画（旋转 spinner）
- ✅ Feature 更新模式（已存在的 feature 可继续对话更新）

### Run TUI

- `Ctrl+C` - 退出
- (自动执行，无需输入)

## 📝 Prompt 模板

Code Agent 使用 13 个内置模板，支持自定义。

**模板位置**: `~/.code-agent/templates/` (可通过 `config.toml` 或 `CA_TEMPLATE_DIR` 覆盖)

**模板结构** (3 文件):

```
templates/
└── run/
    └── phase1_observer/
        ├── config.yml       # 任务配置
        ├── system.jinja     # 系统提示词 (可选)
        └── user.jinja       # 用户提示词 (必需)
```

**config.yml 示例**:

```yaml
preset: true                # 使用 Agent preset
tools: []                   # 允许的工具 (空=全部)
disallowed_tools:           # 禁止的工具
  - Delete
permission_mode: default    # 权限模式
max_turns: 20               # 最大轮次
max_budget_usd: 5.0         # 预算限制
```

**查看模板**:

```bash
code-agent templates --verbose
```

## 🔍 故障排查

### 1. API Key 未设置

**错误**:

```
❌ 未找到 Claude API Key。请设置环境变量: ANTHROPIC_API_KEY
```

**解决**（三选一）:

**选项 1: 阿里百炼（国内推荐）**
```bash
export DASHSCOPE_API_KEY='sk-...'
export ANTHROPIC_BASE_URL='https://dashscope.aliyuncs.com/compatible-mode/v1'

# 永久保存
echo 'export DASHSCOPE_API_KEY="sk-..."' >> ~/.bashrc
echo 'export ANTHROPIC_BASE_URL="https://dashscope.aliyuncs.com/compatible-mode/v1"' >> ~/.bashrc
source ~/.bashrc
```

**选项 2: Anthropic 官方（需代理）**
```bash
export ANTHROPIC_API_KEY='sk-ant-xxx'
export HTTP_PROXY='http://127.0.0.1:7890'  # 如需代理

# 永久保存
echo 'export ANTHROPIC_API_KEY="sk-ant-xxx"' >> ~/.bashrc
source ~/.bashrc
```

**选项 3: OpenRouter**
```bash
export ANTHROPIC_AUTH_TOKEN='sk-or-v1-xxx'
export ANTHROPIC_BASE_URL='https://openrouter.ai/api/v1'

# 永久保存
echo 'export ANTHROPIC_AUTH_TOKEN="sk-or-v1-xxx"' >> ~/.bashrc
echo 'export ANTHROPIC_BASE_URL="https://openrouter.ai/api/v1"' >> ~/.bashrc
source ~/.bashrc
```

### 2. Git 未安装

**错误**:

```
❌ Git 命令不可用
```

**解决**:

```bash
# Ubuntu/Debian
sudo apt install git

# macOS
brew install git

# 或: 非 git 仓库下 Code Agent 自动使用主目录
```

### 3. Worktree 已存在

**错误**:

```
❌ Worktree 已存在: .trees/001-add-auth
```

**解决**:

```bash
# 手动删除 worktree
git worktree remove .trees/001-add-auth

# 或使用 clean 命令 (仅清理已完成的)
code-agent clean
```

### 4. 权限错误 (Windows)

**错误**:

```
❌ 权限不足: 无法创建软链接
```

**解决**:
- 以管理员身份运行 PowerShell
- 或启用开发者模式: 设置 → 更新和安全 → 开发者选项

### 5. 测试失败

**错误**:

```
❌ Phase 7: Verification 失败
```

**解决**:

```bash
# 查看详细日志
cat specs/001-add-auth/.ca-state/phase7_output.md

# 手动运行测试
cargo test   # Rust 项目
npm test     # Node 项目

# 修复后重新运行
code-agent run add-auth --phase 7
```

更多问题请参见 [CONTRIBUTING.md](CONTRIBUTING.md) 开发指南。

## 📚 文档

- [贡献指南](CONTRIBUTING.md) - 开发规范与贡献流程
- [更新日志](CHANGELOG.md) - 版本历史

## 🏗️ 架构

```
code-agent/
├── crates/
│   ├── ca-core/       # 核心执行引擎
│   │   ├── agent/     # Agent SDK 适配器
│   │   ├── engine/    # 执行引擎
│   │   ├── state/     # 状态管理
│   │   ├── event/     # EventHandler (流式输出)
│   │   ├── review/    # KeywordMatcher (Review 循环)
│   │   └── worktree/  # Git Worktree 管理
│   └── ca-pm/         # Prompt 管理器
│       ├── templates/ # Prompt 模板 (3 文件结构)
│       └── manager.rs # 模板加载和渲染
└── apps/
    └── ca-cli/        # 命令行界面
        └── commands/  # 命令实现
```

## 🤝 贡献

欢迎贡献! 请查看 [CONTRIBUTING.md](CONTRIBUTING.md) 了解详情。

## 📄 许可证

[MIT License](LICENSE)
