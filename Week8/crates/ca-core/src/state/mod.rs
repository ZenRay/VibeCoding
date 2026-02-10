pub mod types;

use chrono::Utc;
use std::path::{Path, PathBuf};

use crate::error::Result;
pub use types::*;

/// State Manager - 管理功能执行状态
pub struct StateManager {
    state_file: PathBuf,
    state: FeatureState,
}

impl StateManager {
    /// 创建新的 state manager
    pub fn new(feature_slug: &str, repo_path: &Path) -> Result<Self> {
        let state_file = Self::state_file_path(feature_slug, repo_path);

        // 尝试加载现有状态
        let state = if state_file.exists() {
            Self::load_state(&state_file)?
        } else {
            FeatureState::new(
                feature_slug.to_string(),
                feature_slug.replace('-', " ").to_string(),
                "Claude".to_string(),
                "claude-3-5-sonnet-20241022".to_string(),
            )
        };

        Ok(Self { state_file, state })
    }

    /// 获取状态文件路径
    fn state_file_path(feature_slug: &str, repo_path: &Path) -> PathBuf {
        repo_path.join("specs").join(feature_slug).join("state.yml")
    }

    /// 加载状态
    fn load_state(path: &PathBuf) -> Result<FeatureState> {
        let content = std::fs::read_to_string(path)?;
        let state: FeatureState = serde_yaml::from_str(&content)?;
        Ok(state)
    }

    /// 保存状态
    pub fn save(&self) -> Result<()> {
        // 确保目录存在
        if let Some(parent) = self.state_file.parent() {
            std::fs::create_dir_all(parent)?;
        }

        // 序列化并保存
        let yaml = serde_yaml::to_string(&self.state)?;
        std::fs::write(&self.state_file, yaml)?;

        tracing::info!("State saved to {}", self.state_file.display());
        Ok(())
    }

    /// 获取当前状态
    pub fn state(&self) -> &FeatureState {
        &self.state
    }

    /// 获取可变状态
    pub fn state_mut(&mut self) -> &mut FeatureState {
        &mut self.state
    }

    /// 更新 phase 状态
    pub fn update_phase_status(&mut self, phase_number: u8, status: Status) -> Result<()> {
        self.state.feature.updated_at = Utc::now();

        if let Some(phase) = self
            .state
            .phases
            .iter_mut()
            .find(|p| p.phase == phase_number)
        {
            phase.status = status;
            if status == Status::Completed {
                phase.completed_at = Some(Utc::now());
                if let Some(started) = phase.started_at {
                    phase.duration_seconds = Some((Utc::now() - started).num_seconds() as u64);
                }
            }
        }

        self.save()
    }

    /// 开始新的 phase
    pub fn start_phase(&mut self, phase_number: u8, phase_name: String) -> Result<()> {
        self.state.feature.updated_at = Utc::now();
        self.state.status.current_phase = phase_number;

        let phase_state = PhaseState {
            phase: phase_number,
            name: phase_name,
            status: Status::InProgress,
            started_at: Some(Utc::now()),
            completed_at: None,
            duration_seconds: None,
            cost: None,
            result: None,
        };

        self.state.phases.push(phase_state);
        self.save()
    }

    /// 完成 phase
    pub fn complete_phase(&mut self, phase_number: u8, result: PhaseResult) -> Result<()> {
        self.state.feature.updated_at = Utc::now();

        if let Some(phase) = self
            .state
            .phases
            .iter_mut()
            .find(|p| p.phase == phase_number)
        {
            phase.status = Status::Completed;
            phase.completed_at = Some(Utc::now());
            phase.result = Some(result);

            if let Some(started) = phase.started_at {
                phase.duration_seconds = Some((Utc::now() - started).num_seconds() as u64);
            }
        }

        self.save()
    }

    /// 添加任务
    pub fn add_task(&mut self, task: TaskState) -> Result<()> {
        self.state.feature.updated_at = Utc::now();
        self.state.tasks.push(task);
        self.save()
    }

    /// 更新任务状态
    pub fn update_task_status(&mut self, task_id: &str, status: Status) -> Result<()> {
        self.state.feature.updated_at = Utc::now();

        if let Some(task) = self.state.tasks.iter_mut().find(|t| t.id == task_id) {
            task.status = status;
        }

        self.save()
    }

    /// 创建检查点
    pub fn checkpoint(&mut self, checkpoint_name: &str, context: String) -> Result<()> {
        self.state.feature.updated_at = Utc::now();
        self.state.resume.last_checkpoint = checkpoint_name.to_string();
        self.state.resume.resume_prompt_context = context;
        self.state.resume.can_resume_from_phase = self.state.status.current_phase;
        self.state.status.can_resume = true;

        self.save()
    }

    /// 记录文件修改
    pub fn record_file_change(&mut self, modification: FileModification) -> Result<()> {
        self.state.feature.updated_at = Utc::now();
        self.state.files_modified.push(modification);
        self.save()
    }

    /// 添加成本
    pub fn add_cost(&mut self, phase_number: u8, cost: PhaseCost) -> Result<()> {
        self.state.feature.updated_at = Utc::now();

        if let Some(phase) = self
            .state
            .phases
            .iter_mut()
            .find(|p| p.phase == phase_number)
        {
            phase.cost = Some(cost.clone());
        }

        self.state.cost_summary.total_tokens_input += cost.tokens_input;
        self.state.cost_summary.total_tokens_output += cost.tokens_output;
        self.state.cost_summary.total_cost_usd += cost.cost_usd;

        self.save()
    }

    /// 记录错误
    pub fn record_error(&mut self, error: ExecutionError) -> Result<()> {
        self.state.feature.updated_at = Utc::now();
        self.state.errors.push(error);
        self.save()
    }

    /// 检查是否可以恢复
    pub fn can_resume(&self) -> bool {
        self.state.status.can_resume
    }

    /// 生成恢复上下文
    pub fn generate_resume_context(&self) -> String {
        format!(
            "Resuming from phase {} ({}). Last checkpoint: {}. {} tasks completed.",
            self.state.status.current_phase,
            self.state
                .phases
                .iter()
                .find(|p| p.phase == self.state.status.current_phase)
                .map(|p| p.name.as_str())
                .unwrap_or("Unknown"),
            self.state.resume.last_checkpoint,
            self.state
                .tasks
                .iter()
                .filter(|t| t.status == Status::Completed)
                .count()
        )
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::TempDir;

    #[test]
    fn test_state_manager_creation() {
        let temp_dir = TempDir::new().unwrap();
        let manager = StateManager::new("test-feature", temp_dir.path()).unwrap();

        assert_eq!(manager.state().feature.slug, "test-feature");
        assert_eq!(manager.state().status.overall_status, Status::Pending);
    }

    #[test]
    fn test_save_and_load_state() {
        let temp_dir = TempDir::new().unwrap();

        {
            let mut manager = StateManager::new("test-feature", temp_dir.path()).unwrap();
            manager.start_phase(1, "Test Phase".to_string()).unwrap();
        }

        // 重新加载
        let manager = StateManager::new("test-feature", temp_dir.path()).unwrap();
        assert_eq!(manager.state().phases.len(), 1);
        assert_eq!(manager.state().phases[0].name, "Test Phase");
    }
}
