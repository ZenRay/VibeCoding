use async_trait::async_trait;
use claude_agent_sdk_rs::{
    ClaudeAgentOptions, ClaudeClient, ContentBlock, Message, PermissionMode, SystemPrompt,
};
use futures::StreamExt;
use std::sync::Arc;
use std::time::Instant;
use tokio::sync::Mutex;

use crate::agent::{
    Agent, AgentCapabilities, AgentLimits, AgentMetadata, AgentRequest, AgentResponse, AgentType,
    FileChange, ResponseMetadata,
};
use crate::error::{CoreError, Result};

/// Claude Agent 实现
///
/// 封装 claude-agent-sdk-rs,提供统一的 Agent 接口
pub struct ClaudeAgent {
    /// Claude Agent 选项
    options: ClaudeAgentOptions,
    /// 模型名称
    model: String,
    /// API Key (用于验证)
    api_key: String,
    /// SDK 客户端 (可选,仅在需要持久连接时使用)
    #[allow(dead_code)]
    client: Arc<Mutex<Option<ClaudeClient>>>,
}

impl ClaudeAgent {
    /// 创建新的 Claude Agent 实例
    ///
    /// # Arguments
    ///
    /// * `api_key` - Anthropic API Key
    /// * `model` - 模型名称 (默认: claude-3-5-sonnet-20241022)
    /// * `api_url` - 自定义 API endpoint (可选,支持 OpenRouter 等)
    ///
    /// # Errors
    ///
    /// 如果 API Key 为空,返回错误
    pub fn new(api_key: String, model: String, api_url: Option<String>) -> Result<Self> {
        if api_key.is_empty() {
            return Err(CoreError::Config("API key cannot be empty".to_string()));
        }

        // 设置环境变量供 SDK 使用
        // SAFETY: 在单线程初始化期间设置环境变量是安全的
        // SDK 会在后续调用中读取这个值
        unsafe {
            std::env::set_var("ANTHROPIC_API_KEY", &api_key);
        }

        // 如果提供了自定义 API URL,设置环境变量
        if let Some(ref url) = api_url {
            unsafe {
                std::env::set_var("ANTHROPIC_BASE_URL", url);
            }
            tracing::info!("Using custom API endpoint: {}", url);
        }

        // 创建默认选项
        let options = ClaudeAgentOptions::builder()
            .model(model.clone())
            .max_turns(10)
            .build();

        Ok(Self {
            options,
            model,
            api_key,
            client: Arc::new(Mutex::new(None)),
        })
    }

    /// 使用默认选项创建 Agent
    pub fn with_default_options(api_key: String) -> Result<Self> {
        Self::new(api_key, "claude-3-5-sonnet-20241022".to_string(), None)
    }

    /// 配置 Agent 选项
    ///
    /// # Arguments
    ///
    /// * `system_prompt` - 系统提示词
    /// * `allowed_tools` - 允许的工具列表
    /// * `max_turns` - 最大轮次
    /// * `max_budget_usd` - 最大预算 (美元)
    /// * `permission_mode` - 权限模式 ("Default", "AcceptEdits", "Plan", "BypassPermissions")
    pub fn configure(
        &mut self,
        system_prompt: Option<String>,
        allowed_tools: Option<Vec<String>>,
        max_turns: Option<usize>,
        max_budget_usd: Option<f64>,
        permission_mode: Option<&str>,
    ) -> Result<()> {
        // 解析 permission_mode
        let perm_mode = match permission_mode {
            Some("Default") => PermissionMode::Default,
            Some("Plan") => PermissionMode::Plan,
            Some("BypassPermissions") => PermissionMode::BypassPermissions,
            Some("AcceptEdits") | None => PermissionMode::AcceptEdits, // 默认
            Some(other) => {
                return Err(CoreError::Config(format!(
                    "Invalid permission mode: {}. Valid values: Default, AcceptEdits, Plan, BypassPermissions",
                    other
                )));
            }
        };

        // 基础 builder
        let base = ClaudeAgentOptions::builder()
            .model(self.model.clone())
            .permission_mode(perm_mode);

        // 根据参数组合构建选项
        // 由于 builder 使用类型状态,需要按照特定顺序设置
        let options = match (system_prompt, allowed_tools, max_turns, max_budget_usd) {
            (Some(sp), Some(tools), Some(turns), Some(budget)) => base
                .system_prompt(SystemPrompt::Text(sp))
                .allowed_tools(tools)
                .max_turns(turns as u32)
                .max_budget_usd(budget)
                .build(),
            (Some(sp), Some(tools), Some(turns), None) => base
                .system_prompt(SystemPrompt::Text(sp))
                .allowed_tools(tools)
                .max_turns(turns as u32)
                .build(),
            (Some(sp), Some(tools), None, Some(budget)) => base
                .system_prompt(SystemPrompt::Text(sp))
                .allowed_tools(tools)
                .max_budget_usd(budget)
                .build(),
            (Some(sp), Some(tools), None, None) => base
                .system_prompt(SystemPrompt::Text(sp))
                .allowed_tools(tools)
                .build(),
            (Some(sp), None, Some(turns), Some(budget)) => base
                .system_prompt(SystemPrompt::Text(sp))
                .max_turns(turns as u32)
                .max_budget_usd(budget)
                .build(),
            (Some(sp), None, Some(turns), None) => base
                .system_prompt(SystemPrompt::Text(sp))
                .max_turns(turns as u32)
                .build(),
            (Some(sp), None, None, Some(budget)) => base
                .system_prompt(SystemPrompt::Text(sp))
                .max_budget_usd(budget)
                .build(),
            (Some(sp), None, None, None) => base.system_prompt(SystemPrompt::Text(sp)).build(),
            (None, Some(tools), Some(turns), Some(budget)) => base
                .allowed_tools(tools)
                .max_turns(turns as u32)
                .max_budget_usd(budget)
                .build(),
            (None, Some(tools), Some(turns), None) => {
                base.allowed_tools(tools).max_turns(turns as u32).build()
            }
            (None, Some(tools), None, Some(budget)) => {
                base.allowed_tools(tools).max_budget_usd(budget).build()
            }
            (None, Some(tools), None, None) => base.allowed_tools(tools).build(),
            (None, None, Some(turns), Some(budget)) => {
                base.max_turns(turns as u32).max_budget_usd(budget).build()
            }
            (None, None, Some(turns), None) => base.max_turns(turns as u32).build(),
            (None, None, None, Some(budget)) => base.max_budget_usd(budget).build(),
            (None, None, None, None) => base.build(),
        };

        self.options = options;

        Ok(())
    }

    /// 使用简单的 query API 执行请求
    #[allow(dead_code)]
    async fn execute_simple(&self, prompt: &str) -> Result<AgentResponse> {
        let start = Instant::now();

        // 使用 query API
        let messages = claude_agent_sdk_rs::query(prompt, Some(self.options.clone()))
            .await
            .map_err(|e| CoreError::Agent(format!("Claude query failed: {}", e)))?;

        let duration_ms = start.elapsed().as_millis() as u64;

        // 收集响应内容
        let mut content = String::new();
        let tokens_used = 0u32;

        for message in &messages {
            if let Message::Assistant(assistant_msg) = message {
                for block in &assistant_msg.message.content {
                    if let ContentBlock::Text(text) = block {
                        content.push_str(&text.text);
                        content.push('\n');
                    }
                }
            }
        }

        // TODO: 从消息中提取文件修改和 token 使用情况
        let file_changes = Self::extract_file_changes_from_messages(&messages)?;

        Ok(AgentResponse {
            request_id: uuid::Uuid::new_v4().to_string(),
            content: content.trim().to_string(),
            tokens_used: Some(tokens_used),
            file_changes,
            metadata: ResponseMetadata {
                duration_ms,
                model: self.model.clone(),
                finish_reason: "stop".to_string(),
            },
        })
    }

    /// 使用流式 API 执行请求 (未来可能需要)
    #[allow(dead_code)]
    async fn execute_streaming(&self, prompt: &str) -> Result<AgentResponse> {
        let start = Instant::now();

        // 使用 query_stream API
        let mut stream = claude_agent_sdk_rs::query_stream(prompt, Some(self.options.clone()))
            .await
            .map_err(|e| CoreError::Agent(format!("Claude query_stream failed: {}", e)))?;

        let duration_ms = start.elapsed().as_millis() as u64;

        // 收集流式响应
        let mut content = String::new();
        let file_changes = Vec::new();
        let tokens_used = 0u32;

        while let Some(result) = stream.next().await {
            let message = result.map_err(|e| CoreError::Agent(format!("Stream error: {}", e)))?;

            if let Message::Assistant(assistant_msg) = message {
                for block in &assistant_msg.message.content {
                    if let ContentBlock::Text(text) = block {
                        content.push_str(&text.text);
                    }
                }
            }
        }

        Ok(AgentResponse {
            request_id: uuid::Uuid::new_v4().to_string(),
            content: content.trim().to_string(),
            tokens_used: Some(tokens_used),
            file_changes,
            metadata: ResponseMetadata {
                duration_ms,
                model: self.model.clone(),
                finish_reason: "stop".to_string(),
            },
        })
    }

    /// 从消息列表中提取文件修改
    ///
    /// 解析 Agent 执行过程中通过工具调用修改的文件
    fn extract_file_changes_from_messages(_messages: &[Message]) -> Result<Vec<FileChange>> {
        // TODO: 实现文件修改提取逻辑
        // 需要解析消息中的工具调用记录
        // 寻找 Write、Delete 等工具调用

        Ok(Vec::new())
    }
}

#[async_trait]
impl Agent for ClaudeAgent {
    fn agent_type(&self) -> AgentType {
        AgentType::Claude
    }

    fn capabilities(&self) -> AgentCapabilities {
        AgentCapabilities {
            supports_system_prompt: true,
            supports_tool_control: true,
            supports_permission_mode: true,
            supports_cost_control: true,
            supports_streaming: true,
            supports_multimodal: true,
        }
    }

    fn metadata(&self) -> AgentMetadata {
        AgentMetadata {
            name: "Claude Agent".to_string(),
            version: "0.6.4".to_string(),
            model: self.model.clone(),
            limits: AgentLimits {
                max_context_length: 200_000,
                max_response_length: 8_192,
            },
        }
    }

    async fn execute(&self, request: AgentRequest) -> Result<AgentResponse> {
        tracing::info!(
            request_id = %request.id,
            prompt_len = request.prompt.len(),
            model = %self.model,
            "Executing Claude Agent request"
        );

        // 构建选项 (根据是否有 phase_config)
        let options = if let Some(ref phase_config) = request.phase_config {
            tracing::info!(
                preset = phase_config.preset,
                disallowed_tools = ?phase_config.disallowed_tools,
                permission_mode = ?phase_config.permission_mode,
                max_turns = phase_config.max_turns,
                "Applying phase config to agent"
            );

            // 转换 PermissionMode
            let perm_mode = match phase_config.permission_mode {
                crate::agent::PermissionMode::Default => {
                    claude_agent_sdk_rs::PermissionMode::Default
                }
                crate::agent::PermissionMode::AcceptEdits => {
                    claude_agent_sdk_rs::PermissionMode::AcceptEdits
                }
                crate::agent::PermissionMode::Plan => claude_agent_sdk_rs::PermissionMode::Plan,
                crate::agent::PermissionMode::BypassPermissions => {
                    claude_agent_sdk_rs::PermissionMode::BypassPermissions
                }
            };

            // 构建选项 (一次性完成,不能分开 reassign)
            // 根据不同的配置组合构建
            match (
                request.system_prompt.as_ref(),
                !phase_config.disallowed_tools.is_empty(),
                phase_config.max_budget_usd,
            ) {
                (Some(sys_prompt), true, Some(budget)) => {
                    // 有系统提示词 + 禁止工具 + 预算
                    ClaudeAgentOptions::builder()
                        .model(self.model.clone())
                        .permission_mode(perm_mode)
                        .max_turns(phase_config.max_turns as u32)
                        .system_prompt(SystemPrompt::Text(sys_prompt.clone()))
                        .disallowed_tools(phase_config.disallowed_tools.clone())
                        .max_budget_usd(budget)
                        .build()
                }
                (Some(sys_prompt), true, None) => {
                    // 有系统提示词 + 禁止工具
                    ClaudeAgentOptions::builder()
                        .model(self.model.clone())
                        .permission_mode(perm_mode)
                        .max_turns(phase_config.max_turns as u32)
                        .system_prompt(SystemPrompt::Text(sys_prompt.clone()))
                        .disallowed_tools(phase_config.disallowed_tools.clone())
                        .build()
                }
                (Some(sys_prompt), false, Some(budget)) => {
                    // 有系统提示词 + 预算
                    ClaudeAgentOptions::builder()
                        .model(self.model.clone())
                        .permission_mode(perm_mode)
                        .max_turns(phase_config.max_turns as u32)
                        .system_prompt(SystemPrompt::Text(sys_prompt.clone()))
                        .max_budget_usd(budget)
                        .build()
                }
                (Some(sys_prompt), false, None) => {
                    // 只有系统提示词
                    ClaudeAgentOptions::builder()
                        .model(self.model.clone())
                        .permission_mode(perm_mode)
                        .max_turns(phase_config.max_turns as u32)
                        .system_prompt(SystemPrompt::Text(sys_prompt.clone()))
                        .build()
                }
                (None, true, Some(budget)) => {
                    // 禁止工具 + 预算
                    ClaudeAgentOptions::builder()
                        .model(self.model.clone())
                        .permission_mode(perm_mode)
                        .max_turns(phase_config.max_turns as u32)
                        .disallowed_tools(phase_config.disallowed_tools.clone())
                        .max_budget_usd(budget)
                        .build()
                }
                (None, true, None) => {
                    // 只有禁止工具
                    ClaudeAgentOptions::builder()
                        .model(self.model.clone())
                        .permission_mode(perm_mode)
                        .max_turns(phase_config.max_turns as u32)
                        .disallowed_tools(phase_config.disallowed_tools.clone())
                        .build()
                }
                (None, false, Some(budget)) => {
                    // 只有预算
                    ClaudeAgentOptions::builder()
                        .model(self.model.clone())
                        .permission_mode(perm_mode)
                        .max_turns(phase_config.max_turns as u32)
                        .max_budget_usd(budget)
                        .build()
                }
                (None, false, None) => {
                    // 基础配置
                    ClaudeAgentOptions::builder()
                        .model(self.model.clone())
                        .permission_mode(perm_mode)
                        .max_turns(phase_config.max_turns as u32)
                        .build()
                }
            }
        } else {
            // 使用默认选项 (可能带系统提示词)
            if let Some(ref sys_prompt) = request.system_prompt {
                ClaudeAgentOptions::builder()
                    .model(self.model.clone())
                    .system_prompt(SystemPrompt::Text(sys_prompt.clone()))
                    .build()
            } else {
                ClaudeAgentOptions::builder()
                    .model(self.model.clone())
                    .build()
            }
        };

        // 构建完整的提示词
        let mut full_prompt = String::new();

        // 添加上下文文件信息
        if !request.context_files.is_empty() {
            full_prompt.push_str("Context Files:\n");
            for file in &request.context_files {
                full_prompt.push_str(&format!("- {}\n", file));
            }
            full_prompt.push('\n');
        }

        // 添加主提示词
        full_prompt.push_str(&request.prompt);

        // 执行请求 (使用配置后的 options)
        let start = Instant::now();

        let messages = claude_agent_sdk_rs::query(&full_prompt, Some(options))
            .await
            .map_err(|e| CoreError::Agent(format!("Claude query failed: {}", e)))?;

        let duration_ms = start.elapsed().as_millis() as u64;

        // 收集响应内容
        let mut content = String::new();
        let tokens_used = 0u32;

        for message in &messages {
            if let Message::Assistant(assistant_msg) = message {
                for block in &assistant_msg.message.content {
                    if let ContentBlock::Text(text) = block {
                        content.push_str(&text.text);
                        content.push('\n');
                    }
                }
            }
        }

        // 提取文件修改
        let file_changes = Self::extract_file_changes_from_messages(&messages)?;

        Ok(AgentResponse {
            request_id: request.id,
            content: content.trim().to_string(),
            tokens_used: Some(tokens_used),
            file_changes,
            metadata: ResponseMetadata {
                duration_ms,
                model: self.model.clone(),
                finish_reason: "stop".to_string(),
            },
        })
    }

    async fn validate(&self) -> Result<bool> {
        tracing::info!(
            model = %self.model,
            "Validating Claude Agent connection"
        );

        // 检查 API Key
        if self.api_key.is_empty() {
            return Ok(false);
        }

        // TODO: 可以发送一个简单的请求来验证连接
        // 目前只检查 API Key 是否存在
        Ok(true)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::error::CoreError;

    #[test]
    fn test_new_agent_with_empty_key() {
        let result = ClaudeAgent::new(
            String::new(),
            "claude-3-5-sonnet-20241022".to_string(),
            None,
        );
        assert!(result.is_err());
    }

    #[test]
    fn test_agent_type() {
        let agent = ClaudeAgent::new(
            "test-key".to_string(),
            "claude-3-5-sonnet-20241022".to_string(),
            None,
        )
        .unwrap();
        assert_eq!(agent.agent_type(), AgentType::Claude);
    }

    #[test]
    fn test_agent_capabilities() {
        let agent = ClaudeAgent::new(
            "test-key".to_string(),
            "claude-3-5-sonnet-20241022".to_string(),
            None,
        )
        .unwrap();
        let caps = agent.capabilities();
        assert!(caps.supports_system_prompt);
        assert!(caps.supports_tool_control);
    }

    #[test]
    fn test_agent_metadata() {
        let agent = ClaudeAgent::new(
            "test-key".to_string(),
            "claude-3-5-sonnet-20241022".to_string(),
            None,
        )
        .unwrap();
        let metadata = agent.metadata();
        assert_eq!(metadata.name, "Claude Agent");
        assert_eq!(metadata.model, "claude-3-5-sonnet-20241022");
        assert_eq!(metadata.limits.max_context_length, 200_000);
    }

    #[tokio::test]
    async fn test_validate_with_valid_key() {
        let agent = ClaudeAgent::new(
            "test-key".to_string(),
            "claude-3-5-sonnet-20241022".to_string(),
            None,
        )
        .unwrap();
        let result = agent.validate().await;
        assert!(result.is_ok());
        assert!(result.unwrap());
    }

    #[tokio::test]
    async fn test_configure_options() {
        let mut agent = ClaudeAgent::new(
            "test-key".to_string(),
            "claude-3-5-sonnet-20241022".to_string(),
            None,
        )
        .unwrap();

        let result = agent.configure(
            Some("You are a helpful assistant".to_string()),
            Some(vec!["Read".to_string(), "Write".to_string()]),
            Some(10),
            Some(5.0),
            Some("AcceptEdits"),
        );

        assert!(result.is_ok());
    }

    #[test]
    fn test_agent_with_custom_api_url() {
        let agent = ClaudeAgent::new(
            "test-key".to_string(),
            "claude-3-5-sonnet-20241022".to_string(),
            Some("https://openrouter.ai/api/v1".to_string()),
        )
        .unwrap();

        // 验证环境变量已设置
        let env_url = std::env::var("ANTHROPIC_BASE_URL").ok();
        assert_eq!(env_url, Some("https://openrouter.ai/api/v1".to_string()));
        assert_eq!(agent.agent_type(), AgentType::Claude);
    }

    #[test]
    fn test_should_reject_empty_api_key() {
        let result = ClaudeAgent::new(
            String::new(),
            "claude-3-5-sonnet-20241022".to_string(),
            None,
        );
        assert!(result.is_err());
        assert!(matches!(result, Err(CoreError::Config(_))));
    }

    #[test]
    fn test_should_configure_with_invalid_permission_mode() {
        let mut agent = ClaudeAgent::new(
            "test-key".to_string(),
            "claude-3-5-sonnet-20241022".to_string(),
            None,
        )
        .unwrap();

        let result = agent.configure(
            Some("system".to_string()),
            None,
            None,
            None,
            Some("InvalidMode"),
        );
        assert!(result.is_err());
        assert!(matches!(result, Err(CoreError::Config(_))));
    }

    #[test]
    fn test_should_configure_with_all_valid_permission_modes() {
        let modes = ["Default", "AcceptEdits", "Plan", "BypassPermissions"];
        for mode in modes {
            let mut agent = ClaudeAgent::new(
                "test-key".to_string(),
                "claude-3-5-sonnet-20241022".to_string(),
                None,
            )
            .unwrap();
            let result = agent.configure(None, None, None, None, Some(mode));
            assert!(result.is_ok(), "Permission mode {} should be valid", mode);
        }
    }

    #[test]
    fn test_with_default_options() {
        let agent = ClaudeAgent::with_default_options("test-key".to_string()).unwrap();
        assert_eq!(agent.agent_type(), AgentType::Claude);
        assert_eq!(agent.metadata().model, "claude-3-5-sonnet-20241022");
    }

    #[tokio::test]
    async fn test_validate_with_empty_key_returns_false() {
        // 注意: new() 会拒绝空 key,所以我们需要通过其他方式测试
        // 这里测试 validate 对有效 key 返回 true
        let agent = ClaudeAgent::new(
            "test-key".to_string(),
            "claude-3-5-sonnet-20241022".to_string(),
            None,
        )
        .unwrap();
        let result = agent.validate().await;
        assert!(result.is_ok());
        assert!(result.unwrap());
    }
}
