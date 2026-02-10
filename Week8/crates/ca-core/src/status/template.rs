//! Status 文档 Markdown 模板渲染

use super::*;
use chrono::{DateTime, Utc};

/// 渲染 Status 文档为 Markdown
pub fn render_status_markdown(doc: &StatusDocument) -> String {
    let mut output = String::new();
    
    // 标题和基本信息
    output.push_str(&render_header(doc));
    output.push_str("\n---\n\n");
    
    // 功能概述
    output.push_str(&render_overview(doc));
    output.push_str("\n---\n\n");
    
    // 执行进度
    output.push_str(&render_progress(doc));
    output.push_str("\n---\n\n");
    
    // 技术实施摘要
    output.push_str(&render_tech_summary(doc));
    output.push_str("\n---\n\n");
    
    // 成本追踪
    output.push_str(&render_cost(doc));
    output.push_str("\n---\n\n");
    
    // 当前问题和风险
    output.push_str(&render_issues(doc));
    output.push_str("\n---\n\n");
    
    // 变更记录
    output.push_str(&render_changelog(doc));
    output.push_str("\n---\n\n");
    
    // 下一步计划
    output.push_str(&render_next_steps(doc));
    output.push_str("\n---\n\n");
    
    // 页脚
    output.push_str(&render_footer(doc));
    
    output
}

/// 渲染头部
fn render_header(doc: &StatusDocument) -> String {
    format!(
        r#"# 功能开发状态 - {}

**功能编号**: {}  
**创建时间**: {}  
**最后更新**: {}  
**当前阶段**: Phase {} - {}  
**整体进度**: {}%  
**状态**: {}"#,
        doc.feature_name,
        doc.feature_slug,
        format_datetime(&doc.created_at),
        format_datetime(&doc.updated_at),
        doc.current_phase,
        doc.current_phase_name,
        doc.overall_progress,
        format_project_status(doc.status)
    )
}

/// 渲染功能概述
fn render_overview(doc: &StatusDocument) -> String {
    format!(
        r#"## 📋 功能概述

{}"#,
        doc.feature_overview
    )
}

/// 渲染执行进度
fn render_progress(doc: &StatusDocument) -> String {
    let mut output = String::from("## 📊 执行进度\n\n### 阶段完成情况\n\n");
    
    // 阶段表格
    output.push_str("| 阶段 | 名称 | 状态 | 开始时间 | 完成时间 | 耗时 | 成本 |\n");
    output.push_str("|------|------|------|----------|----------|------|------|\n");
    
    // 确保显示所有 7 个阶段
    for phase_num in 1..=7 {
        if let Some(phase) = doc.phases.iter().find(|p| p.phase == phase_num) {
            output.push_str(&format!(
                "| Phase {} | {} | {} | {} | {} | {} | {} |\n",
                phase.phase,
                phase.name,
                format_phase_status(phase.status),
                format_optional_datetime(&phase.started_at),
                format_optional_datetime(&phase.completed_at),
                format_optional_duration(phase.duration_seconds),
                format_optional_cost(phase.cost_usd)
            ));
        } else {
            output.push_str(&format!(
                "| Phase {} | {} | {} | - | - | - | - |\n",
                phase_num,
                super::get_phase_name(phase_num),
                format_phase_status(PhaseStatus::Pending)
            ));
        }
    }
    
    // 进度统计
    let completed_count = doc.phases.iter().filter(|p| p.status == PhaseStatus::Completed).count();
    let in_progress_count = doc.phases.iter().filter(|p| p.status == PhaseStatus::InProgress).count();
    let pending_count = 7 - completed_count - in_progress_count;
    
    output.push_str(&format!(
        r#"

**进度统计**:
- 已完成: {}/7 阶段
- 进行中: {}/7 阶段
- 待开始: {}/7 阶段
- 总体进度: {}%
"#,
        completed_count,
        in_progress_count,
        pending_count,
        doc.overall_progress
    ));
    
    // 当前任务
    if !doc.current_tasks.is_empty() {
        output.push_str("\n### 当前任务进度\n\n");
        output.push_str(&format!("**Phase {} 任务**:\n", doc.current_phase));
        
        for task in &doc.current_tasks {
            let progress_str = if let Some(p) = task.progress_percentage {
                format!(" ({}%)", p)
            } else {
                String::new()
            };
            
            output.push_str(&format!(
                "- {} {}: {}{}\n",
                format_task_status(task.status),
                task.id,
                task.description,
                progress_str
            ));
        }
    }
    
    output
}

/// 渲染技术摘要
fn render_tech_summary(doc: &StatusDocument) -> String {
    let mut output = String::from("## 🔧 技术实施摘要\n\n");
    
    // 已完成的工作
    if !doc.tech_summary.completed_work.is_empty() {
        output.push_str("### 已完成的主要工作\n\n");
        for work in &doc.tech_summary.completed_work {
            output.push_str(&format!("- {}\n", work));
        }
        output.push('\n');
    }
    
    // 代码修改统计
    if !doc.tech_summary.code_changes.is_empty() {
        output.push_str("### 代码修改统计\n\n");
        output.push_str("| 文件 | 状态 | 行数变化 | 说明 |\n");
        output.push_str("|------|------|----------|------|\n");
        
        for change in &doc.tech_summary.code_changes {
            output.push_str(&format!(
                "| `{}` | {} | {} | {} |\n",
                change.file,
                format_file_status(&change.status),
                change.lines_changed.as_deref().unwrap_or("-"),
                if change.description.is_empty() { "-" } else { &change.description }
            ));
        }
        
        output.push_str(&format!(
            "\n**总计**: {} 个文件变更\n",
            doc.tech_summary.code_changes.len()
        ));
    } else {
        output.push_str("暂无代码修改记录\n");
    }
    
    output
}

/// 渲染成本统计
fn render_cost(doc: &StatusDocument) -> String {
    let mut output = String::from("## 💰 成本追踪\n\n");
    
    output.push_str("| 项目 | 数值 |\n");
    output.push_str("|------|------|\n");
    output.push_str(&format!(
        "| **总 Token 使用** | {} input + {} output |\n",
        format_number(doc.cost.total_tokens_input),
        format_number(doc.cost.total_tokens_output)
    ));
    output.push_str(&format!("| **累计成本** | ${:.2} |\n", doc.cost.total_cost_usd));
    output.push_str(&format!(
        "| **预估剩余成本** | ${:.2} |\n",
        doc.cost.estimated_remaining_cost_usd
    ));
    
    let total_estimated = doc.cost.total_cost_usd + doc.cost.estimated_remaining_cost_usd;
    let used_percentage = if total_estimated > 0.0 {
        (doc.cost.total_cost_usd / total_estimated * 100.0) as u8
    } else {
        0
    };
    
    let budget_status = if used_percentage < 60 {
        "🟢 正常"
    } else if used_percentage < 80 {
        "🟡 注意"
    } else {
        "🔴 超支"
    };
    
    output.push_str(&format!(
        "| **预算状态** | {} ({}% 已使用) |\n",
        budget_status, used_percentage
    ));
    
    // 阶段成本明细
    if !doc.cost.phase_costs.is_empty() {
        output.push_str("\n**阶段成本明细**:\n");
        for phase in &doc.cost.phase_costs {
            output.push_str(&format!("- Phase {}: ${:.2}\n", phase.phase, phase.cost_usd));
        }
    }
    
    output
}

/// 渲染问题列表
fn render_issues(doc: &StatusDocument) -> String {
    let mut output = String::from("## ⚠️ 当前问题和风险\n\n");
    
    if doc.issues.is_empty() {
        output.push_str("🎉 暂无问题和风险\n");
        return output;
    }
    
    // 按严重程度分组
    let critical: Vec<_> = doc.issues.iter().filter(|i| i.severity == IssueSeverity::Critical).collect();
    let high: Vec<_> = doc.issues.iter().filter(|i| i.severity == IssueSeverity::High).collect();
    let medium: Vec<_> = doc.issues.iter().filter(|i| i.severity == IssueSeverity::Medium).collect();
    let low: Vec<_> = doc.issues.iter().filter(|i| i.severity == IssueSeverity::Low).collect();
    
    // 阻塞问题
    output.push_str(&format!("### 阻塞问题 ({})\n\n", critical.len()));
    if critical.is_empty() {
        output.push_str("无\n\n");
    } else {
        for (i, issue) in critical.iter().enumerate() {
            output.push_str(&format_issue(i + 1, issue));
        }
    }
    
    // 高优先级问题
    output.push_str(&format!("### 高优先级问题 ({})\n\n", high.len()));
    if high.is_empty() {
        output.push_str("无\n\n");
    } else {
        for (i, issue) in high.iter().enumerate() {
            output.push_str(&format_issue(i + 1, issue));
        }
    }
    
    // 中优先级问题
    if !medium.is_empty() {
        output.push_str(&format!("### 中优先级问题 ({})\n\n", medium.len()));
        for (i, issue) in medium.iter().enumerate() {
            output.push_str(&format_issue(i + 1, issue));
        }
    }
    
    // 低优先级问题
    if !low.is_empty() {
        output.push_str(&format!("### 低优先级问题 ({})\n\n", low.len()));
        for (i, issue) in low.iter().enumerate() {
            output.push_str(&format_issue(i + 1, issue));
        }
    }
    
    output
}

/// 渲染单个问题
fn format_issue(num: usize, issue: &Issue) -> String {
    format!(
        r#"{}. **{}** ({})
   - **问题**: {}
   - **影响**: {}
   - **计划**: {}
   - **状态**: {}

"#,
        num,
        issue.title,
        issue.category,
        issue.description,
        issue.impact,
        issue.plan,
        format_issue_status(issue.status)
    )
}

/// 渲染变更记录
fn render_changelog(doc: &StatusDocument) -> String {
    let mut output = String::from("## 📝 变更记录\n\n");
    
    if doc.change_log.is_empty() {
        output.push_str("暂无变更记录\n");
        return output;
    }
    
    output.push_str("### 最近更新 (最新 5 条)\n\n");
    
    for (i, entry) in doc.change_log.iter().rev().take(5).enumerate() {
        output.push_str(&format!(
            "{}. **{}** - {}\n",
            i + 1,
            format_datetime(&entry.timestamp),
            entry.message
        ));
    }
    
    output
}

/// 渲染下一步计划
fn render_next_steps(doc: &StatusDocument) -> String {
    let mut output = String::from("## 🎯 下一步计划\n\n");
    
    // 立即行动
    output.push_str("### 立即行动 (今天)\n\n");
    if doc.next_steps.immediate.is_empty() {
        output.push_str("暂无立即行动项\n\n");
    } else {
        for item in &doc.next_steps.immediate {
            output.push_str(&format!("- {}\n", item));
        }
        output.push('\n');
    }
    
    // 短期目标
    output.push_str("### 短期目标 (本周)\n\n");
    if doc.next_steps.short_term.is_empty() {
        output.push_str("暂无短期目标\n\n");
    } else {
        for item in &doc.next_steps.short_term {
            output.push_str(&format!("- {}\n", item));
        }
        output.push('\n');
    }
    
    // 长期目标
    output.push_str("### 长期目标\n\n");
    if doc.next_steps.long_term.is_empty() {
        output.push_str("暂无长期目标\n\n");
    } else {
        for item in &doc.next_steps.long_term {
            output.push_str(&format!("- {}\n", item));
        }
        output.push('\n');
    }
    
    output
}

/// 渲染页脚
fn render_footer(doc: &StatusDocument) -> String {
    format!(
        r#"## 📞 联系信息

- **项目负责人**: Code Agent
- **开发团队**: AI Agent
- **问题报告**: 更新此文档的"当前问题和风险"部分
- **状态查询**: 查看 `state.yml` 获取实时状态

---

**文档版本**: 1.0  
**自动生成**: 由 Code Agent 自动维护  
**最后更新**: {}"#,
        format_datetime(&doc.updated_at)
    )
}

//
// 格式化辅助函数
//

fn format_datetime(dt: &DateTime<Utc>) -> String {
    dt.format("%Y-%m-%d %H:%M:%S").to_string()
}

fn format_optional_datetime(dt: &Option<DateTime<Utc>>) -> String {
    dt.as_ref()
        .map(|d: &DateTime<Utc>| d.format("%Y-%m-%d %H:%M").to_string())
        .unwrap_or_else(|| "-".to_string())
}

fn format_optional_duration(seconds: Option<u64>) -> String {
    seconds
        .map(|s| {
            if s < 60 {
                format!("{}秒", s)
            } else if s < 3600 {
                format!("{}分钟", s / 60)
            } else {
                format!("{}小时", s / 3600)
            }
        })
        .unwrap_or_else(|| "-".to_string())
}

fn format_optional_cost(cost: Option<f64>) -> String {
    cost.map(|c| format!("${:.2}", c))
        .unwrap_or_else(|| "-".to_string())
}

fn format_project_status(status: ProjectStatus) -> String {
    match status {
        ProjectStatus::InProgress => "🟢 进行中",
        ProjectStatus::Paused => "🟡 暂停",
        ProjectStatus::Blocked => "🔴 阻塞",
        ProjectStatus::Completed => "✅ 完成",
    }
    .to_string()
}

fn format_phase_status(status: PhaseStatus) -> String {
    match status {
        PhaseStatus::Pending => "⏳ 待开始",
        PhaseStatus::InProgress => "🟢 进行中",
        PhaseStatus::Completed => "✅ 完成",
        PhaseStatus::Failed => "🔴 失败",
    }
    .to_string()
}

fn format_task_status(status: TaskStatus) -> String {
    match status {
        TaskStatus::Pending => "⏳",
        TaskStatus::InProgress => "🟢",
        TaskStatus::Completed => "✅",
        TaskStatus::Failed => "🔴",
    }
    .to_string()
}

fn format_file_status(status: &str) -> String {
    match status {
        "added" => "✅ 已添加".to_string(),
        "modified" => "✅ 已修改".to_string(),
        "in_progress" => "🟢 进行中".to_string(),
        "deleted" => "❌ 已删除".to_string(),
        _ => status.to_string(),
    }
}

fn format_issue_status(status: IssueStatus) -> String {
    match status {
        IssueStatus::Pending => "⏳ 待处理",
        IssueStatus::InProgress => "🟡 处理中",
        IssueStatus::Resolved => "✅ 已解决",
        IssueStatus::Wontfix => "⚠️  不修复",
    }
    .to_string()
}

fn format_number(n: u32) -> String {
    // 简单的千位分隔符
    let s = n.to_string();
    let bytes = s.as_bytes();
    let len = bytes.len();
    
    if len <= 3 {
        return s;
    }
    
    let mut result = String::new();
    for (i, &b) in bytes.iter().enumerate() {
        if i > 0 && (len - i).is_multiple_of(3) {
            result.push(',');
        }
        result.push(b as char);
    }
    result
}
