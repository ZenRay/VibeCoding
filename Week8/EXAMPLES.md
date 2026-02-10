# Code Agent 使用示例

本文档提供了 Code Agent 的实际使用示例,包括使用不同 API 提供商的场景。

## 基础使用 - Anthropic 官方 API

### 1. 环境设置

```bash
# 设置 API Key
export ANTHROPIC_API_KEY='sk-ant-api03-xxxxxxxxxxxxx'

# 可选: 指定模型
export CLAUDE_MODEL='claude-3-5-sonnet-20241022'
```

### 2. 验证配置

```bash
code-agent init --interactive
```

**输出示例:**

```
🚀 欢迎使用 Code Agent!

🔧 Code Agent 使用零配置文件方案 - 所有配置通过环境变量提供

选择 Agent 类型:
  1. Claude Agent (Tier 1: 完全支持)
  2. Cursor Agent (Tier 2: 基础支持) - 即将推出
  3. GitHub Copilot Agent (Tier 3: 实验性) - 即将推出

请选择 [1-3] (默认: 1): 1

✓ 从环境变量 ANTHROPIC_API_KEY 检测到 API Key
使用此 Key? [Y/n]: y

模型名称 (默认: claude-3-5-sonnet-20241022): 

📋 检测到的配置:
  Agent 类型: Claude
  模型: claude-3-5-sonnet-20241022
  API Key: sk-a***

🔌 测试 Agent 连接...
✅ 连接成功!

🎉 初始化完成! 现在可以运行:
   code-agent plan <feature-name>
   code-agent run <feature-name>
```

### 3. 规划功能

```bash
code-agent plan user-authentication \
  --description "实现基于 JWT 的用户认证系统,包括注册、登录、登出功能"
```

### 4. 执行开发

```bash
code-agent run user-authentication
```

---

## 使用 OpenRouter

OpenRouter 提供了访问多个 AI 模型的统一接口,支持按使用付费。

### 1. 注册 OpenRouter

1. 访问 [https://openrouter.ai/](https://openrouter.ai/)
2. 注册账号
3. 在 Keys 页面创建 API Key

### 2. 配置环境变量

```bash
# 使用 OpenRouter API Key
export ANTHROPIC_API_KEY='sk-or-v1-xxxxxxxxxxxxx'

# 设置 OpenRouter 的 base URL
export ANTHROPIC_BASE_URL='https://openrouter.ai/api/v1'

# 可选: 指定 OpenRouter 上的模型
# OpenRouter 的模型格式: provider/model-name
export CLAUDE_MODEL='anthropic/claude-3.5-sonnet'
```

### 3. 验证连接

```bash
code-agent init
```

**输出示例:**

```
🚀 欢迎使用 Code Agent!

📋 检测到的配置:
  Agent 类型: Claude
  模型: anthropic/claude-3.5-sonnet
  API Key: sk-o***

🔌 测试 Agent 连接...
ℹ️  Using custom API endpoint: https://openrouter.ai/api/v1
✅ 连接成功!
```

### 4. 使用不同模型

OpenRouter 支持多种模型:

```bash
# 使用 Claude 3.5 Sonnet
export CLAUDE_MODEL='anthropic/claude-3.5-sonnet'

# 使用 GPT-4
export CLAUDE_MODEL='openai/gpt-4-turbo-preview'

# 使用 Google Gemini
export CLAUDE_MODEL='google/gemini-pro-1.5'

# 使用 Meta Llama
export CLAUDE_MODEL='meta-llama/llama-3-70b-instruct'
```

### 5. 查看费用 (OpenRouter)

OpenRouter 在响应头中返回费用信息。你可以在 OpenRouter Dashboard 查看详细的使用记录。

---

## 使用 Azure OpenAI

Azure OpenAI 提供企业级的 API 服务。

### 1. Azure 配置

```bash
# Azure OpenAI endpoint
export ANTHROPIC_BASE_URL='https://your-resource-name.openai.azure.com'

# Azure API Key
export ANTHROPIC_API_KEY='your-azure-api-key'

# Azure 部署名称 (作为模型名称)
export CLAUDE_MODEL='your-deployment-name'
```

### 2. 使用

```bash
code-agent plan my-feature --description "添加缓存层"
```

**注意:** Azure OpenAI 的 API 格式可能与标准 OpenAI API 略有不同,可能需要额外的适配。

---

## CLI 参数覆盖

你可以使用 CLI 参数临时覆盖环境变量:

### 覆盖 API URL

```bash
code-agent plan my-feature \
  --api-url https://custom-proxy.example.com/v1 \
  --description "实现功能"
```

### 覆盖模型

```bash
code-agent run my-feature \
  --model anthropic/claude-3-opus
```

### 覆盖 API Key

```bash
code-agent plan my-feature \
  --api-key sk-temp-key-xxxxx \
  --description "测试功能"
```

### 组合使用

```bash
code-agent plan my-feature \
  --api-url https://openrouter.ai/api/v1 \
  --api-key sk-or-v1-xxxxx \
  --model anthropic/claude-3.5-sonnet \
  --description "实现新功能"
```

---

## 高级场景

### 1. 使用代理

如果你在防火墙后面,可以通过 HTTP 代理访问 API:

```bash
# 设置代理
export HTTP_PROXY='http://proxy.example.com:8080'
export HTTPS_PROXY='http://proxy.example.com:8080'

# 然后正常使用
code-agent plan my-feature
```

### 2. 多项目管理

为不同项目使用不同的 API Key:

```bash
# 项目 A (使用 Anthropic)
cd ~/projects/project-a
export ANTHROPIC_API_KEY='sk-ant-project-a-xxx'
unset ANTHROPIC_BASE_URL
code-agent plan feature-a

# 项目 B (使用 OpenRouter)
cd ~/projects/project-b
export ANTHROPIC_API_KEY='sk-or-v1-project-b-xxx'
export ANTHROPIC_BASE_URL='https://openrouter.ai/api/v1'
code-agent plan feature-b
```

### 3. 使用 direnv 自动切换配置

安装 [direnv](https://direnv.net/) 后:

```bash
cd ~/projects/my-project

# 创建 .envrc 文件
cat > .envrc << 'EOF'
export ANTHROPIC_API_KEY='sk-ant-xxx'
export ANTHROPIC_BASE_URL='https://openrouter.ai/api/v1'
export CLAUDE_MODEL='anthropic/claude-3.5-sonnet'
EOF

# 允许加载
direnv allow

# 现在进入目录时会自动加载配置
cd ~/projects/my-project  # 配置自动加载
code-agent plan my-feature
```

---

## 故障排查

### 问题 1: API 连接失败

```bash
❌ 连接测试失败: API key not found
```

**解决方案:**

```bash
# 检查环境变量
echo $ANTHROPIC_API_KEY

# 如果为空,设置它
export ANTHROPIC_API_KEY='sk-ant-xxx'

# 重新验证
code-agent init
```

### 问题 2: 自定义 endpoint 未生效

```bash
# 确认环境变量已设置
echo $ANTHROPIC_BASE_URL

# 使用 CLI 参数强制覆盖
code-agent plan my-feature \
  --api-url https://openrouter.ai/api/v1
```

### 问题 3: OpenRouter 模型未找到

```bash
❌ Model not found: claude-3-5-sonnet-20241022
```

**解决方案:** OpenRouter 使用 `provider/model` 格式:

```bash
export CLAUDE_MODEL='anthropic/claude-3.5-sonnet'
```

### 问题 4: 查看详细日志

```bash
# 启用详细日志
code-agent plan my-feature --verbose
```

---

## 成本优化建议

### 1. 使用合适的模型

不同模型的成本差异很大:

| 模型 | 适用场景 | 相对成本 |
|------|----------|----------|
| `claude-3-haiku` | 简单任务、快速响应 | 💰 低 |
| `claude-3.5-sonnet` | 平衡性能和成本 | 💰💰 中 |
| `claude-3-opus` | 复杂任务、高质量 | 💰💰💰 高 |

```bash
# 简单任务使用 Haiku
export CLAUDE_MODEL='claude-3-haiku-20240307'
code-agent plan simple-feature

# 复杂任务使用 Sonnet
export CLAUDE_MODEL='claude-3-5-sonnet-20241022'
code-agent plan complex-feature
```

### 2. 使用 OpenRouter 的成本控制

OpenRouter 允许你设置预算限制和模型回退策略。

### 3. 监控使用量

定期检查 API 使用情况:

- Anthropic: https://console.anthropic.com/settings/usage
- OpenRouter: https://openrouter.ai/activity

---

## 完整示例: 从零开始

```bash
# 1. 安装 Code Agent
cd ~/Documents/VibeCoding/Week8
cargo build --release
sudo cp target/release/code-agent /usr/local/bin/

# 2. 配置环境 (使用 OpenRouter)
cat >> ~/.bashrc << 'EOF'
export ANTHROPIC_API_KEY='sk-or-v1-xxxxxxxxxxxxx'
export ANTHROPIC_BASE_URL='https://openrouter.ai/api/v1'
export CLAUDE_MODEL='anthropic/claude-3.5-sonnet'
EOF
source ~/.bashrc

# 3. 验证配置
code-agent init

# 4. 进入项目目录
cd ~/my-project

# 5. 规划功能
code-agent plan user-profile \
  --description "实现用户个人资料页面,支持头像上传、信息编辑和隐私设置"

# 6. 查看生成的规划文档
ls specs/001-user-profile/
# 输出: spec.md, design.md, plan.md, tasks.md

# 7. 执行开发
code-agent run user-profile

# 8. 如果中断,可以恢复
code-agent run user-profile --resume

# 9. 完成后查看生成的代码和文档
ls specs/001-user-profile/.ca-state/
```

---

## 参考链接

- **Anthropic Claude API**: https://docs.anthropic.com/
- **OpenRouter**: https://openrouter.ai/docs
- **Azure OpenAI**: https://learn.microsoft.com/azure/ai-services/openai/
- **Code Agent GitHub**: (待添加)

---

**提示:** 如果你有任何问题或建议,请提交 Issue 或 Pull Request!
