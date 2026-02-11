//! `code-agent clean` 命令实现
//!
//! 清理已完成功能的 worktree，仅针对 `.trees/` 目录。
//! **specs/ 目录作为功能历史存档，永久保留，绝不清理。**

use std::fs;
use std::io::{self, Write};
use std::path::{Path, PathBuf};

use anyhow::{Context, Result};
use ca_core::state::{FeatureState, Status};
use tracing::debug;

use crate::config::AppConfig;

/// 清理候选项 (仅 worktree)
#[derive(Debug, Clone)]
struct CleanCandidate {
    /// Feature 目录名 (如 001-add-user-auth)
    dir_name: String,
    /// specs 目录路径 (保留存档)
    specs_path: PathBuf,
    /// worktree 路径 (.trees/<dir_name>/)
    worktree_path: PathBuf,
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
}

/// 跳过的 worktree (安全保护)
#[derive(Debug, Clone)]
struct SkippedCandidate {
    dir_name: String,
    reason: SkipReason,
}

/// 跳过原因
#[derive(Debug, Clone)]
enum SkipReason {
    /// 进行中
    InProgress,
    /// PR 仍开放
    PrOpen(u32),
    /// 无 PR 信息
    NoPr,
}

/// 执行 clean 命令
///
/// 仅清理 `.trees/` 中的 worktree，绝不清理 `specs/` 目录。
pub async fn execute_clean(dry_run: bool, _all: bool, config: &AppConfig) -> Result<()> {
    debug!(dry_run = dry_run, "执行 clean 命令");

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

    let trees_dir = repo_path.join(".trees");
    if !trees_dir.exists() {
        println!("✨ .trees/ 目录不存在，无需清理");
        return Ok(());
    }

    // 扫描 specs/ 获取所有功能，检查 PR 状态，分类可清理与需跳过
    let (to_clean, skipped) =
        collect_and_classify(&specs_dir, &trees_dir, repo_path).await?;

    // 输出：将清理的 worktree
    if !to_clean.is_empty() {
        println!("将清理以下 worktree:\n");
        for c in &to_clean {
            let reason_text = match &c.reason {
                CleanReason::PrMerged(pr) => format!("PR #{} 已合并", pr),
                CleanReason::PrClosed(pr) => format!("PR #{} 已关闭", pr),
            };
            println!("✓ {} ({})", c.dir_name, reason_text);
            println!("  - {}     # 删除 worktree", c.worktree_path.display());
            println!("  - {}      # 保留存档 ✓", c.specs_path.display());
            println!();
        }
    }

    // 输出：跳过的 worktree (安全保护)
    if !skipped.is_empty() {
        println!("跳过以下 worktree (安全保护):\n");
        for s in &skipped {
            let reason_text = match &s.reason {
                SkipReason::InProgress => "进行中".to_string(),
                SkipReason::PrOpen(pr) => format!("PR #{} 仍开放", pr),
                SkipReason::NoPr => "无 PR 信息".to_string(),
            };
            println!("⚠ {} ({})", s.dir_name, reason_text);
        }
        println!();
    }

    let total = to_clean.len();
    println!("总计: {} 个 worktree 将被清理", total);
    println!("注意: specs/ 目录作为功能历史存档，永久保留");

    if total == 0 {
        return Ok(());
    }

    // dry-run 模式
    if dry_run {
        println!();
        println!("(dry-run) 运行 'code-agent clean' 执行实际清理");
        return Ok(());
    }

    // 请求确认
    if !confirm_clean(total)? {
        println!("❌ 已取消清理");
        return Ok(());
    }

    println!();
    println!("🧹 开始清理...");
    let cleaned = perform_clean(&to_clean)?;
    println!();
    println!("✅ 已清理 {} 个 worktree", cleaned);

    Ok(())
}

/// 扫描 specs/，检查 PR 状态，分类可清理与需跳过的 worktree
async fn collect_and_classify(
    specs_dir: &Path,
    trees_dir: &Path,
    repo_path: &Path,
) -> Result<(Vec<CleanCandidate>, Vec<SkippedCandidate>)> {
    let entries = fs::read_dir(specs_dir)
        .with_context(|| format!("无法读取目录: {}", specs_dir.display()))?;

    let mut to_clean = Vec::new();
    let mut skipped = Vec::new();

    for entry in entries.flatten() {
        let path = entry.path();
        if !path.is_dir() {
            continue;
        }

        let dir_name = match path.file_name().and_then(|n| n.to_str()) {
            Some(name) if !name.starts_with('.') => name.to_string(),
            _ => continue,
        };

        let worktree_path = trees_dir.join(&dir_name);
        if !worktree_path.exists() {
            debug!(dir = %dir_name, "无对应 worktree，跳过");
            continue;
        }

        let state_file = path.join("state.yml");
        if !state_file.exists() {
            debug!(dir = %dir_name, "跳过无 state.yml 的目录");
            continue;
        }

        let state = match load_feature_state(&state_file) {
            Ok(s) => s,
            Err(e) => {
                debug!(error = %e, dir = %dir_name, "加载 state.yml 失败");
                continue;
            }
        };

        match classify_feature(&dir_name, &path, &worktree_path, &state, repo_path).await {
            Some(Ok(candidate)) => to_clean.push(candidate),
            Some(Err(skip)) => skipped.push(skip),
            None => {}
        }
    }

    Ok((to_clean, skipped))
}

/// 分析 feature 状态，返回 CleanCandidate 或 SkippedCandidate
async fn classify_feature(
    dir_name: &str,
    specs_path: &Path,
    worktree_path: &Path,
    state: &FeatureState,
    repo_path: &Path,
) -> Option<Result<CleanCandidate, SkippedCandidate>> {
    // 功能进行中 → 跳过
    if state.status.overall_status == Status::InProgress {
        return Some(Err(SkippedCandidate {
            dir_name: dir_name.to_string(),
            reason: SkipReason::InProgress,
        }));
    }

    // Pending / Paused → 跳过
    if matches!(
        state.status.overall_status,
        Status::Pending | Status::Paused
    ) {
        return Some(Err(SkippedCandidate {
            dir_name: dir_name.to_string(),
            reason: SkipReason::InProgress,
        }));
    }

    // Failed → 跳过 (安全保护)
    if state.status.overall_status == Status::Failed {
        return Some(Err(SkippedCandidate {
            dir_name: dir_name.to_string(),
            reason: SkipReason::InProgress,
        }));
    }

    // Completed：检查 PR 状态
    let pr_number = match state.delivery.pr_number {
        Some(n) => n,
        None => {
            return Some(Err(SkippedCandidate {
                dir_name: dir_name.to_string(),
                reason: SkipReason::NoPr,
            }));
        }
    };

    let pr_status = match get_pr_status(pr_number, repo_path).await {
        Ok(s) => s,
        Err(e) => {
            debug!(error = %e, pr_number = pr_number, "获取 PR 状态失败");
            if state.delivery.merged {
                return Some(Ok(CleanCandidate {
                    dir_name: dir_name.to_string(),
                    specs_path: specs_path.to_path_buf(),
                    worktree_path: worktree_path.to_path_buf(),
                    reason: CleanReason::PrMerged(pr_number),
                }));
            }
            return Some(Err(SkippedCandidate {
                dir_name: dir_name.to_string(),
                reason: SkipReason::NoPr,
            }));
        }
    };

    let reason = match pr_status.as_str() {
        "MERGED" => CleanReason::PrMerged(pr_number),
        "CLOSED" => CleanReason::PrClosed(pr_number),
        _ => {
            return Some(Err(SkippedCandidate {
                dir_name: dir_name.to_string(),
                reason: SkipReason::PrOpen(pr_number),
            }));
        }
    };

    Some(Ok(CleanCandidate {
        dir_name: dir_name.to_string(),
        specs_path: specs_path.to_path_buf(),
        worktree_path: worktree_path.to_path_buf(),
        reason,
    }))
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
async fn get_pr_status(pr_number: u32, repo_path: &Path) -> Result<String> {
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
        .current_dir(repo_path)
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

/// 请求用户确认
fn confirm_clean(count: usize) -> Result<bool> {
    print!("⚠️  确认删除 {} 个 worktree? [y/N] ", count);
    io::stdout().flush()?;

    let mut input = String::new();
    io::stdin().read_line(&mut input)?;

    Ok(input.trim().eq_ignore_ascii_case("y"))
}

/// 执行清理：仅删除 .trees/ 中的 worktree，绝不触碰 specs/
fn perform_clean(candidates: &[CleanCandidate]) -> Result<usize> {
    let mut cleaned = 0;

    for c in candidates {
        match fs::remove_dir_all(&c.worktree_path) {
            Ok(()) => {
                println!("  ✓ 已删除 worktree: {}", c.dir_name);
                cleaned += 1;
            }
            Err(e) => {
                eprintln!("  ✗ 删除失败 {}: {}", c.dir_name, e);
            }
        }
    }

    Ok(cleaned)
}

 #[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_clean_reason_display() {
        let merged = CleanReason::PrMerged(123);
        let closed = CleanReason::PrClosed(456);
        assert!(matches!(merged, CleanReason::PrMerged(123)));
        assert!(matches!(closed, CleanReason::PrClosed(456)));
    }
}
