//! `code-agent clean` 命令实现
//!
//! 清理已完成功能的 worktree，仅针对 `.trees/` 目录。
//! **specs/ 目录作为功能历史存档，永久保留，绝不清理。**

use std::io::{self, Write};

use anyhow::Result;
use ca_core::WorktreeManager;
use tracing::debug;

use crate::config::AppConfig;

/// 执行 clean 命令
///
/// 仅清理 `.trees/` 中的 worktree，绝不清理 `specs/` 目录。
pub async fn execute_clean(dry_run: bool, _all: bool, config: &AppConfig) -> Result<()> {
    debug!(dry_run = dry_run, "执行 clean 命令");

    let current_dir = std::env::current_dir()?;
    let repo_path = config.default_repo.as_ref().unwrap_or(&current_dir);

    let worktree_manager = WorktreeManager::new(repo_path).map_err(|e| anyhow::anyhow!("{}", e))?;

    if !worktree_manager.is_git_repo() {
        println!("ℹ️  非 git 仓库，无 worktree 需要清理");
        return Ok(());
    }

    println!("🔍 扫描已完成的功能...");

    let to_remove = worktree_manager.clean_completed(true)?;

    if to_remove.is_empty() {
        println!("✅ 没有需要清理的 worktree");
        println!();
        println!("📁 specs/ 目录作为功能历史存档，已永久保留");
        return Ok(());
    }

    for feature in &to_remove {
        if dry_run {
            println!("  [DRY RUN] 将删除: .trees/{}", feature);
        } else {
            println!("  ✓ 将删除: .trees/{}", feature);
        }
    }

    println!();
    println!("总计: {} 个 worktree 将被清理", to_remove.len());
    println!("注意: specs/ 目录作为功能历史存档，永久保留");

    if dry_run {
        println!();
        println!("💡 运行 `code-agent clean` (不带 --dry-run) 以实际删除");
        return Ok(());
    }

    print!("⚠️  确认删除 {} 个 worktree? [y/N] ", to_remove.len());
    io::stdout().flush()?;
    let mut input = String::new();
    std::io::stdin().read_line(&mut input)?;
    if !input.trim().eq_ignore_ascii_case("y") {
        println!("❌ 已取消清理");
        return Ok(());
    }

    println!();
    println!("🧹 开始清理...");
    let removed = worktree_manager.clean_completed(false)?;
    println!();
    println!("✅ 已清理 {} 个 worktree", removed.len());
    println!();
    println!("📁 specs/ 目录作为功能历史存档，已永久保留");

    Ok(())
}
