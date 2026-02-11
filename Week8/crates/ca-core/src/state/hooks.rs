//! State Hooks - 状态变化时的回调机制

use crate::error::Result;
use crate::state::FeatureState;
use crate::status::{ChangeLogEntry, StatusDocument};
use chrono::Utc;
use std::path::PathBuf;
use std::sync::Arc;

/// State Hook trait
pub trait StateHook: Send + Sync {
    /// Phase 开始时调用
    fn on_phase_start(&self, state: &FeatureState, phase: u8) -> Result<()>;
    
    /// Phase 完成时调用
    fn on_phase_complete(&self, state: &FeatureState, phase: u8) -> Result<()>;
    
    /// 任务完成时调用
    fn on_task_complete(&self, state: &FeatureState, task_id: &str) -> Result<()>;
    
    /// 错误记录时调用
    fn on_error_recorded(&self, state: &FeatureState) -> Result<()>;
}

/// Status 文档更新 Hook
pub struct StatusDocumentHook {
    specs_dir: PathBuf,
    spec_content: String,
}

impl StatusDocumentHook {
    /// 创建新的 StatusDocumentHook
    pub fn new(specs_dir: PathBuf, spec_content: String) -> Self {
        Self {
            specs_dir,
            spec_content,
        }
    }
    
    /// 获取 status.md 文件路径
    fn get_status_path(&self, feature_slug: &str) -> PathBuf {
        self.specs_dir.join(feature_slug).join("status.md")
    }
}

impl StateHook for StatusDocumentHook {
    fn on_phase_start(&self, state: &FeatureState, phase: u8) -> Result<()> {
        let status_path = self.get_status_path(&state.feature.slug);
        
        // 加载或创建 status.md
        let mut doc = StatusDocument::load_or_create(&status_path, state, &self.spec_content)?;
        
        // 更新当前阶段信息
        let phase_name = get_phase_name(phase);
        doc.update_current_phase(phase, &phase_name);
        
        // 添加变更记录
        doc.add_change_log(ChangeLogEntry {
            timestamp: Utc::now(),
            message: format!("开始 Phase {} - {}", phase, phase_name),
        });
        
        // 保存
        doc.save(&status_path)?;
        
        tracing::debug!("Status hook: phase {} started", phase);
        Ok(())
    }
    
    fn on_phase_complete(&self, state: &FeatureState, phase: u8) -> Result<()> {
        let status_path = self.get_status_path(&state.feature.slug);
        
        // 加载或创建 status.md
        let mut doc = StatusDocument::load_or_create(&status_path, state, &self.spec_content)?;
        
        // 查找对应的 phase state
        if let Some(phase_state) = state.phases.iter().find(|p| p.phase == phase) {
            // 更新阶段完成状态
            doc.update_phase_status(phase, phase_state);
        }
        
        // 更新成本统计
        doc.update_cost_summary(&state.cost_summary);
        
        // 更新进度百分比
        let progress = calculate_progress(state);
        doc.update_overall_progress(progress);
        
        // 添加变更记录
        let phase_name = get_phase_name(phase);
        doc.add_change_log(ChangeLogEntry {
            timestamp: Utc::now(),
            message: format!("完成 Phase {} - {}", phase, phase_name),
        });
        
        // 保存
        doc.save(&status_path)?;
        
        tracing::debug!("Status hook: phase {} completed", phase);
        Ok(())
    }
    
    fn on_task_complete(&self, state: &FeatureState, task_id: &str) -> Result<()> {
        let status_path = self.get_status_path(&state.feature.slug);
        
        // 加载或创建 status.md
        let mut doc = StatusDocument::load_or_create(&status_path, state, &self.spec_content)?;
        
        // 查找任务
        if let Some(task) = state.tasks.iter().find(|t| t.id == task_id) {
            // 添加变更记录
            doc.add_change_log(ChangeLogEntry {
                timestamp: Utc::now(),
                message: format!("完成任务: {} - {}", task_id, task.description),
            });
            
            // 更新进度
            let progress = calculate_progress(state);
            doc.update_overall_progress(progress);
        }
        
        // 保存
        doc.save(&status_path)?;
        
        tracing::debug!("Status hook: task {} completed", task_id);
        Ok(())
    }
    
    fn on_error_recorded(&self, state: &FeatureState) -> Result<()> {
        let status_path = self.get_status_path(&state.feature.slug);
        
        // 加载或创建 status.md
        let mut doc = StatusDocument::load_or_create(&status_path, state, &self.spec_content)?;
        
        // 获取最新的错误
        if let Some(error) = state.errors.last() {
            // 转换为 Issue 并添加
            let issue = crate::status::Issue::from_execution_error(error);
            doc.add_issue(issue);
            
            // 添加变更记录
            doc.add_change_log(ChangeLogEntry {
                timestamp: Utc::now(),
                message: format!("记录错误: {} (Phase {})", error.error_type, error.phase),
            });
        }
        
        // 保存
        doc.save(&status_path)?;
        
        tracing::debug!("Status hook: error recorded");
        Ok(())
    }
}

/// 计算整体进度百分比
fn calculate_progress(state: &FeatureState) -> u8 {
    use crate::state::Status;
    
    // 基于阶段完成情况计算
    let total_phases = 7u32;
    let completed_phases = state
        .phases
        .iter()
        .filter(|p| p.status == Status::Completed)
        .count() as u32;
    
    // 基于任务完成情况计算
    let total_tasks = state.tasks.len() as u32;
    let completed_tasks = state
        .tasks
        .iter()
        .filter(|t| t.status == Status::Completed)
        .count() as u32;
    
    // 综合计算 (70% 来自阶段, 30% 来自任务)
    let phase_progress = if total_phases > 0 {
        (completed_phases * 100 / total_phases) as u8
    } else {
        0
    };
    
    let task_progress = if total_tasks > 0 {
        (completed_tasks * 100 / total_tasks) as u8
    } else {
        0
    };
    
    ((phase_progress as u32 * 70 + task_progress as u32 * 30) / 100) as u8
}

/// 获取阶段名称
fn get_phase_name(phase: u8) -> String {
    match phase {
        0 => "未开始".to_string(),
        1 => "构建 Observer".to_string(),
        2 => "制定计划".to_string(),
        3 => "执行实施 1".to_string(),
        4 => "执行实施 2".to_string(),
        5 => "代码审查".to_string(),
        6 => "应用修复".to_string(),
        7 => "验证测试".to_string(),
        _ => format!("Phase {}", phase),
    }
}

/// Hook 集合
pub struct HookRegistry {
    hooks: Vec<Arc<dyn StateHook>>,
}

impl HookRegistry {
    /// 创建新的 Hook 注册表
    pub fn new() -> Self {
        Self { hooks: Vec::new() }
    }
    
    /// 添加 Hook
    pub fn add(&mut self, hook: Arc<dyn StateHook>) {
        self.hooks.push(hook);
    }
    
    /// 触发所有 hooks: phase start
    pub fn trigger_phase_start(&self, state: &FeatureState, phase: u8) {
        for hook in &self.hooks {
            if let Err(e) = hook.on_phase_start(state, phase) {
                tracing::warn!("Hook on_phase_start failed: {}", e);
            }
        }
    }
    
    /// 触发所有 hooks: phase complete
    pub fn trigger_phase_complete(&self, state: &FeatureState, phase: u8) {
        for hook in &self.hooks {
            if let Err(e) = hook.on_phase_complete(state, phase) {
                tracing::warn!("Hook on_phase_complete failed: {}", e);
            }
        }
    }
    
    /// 触发所有 hooks: task complete
    pub fn trigger_task_complete(&self, state: &FeatureState, task_id: &str) {
        for hook in &self.hooks {
            if let Err(e) = hook.on_task_complete(state, task_id) {
                tracing::warn!("Hook on_task_complete failed: {}", e);
            }
        }
    }
    
    /// 触发所有 hooks: error recorded
    pub fn trigger_error_recorded(&self, state: &FeatureState) {
        for hook in &self.hooks {
            if let Err(e) = hook.on_error_recorded(state) {
                tracing::warn!("Hook on_error_recorded failed: {}", e);
            }
        }
    }
}

impl Default for HookRegistry {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::state::{FeatureState, PhaseState, Status};
    use tempfile::TempDir;
    
    #[test]
    fn test_status_document_hook() {
        let temp_dir = TempDir::new().unwrap();
        let specs_dir = temp_dir.path().join("specs");
        std::fs::create_dir_all(&specs_dir).unwrap();
        
        let hook = StatusDocumentHook::new(
            specs_dir.clone(),
            "## 概述\n测试功能".to_string(),
        );
        
        let mut state = FeatureState::new(
            "test-feature".to_string(),
            "Test Feature".to_string(),
            "Claude".to_string(),
            "claude-3-5-sonnet-20241022".to_string(),
        );
        
        // 模拟 phase start
        state.phases.push(PhaseState {
            phase: 1,
            name: "Build Observer".to_string(),
            status: Status::InProgress,
            started_at: Some(Utc::now()),
            completed_at: None,
            duration_seconds: None,
            cost: None,
            result: None,
        });
        
        hook.on_phase_start(&state, 1).unwrap();
        
        // 检查 status.md 是否创建
        let status_path = specs_dir.join("test-feature").join("status.md");
        assert!(status_path.exists());
        
        let content = std::fs::read_to_string(status_path).unwrap();
        assert!(content.contains("功能开发状态"));
        assert!(content.contains("test-feature"));
    }
    
    #[test]
    fn test_progress_calculation() {
        let mut state = FeatureState::new(
            "test".to_string(),
            "Test".to_string(),
            "Claude".to_string(),
            "claude-3-5-sonnet-20241022".to_string(),
        );
        
        // 无阶段和任务
        assert_eq!(calculate_progress(&state), 0);
        
        // 添加完成的阶段
        state.phases.push(PhaseState {
            phase: 1,
            name: "Test".to_string(),
            status: Status::Completed,
            started_at: Some(Utc::now()),
            completed_at: Some(Utc::now()),
            duration_seconds: Some(60),
            cost: None,
            result: None,
        });
        
        // 1/7 完成 ≈ 10% (70% 权重)
        let progress = calculate_progress(&state);
        assert!(progress >= 9 && progress <= 11);
    }
}
