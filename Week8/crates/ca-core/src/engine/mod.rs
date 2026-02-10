pub mod phase_config;

use serde::{Deserialize, Serialize};
use std::sync::Arc;

use crate::agent::{Agent, AgentRequest};
use crate::error::Result;
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
}

impl ExecutionEngine {
    /// 创建新的执行引擎
    pub fn new(agent: Arc<dyn Agent>, repository: Arc<Repository>) -> Self {
        Self {
            agent,
            repository,
            state_manager: None,
        }
    }

    /// 设置 state manager
    pub fn with_state_manager(mut self, state_manager: StateManager) -> Self {
        self.state_manager = Some(state_manager);
        self
    }

    /// 执行指定阶段
    pub async fn execute_phase(&self, phase: Phase, prompt: String) -> Result<ExecutionResult> {
        tracing::info!(phase = ?phase, "Starting phase execution");

        // 获取 phase 配置
        let config = PhaseConfig::for_phase(phase)?;

        // 配置 Agent 的 Permission Mode 和其他选项
        // 注意: 这里需要确保 agent 是可变的,但我们使用 Arc<dyn Agent>
        // 解决方案: 通过 ClaudeAgent 的 configure 方法在执行前配置
        
        // TODO: 目前无法直接修改 Arc<dyn Agent>,需要重构为支持运行时配置
        // 临时方案: 在创建 Agent 时就配置好所有选项
        
        // 构建 Agent 请求
        let request = AgentRequest {
            id: uuid::Uuid::new_v4().to_string(),
            prompt,
            system_prompt: Some(config.system_prompt),
            context_files: Vec::new(),
            max_tokens: None,
            temperature: None,
            metadata: std::collections::HashMap::new(),
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
        })
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
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::agent::{AgentType, ClaudeAgent};

    #[tokio::test]
    async fn test_execution_engine_creation() {
        let agent = Arc::new(
            ClaudeAgent::new(
                "test_key".to_string(),
                "claude-3-5-sonnet-20241022".to_string(),
            )
            .unwrap(),
        );

        let temp_dir = std::env::temp_dir();
        let repo = Arc::new(Repository::new(temp_dir).unwrap());

        let engine = ExecutionEngine::new(agent, repo);
        assert!(engine.state_manager.is_none());
    }
}
