//! Status 文档类型定义

use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};

/// Status 文档结构
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StatusDocument {
    pub feature_name: String,
    pub feature_slug: String,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
    pub current_phase: u8,
    pub current_phase_name: String,
    pub overall_progress: u8,
    pub status: ProjectStatus,
    pub feature_overview: String,
    pub phases: Vec<PhaseProgress>,
    pub current_tasks: Vec<TaskProgress>,
    pub tech_summary: TechSummary,
    pub cost: CostSummary,
    pub issues: Vec<Issue>,
    pub change_log: Vec<ChangeLogEntry>,
    pub next_steps: NextSteps,
}

/// 项目状态
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum ProjectStatus {
    InProgress,  // 🟢 进行中
    Paused,      // 🟡 暂停
    Blocked,     // 🔴 阻塞
    Completed,   // ✅ 完成
}

/// 阶段进度
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PhaseProgress {
    pub phase: u8,
    pub name: String,
    pub status: PhaseStatus,
    pub started_at: Option<DateTime<Utc>>,
    pub completed_at: Option<DateTime<Utc>>,
    pub duration_seconds: Option<u64>,
    pub cost_usd: Option<f64>,
}

impl PhaseProgress {
    pub fn from_phase_state(state: &crate::state::PhaseState) -> Self {
        Self {
            phase: state.phase,
            name: state.name.clone(),
            status: match state.status {
                crate::state::Status::Pending => PhaseStatus::Pending,
                crate::state::Status::InProgress => PhaseStatus::InProgress,
                crate::state::Status::Completed => PhaseStatus::Completed,
                crate::state::Status::Failed => PhaseStatus::Failed,
                crate::state::Status::Paused => PhaseStatus::Pending,
            },
            started_at: state.started_at,
            completed_at: state.completed_at,
            duration_seconds: state.duration_seconds,
            cost_usd: state.cost.as_ref().map(|c| c.cost_usd),
        }
    }
}

/// 阶段状态
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum PhaseStatus {
    Pending,     // ⏳ 待开始
    InProgress,  // 🟢 进行中
    Completed,   // ✅ 完成
    Failed,      // 🔴 失败
}

/// 任务进度
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TaskProgress {
    pub id: String,
    pub kind: TaskKind,
    pub description: String,
    pub status: TaskStatus,
    pub progress_percentage: Option<u8>,
    pub files: Vec<String>,
}

impl TaskProgress {
    pub fn from_task_state(state: &crate::state::TaskState) -> Self {
        Self {
            id: state.id.clone(),
            kind: match state.kind {
                crate::state::TaskKind::Implementation => TaskKind::Implementation,
                crate::state::TaskKind::Refactoring => TaskKind::Refactoring,
                crate::state::TaskKind::Bugfix => TaskKind::Bugfix,
                crate::state::TaskKind::Testing => TaskKind::Testing,
                crate::state::TaskKind::Verification => TaskKind::Verification,
            },
            description: state.description.clone(),
            status: match state.status {
                crate::state::Status::Pending => TaskStatus::Pending,
                crate::state::Status::InProgress => TaskStatus::InProgress,
                crate::state::Status::Completed => TaskStatus::Completed,
                crate::state::Status::Failed => TaskStatus::Failed,
                crate::state::Status::Paused => TaskStatus::Pending,
            },
            progress_percentage: None,
            files: state.files.clone(),
        }
    }
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

/// 任务状态
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum TaskStatus {
    Pending,     // ⏳ 待开始
    InProgress,  // 🟢 进行中
    Completed,   // ✅ 完成
    Failed,      // 🔴 失败
}

/// 技术实施摘要
#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct TechSummary {
    pub completed_work: Vec<String>,
    pub code_changes: Vec<CodeChange>,
}

impl TechSummary {
    pub fn from_feature_state(state: &crate::state::FeatureState) -> Self {
        let completed_work = state
            .phases
            .iter()
            .filter(|p| p.status == crate::state::Status::Completed)
            .map(|p| {
                format!(
                    "Phase {}: {} (完成于 {})",
                    p.phase,
                    p.name,
                    p.completed_at
                        .map(|d| d.format("%Y-%m-%d %H:%M").to_string())
                        .unwrap_or_else(|| "未知".to_string())
                )
            })
            .collect();
        
        let code_changes = state
            .files_modified
            .iter()
            .map(|f| CodeChange {
                file: f.path.clone(),
                status: f.status.clone(),
                lines_changed: None,
                description: String::new(),
            })
            .collect();
        
        Self {
            completed_work,
            code_changes,
        }
    }
}

/// 代码变更
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CodeChange {
    pub file: String,
    pub status: String,
    pub lines_changed: Option<String>,
    pub description: String,
}

/// 成本统计
#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct CostSummary {
    pub total_tokens_input: u32,
    pub total_tokens_output: u32,
    pub total_cost_usd: f64,
    pub estimated_remaining_cost_usd: f64,
    pub phase_costs: Vec<PhaseCostDetail>,
}

/// 阶段成本详情
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PhaseCostDetail {
    pub phase: u8,
    pub name: String,
    pub cost_usd: f64,
}

/// 问题
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Issue {
    pub severity: IssueSeverity,
    pub category: String,
    pub title: String,
    pub description: String,
    pub impact: String,
    pub plan: String,
    pub status: IssueStatus,
    pub timestamp: DateTime<Utc>,
}

impl Issue {
    pub fn from_execution_error(error: &crate::state::ExecutionError) -> Self {
        Self {
            severity: IssueSeverity::High,
            category: error.error_type.clone(),
            title: format!("Phase {} 错误", error.phase),
            description: error.message.clone(),
            impact: "可能阻塞后续任务执行".to_string(),
            plan: error.resolution.clone().unwrap_or_else(|| "待评估".to_string()),
            status: if error.resolved {
                IssueStatus::Resolved
            } else {
                IssueStatus::InProgress
            },
            timestamp: error.timestamp,
        }
    }
}

/// 问题严重程度
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum IssueSeverity {
    Critical,  // 🔴 阻塞
    High,      // 🟠 高优先级
    Medium,    // 🟡 中优先级
    Low,       // 🟢 低优先级
}

/// 问题状态
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum IssueStatus {
    Pending,     // ⏳ 待处理
    InProgress,  // 🟡 处理中
    Resolved,    // ✅ 已解决
    Wontfix,     // ⚠️  不修复
}

/// 变更记录条目
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ChangeLogEntry {
    pub timestamp: DateTime<Utc>,
    pub message: String,
}

/// 下一步计划
#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct NextSteps {
    pub immediate: Vec<String>,
    pub short_term: Vec<String>,
    pub long_term: Vec<String>,
}

impl NextSteps {
    pub fn from_feature_state(state: &crate::state::FeatureState) -> Self {
        let mut immediate = Vec::new();
        let mut short_term = Vec::new();
        
        // 当前阶段的下一步
        if state.status.current_phase > 0 && state.status.current_phase <= 7 {
            let current_phase = state.status.current_phase;
            immediate.push(format!("完成 Phase {} 的剩余任务", current_phase));
            
            if current_phase < 7 {
                short_term.push(format!("开始 Phase {} - {}", 
                    current_phase + 1, 
                    crate::status::get_phase_name(current_phase + 1)
                ));
            }
        }
        
        // 未完成的任务
        let pending_tasks: Vec<_> = state
            .tasks
            .iter()
            .filter(|t| t.status != crate::state::Status::Completed)
            .take(3)
            .collect();
        
        for task in pending_tasks {
            immediate.push(format!("{}: {}", task.id, task.description));
        }
        
        // 长期目标
        let long_term = vec![
            "完成所有 7 个阶段".to_string(),
            "生成 Pull Request".to_string(),
            "合并到主分支".to_string(),
        ];
        
        Self {
            immediate,
            short_term,
            long_term,
        }
    }
}
