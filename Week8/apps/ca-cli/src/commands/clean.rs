//! `code-agent clean` 命令实现
//!
//! 清理已完成的功能

use std::fs;
use std::io::{self, Write};
use std::path::{Path, PathBuf};

use anyhow::{Context, Result};
use ca_core::state::{FeatureState, Status};
use tracing::debug;

use crate::config::AppConfig;

/// 清理候选项
#[derive(Debug)]
struct CleanCandidate {
    /// Feature 目录名
    dir_name: String,
    /// Feature 目录路径
    path: PathBuf,
    /// Feature slug
    slug: String,
    /// 清理原因
    reason: CleanReason,
}

/// 清理原因
#[derive(Debug, Clone, PartialEq)]
enum CleanReason {
    /// PR 已合并
    PrMerged(u32),
    /// PR 已关闭
    PrClosed(u32),
    /// 功能已完成但无 PR (需要确认)
    CompletedNoPr,
    /// 功能失败 (需要 force)
    Failed,
    /// 功能进行中 (需要 force)
    InProgress,
}

/// 执行 clean 命令
pub async fn execute_clean(dry_run: bool, force: bool, config: &AppConfig) -> Result<()> {
    debug!(dry_run = dry_run, force = force, "执行 clean 命令");

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

    // 收集清理候选项
    let candidates = collect_clean_candidates(&specs_dir, force).await?;

    if candidates.is_empty() {
        println!("✨ 没有需要清理的功能");
        return Ok(());
    }

    // 分类候选项
    let (can_clean, need_force) = categorize_candidates(&candidates, force);

    // 显示将要清理的项目
    if !can_clean.is_empty() {
        println!("将清理以下功能:");
        println!();
        for candidate in &can_clean {
            print_candidate(candidate);
        }
    }

    // 显示跳过的项目
    if !need_force.is_empty() {
        println!();
        println!("跳过以下功能:");
        println!();
        for candidate in &need_force {
            print_skipped_candidate(candidate);
        }
    }

    println!();
    println!("总计: {} 个功能将被清理", can_clean.len());

    // 如果是 dry-run，提示如何执行
    if dry_run {
        println!();
        println!("运行 'code-agent clean' 执行清理");
        if !need_force.is_empty() {
            println!("运行 'code-agent clean --force' 强制清理所有功能 (危险操作)");
        }
        return Ok(());
    }

    // 执行清理
    if !can_clean.is_empty() {
        // 请求确认
        if !confirm_clean(can_clean.len())? {
            println!("❌ 已取消清理");
            return Ok(());
        }

        println!();
        println!("🧹 开始清理...");
        let cleaned = perform_clean(&can_clean)?;
        println!();
        println!("✅ 已清理 {} 个功能", cleaned);
    }

    Ok(())
}

/// 收集清理候选项
async fn collect_clean_candidates(
    specs_dir: &Path,
    force: bool,
) -> Result<Vec<CleanCandidate>> {
    let entries = fs::read_dir(specs_dir)
        .with_context(|| format!("无法读取目录: {}", specs_dir.display()))?;

    let mut candidates = Vec::new();

    for entry in entries.flatten() {
        let path = entry.path();
        if !path.is_dir() {
            continue;
        }

        let dir_name = match path.file_name().and_then(|n| n.to_str()) {
            Some(name) if !name.starts_with('.') => name.to_string(),
            _ => continue,
        };

        // 检查是否有 state.yml
        let state_file = path.join("state.yml");
        if !state_file.exists() {
            debug!(dir = %dir_name, "跳过无 state.yml 的目录");
            continue;
        }

        // 加载状态
        match load_feature_state(&state_file) {
            Ok(state) => {
                if let Some(candidate) = analyze_feature(&dir_name, &path, &state, force).await {
                    candidates.push(candidate);
                }
            }
            Err(e) => {
                debug!(error = %e, dir = %dir_name, "加载 state.yml 失败");
            }
        }
    }

    Ok(candidates)
}

/// 分析 feature 是否可以清理
async fn analyze_feature(
    dir_name: &str,
    path: &Path,
    state: &FeatureState,
    _force: bool,
) -> Option<CleanCandidate> {
    let reason = match state.status.overall_status {
        Status::Completed => {
            // 检查 PR 状态
            if let Some(pr_number) = state.delivery.pr_number {
                match get_pr_status(pr_number).await {
                    Ok(status) => {
                        if status == "MERGED" {
                            CleanReason::PrMerged(pr_number)
                        } else if status == "CLOSED" {
                            CleanReason::PrClosed(pr_number)
                        } else {
                            // PR 仍然 open，不清理
                            return None;
                        }
                    }
                    Err(e) => {
                        debug!(error = %e, pr_number = pr_number, "获取 PR 状态失败");
                        // 如果无法获取 PR 状态，检查 delivery 中的 merged 标记
                        if state.delivery.merged {
                            CleanReason::PrMerged(pr_number)
                        } else {
                            return None;
                        }
                    }
                }
            } else {
                // 已完成但无 PR
                CleanReason::CompletedNoPr
            }
        }
        Status::Failed => CleanReason::Failed,
        Status::InProgress => CleanReason::InProgress,
        Status::Pending | Status::Paused => {
            // 不清理 pending 或 paused 的功能
            return None;
        }
    };

    Some(CleanCandidate {
        dir_name: dir_name.to_string(),
        path: path.to_path_buf(),
        slug: state.feature.slug.clone(),
        reason,
    })
}

/// 加载 feature state
fn load_feature_state(state_file: &Path) -> Result<FeatureState> {
    let content = fs::read_to_string(state_file)
        .with_context(|| format!("无法读取文件: {}", state_file.display()))?;
    let state: FeatureState = serde_yaml::from_str(&content)
        .with_context(|| format!("无法解析 state.yml: {}", state_file.display()))?;
    Ok(state)
}

/// 获取 PR 状态 (使用 gh CLI)
async fn get_pr_status(pr_number: u32) -> Result<String> {
    let output = tokio::process::Command::new("gh")
        .args([
            "pr",
            "view",
            &pr_number.to_string(),
            "--json",
            "state",
            "-q",
            ".state",
        ])
        .output()
        .await
        .context("执行 gh 命令失败")?;

    if !output.status.success() {
        anyhow::bail!("gh 命令返回错误");
    }

    let status = String::from_utf8(output.stdout)
        .context("解析 gh 输出失败")?
        .trim()
        .to_uppercase();

    Ok(status)
}

/// 分类候选项
fn categorize_candidates(
    candidates: &[CleanCandidate],
    force: bool,
) -> (Vec<CleanCandidate>, Vec<CleanCandidate>) {
    let mut can_clean = Vec::new();
    let mut need_force = Vec::new();

    for candidate in candidates {
        match &candidate.reason {
            CleanReason::PrMerged(_) | CleanReason::PrClosed(_) => {
                can_clean.push(candidate.clone());
            }
            CleanReason::CompletedNoPr => {
                if force {
                    can_clean.push(candidate.clone());
                } else {
                    need_force.push(candidate.clone());
                }
            }
            CleanReason::Failed | CleanReason::InProgress => {
                if force {
                    can_clean.push(candidate.clone());
                } else {
                    need_force.push(candidate.clone());
                }
            }
        }
    }

    (can_clean, need_force)
}

/// 打印候选项
fn print_candidate(candidate: &CleanCandidate) {
    let reason_text = match &candidate.reason {
        CleanReason::PrMerged(pr) => format!("PR #{} 已合并", pr),
        CleanReason::PrClosed(pr) => format!("PR #{} 已关闭", pr),
        CleanReason::CompletedNoPr => "已完成但无 PR".to_string(),
        CleanReason::Failed => "执行失败".to_string(),
        CleanReason::InProgress => "执行中".to_string(),
    };

    println!("  ✓ {} ({})", candidate.dir_name, reason_text);
    println!("    - {}", candidate.path.display());
}

/// 打印跳过的候选项
fn print_skipped_candidate(candidate: &CleanCandidate) {
    let reason_text = match &candidate.reason {
        CleanReason::CompletedNoPr => "已完成但无 PR (需要 --force)",
        CleanReason::Failed => "执行失败 (需要 --force)",
        CleanReason::InProgress => "执行中 (需要 --force)",
        _ => "未知原因",
    };

    println!("  ⚠ {} ({})", candidate.dir_name, reason_text);
}

/// 请求用户确认
fn confirm_clean(count: usize) -> Result<bool> {
    print!("⚠️  确认删除 {} 个功能目录? [y/N] ", count);
    io::stdout().flush()?;

    let mut input = String::new();
    io::stdin().read_line(&mut input)?;

    Ok(input.trim().eq_ignore_ascii_case("y"))
}

/// 执行清理
fn perform_clean(candidates: &[CleanCandidate]) -> Result<usize> {
    let mut cleaned = 0;

    for candidate in candidates {
        match fs::remove_dir_all(&candidate.path) {
            Ok(()) => {
                println!("  ✓ 已删除: {}", candidate.dir_name);
                cleaned += 1;
            }
            Err(e) => {
                eprintln!("  ✗ 删除失败 {}: {}", candidate.dir_name, e);
            }
        }
    }

    Ok(cleaned)
}

impl Clone for CleanCandidate {
    fn clone(&self) -> Self {
        Self {
            dir_name: self.dir_name.clone(),
            path: self.path.clone(),
            slug: self.slug.clone(),
            reason: self.reason.clone(),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_categorize_candidates() {
        let candidates = vec![
            CleanCandidate {
                dir_name: "001-merged".to_string(),
                path: PathBuf::from("/tmp/001"),
                slug: "merged".to_string(),
                reason: CleanReason::PrMerged(123),
            },
            CleanCandidate {
                dir_name: "002-in-progress".to_string(),
                path: PathBuf::from("/tmp/002"),
                slug: "in-progress".to_string(),
                reason: CleanReason::InProgress,
            },
        ];

        // 不带 force
        let (can_clean, need_force) = categorize_candidates(&candidates, false);
        assert_eq!(can_clean.len(), 1);
        assert_eq!(need_force.len(), 1);

        // 带 force
        let (can_clean, need_force) = categorize_candidates(&candidates, true);
        assert_eq!(can_clean.len(), 2);
        assert_eq!(need_force.len(), 0);
    }
}
