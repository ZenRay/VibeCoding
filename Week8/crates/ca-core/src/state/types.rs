use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::path::PathBuf;

/// 执行状态
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum Status {
    Pending,
    InProgress,
    Completed,
    Failed,
    Paused,
}

/// 任务类型
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum TaskKind {
    Implementation,
    Refactoring,
    Bugfix,
    Testing,
    Verification,
}

/// Feature 执行状态
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FeatureState {
    pub version: String,
    pub feature: FeatureInfo,
    pub status: ExecutionStatus,
    pub agent: AgentInfo,
    pub phases: Vec<PhaseState>,
    pub tasks: Vec<TaskState>,
    pub resume: ResumeInfo,
    pub cost_summary: CostSummary,
    pub files_modified: Vec<FileModification>,
    pub delivery: DeliveryInfo,
    pub metadata: StateMetadata,
    pub errors: Vec<ExecutionError>,
}

impl FeatureState {
    /// 创建新的 feature 状态
    pub fn new(
        feature_slug: String,
        feature_name: String,
        agent_type: String,
        model: String,
    ) -> Self {
        Self {
            version: "1.0".to_string(),
            feature: FeatureInfo {
                slug: feature_slug.clone(),
                name: feature_name,
                created_at: Utc::now(),
                updated_at: Utc::now(),
            },
            status: ExecutionStatus {
                current_phase: 0,
                overall_status: Status::Pending,
                completion_percentage: 0,
                can_resume: false,
            },
            agent: AgentInfo {
                agent_type,
                model,
                session_id: uuid::Uuid::new_v4().to_string(),
            },
            phases: Vec::new(),
            tasks: Vec::new(),
            resume: ResumeInfo {
                last_checkpoint: String::new(),
                resume_prompt_context: String::new(),
                can_resume_from_phase: 0,
            },
            cost_summary: CostSummary {
                total_tokens_input: 0,
                total_tokens_output: 0,
                total_cost_usd: 0.0,
                estimated_remaining_cost_usd: 0.0,
            },
            files_modified: Vec::new(),
            delivery: DeliveryInfo::default(),
            metadata: StateMetadata {
                repository: PathBuf::new(),
                base_branch: "main".to_string(),
                target_branch: format!("feature/{}", feature_slug),
                code_agent_version: env!("CARGO_PKG_VERSION").to_string(),
            },
            errors: Vec::new(),
        }
    }
}

/// Feature 信息
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FeatureInfo {
    pub slug: String,
    pub name: String,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
}

/// 执行状态信息
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ExecutionStatus {
    pub current_phase: u8,
    pub overall_status: Status,
    pub completion_percentage: u8,
    pub can_resume: bool,
}

/// Agent 信息
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AgentInfo {
    #[serde(rename = "type")]
    pub agent_type: String,
    pub model: String,
    pub session_id: String,
}

/// Phase 状态
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PhaseState {
    pub phase: u8,
    pub name: String,
    pub status: Status,
    pub started_at: Option<DateTime<Utc>>,
    pub completed_at: Option<DateTime<Utc>>,
    pub duration_seconds: Option<u64>,
    pub cost: Option<PhaseCost>,
    pub result: Option<PhaseResult>,
}

/// Phase 成本
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PhaseCost {
    pub tokens_input: u32,
    pub tokens_output: u32,
    pub cost_usd: f64,
}

/// Phase 结果
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PhaseResult {
    pub success: bool,
    pub output_file: Option<String>,
    #[serde(flatten)]
    pub extra: HashMap<String, serde_json::Value>,
}

/// 任务状态
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TaskState {
    pub id: String,
    pub kind: TaskKind,
    pub description: String,
    pub status: Status,
    pub assigned_phase: u8,
    pub files: Vec<String>,
}

/// 恢复信息
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ResumeInfo {
    pub last_checkpoint: String,
    pub resume_prompt_context: String,
    pub can_resume_from_phase: u8,
}

/// 成本汇总
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CostSummary {
    pub total_tokens_input: u32,
    pub total_tokens_output: u32,
    pub total_cost_usd: f64,
    pub estimated_remaining_cost_usd: f64,
}

/// 文件修改记录
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FileModification {
    pub path: String,
    pub status: String,
    pub phase: u8,
    pub size_bytes: u64,
    pub backup: Option<String>,
}

/// 交付信息
#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct DeliveryInfo {
    pub pr_url: Option<String>,
    pub pr_number: Option<u32>,
    pub merged: bool,
    pub merged_at: Option<DateTime<Utc>>,
    pub branch_name: String,
}

/// 状态元数据
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StateMetadata {
    pub repository: PathBuf,
    pub base_branch: String,
    pub target_branch: String,
    pub code_agent_version: String,
}

/// 执行错误
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ExecutionError {
    pub phase: u8,
    pub task: String,
    pub timestamp: DateTime<Utc>,
    pub error_type: String,
    pub message: String,
    pub resolved: bool,
    pub resolution: Option<String>,
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_feature_state_creation() {
        let state = FeatureState::new(
            "test-feature".to_string(),
            "Test Feature".to_string(),
            "Claude".to_string(),
            "claude-3-5-sonnet-20241022".to_string(),
        );

        assert_eq!(state.feature.slug, "test-feature");
        assert_eq!(state.status.overall_status, Status::Pending);
        assert_eq!(state.version, "1.0");
    }

    #[test]
    fn test_phase_state() {
        let phase = PhaseState {
            phase: 1,
            name: "Build Observer".to_string(),
            status: Status::Completed,
            started_at: Some(Utc::now()),
            completed_at: Some(Utc::now()),
            duration_seconds: Some(120),
            cost: None,
            result: None,
        };

        assert_eq!(phase.phase, 1);
        assert_eq!(phase.status, Status::Completed);
    }
}
