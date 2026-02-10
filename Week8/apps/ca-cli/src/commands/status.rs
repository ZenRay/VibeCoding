//! `code-agent status` 命令实现
//!
//! 查看单个功能的详细状态

use std::fs;
use std::path::Path;

use anyhow::{Context, Result};
use ca_core::state::{FeatureState, Status};
use chrono::{DateTime, Local, Utc};
use comfy_table::{Cell, Color, Table};
use tracing::debug;

use crate::config::AppConfig;

/// 执行 status 命令
pub async fn execute_status(feature_slug: String, config: &AppConfig) -> Result<()> {
    debug!(feature_slug = %feature_slug, "执行 status 命令");

    // 确定工作目录
    let current_dir = std::env::current_dir()?;
    let repo_path = config
        .default_repo
        .as_ref()
        .unwrap_or(&current_dir);

    let specs_dir = repo_path.join("specs");
    if !specs_dir.exists() {
        anyhow::bail!("❌ specs/ 目录不存在: {}", specs_dir.display());
    }

    // 查找 feature 目录
    let feature_dir = find_feature_dir(&specs_dir, &feature_slug)?;

    // 加载状态
    let state_file = feature_dir.join("state.yml");
    if !state_file.exists() {
        anyhow::bail!(
            "❌ 功能 '{}' 没有 state.yml 文件",
            feature_slug
        );
    }

    let state = load_feature_state(&state_file)?;

    // 显示详细信息
    print_feature_info(&state, &feature_dir);
    println!();
    print_phases_table(&state);
    println!();
    print_total_stats(&state);
    println!();
    print_delivery_info(&state).await;

    Ok(())
}

/// 查找 feature 目录
fn find_feature_dir(specs_dir: &Path, feature_slug: &str) -> Result<std::path::PathBuf> {
    let entries = fs::read_dir(specs_dir)
        .with_context(|| format!("无法读取目录: {}", specs_dir.display()))?;

    for entry in entries.flatten() {
        let path = entry.path();
        if !path.is_dir() {
            continue;
        }

        let dir_name = match path.file_name().and_then(|n| n.to_str()) {
            Some(name) => name,
            None => continue,
        };

        // 检查目录名是否包含 feature_slug
        // 支持 "001-feature-slug" 或 "feature-slug" 格式
        if dir_name == feature_slug || dir_name.ends_with(&format!("-{}", feature_slug)) {
            return Ok(path);
        }
    }

    anyhow::bail!("❌ 未找到功能: {}", feature_slug)
}

/// 加载 feature state
fn load_feature_state(state_file: &Path) -> Result<FeatureState> {
    let content = fs::read_to_string(state_file)
        .with_context(|| format!("无法读取文件: {}", state_file.display()))?;
    let state: FeatureState = serde_yaml::from_str(&content)
        .with_context(|| format!("无法解析 state.yml: {}", state_file.display()))?;
    Ok(state)
}

/// 打印 feature 基本信息
fn print_feature_info(state: &FeatureState, feature_dir: &Path) {
    // 提取 feature ID
    let feature_id = feature_dir
        .file_name()
        .and_then(|n| n.to_str())
        .and_then(|name| name.split('-').next())
        .unwrap_or("???");

    println!("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
    println!("📦 Feature: {} ({})", state.feature.slug, feature_id);
    println!("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
    println!();
    println!("名称:      {}", state.feature.name);
    println!("状态:      {}", format_status_with_emoji(&state.status.overall_status));
    println!("进度:      {}%", state.status.completion_percentage);
    println!("创建时间:  {}", format_datetime(&state.feature.created_at));
    println!("更新时间:  {}", format_datetime(&state.feature.updated_at));
    println!("Agent:     {} ({})", state.agent.agent_type, state.agent.model);
    println!("分支:      {}", state.metadata.target_branch);
}

/// 打印 phases 表格
fn print_phases_table(state: &FeatureState) {
    println!("阶段执行情况:");
    println!();

    let mut table = Table::new();
    table.set_header(vec!["#", "名称", "状态", "耗时", "成本"]);

    for phase in &state.phases {
        let status_cell = Cell::new(format_status(&phase.status))
            .fg(status_color(&phase.status));

        let duration = if let Some(seconds) = phase.duration_seconds {
            format_duration(seconds)
        } else {
            "-".to_string()
        };

        let cost = if let Some(ref cost_info) = phase.cost {
            format!("${:.2}", cost_info.cost_usd)
        } else {
            "-".to_string()
        };

        table.add_row(vec![
            Cell::new(phase.phase.to_string()),
            Cell::new(&phase.name),
            status_cell,
            Cell::new(duration),
            Cell::new(cost),
        ]);
    }

    println!("{table}");
}

/// 打印总体统计
fn print_total_stats(state: &FeatureState) {
    println!("总体统计:");
    println!();
    
    // 计算总 turns (从 phases 中累加)
    let _total_turns: u32 = state.phases.iter()
        .filter_map(|p| p.cost.as_ref())
        .map(|c| c.tokens_input + c.tokens_output)
        .sum::<u32>() / 1000; // 粗略估算

    println!("  • 输入 tokens:  {:>12}", format_number(state.cost_summary.total_tokens_input));
    println!("  • 输出 tokens:  {:>12}", format_number(state.cost_summary.total_tokens_output));
    println!("  • 总成本:       {:>12}", format!("${:.2}", state.cost_summary.total_cost_usd));
    
    if state.cost_summary.estimated_remaining_cost_usd > 0.0 {
        println!("  • 预计剩余成本: {:>12}", format!("${:.2}", state.cost_summary.estimated_remaining_cost_usd));
    }

    // 文件修改统计
    if !state.files_modified.is_empty() {
        println!();
        println!("  • 修改文件数:   {:>12}", state.files_modified.len());
    }

    // 错误统计
    let unresolved_errors = state.errors.iter().filter(|e| !e.resolved).count();
    if unresolved_errors > 0 {
        println!();
        println!("  ⚠️  未解决错误:   {:>12}", unresolved_errors);
    }
}

/// 打印交付信息
async fn print_delivery_info(state: &FeatureState) {
    println!("交付信息:");
    println!();

    if let Some(ref pr_url) = state.delivery.pr_url {
        println!("  • PR URL:  {}", pr_url);
        
        // 尝试获取 PR 状态
        if let Some(pr_number) = state.delivery.pr_number {
            match get_pr_status(pr_number).await {
                Ok(status) => {
                    let status_emoji = match status.as_str() {
                        "MERGED" => "✓",
                        "CLOSED" => "✗",
                        "OPEN" => "○",
                        _ => "?",
                    };
                    println!("  • PR 状态: {} {}", status_emoji, status);
                }
                Err(e) => {
                    debug!(error = %e, "获取 PR 状态失败");
                }
            }
        }

        if state.delivery.merged {
            if let Some(merged_at) = state.delivery.merged_at {
                println!("  • 合并时间: {}", format_datetime(&merged_at));
            }
        }
    } else {
        println!("  (尚未创建 PR)");
    }
}

/// 获取 PR 状态 (使用 gh CLI)
async fn get_pr_status(pr_number: u32) -> Result<String> {
    let output = tokio::process::Command::new("gh")
        .args(["pr", "view", &pr_number.to_string(), "--json", "state", "-q", ".state"])
        .output()
        .await
        .context("执行 gh 命令失败")?;

    if !output.status.success() {
        anyhow::bail!("gh 命令返回错误");
    }

    let status = String::from_utf8(output.stdout)
        .context("解析 gh 输出失败")?
        .trim()
        .to_string();

    Ok(status)
}

/// 格式化状态显示（带 emoji）
fn format_status_with_emoji(status: &Status) -> String {
    match status {
        Status::Pending => "⏸️  planned",
        Status::InProgress => "🔄 inProgress",
        Status::Completed => "✅ completed",
        Status::Failed => "❌ failed",
        Status::Paused => "⏸️  paused",
    }
    .to_string()
}

/// 格式化状态显示
fn format_status(status: &Status) -> String {
    match status {
        Status::Pending => "planned",
        Status::InProgress => "inProgress",
        Status::Completed => "completed",
        Status::Failed => "failed",
        Status::Paused => "paused",
    }
    .to_string()
}

/// 获取状态颜色
fn status_color(status: &Status) -> Color {
    match status {
        Status::Pending => Color::Yellow,
        Status::InProgress => Color::Cyan,
        Status::Completed => Color::Green,
        Status::Failed => Color::Red,
        Status::Paused => Color::Magenta,
    }
}

/// 格式化日期时间
fn format_datetime(dt: &DateTime<Utc>) -> String {
    let local: DateTime<Local> = DateTime::from(*dt);
    local.format("%Y-%m-%d %H:%M:%S").to_string()
}

/// 格式化持续时间
fn format_duration(seconds: u64) -> String {
    if seconds < 60 {
        format!("{}s", seconds)
    } else if seconds < 3600 {
        format!("{}m {}s", seconds / 60, seconds % 60)
    } else {
        format!("{}h {}m", seconds / 3600, (seconds % 3600) / 60)
    }
}

/// 格式化数字（添加千位分隔符）
fn format_number(n: u32) -> String {
    let s = n.to_string();
    let mut result = String::new();
    for (i, ch) in s.chars().rev().enumerate() {
        if i > 0 && i % 3 == 0 {
            result.push(',');
        }
        result.push(ch);
    }
    result.chars().rev().collect()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_format_duration() {
        assert_eq!(format_duration(30), "30s");
        assert_eq!(format_duration(90), "1m 30s");
        assert_eq!(format_duration(3661), "1h 1m");
    }

    #[test]
    fn test_format_number() {
        assert_eq!(format_number(123), "123");
        assert_eq!(format_number(1234), "1,234");
        assert_eq!(format_number(1234567), "1,234,567");
    }
}
