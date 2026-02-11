//! Git 命令封装
//!
//! 封装 `git worktree` 相关操作，使用 `std::process::Command` 执行。

use std::path::{Path, PathBuf};
use std::process::Command;

use crate::error::{CoreError, Result};
use crate::worktree::WorktreeInfo;

/// Git 命令执行器
pub struct GitCommand {
    repo_path: PathBuf,
}

impl GitCommand {
    /// 创建新的 Git 命令执行器
    pub fn new(repo_path: &Path) -> Self {
        Self {
            repo_path: repo_path.to_path_buf(),
        }
    }

    /// 执行 git 命令
    fn run(&self, args: &[&str]) -> Result<String> {
        let output = Command::new("git")
            .args(args)
            .current_dir(&self.repo_path)
            .output()
            .map_err(|e| CoreError::Worktree(format!("执行 git 命令失败: {}", e)))?;

        if !output.status.success() {
            let stderr = String::from_utf8_lossy(&output.stderr);
            return Err(CoreError::Worktree(format!(
                "git 命令失败: {}",
                stderr.trim()
            )));
        }

        Ok(String::from_utf8_lossy(&output.stdout).trim().to_string())
    }

    /// 创建 worktree
    /// `git worktree add <path> -b <branch> [<start_point>]`
    pub fn add_worktree(&self, path: &Path, branch: &str, base_branch: Option<&str>) -> Result<()> {
        let path_str = path
            .to_str()
            .ok_or_else(|| CoreError::Worktree("无效的 worktree 路径".to_string()))?;

        let mut args: Vec<&str> = vec!["worktree", "add", path_str, "-b", branch];
        if let Some(base) = base_branch {
            args.push(base);
        }

        self.run(&args)?;
        Ok(())
    }

    /// 删除 worktree
    /// `git worktree remove <path>`
    pub fn remove_worktree(&self, path: &Path) -> Result<()> {
        let path_str = path
            .to_str()
            .ok_or_else(|| CoreError::Worktree("无效的 worktree 路径".to_string()))?;

        self.run(&["worktree", "remove", path_str])?;
        Ok(())
    }

    /// 强制删除 worktree (用于包含未提交更改的情况)
    /// `git worktree remove --force <path>`
    pub fn remove_worktree_force(&self, path: &Path) -> Result<()> {
        let path_str = path
            .to_str()
            .ok_or_else(|| CoreError::Worktree("无效的 worktree 路径".to_string()))?;

        self.run(&["worktree", "remove", "--force", path_str])?;
        Ok(())
    }

    /// 列出所有 worktree
    /// `git worktree list --porcelain`
    pub fn list_worktrees(&self) -> Result<Vec<WorktreeInfo>> {
        let output = self.run(&["worktree", "list", "--porcelain"])?;
        parse_worktree_list(&output, &self.repo_path)
    }

    /// 修剪 worktree (清理已删除的)
    /// `git worktree prune`
    pub fn prune(&self) -> Result<()> {
        self.run(&["worktree", "prune"])?;
        Ok(())
    }

    /// 检查 git 是否可用
    pub fn check_git_available() -> bool {
        Command::new("git")
            .arg("--version")
            .output()
            .map(|o| o.status.success())
            .unwrap_or(false)
    }

    /// 获取默认分支名 (HEAD 指向的分支)
    pub fn default_branch(&self) -> Result<String> {
        let branch = self.run(&["rev-parse", "--abbrev-ref", "HEAD"])?;
        Ok(branch.trim().to_string())
    }
}

/// 解析 `git worktree list --porcelain` 输出
fn parse_worktree_list(output: &str, _repo_path: &Path) -> Result<Vec<WorktreeInfo>> {
    let mut result = Vec::new();
    let mut current_path: Option<PathBuf> = None;
    let mut current_branch: Option<String> = None;

    for line in output.lines() {
        if line.starts_with("worktree ") {
            if let Some((_, path)) = line.split_once(' ') {
                current_path = Some(PathBuf::from(path.trim()));
                current_branch = None;
            }
        } else if line.starts_with("branch ") {
            let branch_ref = line.trim_start_matches("branch ");
            current_branch = branch_ref
                .strip_prefix("refs/heads/")
                .map(|s| s.to_string())
                .or_else(|| Some(branch_ref.to_string()));
        } else if line.is_empty()
            && let Some(path) = current_path.take()
        {
            let name = path
                .file_name()
                .and_then(|n| n.to_str())
                .unwrap_or("")
                .to_string();
            let branch = current_branch
                .clone()
                .unwrap_or_else(|| "detached".to_string());
            let exists = path.exists();
            result.push(WorktreeInfo {
                name,
                path,
                branch,
                exists,
            });
        }
    }

    if let Some(path) = current_path {
        let name = path
            .file_name()
            .and_then(|n| n.to_str())
            .unwrap_or("")
            .to_string();
        let branch = current_branch.unwrap_or_else(|| "detached".to_string());
        let exists = path.exists();
        result.push(WorktreeInfo {
            name,
            path,
            branch,
            exists,
        });
    }

    Ok(result)
}

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::TempDir;

    #[test]
    fn test_should_create_git_command() {
        let temp_dir = TempDir::new().unwrap();
        let git = GitCommand::new(temp_dir.path());
        assert_eq!(git.repo_path, temp_dir.path());
    }

    #[test]
    fn test_should_check_git_available() {
        assert!(GitCommand::check_git_available());
    }

    #[test]
    fn test_should_parse_worktree_list_empty() {
        let temp_dir = TempDir::new().unwrap();
        let result = parse_worktree_list("", temp_dir.path()).unwrap();
        assert!(result.is_empty());
    }

    #[test]
    fn test_should_parse_worktree_list_single() {
        let temp_dir = TempDir::new().unwrap();
        let output = r#"worktree /tmp/repo/.trees/001-add-auth
HEAD abc123
branch refs/heads/feature/001-add-auth

"#;
        let result = parse_worktree_list(output, temp_dir.path()).unwrap();
        assert_eq!(result.len(), 1);
        assert_eq!(result[0].name, "001-add-auth");
        assert_eq!(result[0].branch, "feature/001-add-auth");
    }
}
