# OpenRouter 和第三方 API 支持方案

## 问题分析

当前的 `ClaudeAgent` 实现使用 `claude-agent-sdk-rs` 0.6.4，该 SDK 直接调用 Anthropic 官方 API，**不支持**自定义 API endpoint（如 OpenRouter）。

### 当前限制

1. **SDK 限制**: `claude-agent-sdk-rs` 没有提供设置自定义 base URL 的接口
2. **api_url 未使用**: `AgentConfig.api_url` 字段存在但未被使用
3. **硬编码环境变量**: 只设置 `ANTHROPIC_API_KEY`，无法指定自定义 endpoint

## 解决方案

### 方案 1: 使用 HTTP 客户端直接调用（推荐）⭐

**优点**:
- 完全控制 API endpoint
- 支持任何兼容 Claude API 的服务（OpenRouter, Azure, etc.）
- 可以自定义请求头和参数

**缺点**:
- 需要实现自己的 API 客户端
- 失去 SDK 提供的便利功能（tool calling 等）

**实现步骤**:

1. 添加依赖到 `crates/ca-core/Cargo.toml`:
```toml
[dependencies]
reqwest = { version = "0.12", features = ["json", "stream"] }
```

2. 创建 `crates/ca-core/src/agent/claude_api_client.rs`:
```rust
use reqwest::Client;
use serde::{Deserialize, Serialize};

#[derive(Debug, Serialize)]
pub struct ClaudeApiRequest {
    pub model: String,
    pub messages: Vec<Message>,
    pub max_tokens: u32,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub system: Option<String>,
}

#[derive(Debug, Deserialize)]
pub struct ClaudeApiResponse {
    pub id: String,
    pub content: Vec<ContentBlock>,
    pub model: String,
    pub usage: Usage,
}

pub struct ClaudeApiClient {
    client: Client,
    api_key: String,
    base_url: String,
}

impl ClaudeApiClient {
    pub fn new(api_key: String, base_url: Option<String>) -> Self {
        let base_url = base_url.unwrap_or_else(|| {
            "https://api.anthropic.com/v1".to_string()
        });
        
        Self {
            client: Client::new(),
            api_key,
            base_url,
        }
    }
    
    /// 支持 OpenRouter
    pub fn new_openrouter(api_key: String) -> Self {
        Self::new(
            api_key,
            Some("https://openrouter.ai/api/v1".to_string()),
        )
    }
    
    pub async fn complete(&self, request: ClaudeApiRequest) -> Result<ClaudeApiResponse> {
        let url = format!("{}/messages", self.base_url);
        
        let response = self.client
            .post(&url)
            .header("x-api-key", &self.api_key)
            .header("anthropic-version", "2023-06-01")
            .json(&request)
            .send()
            .await?
            .json::<ClaudeApiResponse>()
            .await?;
        
        Ok(response)
    }
}
```

3. 修改 `ClaudeAgent` 支持自定义 API client:
```rust
pub struct ClaudeAgent {
    api_client: Option<ClaudeApiClient>,  // 新增
    options: ClaudeAgentOptions,
    // ...
}

impl ClaudeAgent {
    pub fn new_with_endpoint(
        api_key: String,
        model: String,
        api_url: Option<String>,
    ) -> Result<Self> {
        let api_client = if api_url.is_some() {
            Some(ClaudeApiClient::new(api_key.clone(), api_url))
        } else {
            None
        };
        
        // ... 原有逻辑
    }
    
    async fn execute_simple(&self, prompt: &str) -> Result<AgentResponse> {
        if let Some(client) = &self.api_client {
            // 使用自定义 API client
            self.execute_with_custom_client(client, prompt).await
        } else {
            // 使用 SDK (原有逻辑)
            // ...
        }
    }
}
```

### 方案 2: 环境变量设置（简单但有限）

适用于 OpenRouter 等兼容 Anthropic SDK 的服务。

**实现**:

1. 添加环境变量支持到 `config.rs`:
```rust
impl Config {
    pub fn from_env() -> Result<Self> {
        let agent_type = Self::detect_agent_type();
        let api_key = Self::load_api_key(&agent_type)?;
        let api_url = Self::load_api_url(&agent_type);  // 新增
        
        Ok(Self {
            agent: AgentConfig {
                agent_type,
                api_key,
                model: Self::load_model(&agent_type),
                api_url,  // 使用加载的 URL
            },
            // ...
        })
    }
    
    fn load_api_url(agent_type: &AgentType) -> Option<String> {
        match agent_type {
            AgentType::Claude => {
                std::env::var("ANTHROPIC_BASE_URL").ok()
                    .or_else(|| std::env::var("CLAUDE_BASE_URL").ok())
            }
            AgentType::Copilot => {
                std::env::var("COPILOT_BASE_URL").ok()
            }
            AgentType::Cursor => {
                std::env::var("CURSOR_BASE_URL").ok()
            }
        }
    }
}
```

2. 在 `ClaudeAgent::new()` 中设置环境变量:
```rust
pub fn new(api_key: String, model: String, api_url: Option<String>) -> Result<Self> {
    // 设置 API key
    std::env::set_var("ANTHROPIC_API_KEY", &api_key);
    
    // 设置自定义 base URL (如果提供)
    if let Some(url) = api_url {
        std::env::set_var("ANTHROPIC_BASE_URL", url);
    }
    
    // ...
}
```

**局限性**: 这取决于 `claude-agent-sdk-rs` 是否支持 `ANTHROPIC_BASE_URL` 环境变量（需要检查 SDK 文档）。

### 方案 3: Fork SDK 并修改（不推荐）

修改 `claude-agent-sdk-rs` 源码以支持自定义 endpoint。

**缺点**:
- 需要维护 fork
- 升级困难
- 不适合长期维护

## OpenRouter 使用示例

### 使用方案 1 (HTTP 客户端):

```bash
# 设置 OpenRouter API key
export ANTHROPIC_API_KEY='sk-or-v1-xxx'
export ANTHROPIC_BASE_URL='https://openrouter.ai/api/v1'

# 或者使用专用环境变量
export OPENROUTER_API_KEY='sk-or-v1-xxx'

# 使用 code-agent
cd Week8
cargo run -- init --agent claude --api-url https://openrouter.ai/api/v1

# 或在命令行指定
cargo run -- run my-feature --api-url https://openrouter.ai/api/v1
```

### CLI 参数支持:

修改 `apps/ca-cli/src/main.rs`:
```rust
#[derive(Parser)]
#[command(name = "code-agent")]
struct Cli {
    /// API base URL (for OpenRouter, Azure, etc.)
    #[arg(long, global = true)]
    api_url: Option<String>,
    
    // ... 其他参数
}
```

## 推荐实施步骤

### Phase 1: 快速验证（1-2 小时）
1. 添加 `api_url` CLI 参数
2. 修改 `Config::from_env()` 加载 `ANTHROPIC_BASE_URL`
3. 在 `ClaudeAgent::new()` 中设置环境变量
4. 测试是否能工作（取决于 SDK 支持）

### Phase 2: 完整实现（4-6 小时）
如果 Phase 1 不工作:
1. 实现 `ClaudeApiClient`
2. 修改 `ClaudeAgent` 使用自定义客户端
3. 保持与 SDK 的兼容性（双模式）
4. 添加集成测试

### Phase 3: 完善功能（2-3 小时）
1. 支持其他 API 提供商（Azure, Bedrock）
2. 添加 API 兼容性检测
3. 更新文档和示例

## 测试方案

### OpenRouter 测试:

```bash
# 1. 设置环境变量
export OPENROUTER_API_KEY='sk-or-v1-xxx'

# 2. 测试连接
cargo run -- init --api-url https://openrouter.ai/api/v1

# 3. 测试功能
cargo run -- plan test-feature

# 4. 验证输出
cat specs/001-test-feature/0001_feature.md
```

## 参考资源

- **OpenRouter 文档**: https://openrouter.ai/docs
- **Claude API 规范**: https://docs.anthropic.com/claude/reference/messages_post
- **reqwest 文档**: https://docs.rs/reqwest/latest/reqwest/

## 结论

**推荐方案 1 (HTTP 客户端)** 作为长期解决方案，提供最大灵活性。

**短期**: 可以先尝试方案 2 (环境变量)，如果 SDK 支持就很简单。

**实施优先级**: 中等 - 这是一个有用的功能，但不是核心功能的阻塞项。
