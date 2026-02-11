//! # Code Agent Core (ca-core)
//!
//! 多 Agent SDK 统一封装的核心库,提供执行引擎、状态管理、代码审查等能力。
//!
//! ## 模块概览
//!
//! - [`agent`] - Agent 抽象层和 Claude 实现
//! - [`config`] - 零配置文件,环境变量优先
//! - [`engine`] - 执行引擎,协调任务执行
//! - [`event`] - 流式输出和 TUI 事件
//! - [`repository`] - 仓库文件操作,支持 .gitignore
//! - [`review`] - 代码审查关键词匹配
//! - [`state`] - 状态管理和断点恢复
//! - [`status`] - 项目状态文档
//! - [`worktree`] - Git Worktree 管理
//!
//! ## 示例
//!
//! ```no_run
//! use ca_core::{AgentFactory, AgentConfig, AgentType, ExecutionEngine, Repository};
//! use std::sync::Arc;
//!
//! # async fn example() -> Result<(), Box<dyn std::error::Error>> {
//! let config = AgentConfig {
//!     agent_type: AgentType::Claude,
//!     api_key: std::env::var("ANTHROPIC_API_KEY")?,
//!     model: None,
//!     api_url: None,
//! };
//! let agent = AgentFactory::create(config)?;
//! let repo = Arc::new(Repository::new(".")?);
//! let engine = ExecutionEngine::new(agent, repo);
//! # Ok(())
//! # }
//! ```

pub mod agent;
pub mod config;
pub mod engine;
pub mod error;
pub mod event;
pub mod repository;
pub mod review;
pub mod state;
pub mod status;
pub mod worktree;

pub use agent::{
    Agent, AgentCapabilities, AgentConfig, AgentFactory, AgentLimits, AgentMetadata, AgentRequest,
    AgentResponse, AgentType, ChangeType, ClaudeAgent, FileChange, ResponseMetadata,
};
pub use config::Config;
pub use engine::{ExecutionEngine, ExecutionResult, Phase, PhaseConfig};
pub use error::{CoreError, Result};
pub use event::{CliEventHandler, EventHandler, TuiEvent, TuiEventHandler};
pub use repository::{FileFilter, FileInfo, Repository};
pub use review::KeywordMatcher;
pub use state::{
    ExecutionError, FeatureState, FileModification, HookRegistry, PhaseCost, PhaseResult,
    PhaseState, StateHook, StateManager, Status, StatusDocumentHook, TaskKind, TaskState,
};
pub use status::{ProjectStatus, StatusDocument};
pub use worktree::{GitCommand, WorktreeInfo, WorktreeManager};
