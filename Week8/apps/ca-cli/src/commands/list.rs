//! `code-agent list` 命令实现
//!
//! 列出所有功能及其状态

use anyhow::{Context, Result};
use ca_core::state::{FeatureState, Status};
use comfy_table::{Table, modifiers::UTF8_ROUND_CORNERS, presets::UTF8_FULL};
use std::fs;
use std::path::{Path, PathBuf};
use tracing::debug;

use crate::config::AppConfig;

/// 功能信息（用于显示）
#[derive(Debug)]
struct FeatureInfo {
    id: String,
    slug: String,
    status: String,
    progress: String,
    cost: String,
}

/// 执行 list 命令
pub async fn execute_list(
    all: bool,
    status_filter: Option<String>,
    _config: &AppConfig,
) -> Result<()> {
    let repo_root = find_repo_root()?;
    let specs_dir = repo_root.join("specs");

    if !specs_dir.exists() {
        println!("📂 未找到 specs 目录");
        println!("   运行 'code-agent plan <feature-slug>' 创建第一个功能");
        return Ok(());
    }

    debug!("扫描功能目录: {}", specs_dir.display());

    let features = collect_features(&specs_dir)?;

    if features.is_empty() {
        println!("📂 没有找到任何功能");
        println!("   运行 'code-agent plan <feature-slug>' 创建第一个功能");
        return Ok(());
    }

    // 按状态筛选
    let filtered_features = if let Some(filter) = status_filter {
        features
            .into_iter()
            .filter(|f| f.status.to_lowercase() == filter.to_lowercase())
            .collect()
    } else if all {
        features
    } else {
        // 默认不显示已完成的
        features
            .into_iter()
            .filter(|f| f.status != "completed")
            .collect()
    };

    if filtered_features.is_empty() {
        println!("📂 没有匹配的功能");
        return Ok(());
    }

    // 使用 comfy-table 显示表格
    let mut table = Table::new();
    table
        .load_preset(UTF8_FULL)
        .apply_modifier(UTF8_ROUND_CORNERS)
        .set_header(vec!["ID", "SLUG", "STATUS", "PROGRESS", "COST"]);

    for feature in &filtered_features {
        table.add_row(vec![
            &feature.id,
            &feature.slug,
            &format_status(&feature.status),
            &feature.progress,
            &feature.cost,
        ]);
    }

    println!("{table}");
    println!();

    // 统计信息
    let total = filtered_features.len();
    let in_progress = filtered_features
        .iter()
        .filter(|f| f.status == "inprogress")
        .count();
    let completed = filtered_features
        .iter()
        .filter(|f| f.status == "completed")
        .count();
    let failed = filtered_features
        .iter()
        .filter(|f| f.status == "failed")
        .count();

    print!("📊 总计: {} 个功能", total);
    if in_progress > 0 {
        print!(" | 进行中: {}", in_progress);
    }
    if completed > 0 {
        print!(" | 已完成: {}", completed);
    }
    if failed > 0 {
        print!(" | 失败: {}", failed);
    }
    println!();

    Ok(())
}

/// 收集所有功能信息
fn collect_features(specs_dir: &Path) -> Result<Vec<FeatureInfo>> {
    let mut features = Vec::new();

    let entries = fs::read_dir(specs_dir)
        .with_context(|| format!("无法读取目录: {}", specs_dir.display()))?;

    for entry in entries.flatten() {
        let path = entry.path();
        if !path.is_dir() {
            continue;
        }

        let dir_name = match path.file_name().and_then(|n| n.to_str()) {
            Some(name) if !name.starts_with('.') => name,
            _ => continue,
        };

        // 查找 state.yml
        let state_file = path.join("state.yml");
        if !state_file.exists() {
            // 没有 state.yml 说明是刚 plan 的功能
            if let Some((id, slug)) = parse_feature_dir_name(dir_name) {
                features.push(FeatureInfo {
                    id,
                    slug,
                    status: "planned".to_string(),
                    progress: "-".to_string(),
                    cost: "-".to_string(),
                });
            }
            continue;
        }

        // 加载 state.yml
        match load_feature_state(&state_file) {
            Ok(state) => {
                let feature_info = extract_feature_info(state);
                features.push(feature_info);
            }
            Err(e) => {
                debug!("无法加载 state.yml: {} - {}", state_file.display(), e);
                if let Some((id, slug)) = parse_feature_dir_name(dir_name) {
                    features.push(FeatureInfo {
                        id,
                        slug,
                        status: "error".to_string(),
                        progress: "-".to_string(),
                        cost: "-".to_string(),
                    });
                }
            }
        }
    }

    // 按 ID 排序
    features.sort_by(|a, b| a.id.cmp(&b.id));

    Ok(features)
}

/// 加载 feature state
fn load_feature_state(state_file: &Path) -> Result<FeatureState> {
    let content = fs::read_to_string(state_file)
        .with_context(|| format!("无法读取文件: {}", state_file.display()))?;

    let state: FeatureState = serde_yaml::from_str(&content)
        .with_context(|| format!("无法解析 YAML: {}", state_file.display()))?;

    Ok(state)
}

/// 从 FeatureState 提取显示信息
fn extract_feature_info(state: FeatureState) -> FeatureInfo {
    // 提取 ID (从 slug 前缀，如 001-feature-name)
    let id = state
        .feature
        .slug
        .split('-')
        .next()
        .unwrap_or("???")
        .to_string();

    // 计算进度
    let total_phases = state.phases.len();
    let completed_phases = state
        .phases
        .iter()
        .filter(|p| p.status == Status::Completed)
        .count();

    let progress = if total_phases > 0 {
        format!("{}/{}", completed_phases, total_phases)
    } else {
        "-".to_string()
    };

    // 格式化成本
    let cost = if state.cost_summary.total_cost_usd > 0.0 {
        format!("${:.2}", state.cost_summary.total_cost_usd)
    } else {
        "-".to_string()
    };

    // 格式化状态
    let status = format!("{:?}", state.status.overall_status).to_lowercase();

    FeatureInfo {
        id,
        slug: state.feature.slug,
        status,
        progress,
        cost,
    }
}

/// 解析功能目录名 (格式: 001-feature-name)
fn parse_feature_dir_name(dir_name: &str) -> Option<(String, String)> {
    let parts: Vec<&str> = dir_name.splitn(2, '-').collect();
    if parts.len() == 2 {
        Some((parts[0].to_string(), dir_name.to_string()))
    } else {
        None
    }
}

/// 格式化状态显示（添加 emoji）
fn format_status(status: &str) -> String {
    match status {
        "planned" => "📋 planned".to_string(),
        "inprogress" => "🔄 inProgress".to_string(),
        "completed" => "✅ completed".to_string(),
        "failed" => "❌ failed".to_string(),
        "paused" => "⏸️  paused".to_string(),
        _ => status.to_string(),
    }
}

/// 查找仓库根目录
fn find_repo_root() -> Result<PathBuf> {
    let current = std::env::current_dir().context("无法获取当前目录")?;

    let mut path = current.as_path();
    loop {
        if path.join(".git").exists() {
            return Ok(path.to_path_buf());
        }

        path = match path.parent() {
            Some(p) => p,
            None => anyhow::bail!("未找到 Git 仓库根目录"),
        };
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_parse_feature_dir_name() {
        assert_eq!(
            parse_feature_dir_name("001-test-feature"),
            Some(("001".to_string(), "001-test-feature".to_string()))
        );

        assert_eq!(parse_feature_dir_name("invalid"), None);
    }

    #[test]
    fn test_format_status() {
        assert_eq!(format_status("planned"), "📋 planned");
        assert_eq!(format_status("inprogress"), "🔄 inProgress");
        assert_eq!(format_status("completed"), "✅ completed");
    }
}
