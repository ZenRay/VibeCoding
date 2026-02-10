# OpenRouter 配置指南

**适用版本**: v0.1.0+  
**更新日期**: 2026-02-10

---

## 概述

Code Agent 现已支持 OpenRouter 的标准环境变量名 `ANTHROPIC_AUTH_TOKEN` 和 `OPENROUTER_API_KEY`，让用户可以更方便地使用 OpenRouter 服务。

---

## 支持的环境变量

Code Agent 按以下优先级顺序尝试加载 API Key：

| 优先级 | 环境变量名 | 用途 | 示例值 |
|--------|-----------|------|--------|
| 1 | `ANTHROPIC_API_KEY` | Anthropic 官方标准 | `sk-ant-xxx` |
| 2 | `CLAUDE_API_KEY` | 常见别名 | `sk-ant-xxx` |
| 3 | `ANTHROPIC_AUTH_TOKEN` | **OpenRouter 标准** ✨ | `sk-or-v1-xxx` |
| 4 | `OPENROUTER_API_KEY` | **OpenRouter 别名** ✨ | `sk-or-v1-xxx` |

**说明**:
- ✅ 如果你使用 **Anthropic 官方 API**，推荐使用 `ANTHROPIC_API_KEY`
- ✅ 如果你使用 **OpenRouter**，推荐使用 `ANTHROPIC_AUTH_TOKEN` 或 `OPENROUTER_API_KEY`
- ⚠️ 如果同时设置多个变量，会按优先级使用第一个找到的值

---

## OpenRouter 配置方法

### 方法 1: 使用 ANTHROPIC_AUTH_TOKEN (推荐) ⭐

这是 OpenRouter 的标准环境变量名：

```bash
# 设置环境变量
export ANTHROPIC_AUTH_TOKEN='sk-or-v1-xxxxxxxxxxxxx'
export ANTHROPIC_BASE_URL='https://openrouter.ai/api/v1'

# (可选) 指定模型
export CLAUDE_MODEL='anthropic/claude-3.5-sonnet'

# 验证配置
code-agent init
```

### 方法 2: 使用 OPENROUTER_API_KEY (别名)

使用更直观的变量名：

```bash
# 设置环境变量
export OPENROUTER_API_KEY='sk-or-v1-xxxxxxxxxxxxx'
export ANTHROPIC_BASE_URL='https://openrouter.ai/api/v1'

# (可选) 指定模型
export CLAUDE_MODEL='anthropic/claude-3.5-sonnet'

# 验证配置
code-agent init
```

### 方法 3: 使用 CLI 参数

不修改环境变量，直接在命令行传递：

```bash
code-agent plan my-feature \
  --api-key sk-or-v1-xxxxxxxxxxxxx \
  --api-url https://openrouter.ai/api/v1 \
  --model anthropic/claude-3.5-sonnet
```

---

## 完整设置步骤

### 1. 获取 OpenRouter API Key

1. 访问 [OpenRouter](https://openrouter.ai/)
2. 注册并登录账号
3. 进入 Settings → API Keys
4. 创建新的 API Key (格式: `sk-or-v1-xxxxxxxxxxxxx`)
5. 复制 API Key

### 2. 设置环境变量

#### 临时设置 (当前会话)

```bash
export ANTHROPIC_AUTH_TOKEN='sk-or-v1-xxxxxxxxxxxxx'
export ANTHROPIC_BASE_URL='https://openrouter.ai/api/v1'
```

#### 永久设置 (推荐)

**Bash** (`~/.bashrc`):

```bash
echo 'export ANTHROPIC_AUTH_TOKEN="sk-or-v1-xxxxxxxxxxxxx"' >> ~/.bashrc
echo 'export ANTHROPIC_BASE_URL="https://openrouter.ai/api/v1"' >> ~/.bashrc
source ~/.bashrc
```

**Zsh** (`~/.zshrc`):

```bash
echo 'export ANTHROPIC_AUTH_TOKEN="sk-or-v1-xxxxxxxxxxxxx"' >> ~/.zshrc
echo 'export ANTHROPIC_BASE_URL="https://openrouter.ai/api/v1"' >> ~/.zshrc
source ~/.zshrc
```

**Fish** (`~/.config/fish/config.fish`):

```fish
set -Ux ANTHROPIC_AUTH_TOKEN "sk-or-v1-xxxxxxxxxxxxx"
set -Ux ANTHROPIC_BASE_URL "https://openrouter.ai/api/v1"
```

### 3. 验证配置

```bash
# 检查环境变量
echo $ANTHROPIC_AUTH_TOKEN
echo $ANTHROPIC_BASE_URL

# 测试连接
code-agent init
```

**预期输出**:

```
🔧 Code Agent 初始化

📋 配置检查:
  ✅ Agent 类型: Claude
  ✅ API Key: sk-or-v***xxxxx4 (已设置)
  ✅ 自定义 API endpoint: https://openrouter.ai/api/v1 ✨
  ✅ 模型: claude-3-5-sonnet-20241022 (默认)

🔌 测试连接...
  ℹ️  Using custom API endpoint: https://openrouter.ai/api/v1
  ✅ 连接成功!

✅ 初始化完成!
```

### 4. 使用 Code Agent

```bash
# 规划功能
code-agent plan my-feature --description "实现用户登录功能"

# 执行开发
code-agent run my-feature
```

---

## 可用模型

OpenRouter 支持多种 Claude 模型：

| 模型名称 | 环境变量值 | 说明 |
|---------|-----------|------|
| Claude 3.5 Sonnet | `anthropic/claude-3.5-sonnet` | 推荐，平衡性能和成本 |
| Claude 3 Opus | `anthropic/claude-3-opus` | 最高性能 |
| Claude 3 Sonnet | `anthropic/claude-3-sonnet` | 中等性能 |
| Claude 3 Haiku | `anthropic/claude-3-haiku` | 快速且经济 |

**设置方法**:

```bash
export CLAUDE_MODEL='anthropic/claude-3.5-sonnet'
```

**注意**: 不同模型的定价不同，请查看 [OpenRouter Pricing](https://openrouter.ai/docs/pricing)

---

## 故障排查

### 问题 1: API Key 未被识别

**症状**:

```
❌ API key not found. Set one of:
  export ANTHROPIC_API_KEY='sk-ant-xxx'
  ...
```

**解决方法**:

```bash
# 检查环境变量是否设置
echo $ANTHROPIC_AUTH_TOKEN

# 如果为空，重新设置
export ANTHROPIC_AUTH_TOKEN='sk-or-v1-xxxxxxxxxxxxx'

# 验证
code-agent init
```

### 问题 2: 连接失败

**症状**:

```
❌ Connection failed: HTTP 401 Unauthorized
```

**可能原因**:
1. API Key 无效或过期
2. OpenRouter 账户余额不足
3. API Key 权限不足

**解决方法**:

```bash
# 1. 验证 API Key 格式
echo $ANTHROPIC_AUTH_TOKEN
# 应该以 'sk-or-v1-' 开头

# 2. 检查 OpenRouter 账户状态
# 访问 https://openrouter.ai/account

# 3. 重新生成 API Key
# 在 OpenRouter Settings → API Keys 中重新创建
```

### 问题 3: 错误的 Base URL

**症状**:

```
❌ Connection failed: 404 Not Found
```

**解决方法**:

```bash
# 确保使用正确的 Base URL
export ANTHROPIC_BASE_URL='https://openrouter.ai/api/v1'

# 注意: 不要使用 /v1/messages 等子路径
```

### 问题 4: 模型不可用

**症状**:

```
❌ Model not available: claude-3-5-sonnet-20241022
```

**解决方法**:

```bash
# OpenRouter 使用不同的模型命名
export CLAUDE_MODEL='anthropic/claude-3.5-sonnet'

# 或不指定模型，使用默认值
unset CLAUDE_MODEL
```

---

## 与 Anthropic 官方 API 的区别

| 特性 | Anthropic 官方 | OpenRouter |
|------|---------------|-----------|
| API Key 格式 | `sk-ant-xxx` | `sk-or-v1-xxx` |
| 环境变量名 | `ANTHROPIC_API_KEY` | `ANTHROPIC_AUTH_TOKEN` 或 `OPENROUTER_API_KEY` |
| Base URL | `https://api.anthropic.com` | `https://openrouter.ai/api/v1` |
| 模型名称 | `claude-3-5-sonnet-20241022` | `anthropic/claude-3.5-sonnet` |
| 计费方式 | 预付费 | 按使用付费 |
| 支持模型 | 仅 Claude 系列 | 支持多种模型 (Claude, GPT, Gemini 等) |

---

## 费用估算

OpenRouter 的 Claude 3.5 Sonnet 定价（2026-02-10）：

- **Input**: $3.00 / 1M tokens
- **Output**: $15.00 / 1M tokens

**典型使用场景**:

| 任务 | 预估 Tokens | 预估费用 |
|-----|-----------|---------|
| Plan 命令 | 5K input + 2K output | ~$0.05 |
| Run 单个 Phase | 10K input + 5K output | ~$0.11 |
| 完整 7 Phases | 70K input + 35K output | ~$0.77 |

**注意**: 实际费用取决于项目规模和复杂度。

---

## 最佳实践

### 1. 环境变量管理

✅ **推荐做法**:

```bash
# 使用专门的配置文件管理不同项目
# ~/.config/code-agent/openrouter.env
ANTHROPIC_AUTH_TOKEN=sk-or-v1-xxxxxxxxxxxxx
ANTHROPIC_BASE_URL=https://openrouter.ai/api/v1
CLAUDE_MODEL=anthropic/claude-3.5-sonnet

# 在 shell 配置中加载
# ~/.bashrc
if [ -f ~/.config/code-agent/openrouter.env ]; then
    set -a
    source ~/.config/code-agent/openrouter.env
    set +a
fi
```

### 2. 安全性

⚠️ **注意事项**:

- ❌ 不要将 API Key 提交到 Git 仓库
- ❌ 不要在公开的文档中分享 API Key
- ✅ 使用环境变量或密钥管理工具
- ✅ 定期轮换 API Key
- ✅ 为不同项目使用不同的 API Key

### 3. 成本控制

💰 **建议**:

- 使用 `--dry-run` 模式测试流程
- 使用 `--phase N` 逐步执行而非一次性全部执行
- 在 OpenRouter 设置使用限额
- 定期检查 OpenRouter 账单

---

## 相关链接

- [OpenRouter 官网](https://openrouter.ai/)
- [OpenRouter 文档](https://openrouter.ai/docs)
- [OpenRouter 定价](https://openrouter.ai/docs/pricing)
- [Code Agent README](README.md)
- [Code Agent 测试指南](TESTING_GUIDE.md)

---

## 获取帮助

如果遇到问题：

1. 查看 [TESTING_GUIDE.md](TESTING_GUIDE.md) 的故障排查部分
2. 运行 `code-agent init` 验证配置
3. 启用调试日志: `export RUST_LOG=debug`
4. 提交 Issue 到 GitHub 仓库

---

**更新日期**: 2026-02-10  
**维护者**: Code Agent Team
