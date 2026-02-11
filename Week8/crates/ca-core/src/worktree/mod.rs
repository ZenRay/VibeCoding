//! Git Worktree 管理模块
//!
//! 为每个功能创建独立的 worktree，实现隔离开发。
//! - Worktree 是**可选功能**，仅在 git 仓库中启用
//! - 非 git 仓库使用主目录，正常工作
//! - `specs/` 目录**永久保留**，不受 clean 影响

mod git;

use std::fs;
use std::path::{Path, PathBuf};

use crate::error::{CoreError, Result};
use crate::state::{FeatureState, Status};

pub use git::GitCommand;

/// Worktree 信息
#[derive(Debug, Clone)]
pub struct WorktreeInfo {
    /// worktree 名称 (如 001-add-auth)
    pub name: String,
    /// worktree 路径
    pub path: PathBuf,
    /// 关联分支
    pub branch: String,
    /// 是否实际存在
    pub exists: bool,
}

/// Worktree 管理器
pub struct WorktreeManager {
    repo_path: PathBuf,
    trees_dir: PathBuf,
}

impl WorktreeManager {
    /// 创建新的 worktree manager
    pub fn new(repo_path: &Path) -> Result<Self> {
        let repo_path = repo_path
            .canonicalize()
            .unwrap_or_else(|_| repo_path.to_path_buf());
        let trees_dir = repo_path.join(".trees");

        Ok(Self {
            repo_path,
            trees_dir,
        })
    }

    /// 检查是否在 git 仓库中
    pub fn is_git_repo(&self) -> bool {
        self.repo_path.join(".git").exists()
            || self
                .repo_path
                .join(".git")
                .metadata()
                .map(|m| m.is_file())
                .unwrap_or(false)
    }

    /// 为功能创建 worktree
    ///
    /// # 参数
    /// - feature_slug: 功能 slug (如 "add-auth")
    /// - feature_number: 功能编号 (如 1)
    /// - base_branch: 基础分支 (默认 "main")
    ///
    /// # 返回
    /// worktree 路径
    pub fn create_worktree(
        &self,
        feature_slug: &str,
        feature_number: u32,
        base_branch: Option<&str>,
    ) -> Result<PathBuf> {
        if !self.is_git_repo() {
            return Err(CoreError::Worktree(format!(
                "非 git 仓库: {}",
                self.repo_path.display()
            )));
        }

        if !GitCommand::check_git_available() {
            return Err(CoreError::Worktree(
                "git 未安装或不可用，请确保 git 在 PATH 中".to_string(),
            ));
        }

        let worktree_name = format!("{:03}-{}", feature_number, feature_slug);
        let worktree_path = self.trees_dir.join(&worktree_name);

        if worktree_path.exists() {
            return Err(CoreError::Worktree(format!(
                "Worktree 已存在: {}",
                worktree_path.display()
            )));
        }

        let branch = format!("feature/{}", worktree_name);
        let base_branch_str = base_branch.map(str::to_string).unwrap_or_else(|| {
            GitCommand::new(&self.repo_path)
                .default_branch()
                .unwrap_or_else(|_| "main".to_string())
        });

        fs::create_dir_all(&self.trees_dir)?;
        let git = GitCommand::new(&self.repo_path);
        git.add_worktree(&worktree_path, &branch, Some(&base_branch_str))?;

        setup_specs_symlink(&self.repo_path, &worktree_path)?;

        Ok(worktree_path)
    }

    /// 删除 worktree
    pub fn remove_worktree(&self, feature_name: &str) -> Result<()> {
        let worktree_path = self.worktree_path(feature_name);
        if !worktree_path.exists() {
            return Err(CoreError::Worktree(format!(
                "Worktree 不存在: {}",
                worktree_path.display()
            )));
        }

        let git = GitCommand::new(&self.repo_path);
        git.remove_worktree(&worktree_path)
            .or_else(|_| git.remove_worktree_force(&worktree_path))?;

        Ok(())
    }

    /// 列出所有 worktree
    pub fn list_worktrees(&self) -> Result<Vec<WorktreeInfo>> {
        if !self.is_git_repo() {
            return Ok(Vec::new());
        }

        let git = GitCommand::new(&self.repo_path);
        let all = git.list_worktrees()?;

        let trees_dir = self
            .trees_dir
            .canonicalize()
            .unwrap_or_else(|_| self.trees_dir.clone());
        Ok(all
            .into_iter()
            .filter(|w| w.path.starts_with(&trees_dir))
            .collect())
    }

    /// 检查 worktree 是否存在
    pub fn worktree_exists(&self, feature_name: &str) -> Result<bool> {
        Ok(self.worktree_path(feature_name).exists())
    }

    /// 获取 worktree 路径
    pub fn worktree_path(&self, feature_name: &str) -> PathBuf {
        self.trees_dir.join(feature_name)
    }

    /// 清理已完成功能的 worktree
    ///
    /// 仅清理状态为 Completed 且 PR 已合并或已关闭的 worktree。
    /// specs/ 目录永久保留。
    ///
    /// # 参数
    /// - dry_run: 仅显示将被删除的 worktree，不实际删除
    pub fn clean_completed(&self, dry_run: bool) -> Result<Vec<String>> {
        if !self.is_git_repo() {
            return Ok(Vec::new());
        }

        let specs_dir = self.repo_path.join("specs");
        if !specs_dir.exists() {
            return Ok(Vec::new());
        }

        let mut to_remove = Vec::new();

        for entry in fs::read_dir(&specs_dir)
            .map_err(|e| CoreError::Worktree(format!("无法读取 specs 目录: {}", e)))?
        {
            let entry = entry.map_err(|e| CoreError::Worktree(format!("读取目录项失败: {}", e)))?;
            let path = entry.path();
            if !path.is_dir() {
                continue;
            }

            let dir_name = path
                .file_name()
                .and_then(|n| n.to_str())
                .filter(|s| !s.starts_with('.'))
                .unwrap_or("");

            if dir_name.is_empty() {
                continue;
            }

            let worktree_path = self.worktree_path(dir_name);
            if !worktree_path.exists() {
                continue;
            }

            let state_file = path.join("state.yml");
            if !state_file.exists() {
                continue;
            }

            let content = match fs::read_to_string(&state_file) {
                Ok(c) => c,
                Err(_) => continue,
            };
            let state: FeatureState = match serde_yaml::from_str(&content) {
                Ok(s) => s,
                Err(_) => continue,
            };

            if state.status.overall_status != Status::Completed {
                continue;
            }

            let pr_number = match state.delivery.pr_number {
                Some(n) => n,
                None => continue,
            };

            let pr_status = get_pr_status_sync(pr_number, &self.repo_path)
                .unwrap_or_else(|| "UNKNOWN".to_string());
            let pr_status = pr_status.to_uppercase();

            if pr_status == "MERGED" || pr_status == "CLOSED" || state.delivery.merged {
                to_remove.push(dir_name.to_string());
            }
        }

        if dry_run {
            return Ok(to_remove);
        }

        let mut removed = Vec::new();
        for name in &to_remove {
            if self.remove_worktree(name).is_ok() {
                removed.push(name.clone());
            }
        }

        Ok(removed)
    }

    /// 获取主仓库路径
    pub fn repo_path(&self) -> &Path {
        &self.repo_path
    }

    /// 获取 .trees 目录路径
    pub fn trees_dir(&self) -> &Path {
        &self.trees_dir
    }
}

/// 创建 specs 软链接
fn setup_specs_symlink(repo_path: &Path, worktree_path: &Path) -> Result<()> {
    let specs_in_worktree = worktree_path.join("specs");
    let specs_target = repo_path.join("specs");

    if specs_in_worktree.exists() {
        fs::remove_dir_all(&specs_in_worktree)?;
    }

    #[cfg(unix)]
    {
        std::os::unix::fs::symlink(&specs_target, &specs_in_worktree)?;
    }

    #[cfg(windows)]
    {
        std::os::windows::fs::symlink_dir(&specs_target, &specs_in_worktree)?;
    }

    #[cfg(not(any(unix, windows)))]
    {
        let _ = specs_target;
        fs::create_dir_all(&specs_in_worktree)?;
    }

    Ok(())
}

/// 同步获取 PR 状态 (使用 gh CLI)
fn get_pr_status_sync(pr_number: u32, repo_path: &Path) -> Option<String> {
    let output = std::process::Command::new("gh")
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
        .ok()?;

    if !output.status.success() {
        return None;
    }

    let status = String::from_utf8(output.stdout).ok()?;
    Some(status.trim().to_string())
}

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::TempDir;

    #[test]
    fn test_should_create_worktree_manager() {
        let temp_dir = TempDir::new().unwrap();
        let manager = WorktreeManager::new(temp_dir.path()).unwrap();
        assert!(!manager.is_git_repo());
    }

    #[test]
    fn test_should_detect_git_repo() {
        let temp_dir = TempDir::new().unwrap();
        std::process::Command::new("git")
            .args(["init"])
            .current_dir(temp_dir.path())
            .output()
            .unwrap();

        let manager = WorktreeManager::new(temp_dir.path()).unwrap();
        assert!(manager.is_git_repo());
    }

    #[test]
    fn test_should_get_worktree_path() {
        let temp_dir = TempDir::new().unwrap();
        let manager = WorktreeManager::new(temp_dir.path()).unwrap();
        let path = manager.worktree_path("001-add-auth");
        assert!(path.ends_with(".trees/001-add-auth"));
    }

    #[test]
    fn test_should_worktree_exists_false_when_not_exists() {
        let temp_dir = TempDir::new().unwrap();
        let manager = WorktreeManager::new(temp_dir.path()).unwrap();
        let exists = manager.worktree_exists("001-add-auth").unwrap();
        assert!(!exists);
    }

    #[test]
    fn test_should_list_worktrees_empty() {
        let temp_dir = TempDir::new().unwrap();
        let manager = WorktreeManager::new(temp_dir.path()).unwrap();
        let list = manager.list_worktrees().unwrap();
        assert!(list.is_empty());
    }

    #[test]
    fn test_should_create_fail_when_not_git_repo() {
        let temp_dir = TempDir::new().unwrap();
        let manager = WorktreeManager::new(temp_dir.path()).unwrap();
        let result = manager.create_worktree("add-auth", 1, None);
        assert!(result.is_err());
    }

    #[test]
    fn test_should_provide_repo_and_trees_paths() {
        let temp_dir = TempDir::new().unwrap();
        let manager = WorktreeManager::new(temp_dir.path()).unwrap();
        assert_eq!(manager.repo_path(), temp_dir.path());
        assert_eq!(manager.trees_dir(), temp_dir.path().join(".trees"));
    }
}
