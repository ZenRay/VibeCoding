# 使用阿里百炼（通义千问）

PostgreSQL MCP Server 支持任何 OpenAI 兼容的 API 服务，包括阿里云百炼。

## 快速开始

**无需修改任何代码或配置文件**，只需设置环境变量：

### 使用阿里百炼

```bash
export OPENAI_API_KEY="sk-your-dashscope-api-key"
export OPENAI_BASE_URL="https://dashscope.aliyuncs.com/compatible-mode/v1"
python -m postgres_mcp
```

### 使用 OpenAI（默认）

```bash
export OPENAI_API_KEY="sk-your-openai-api-key"
python -m postgres_mcp
```

## 支持的模型

### 阿里百炼
- `qwen-turbo` - 快速、经济
- `qwen-plus` - 平衡性能
- `qwen-max` - 最高质量

### OpenAI
- `gpt-4o-mini` - 快速、经济
- `gpt-4o` - 高性能
- `gpt-3.5-turbo` - 经典

## 获取 API Key

- **阿里百炼**: https://bailian.console.aliyun.com/
- **OpenAI**: https://platform.openai.com/

## 优势

使用阿里百炼：
- ✅ 成本更低（比 OpenAI 便宜 70%+）
- ✅ 中文支持更好
- ✅ 国内直连，无需代理
