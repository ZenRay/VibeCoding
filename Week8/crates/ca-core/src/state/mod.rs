//! 状态管理模块
//!
//! 提供功能执行状态持久化、断点恢复、Phase 和 Task 跟踪。
//! 状态保存在 `specs/{feature-slug}/state.yml`。

pub mod hooks;
pub mod types;

use chrono::Utc;
use std::path::{Path, PathBuf};

use crate::error::Result;
pub use hooks::{HookRegistry, StateHook, StatusDocumentHook};
pub use types::*;

/// State Manager - 管理功能执行状态
pub struct StateManager {
    state_file: PathBuf,
    state: FeatureState,
    hooks: HookRegistry,
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

        Ok(Self {
            state_file,
            state,
            hooks: HookRegistry::new(),
        })
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

    /// 添加 Hook
    pub fn add_hook(&mut self, hook: std::sync::Arc<dyn StateHook>) {
        self.hooks.add(hook);
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
        self.save()?;

        // 触发 hooks
        self.hooks.trigger_phase_start(&self.state, phase_number);

        Ok(())
    }

    /// 开始新的 phase (使用默认名称)
    pub fn start_phase_with_default_name(&mut self, phase_number: u8) -> Result<()> {
        let phase_name = match phase_number {
            1 => "Build Observer",
            2 => "Build Plan",
            3 => "Execute Phase 1",
            4 => "Execute Phase 2",
            5 => "Code Review",
            6 => "Apply Fixes",
            7 => "Verification",
            _ => "Unknown Phase",
        };
        self.start_phase(phase_number, phase_name.to_string())
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

        self.save()?;

        // 触发 hooks
        self.hooks.trigger_phase_complete(&self.state, phase_number);

        Ok(())
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
        let was_completed = status == Status::Completed;

        if let Some(task) = self.state.tasks.iter_mut().find(|t| t.id == task_id) {
            task.status = status;
        }

        self.save()?;

        // 如果任务完成，触发 hook
        if was_completed {
            self.hooks.trigger_task_complete(&self.state, task_id);
        }

        Ok(())
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
        self.save()?;

        // 触发 hooks
        self.hooks.trigger_error_recorded(&self.state);

        Ok(())
    }

    /// 检查是否可以恢复
    pub fn can_resume(&self) -> bool {
        self.state.status.can_resume
    }

    /// 设置 PR 信息
    pub fn set_pr_info(&mut self, pr_url: String, pr_number: u32) -> Result<()> {
        self.state.feature.updated_at = Utc::now();
        self.state.delivery.pr_url = Some(pr_url);
        self.state.delivery.pr_number = Some(pr_number);
        self.save()
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
    fn test_should_create_state_manager_for_new_feature() {
        let temp_dir = TempDir::new().unwrap();
        let manager = StateManager::new("test-feature", temp_dir.path()).unwrap();

        assert_eq!(manager.state().feature.slug, "test-feature");
        assert_eq!(manager.state().status.overall_status, Status::Pending);
        assert_eq!(manager.state().status.current_phase, 0);
    }

    #[test]
    fn test_should_save_and_load_state() {
        let temp_dir = TempDir::new().unwrap();

        {
            let mut manager = StateManager::new("test-feature", temp_dir.path()).unwrap();
            manager.start_phase(1, "Test Phase".to_string()).unwrap();
        }

        let manager = StateManager::new("test-feature", temp_dir.path()).unwrap();
        assert_eq!(manager.state().phases.len(), 1);
        assert_eq!(manager.state().phases[0].name, "Test Phase");
        assert_eq!(manager.state().phases[0].status, Status::InProgress);
    }

    #[test]
    fn test_should_update_phase_status() {
        let temp_dir = TempDir::new().unwrap();
        let mut manager = StateManager::new("test-feature", temp_dir.path()).unwrap();
        manager
            .start_phase(1, "Build Observer".to_string())
            .unwrap();

        manager.update_phase_status(1, Status::Completed).unwrap();

        let phase = manager
            .state()
            .phases
            .iter()
            .find(|p| p.phase == 1)
            .unwrap();
        assert_eq!(phase.status, Status::Completed);
        assert!(phase.completed_at.is_some());
    }

    #[test]
    fn test_should_complete_phase_with_result() {
        let temp_dir = TempDir::new().unwrap();
        let mut manager = StateManager::new("test-feature", temp_dir.path()).unwrap();
        manager
            .start_phase(1, "Build Observer".to_string())
            .unwrap();

        let result = PhaseResult {
            success: true,
            output_file: Some("output.md".to_string()),
            extra: std::collections::HashMap::new(),
        };
        manager.complete_phase(1, result).unwrap();

        let phase = manager
            .state()
            .phases
            .iter()
            .find(|p| p.phase == 1)
            .unwrap();
        assert_eq!(phase.status, Status::Completed);
        assert!(phase.result.as_ref().unwrap().success);
    }

    #[test]
    fn test_should_add_and_update_task() {
        let temp_dir = TempDir::new().unwrap();
        let mut manager = StateManager::new("test-feature", temp_dir.path()).unwrap();

        let task = TaskState {
            id: "task-1".to_string(),
            kind: TaskKind::Implementation,
            description: "Implement feature".to_string(),
            status: Status::Pending,
            assigned_phase: 1,
            files: vec!["src/main.rs".to_string()],
        };
        manager.add_task(task).unwrap();
        assert_eq!(manager.state().tasks.len(), 1);

        manager
            .update_task_status("task-1", Status::Completed)
            .unwrap();
        assert_eq!(manager.state().tasks[0].status, Status::Completed);
    }

    #[test]
    fn test_should_create_checkpoint_and_enable_resume() {
        let temp_dir = TempDir::new().unwrap();
        let mut manager = StateManager::new("test-feature", temp_dir.path()).unwrap();
        manager
            .start_phase(1, "Build Observer".to_string())
            .unwrap();

        manager
            .checkpoint("after_observer", "Context for resume".to_string())
            .unwrap();

        assert!(manager.can_resume());
        assert_eq!(manager.state().resume.last_checkpoint, "after_observer");
        assert_eq!(
            manager.state().resume.resume_prompt_context,
            "Context for resume"
        );
    }

    #[test]
    fn test_should_record_file_change() {
        let temp_dir = TempDir::new().unwrap();
        let mut manager = StateManager::new("test-feature", temp_dir.path()).unwrap();

        let modification = FileModification {
            path: "src/lib.rs".to_string(),
            status: "modified".to_string(),
            phase: 1,
            size_bytes: 1024,
            backup: Some("src/lib.rs.bak".to_string()),
        };
        manager.record_file_change(modification).unwrap();

        assert_eq!(manager.state().files_modified.len(), 1);
        assert_eq!(manager.state().files_modified[0].path, "src/lib.rs");
    }

    #[test]
    fn test_should_add_cost_and_update_summary() {
        let temp_dir = TempDir::new().unwrap();
        let mut manager = StateManager::new("test-feature", temp_dir.path()).unwrap();
        manager
            .start_phase(1, "Build Observer".to_string())
            .unwrap();

        let cost = PhaseCost {
            tokens_input: 1000,
            tokens_output: 500,
            cost_usd: 0.05,
        };
        manager.add_cost(1, cost).unwrap();

        assert_eq!(manager.state().cost_summary.total_tokens_input, 1000);
        assert_eq!(manager.state().cost_summary.total_tokens_output, 500);
        assert!((manager.state().cost_summary.total_cost_usd - 0.05).abs() < 0.001);
    }

    #[test]
    fn test_should_record_error() {
        let temp_dir = TempDir::new().unwrap();
        let mut manager = StateManager::new("test-feature", temp_dir.path()).unwrap();

        let error = ExecutionError {
            phase: 1,
            task: "task-1".to_string(),
            timestamp: chrono::Utc::now(),
            error_type: "Timeout".to_string(),
            message: "Request timed out".to_string(),
            resolved: false,
            resolution: None,
        };
        manager.record_error(error).unwrap();

        assert_eq!(manager.state().errors.len(), 1);
        assert_eq!(manager.state().errors[0].error_type, "Timeout");
    }

    #[test]
    fn test_should_set_pr_info() {
        let temp_dir = TempDir::new().unwrap();
        let mut manager = StateManager::new("test-feature", temp_dir.path()).unwrap();

        manager
            .set_pr_info("https://github.com/repo/pull/1".to_string(), 1)
            .unwrap();

        assert_eq!(
            manager.state().delivery.pr_url,
            Some("https://github.com/repo/pull/1".to_string())
        );
        assert_eq!(manager.state().delivery.pr_number, Some(1));
    }

    #[test]
    fn test_should_generate_resume_context() {
        let temp_dir = TempDir::new().unwrap();
        let mut manager = StateManager::new("test-feature", temp_dir.path()).unwrap();
        manager
            .start_phase(1, "Build Observer".to_string())
            .unwrap();
        manager
            .checkpoint("checkpoint", "context".to_string())
            .unwrap();

        let context = manager.generate_resume_context();
        assert!(context.contains("checkpoint"));
        assert!(context.contains("phase 1"));
    }

    #[test]
    fn test_should_use_start_phase_with_default_name() {
        let temp_dir = TempDir::new().unwrap();
        let mut manager = StateManager::new("test-feature", temp_dir.path()).unwrap();

        manager.start_phase_with_default_name(1).unwrap();
        assert_eq!(manager.state().phases[0].name, "Build Observer");

        manager.start_phase_with_default_name(7).unwrap();
        assert_eq!(manager.state().phases[1].name, "Verification");
    }
}
