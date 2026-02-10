pub mod agent;
pub mod config;
pub mod engine;
pub mod error;
pub mod repository;
pub mod state;

pub use agent::{
    Agent, AgentCapabilities, AgentConfig, AgentFactory, AgentLimits, AgentMetadata, AgentRequest,
    AgentResponse, AgentType, ChangeType, ClaudeAgent, FileChange, ResponseMetadata,
};
pub use config::Config;
pub use engine::{ExecutionEngine, ExecutionResult, Phase, PhaseConfig};
pub use error::{CoreError, Result};
pub use repository::{FileFilter, FileInfo, Repository};
pub use state::{
    ExecutionError, FeatureState, FileModification, PhaseCost, PhaseResult, PhaseState,
    StateManager, Status, TaskKind, TaskState,
};
