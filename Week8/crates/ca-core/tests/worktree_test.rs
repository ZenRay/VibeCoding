//! Worktree 集成测试
//!
//! 测试 Git Worktree 完整生命周期。

use ca_core::WorktreeManager;
use std::fs;
use tempfile::TempDir;

fn init_git_repo(dir: &std::path::Path) {
    std::process::Command::new("git")
        .args(["init"])
        .current_dir(dir)
        .output()
        .expect("git init 失败");

    std::process::Command::new("git")
        .args(["config", "user.email", "test@example.com"])
        .current_dir(dir)
        .output()
        .expect("git config 失败");

    std::process::Command::new("git")
        .args(["config", "user.name", "Test User"])
        .current_dir(dir)
        .output()
        .expect("git config 失败");

    fs::write(dir.join("README.md"), "# Test").expect("写入 README 失败");
    std::process::Command::new("git")
        .args(["add", "."])
        .current_dir(dir)
        .output()
        .expect("git add 失败");

    std::process::Command::new("git")
        .args(["commit", "-m", "initial"])
        .current_dir(dir)
        .output()
        .expect("git commit 失败");
}

#[test]
fn test_worktree_full_lifecycle() {
    let temp_dir = TempDir::new().expect("创建临时目录失败");
    init_git_repo(temp_dir.path());

    let manager = WorktreeManager::new(temp_dir.path()).expect("创建 WorktreeManager 失败");
    assert!(manager.is_git_repo());

    let worktree_path = manager
        .create_worktree("add-auth", 1, None)
        .expect("创建 worktree 失败 (将自动检测默认分支)");

    assert!(worktree_path.exists());
    assert!(worktree_path.ends_with(".trees/001-add-auth"));

    let exists = manager
        .worktree_exists("001-add-auth")
        .expect("检查存在性失败");
    assert!(exists);

    let list = manager.list_worktrees().expect("列出 worktree 失败");
    assert!(!list.is_empty());
    assert!(list.iter().any(|w| w.name == "001-add-auth"));

    manager
        .remove_worktree("001-add-auth")
        .expect("删除 worktree 失败");

    let exists_after = manager
        .worktree_exists("001-add-auth")
        .expect("检查存在性失败");
    assert!(!exists_after);
}

#[test]
fn test_worktree_clean_completed_dry_run_empty() {
    let temp_dir = TempDir::new().expect("创建临时目录失败");
    init_git_repo(temp_dir.path());

    let manager = WorktreeManager::new(temp_dir.path()).expect("创建 WorktreeManager 失败");
    let removed = manager.clean_completed(true).expect("clean_completed 失败");
    assert!(removed.is_empty());
}
