pub mod phase_config;

use serde::{Deserialize, Serialize};
use std::sync::Arc;

use crate::agent::{Agent, AgentRequest, PhaseRequestConfig};
use crate::error::Result;
use crate::event::EventHandler;
use crate::repository::Repository;
use crate::state::StateManager;

pub use phase_config::{Phase, PhaseConfig};

/// 执行引擎 - 协调任务执行的核心组件
pub struct ExecutionEngine {
    /// Agent 实例
    agent: Arc<dyn Agent>,
    /// Repository 实例
    repository: Arc<Repository>,
    /// State Manager
    state_manager: Option<StateManager>,
    /// Event Handler (用于流式输出和 TUI 更新)
    event_handler: Option<Box<dyn EventHandler>>,
}

impl ExecutionEngine {
    /// 创建新的执行引擎
    pub fn new(agent: Arc<dyn Agent>, repository: Arc<Repository>) -> Self {
        Self {
            agent,
            repository,
            state_manager: None,
            event_handler: None,
        }
    }

    /// 设置 state manager
    pub fn with_state_manager(mut self, state_manager: StateManager) -> Self {
        self.state_manager = Some(state_manager);
        self
    }

    /// 设置 event handler
    pub fn with_event_handler(mut self, handler: Box<dyn EventHandler>) -> Self {
        self.event_handler = Some(handler);
        self
    }

    /// 执行指定阶段 (新版本 - 支持 TaskTemplate 和 TemplateContext)
    ///
    /// # 参数
    ///
    /// * `phase` - 执行阶段
    /// * `task_config` - 任务配置 (从 TaskTemplate.config)
    /// * `system_prompt` - 系统提示词 (从 TaskTemplate.system_template 渲染)
    /// * `user_prompt` - 用户提示词 (从 TaskTemplate.user_template 渲染)
    pub async fn execute_phase_with_config(
        &mut self,
        phase: Phase,
        task_config: &ca_pm::TaskConfig,
        system_prompt: Option<String>,
        user_prompt: String,
    ) -> Result<ExecutionResult> {
        tracing::info!(phase = ?phase, "Starting phase execution with config");

        // 1. 构建 PhaseRequestConfig (从 TaskConfig)
        let phase_config = PhaseRequestConfig {
            preset: task_config.preset,
            disallowed_tools: task_config.disallowed_tools.clone(),
            permission_mode: Self::convert_permission_mode(task_config.permission_mode),
            max_turns: task_config.max_turns,
            max_budget_usd: Some(task_config.max_budget_usd),
        };

        // 2. 构建 AgentRequest
        let request = AgentRequest {
            id: uuid::Uuid::new_v4().to_string(),
            prompt: user_prompt.clone(),
            system_prompt,
            context_files: Vec::new(),
            max_tokens: None,
            temperature: None,
            metadata: std::collections::HashMap::new(),
            phase_config: Some(phase_config),
        };

        // 3. 执行请求
        let response = self.agent.execute(request).await?;

        // 4. 触发事件 (如果有 EventHandler)
        if let Some(ref mut handler) = self.event_handler {
            handler.on_text(&response.content);
            handler.on_complete();
        }

        // 5. 构建结果
        Ok(ExecutionResult {
            success: true,
            phase,
            message: response.content,
            files_changed: response.file_changes.len(),
            tokens_used: response.tokens_used.unwrap_or(0),
            turns: 1, // TODO: 从响应中获取实际轮次
            cost_usd: 0.0, // TODO: 从响应中计算实际成本
        })
    }

    /// 执行指定阶段 (旧版本 - 向后兼容)
    pub async fn execute_phase(&mut self, phase: Phase, prompt: String) -> Result<ExecutionResult> {
        tracing::info!(phase = ?phase, "Starting phase execution (legacy mode)");

        // 获取 phase 配置
        let config = PhaseConfig::for_phase(phase)?;

        // 构建 Agent 请求
        let request = AgentRequest {
            id: uuid::Uuid::new_v4().to_string(),
            prompt,
            system_prompt: Some(config.system_prompt),
            context_files: Vec::new(),
            max_tokens: None,
            temperature: None,
            metadata: std::collections::HashMap::new(),
            phase_config: None, // 旧模式不传递 phase_config
        };

        // 执行请求
        let response = self.agent.execute(request).await?;

        // 构建结果
        Ok(ExecutionResult {
            success: true,
            phase,
            message: response.content,
            files_changed: response.file_changes.len(),
            tokens_used: response.tokens_used.unwrap_or(0),
            turns: 1,
            cost_usd: 0.0,
        })
    }

    /// 转换权限模式
    fn convert_permission_mode(mode: ca_pm::PermissionMode) -> crate::agent::PermissionMode {
        match mode {
            ca_pm::PermissionMode::Default => crate::agent::PermissionMode::Default,
            ca_pm::PermissionMode::AcceptEdits => crate::agent::PermissionMode::AcceptEdits,
            ca_pm::PermissionMode::Plan => crate::agent::PermissionMode::Plan,
            ca_pm::PermissionMode::BypassPermissions => crate::agent::PermissionMode::BypassPermissions,
        }
    }

    /// 获取 repository
    pub fn repository(&self) -> &Arc<Repository> {
        &self.repository
    }

    /// 获取 agent
    pub fn agent(&self) -> &Arc<dyn Agent> {
        &self.agent
    }

    /// 验证引擎是否可用
    pub async fn validate(&self) -> Result<bool> {
        self.agent.validate().await
    }
}

/// 执行结果
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ExecutionResult {
    /// 是否成功
    pub success: bool,
    /// 执行的阶段
    pub phase: Phase,
    /// 结果消息
    pub message: String,
    /// 修改的文件数量
    pub files_changed: usize,
    /// 使用的 tokens
    pub tokens_used: u32,
    /// 执行轮次
    pub turns: usize,
    /// 成本 (USD)
    pub cost_usd: f64,
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::agent::ClaudeAgent;

    #[tokio::test]
    async fn test_execution_engine_creation() {
        let agent = Arc::new(
            ClaudeAgent::new(
                "test_key".to_string(),
                "claude-3-5-sonnet-20241022".to_string(),
                None,
            )
            .unwrap(),
        );

        let temp_dir = std::env::temp_dir();
        let repo = Arc::new(Repository::new(temp_dir).unwrap());

        let engine = ExecutionEngine::new(agent, repo);
        assert!(engine.state_manager.is_none());
        assert!(engine.event_handler.is_none());
    }
}
