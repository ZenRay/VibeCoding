# Code Agent 手动测试指南

**版本**: v0.1.0  
**日期**: 2026-02-10  
**测试环境**: Linux/macOS

---

## 📋 测试前准备

### 1. 构建状态检查

✅ **Release 版本已构建完成**

```bash
cd /home/ray/Documents/VibeCoding/Week8

# 检查构建状态
ls -lh target/release/code-agent
# -rwxrwxr-x  2 ray ray 7.1M Feb 10 23:06 code-agent ✅
```

**无需重新构建** - 如果需要重新编译：

```bash
# Debug 版本 (快速编译，包含调试信息)
cargo build

# Release 版本 (优化编译，用于测试)
cargo build --release
```

### 2. 安装方式选择

有三种使用方式，**推荐方式 1 或 2**：

#### 方式 1: 使用 alias (推荐，无需安装) ⭐

```bash
# 添加到 ~/.bashrc 或 ~/.zshrc
alias code-agent="/home/ray/Documents/VibeCoding/Week8/target/release/code-agent"

# 立即生效
source ~/.bashrc  # 或 source ~/.zshrc

# 测试
code-agent --version
```

**优点**: 
- 无需安装，立即可用
- 修改代码后重新编译即可，无需重新安装
- 便于开发和调试

#### 方式 2: 安装到 Cargo bin 目录

```bash
cd /home/ray/Documents/VibeCoding/Week8
cargo install --path apps/ca-cli

# 会安装到 ~/.cargo/bin/code-agent
# 确保 ~/.cargo/bin 在 PATH 中

# 测试
code-agent --version
```

**优点**: 
- 标准的 Rust 安装方式
- 可以在任何目录直接使用

#### 方式 3: 直接使用 cargo run

```bash
cd /home/ray/Documents/VibeCoding/Week8

# 使用方式
cargo run --release -- [COMMAND] [OPTIONS]

# 示例
cargo run --release -- --help
cargo run --release -- plan my-feature
```

**优点**: 
- 无需安装
- 适合频繁修改代码时使用

### 3. 环境变量配置

⚠️ **必须配置** - Code Agent 使用零配置文件方案：

```bash
# Claude Agent (官方 Anthropic API)
export ANTHROPIC_API_KEY='sk-ant-xxxxxxxxxxxxx'

# 或使用 OpenRouter (支持多种环境变量名) ✨
export ANTHROPIC_AUTH_TOKEN='sk-or-v1-xxxxxxxxxxxxx'  # OpenRouter 标准
export OPENROUTER_API_KEY='sk-or-v1-xxxxxxxxxxxxx'    # OpenRouter 别名
export ANTHROPIC_BASE_URL='https://openrouter.ai/api/v1'

# 可选: 指定模型
export CLAUDE_MODEL='claude-3-5-sonnet-20241022'
```

**支持的环境变量 (按优先级)**:
1. `ANTHROPIC_API_KEY` - Anthropic 官方标准
2. `CLAUDE_API_KEY` - 常见别名
3. `ANTHROPIC_AUTH_TOKEN` - OpenRouter 标准 ✨ NEW
4. `OPENROUTER_API_KEY` - OpenRouter 别名 ✨ NEW

**永久设置** (推荐):

```bash
# 添加到 ~/.bashrc 或 ~/.zshrc
echo 'export ANTHROPIC_API_KEY="sk-ant-xxxxxxxxxxxxx"' >> ~/.bashrc
source ~/.bashrc
```

**验证环境变量**:

```bash
echo $ANTHROPIC_API_KEY
# 应该显示你的 API key
```

---

## 🧪 测试场景

### 场景 0: 基础功能测试

#### 0.1 检查命令是否可用

```bash
# 显示帮助信息
code-agent --help

# 预期输出: 显示所有命令列表
# Commands:
#   init      初始化项目配置
#   plan      规划功能并生成 specs
#   run       执行功能开发
#   templates 管理 Prompt 模板
#   tui       启动交互式 TUI
#   help      显示帮助信息
```

#### 0.2 检查版本信息

```bash
code-agent --version

# 预期输出: code-agent 0.1.0
```

#### 0.3 查看子命令帮助

```bash
code-agent init --help
code-agent plan --help
code-agent run --help

# 预期: 显示每个命令的详细参数说明
```

---

### 场景 1: Init 命令测试 (环境验证)

#### 测试目的
验证环境变量配置和 API 连接。

#### 步骤

```bash
# 进入测试目录
cd /tmp
mkdir -p code-agent-test
cd code-agent-test

# 执行 init
code-agent init
```

#### 预期输出

```
🔧 Code Agent 初始化

📋 配置检查:
  ✅ Agent 类型: Claude
  ✅ API Key: sk-ant-x***xxxxx4 (已设置)
  ✅ 模型: claude-3-5-sonnet-20241022 (默认)

🔌 测试连接...
  ✅ 连接成功!

✅ 初始化完成!

💡 下一步:
  1. 规划功能: code-agent plan my-feature
  2. 执行开发: code-agent run my-feature

📚 项目结构追踪:
  • status.md - 人类可读的进度报告 (中文)
  • state.yml - 机器可读的状态文件 (英文)
```

#### 验证点

- ✅ 检测到环境变量中的 API Key
- ✅ 自动检测 Agent 类型
- ✅ 连接测试成功
- ✅ 显示友好的提示信息

---

### 场景 2: Plan 命令测试 (功能规划)

#### 测试目的
测试功能规划和 specs 文档生成。

#### 步骤

```bash
# 创建测试项目
cd /tmp/code-agent-test
mkdir test-project
cd test-project

# 初始化 Git (可选，但推荐)
git init
echo "# Test Project" > README.md
git add .
git commit -m "Initial commit"

# 执行 plan 命令
code-agent plan user-auth --description "实现用户认证功能，包括注册、登录和密码重置"
```

#### 预期输出

```
📋 功能规划: user-auth

📝 功能描述:
实现用户认证功能，包括注册、登录和密码重置

🔍 分析项目...
  • 检测到 Git 仓库: /tmp/code-agent-test/test-project
  • 主分支: main
  • 最近提交: Initial commit (1 分钟前)

📂 创建 specs 目录...
  • specs/001-user-auth/

🤖 调用 Agent 进行功能分析...
  ⏳ 正在分析项目结构和需求...
  ⏳ 生成功能规格文档...
  ⏳ 制定实施计划...

✅ 功能规划完成!

📁 生成的文档:
  • specs/001-user-auth/0001_user_auth.md
  • specs/001-user-auth/design.md
  • specs/001-user-auth/plan.md
  • specs/001-user-auth/tasks.md
  • specs/001-user-auth/status.md (NEW)
  • specs/001-user-auth/state.yml

📊 规划统计:
  • 识别任务数: 15-20 个
  • 预估阶段数: 2 个
  • 预估工作量: 中等

🎯 下一步:
  code-agent run user-auth
```

#### 验证点

```bash
# 检查生成的文件
ls -la specs/001-user-auth/

# 预期文件列表:
# 0001_user_auth.md  - 功能规格
# design.md          - 设计文档
# plan.md            - 实施计划
# tasks.md           - 任务列表
# status.md          - 进度状态 (中文) ✨ NEW
# state.yml          - 执行状态 (机器可读)

# 查看 status.md (人类可读)
cat specs/001-user-auth/status.md

# 预期包含:
# - 功能概述
# - 执行进度 (0%)
# - 7 个阶段状态表格
# - 成本追踪
# - 问题列表
# - 变更记录
# - 下一步计划

# 查看 state.yml (机器可读)
cat specs/001-user-auth/state.yml

# 预期: YAML 格式的完整状态数据
```

---

### 场景 3: Run 命令测试 (简单场景)

⚠️ **注意**: 此场景会实际调用 Claude API，会产生费用。

#### 测试目的
测试完整的 7 阶段执行流程和 status.md 自动更新。

#### 测试 3.1: Dry Run (不修改文件)

```bash
# 先使用 dry-run 模式测试
code-agent run user-auth --dry-run

# 预期输出:
# 🔍 [DRY RUN] 模拟执行 - 不会修改任何文件
# 
# Phase 1: 构建 Observer
#   🔍 [DRY RUN] 模拟分析项目...
# 
# Phase 2: 制定计划
#   🔍 [DRY RUN] 模拟生成任务列表...
# ...
```

#### 测试 3.2: 执行单个阶段

```bash
# 只执行 Phase 1 (Observer)
code-agent run user-auth --phase 1

# 预期:
# 📊 执行 Phase 1: 构建 Observer
# 
# 🤖 调用 Agent...
#   ⏳ 正在分析项目结构...
#   ⏳ 识别需要修改的文件...
# 
# ✅ Phase 1 完成!
# 
# 📄 生成的文档:
#   • specs/001-user-auth/.ca-state/phase1-observer.md
# 
# 📊 成本统计:
#   • Input tokens: 2,500
#   • Output tokens: 1,200
#   • 成本: $0.05
# 
# 📝 status.md 已更新 ✨

# 验证 status.md 更新
cat specs/001-user-auth/status.md

# 预期: Phase 1 状态已更新为 "✅ 完成"
```

#### 测试 3.3: 中断恢复

```bash
# 执行到一半按 Ctrl+C 中断

# 恢复执行
code-agent run user-auth --resume

# 预期:
# 🔄 检测到未完成的执行...
# 
# 📊 恢复信息:
#   • 上次中断于: Phase 3, Task 3
#   • 已完成任务: 8 个
#   • 剩余任务: 12 个
# 
# ▶️ 从 Phase 3 继续执行...
```

---

### 场景 4: Status.md 自动更新测试 ✨

#### 测试目的
验证 status.md 在各个阶段自动更新。

#### 步骤

```bash
# 1. 初始状态 (Plan 后)
cat specs/001-user-auth/status.md | head -20

# 预期: 显示初始状态，所有 Phase 为 "⏳ 待开始"

# 2. 执行 Phase 1
code-agent run user-auth --phase 1

# 3. 检查更新
cat specs/001-user-auth/status.md | grep "Phase 1"

# 预期: Phase 1 状态改为 "✅ 完成"，包含开始/结束时间

# 4. 检查变更记录
cat specs/001-user-auth/status.md | grep -A 10 "变更记录"

# 预期: 包含 Phase 1 完成的记录

# 5. 执行 Phase 2
code-agent run user-auth --phase 2

# 6. 再次检查
cat specs/001-user-auth/status.md

# 预期: 
#   - Phase 2 状态更新
#   - 整体进度百分比增加
#   - 成本统计更新
#   - 变更记录新增条目
```

---

### 场景 5: OpenRouter 第三方 API 测试

#### 测试目的
验证使用 OpenRouter 等第三方 API。

#### 步骤

```bash
# 1. 设置 OpenRouter 环境变量 (两种方式任选其一)
# 方式 A: 使用 ANTHROPIC_AUTH_TOKEN (推荐) ✨
export ANTHROPIC_AUTH_TOKEN='sk-or-v1-xxxxxxxxxxxxx'
export ANTHROPIC_BASE_URL='https://openrouter.ai/api/v1'

# 方式 B: 使用 OPENROUTER_API_KEY (别名) ✨
export OPENROUTER_API_KEY='sk-or-v1-xxxxxxxxxxxxx'
export ANTHROPIC_BASE_URL='https://openrouter.ai/api/v1'

# 2. 验证配置
code-agent init

# 预期输出:
# 📋 配置检查:
#   ✅ Agent 类型: Claude
#   ✅ API Key: sk-or-v***xxxxx4
#   ✅ 自定义 API endpoint: https://openrouter.ai/api/v1 ✨
#   ✅ 模型: claude-3-5-sonnet-20241022
# 
# 🔌 测试连接...
#   ℹ️  Using custom API endpoint: https://openrouter.ai/api/v1
#   ✅ 连接成功!

# 3. 执行测试任务
code-agent plan test-feature --description "测试 OpenRouter 集成"

# 预期: 正常执行，使用 OpenRouter API
```

---

## 🔍 调试和故障排查

### 启用调试日志

```bash
# 设置日志级别
export RUST_LOG=debug
# 或
export RUST_LOG=ca_core=debug,ca_cli=debug

# 执行命令
code-agent plan my-feature

# 预期: 显示详细的调试信息
```

### 常见问题

#### 问题 1: API Key 未设置

```
错误输出:
❌ API key not found. Set one of:
  export ANTHROPIC_API_KEY='sk-ant-xxx'            # Anthropic official
  export ANTHROPIC_AUTH_TOKEN='sk-or-v1-xxx'       # OpenRouter
  export OPENROUTER_API_KEY='sk-or-v1-xxx'         # OpenRouter alias
  export CLAUDE_API_KEY='sk-ant-xxx'               # Common alias

解决:
export ANTHROPIC_API_KEY='your-key-here'
# 或
export ANTHROPIC_AUTH_TOKEN='sk-or-v1-xxx'  # 使用 OpenRouter
```

#### 问题 2: 找不到 code-agent 命令

```bash
# 检查是否在 PATH 中
which code-agent

# 如果没有，使用完整路径
/home/ray/Documents/VibeCoding/Week8/target/release/code-agent --help

# 或创建 alias (见前面)
```

#### 问题 3: 权限错误

```bash
# 确保二进制文件可执行
chmod +x /home/ray/Documents/VibeCoding/Week8/target/release/code-agent
```

#### 问题 4: Git 未初始化

```
错误输出:
⚠️  未检测到 Git 仓库

解决:
cd your-project
git init
git add .
git commit -m "Initial commit"
```

---

## 📊 测试检查清单

使用此清单确保所有功能正常：

### 基础功能
- [ ] `code-agent --help` 显示帮助
- [ ] `code-agent --version` 显示版本
- [ ] 环境变量正确设置

### Init 命令
- [ ] `code-agent init` 检测环境变量
- [ ] 连接测试成功
- [ ] 显示友好的提示信息

### Plan 命令
- [ ] 创建 specs 目录结构
- [ ] 生成 6 个文档文件
- [ ] status.md 包含中文内容 ✨
- [ ] state.yml 格式正确

### Run 命令
- [ ] Dry-run 模式工作正常
- [ ] 单阶段执行成功
- [ ] 完整执行流程正常
- [ ] 中断恢复功能正常

### Status.md 功能 ✨
- [ ] Plan 后创建初始 status.md
- [ ] Phase 开始时更新
- [ ] Phase 完成时更新
- [ ] 包含所有必需部分 (进度、成本、问题、变更记录)
- [ ] 使用中文描述

### OpenRouter 支持
- [ ] 检测自定义 API endpoint
- [ ] 连接测试成功
- [ ] 实际调用正常

---

## 📝 测试报告模板

```markdown
# Code Agent 测试报告

**测试日期**: 2026-02-10
**测试人员**: [你的名字]
**版本**: v0.1.0

## 测试环境
- OS: Linux/macOS
- Rust: 1.85+
- API: Claude / OpenRouter

## 测试结果

| 场景 | 测试项 | 结果 | 备注 |
|------|--------|------|------|
| 场景 0 | 基础功能 | ✅ 通过 | - |
| 场景 1 | Init 命令 | ✅ 通过 | - |
| 场景 2 | Plan 命令 | ✅ 通过 | status.md 正常生成 |
| 场景 3 | Run 命令 | ✅ 通过 | - |
| 场景 4 | Status 更新 | ✅ 通过 | 自动更新工作正常 |
| 场景 5 | OpenRouter | ✅ 通过 | - |

## 发现的问题

1. [问题描述]
   - 严重程度: High/Medium/Low
   - 复现步骤: ...
   - 预期行为: ...
   - 实际行为: ...

## 总体评价

[整体评价和建议]
```

---

## 🚀 快速测试脚本

保存为 `quick-test.sh`:

```bash
#!/bin/bash

echo "🧪 Code Agent 快速测试"
echo "====================="

# 检查环境变量
echo "1. 检查环境变量..."
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "  ❌ ANTHROPIC_API_KEY 未设置"
    exit 1
else
    echo "  ✅ ANTHROPIC_API_KEY 已设置"
fi

# 检查命令可用性
echo "2. 检查命令..."
if ! command -v code-agent &> /dev/null; then
    echo "  ❌ code-agent 命令不可用"
    exit 1
else
    echo "  ✅ code-agent 命令可用"
fi

# 测试 Init
echo "3. 测试 Init..."
code-agent init > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "  ✅ Init 成功"
else
    echo "  ❌ Init 失败"
    exit 1
fi

# 创建测试项目
echo "4. 创建测试项目..."
TEST_DIR="/tmp/code-agent-quick-test"
rm -rf $TEST_DIR
mkdir -p $TEST_DIR
cd $TEST_DIR
git init > /dev/null 2>&1
echo "# Test" > README.md
git add .
git commit -m "test" > /dev/null 2>&1
echo "  ✅ 测试项目创建成功"

# 测试 Plan
echo "5. 测试 Plan (dry-run)..."
code-agent plan test-feature --description "测试功能" > /dev/null 2>&1
if [ -f "specs/001-test-feature/status.md" ]; then
    echo "  ✅ Plan 成功 (status.md 已生成)"
else
    echo "  ❌ Plan 失败"
    exit 1
fi

echo ""
echo "✅ 快速测试完成！"
echo "   完整测试请参考 TESTING_GUIDE.md"
```

使用:

```bash
chmod +x quick-test.sh
./quick-test.sh
```

---

## 📚 相关文档

- [README.md](README.md) - 项目总览
- [QUICKSTART.md](QUICKSTART.md) - 快速开始
- [EXAMPLES.md](EXAMPLES.md) - 使用示例
- [STATUS_FEATURE_REPORT.md](STATUS_FEATURE_REPORT.md) - Status.md 功能报告

---

**更新日期**: 2026-02-10  
**维护者**: Code Agent Team
