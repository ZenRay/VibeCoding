# OpenRouter 支持 - 快速参考

## 一分钟快速开始

```bash
# 1. 设置环境变量
export ANTHROPIC_API_KEY='sk-or-v1-xxxxxxxxxxxxx'
export ANTHROPIC_BASE_URL='https://openrouter.ai/api/v1'

# 2. 验证
code-agent init

# 3. 使用
code-agent plan my-feature --description "你的功能描述"
```

## 支持的环境变量

| 环境变量 | 用途 | 示例 |
|---------|------|------|
| `ANTHROPIC_API_KEY` | API 密钥 | `sk-or-v1-xxx` 或 `sk-ant-xxx` |
| `ANTHROPIC_BASE_URL` | API endpoint | `https://openrouter.ai/api/v1` |
| `CLAUDE_MODEL` | 模型名称 | `anthropic/claude-3.5-sonnet` |

## CLI 参数

```bash
code-agent [COMMAND] [OPTIONS]
  --api-url <URL>      # 覆盖 API endpoint
  --api-key <KEY>      # 覆盖 API key
  --model <MODEL>      # 覆盖模型名称
```

## 常见用例

### OpenRouter

```bash
export ANTHROPIC_API_KEY='sk-or-v1-xxx'
export ANTHROPIC_BASE_URL='https://openrouter.ai/api/v1'
export CLAUDE_MODEL='anthropic/claude-3.5-sonnet'
```

### Anthropic 官方 (默认)

```bash
export ANTHROPIC_API_KEY='sk-ant-xxx'
# 不需要设置 BASE_URL
```

### Azure OpenAI

```bash
export ANTHROPIC_BASE_URL='https://your-resource.openai.azure.com'
export ANTHROPIC_API_KEY='your-azure-key'
export CLAUDE_MODEL='your-deployment-name'
```

### 临时测试

```bash
code-agent plan test --api-url https://test.api.com --api-key test-key
```

## 配置优先级

```
CLI 参数 > 环境变量 > 配置文件 > 默认值
```

## 故障排查

### 问题: 连接失败

```bash
# 检查环境变量
echo $ANTHROPIC_API_KEY
echo $ANTHROPIC_BASE_URL

# 使用 --verbose 查看详细日志
code-agent plan test --verbose
```

### 问题: OpenRouter 模型格式

OpenRouter 使用 `provider/model-name` 格式:

```bash
# ✅ 正确
export CLAUDE_MODEL='anthropic/claude-3.5-sonnet'

# ❌ 错误
export CLAUDE_MODEL='claude-3-5-sonnet-20241022'
```

## 文档链接

- **详细示例:** `EXAMPLES.md`
- **技术实现:** `OPENROUTER_SUPPORT.md`
- **完整报告:** `IMPLEMENTATION_REPORT.md`
- **项目 README:** `README.md`

## 测试状态

- ✅ 单元测试: 21/21 通过
- ✅ Clippy: 0 warnings
- ✅ 构建: 成功

## 版本信息

- **实施日期:** 2026-02-10
- **功能版本:** v0.2.0 (OpenRouter 支持)
- **Commit:** df182a7
