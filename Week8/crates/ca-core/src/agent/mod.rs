use async_trait::async_trait;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;

use crate::error::Result;

/// Agent 类型
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum AgentType {
    /// Claude Agent (Tier 1: 完全支持)
    Claude,
    /// Cursor Agent (Tier 2: 基础支持)
    Cursor,
    /// GitHub Copilot Agent (Tier 3: 实验性)
    Copilot,
}

impl AgentType {
    /// 获取官方环境变量名列表
    pub fn env_var_names(&self) -> Vec<&'static str> {
        match self {
            Self::Claude => vec!["ANTHROPIC_API_KEY", "CLAUDE_API_KEY"],
            Self::Copilot => vec!["COPILOT_GITHUB_TOKEN", "GH_TOKEN", "GITHUB_TOKEN"],
            Self::Cursor => vec!["CURSOR_API_KEY"],
        }
    }

    /// 获取主要环境变量名
    pub fn primary_env_var(&self) -> &'static str {
        match self {
            Self::Claude => "ANTHROPIC_API_KEY",
            Self::Copilot => "COPILOT_GITHUB_TOKEN",
            Self::Cursor => "CURSOR_API_KEY",
        }
    }
}

/// Agent 能力定义
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AgentCapabilities {
    /// 支持系统提示词
    pub supports_system_prompt: bool,
    /// 支持工具控制
    pub supports_tool_control: bool,
    /// 支持权限模式
    pub supports_permission_mode: bool,
    /// 支持成本控制
    pub supports_cost_control: bool,
    /// 支持流式响应
    pub supports_streaming: bool,
    /// 支持多模态
    pub supports_multimodal: bool,
}

impl Default for AgentCapabilities {
    fn default() -> Self {
        Self {
            supports_system_prompt: true,
            supports_tool_control: false,
            supports_permission_mode: false,
            supports_cost_control: false,
            supports_streaming: false,
            supports_multimodal: false,
        }
    }
}

/// Agent 元数据
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AgentMetadata {
    /// Agent 名称
    pub name: String,
    /// Agent 版本
    pub version: String,
    /// 模型名称
    pub model: String,
    /// 限制信息
    pub limits: AgentLimits,
}

/// Agent 限制信息
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AgentLimits {
    /// 最大上下文长度
    pub max_context_length: usize,
    /// 最大响应长度
    pub max_response_length: usize,
}

/// Agent 请求
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AgentRequest {
    /// 请求 ID
    pub id: String,
    /// 提示信息
    pub prompt: String,
    /// 系统提示词
    pub system_prompt: Option<String>,
    /// 上下文文件
    pub context_files: Vec<String>,
    /// 最大 tokens
    pub max_tokens: Option<u32>,
    /// 温度参数
    pub temperature: Option<f32>,
    /// 元数据
    pub metadata: HashMap<String, serde_json::Value>,
}

impl AgentRequest {
    /// 创建新的请求
    pub fn new(id: String, prompt: String) -> Self {
        Self {
            id,
            prompt,
            system_prompt: None,
            context_files: Vec::new(),
            max_tokens: None,
            temperature: None,
            metadata: HashMap::new(),
        }
    }
}

/// Agent 响应
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AgentResponse {
    /// 请求 ID
    pub request_id: String,
    /// 响应内容
    pub content: String,
    /// 使用的 tokens
    pub tokens_used: Option<u32>,
    /// 生成的文件修改
    pub file_changes: Vec<FileChange>,
    /// 响应元数据
    pub metadata: ResponseMetadata,
}

/// 响应元数据
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ResponseMetadata {
    /// 执行时长 (毫秒)
    pub duration_ms: u64,
    /// 模型名称
    pub model: String,
    /// 结束原因
    pub finish_reason: String,
}

/// 文件修改
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FileChange {
    /// 文件路径
    pub path: String,
    /// 修改类型
    pub change_type: ChangeType,
    /// 修改内容
    pub content: Option<String>,
}

/// 修改类型
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum ChangeType {
    Create,
    Update,
    Delete,
}

/// Agent trait
#[async_trait]
pub trait Agent: Send + Sync {
    /// 获取 Agent 类型
    fn agent_type(&self) -> AgentType;

    /// 获取 Agent 能力
    fn capabilities(&self) -> AgentCapabilities;

    /// 获取 Agent 元数据
    fn metadata(&self) -> AgentMetadata;

    /// 发送请求
    async fn execute(&self, request: AgentRequest) -> Result<AgentResponse>;

    /// 验证连接
    async fn validate(&self) -> Result<bool>;
}

/// Agent 配置
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AgentConfig {
    /// Agent 类型
    pub agent_type: AgentType,
    /// API 密钥
    pub api_key: String,
    /// 模型名称
    pub model: Option<String>,
    /// API URL
    pub api_url: Option<String>,
}

/// Agent 工厂
pub struct AgentFactory;

impl AgentFactory {
    /// 创建 Agent 实例
    pub fn create(config: AgentConfig) -> Result<Box<dyn Agent>> {
        match config.agent_type {
            AgentType::Claude => {
                let model = config
                    .model
                    .unwrap_or_else(|| "claude-3-5-sonnet-20241022".to_string());
                let agent = ClaudeAgent::new(config.api_key, model)?;
                Ok(Box::new(agent))
            }
            AgentType::Cursor => Err(crate::error::CoreError::Agent(
                "Cursor Agent not yet implemented".to_string(),
            )),
            AgentType::Copilot => Err(crate::error::CoreError::Agent(
                "Copilot Agent not yet implemented".to_string(),
            )),
        }
    }
}

/// Claude Agent 实现
pub struct ClaudeAgent {
    api_key: String,
    api_base_url: String,
    model: String,
    #[allow(dead_code)]
    client: reqwest::Client,
}

impl ClaudeAgent {
    /// 创建新的 Claude Agent
    pub fn new(api_key: String, model: String) -> Result<Self> {
        let client = reqwest::Client::builder()
            .timeout(std::time::Duration::from_secs(300))
            .build()?;

        Ok(Self {
            api_key,
            api_base_url: "https://api.anthropic.com/v1".to_string(),
            model,
            client,
        })
    }

    /// 设置自定义 API URL
    #[allow(dead_code)]
    pub fn with_api_url(mut self, url: String) -> Self {
        self.api_base_url = url;
        self
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
            version: "0.1.0".to_string(),
            model: self.model.clone(),
            limits: AgentLimits {
                max_context_length: 200_000,
                max_response_length: 8_192,
            },
        }
    }

    async fn execute(&self, request: AgentRequest) -> Result<AgentResponse> {
        // TODO: 实现实际的 Claude API 调用
        // 这里需要使用 claude-agent-sdk-rs
        tracing::info!(
            request_id = %request.id,
            prompt_len = request.prompt.len(),
            "Sending request to Claude"
        );

        let start = std::time::Instant::now();

        // 临时返回示例响应
        Ok(AgentResponse {
            request_id: request.id,
            content: "Response from Claude".to_string(),
            tokens_used: Some(100),
            file_changes: vec![],
            metadata: ResponseMetadata {
                duration_ms: start.elapsed().as_millis() as u64,
                model: self.model.clone(),
                finish_reason: "stop".to_string(),
            },
        })
    }

    async fn validate(&self) -> Result<bool> {
        // TODO: 实现连接验证
        tracing::info!("Validating Claude Agent connection");
        Ok(!self.api_key.is_empty())
    }
}
