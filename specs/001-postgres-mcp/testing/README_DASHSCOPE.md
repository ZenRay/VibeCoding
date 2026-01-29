# 使用阿里百炼（通义千问）

PostgreSQL MCP Server 支持任何 OpenAI 兼容的 API 服务。

## 方法 1: 修改配置文件（推荐）

编辑 `config/config.yaml`，取消注释阿里百炼配置：

```yaml
openai:
  api_key_env_var: "OPENAI_API_KEY"
  
  # 取消注释这两行，注释掉 OpenAI 配置
  model: "qwen-turbo"
  base_url: "https://dashscope.aliyuncs.com/compatible-mode/v1"
  
  temperature: 0.0
  max_tokens: 2000
  timeout: 30.0
```

## 方法 2: 使用环境变量

保持配置文件不变，通过环境变量覆盖:
```bash
export OPENAI_API_KEY="sk-your-dashscope-key"
export OPENAI_BASE_URL="https://dashscope.aliyuncs.com/compatible-mode/v1"
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

## 获取 API Key

- **阿里百炼**: https://bailian.console.aliyun.com/
- **OpenAI**: https://platform.openai.com/

## 优势

- ✅ 成本更低（比 OpenAI 便宜 70%+）
- ✅ 中文支持更好
- ✅ 国内直连，无需代理
