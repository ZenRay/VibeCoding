//! Status 模块
//!
//! 生成人类可读的中文项目进度报告 (status.md)

mod template;
mod types;

pub use template::render_status_markdown;
pub use types::*;

use chrono::Utc;
use std::path::Path;

use crate::error::Result;
use crate::state::FeatureState;

impl StatusDocument {
    /// 从 FeatureState 创建新的 Status 文档
    pub fn from_feature_state(state: &FeatureState, spec_content: &str) -> Self {
        let feature_overview = extract_overview_from_spec(spec_content);

        // 将 PhaseState 转换为 PhaseProgress
        let phases = state
            .phases
            .iter()
            .map(PhaseProgress::from_phase_state)
            .collect();

        // 将 TaskState 转换为 TaskProgress
        let current_tasks: Vec<TaskProgress> = state
            .tasks
            .iter()
            .filter(|t| t.status != crate::state::Status::Completed)
            .take(10) // 只显示前 10 个未完成任务
            .map(TaskProgress::from_task_state)
            .collect();

        // 技术摘要
        let tech_summary = TechSummary::from_feature_state(state);

        // 成本统计
        let cost = CostSummary {
            total_tokens_input: state.cost_summary.total_tokens_input,
            total_tokens_output: state.cost_summary.total_tokens_output,
            total_cost_usd: state.cost_summary.total_cost_usd,
            estimated_remaining_cost_usd: state.cost_summary.estimated_remaining_cost_usd,
            phase_costs: state
                .phases
                .iter()
                .filter_map(|p| {
                    p.cost.as_ref().map(|c| PhaseCostDetail {
                        phase: p.phase,
                        name: p.name.clone(),
                        cost_usd: c.cost_usd,
                    })
                })
                .collect(),
        };

        // 问题列表 (从 errors 转换)
        let issues: Vec<Issue> = state
            .errors
            .iter()
            .map(Issue::from_execution_error)
            .collect();

        // 确定项目状态
        let status = determine_project_status(state);

        Self {
            feature_name: state.feature.name.clone(),
            feature_slug: state.feature.slug.clone(),
            created_at: state.feature.created_at,
            updated_at: Utc::now(),
            current_phase: state.status.current_phase,
            current_phase_name: get_phase_name(state.status.current_phase),
            overall_progress: state.status.completion_percentage,
            status,
            feature_overview,
            phases,
            current_tasks,
            tech_summary,
            cost,
            issues,
            change_log: Vec::new(), // 初始为空,后续通过 add_change_log 添加
            next_steps: NextSteps::from_feature_state(state),
        }
    }

    /// 加载或创建 Status 文档
    pub fn load_or_create(path: &Path, state: &FeatureState, spec: &str) -> Result<Self> {
        if path.exists() {
            Self::load(path)
        } else {
            Ok(Self::from_feature_state(state, spec))
        }
    }

    /// 从文件加载 (简化版: 重新生成)
    pub fn load(path: &Path) -> Result<Self> {
        // 简化实现: 我们不解析 markdown,而是依赖 state.yml
        // 在实际使用中,StatusDocument 总是从 state.yml 重新生成
        let content = std::fs::read_to_string(path)?;

        // 提取变更记录 (从 markdown 中解析)
        let change_log = parse_change_log_from_markdown(&content);

        // 其他字段需要从 state.yml 重新加载
        // 这里返回一个占位符,实际使用时会调用 from_feature_state
        Ok(Self {
            feature_name: String::new(),
            feature_slug: String::new(),
            created_at: Utc::now(),
            updated_at: Utc::now(),
            current_phase: 0,
            current_phase_name: String::new(),
            overall_progress: 0,
            status: ProjectStatus::InProgress,
            feature_overview: String::new(),
            phases: Vec::new(),
            current_tasks: Vec::new(),
            tech_summary: TechSummary::default(),
            cost: CostSummary::default(),
            issues: Vec::new(),
            change_log,
            next_steps: NextSteps::default(),
        })
    }

    /// 更新当前阶段
    pub fn update_current_phase(&mut self, phase: u8, phase_name: &str) {
        self.current_phase = phase;
        self.current_phase_name = phase_name.to_string();
        self.updated_at = Utc::now();
    }

    /// 更新整体进度
    pub fn update_overall_progress(&mut self, progress: u8) {
        self.overall_progress = progress;
        self.updated_at = Utc::now();
    }

    /// 更新阶段状态
    pub fn update_phase_status(&mut self, phase: u8, phase_state: &crate::state::PhaseState) {
        if let Some(p) = self.phases.iter_mut().find(|p| p.phase == phase) {
            *p = PhaseProgress::from_phase_state(phase_state);
        } else {
            self.phases
                .push(PhaseProgress::from_phase_state(phase_state));
        }
        self.updated_at = Utc::now();
    }

    /// 更新成本统计
    pub fn update_cost_summary(&mut self, cost: &crate::state::CostSummary) {
        self.cost.total_tokens_input = cost.total_tokens_input;
        self.cost.total_tokens_output = cost.total_tokens_output;
        self.cost.total_cost_usd = cost.total_cost_usd;
        self.cost.estimated_remaining_cost_usd = cost.estimated_remaining_cost_usd;
        self.updated_at = Utc::now();
    }

    /// 添加问题
    pub fn add_issue(&mut self, issue: Issue) {
        self.issues.push(issue);
        self.updated_at = Utc::now();
    }

    /// 添加变更记录
    pub fn add_change_log(&mut self, entry: ChangeLogEntry) {
        self.change_log.push(entry);
        // 保持最近 20 条记录
        if self.change_log.len() > 20 {
            self.change_log = self.change_log.split_off(self.change_log.len() - 20);
        }
        self.updated_at = Utc::now();
    }

    /// 渲染为 Markdown
    pub fn render_to_markdown(&self) -> String {
        render_status_markdown(self)
    }

    /// 保存到文件
    pub fn save(&self, path: &Path) -> Result<()> {
        // 确保目录存在
        if let Some(parent) = path.parent() {
            std::fs::create_dir_all(parent)?;
        }

        let markdown = self.render_to_markdown();
        std::fs::write(path, markdown)?;

        tracing::info!("Status 文档已保存: {}", path.display());
        Ok(())
    }
}

//
// 辅助函数
//

/// 从 spec 中提取功能概述
fn extract_overview_from_spec(spec: &str) -> String {
    let lines: Vec<&str> = spec.lines().collect();
    let mut overview = String::new();
    let mut in_overview = false;

    for line in lines {
        let trimmed = line.trim();

        // 查找概述部分
        if trimmed.starts_with("## 概述") || trimmed.starts_with("## Overview") {
            in_overview = true;
            continue;
        }

        // 遇到下一个标题,停止
        if in_overview && trimmed.starts_with("##") {
            break;
        }

        if in_overview && !trimmed.is_empty() {
            overview.push_str(line);
            overview.push('\n');
        }
    }

    if overview.is_empty() {
        "暂无功能概述".to_string()
    } else {
        overview.trim().to_string()
    }
}

/// 确定项目状态
fn determine_project_status(state: &FeatureState) -> ProjectStatus {
    use crate::state::Status;

    match state.status.overall_status {
        Status::Completed => ProjectStatus::Completed,
        Status::Failed => ProjectStatus::Blocked,
        Status::Paused => ProjectStatus::Paused,
        Status::InProgress => ProjectStatus::InProgress,
        Status::Pending => ProjectStatus::InProgress,
    }
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

/// 从 markdown 中解析变更记录 (简化实现)
fn parse_change_log_from_markdown(_content: &str) -> Vec<ChangeLogEntry> {
    // 简化实现: 返回空列表
    // 实际实现需要解析 markdown 中的 "## 📝 变更记录" 部分
    Vec::new()
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::state::FeatureState;

    #[test]
    fn test_status_document_creation() {
        let state = FeatureState::new(
            "test-feature".to_string(),
            "Test Feature".to_string(),
            "Claude".to_string(),
            "claude-3-5-sonnet-20241022".to_string(),
        );

        let spec = r#"
## 概述

这是一个测试功能。

## 需求

- 需求 1
- 需求 2
"#;

        let doc = StatusDocument::from_feature_state(&state, spec);

        assert_eq!(doc.feature_slug, "test-feature");
        assert_eq!(doc.status, ProjectStatus::InProgress);
        assert!(doc.feature_overview.contains("测试功能"));
    }

    #[test]
    fn test_status_markdown_rendering() {
        let state = FeatureState::new(
            "test-feature".to_string(),
            "Test Feature".to_string(),
            "Claude".to_string(),
            "claude-3-5-sonnet-20241022".to_string(),
        );

        let doc = StatusDocument::from_feature_state(&state, "## 概述\n测试");
        let markdown = doc.render_to_markdown();

        assert!(markdown.contains("功能开发状态"));
        assert!(markdown.contains("test-feature"));
        assert!(markdown.contains("📊 执行进度"));
    }
}
