use std::path::PathBuf;

use crate::config::AppConfig;

mod clean;
mod init;
mod list;
mod plan;
pub(crate) mod run;
mod status;
mod templates;

pub use clean::execute_clean;
pub use init::execute_init;
pub use list::execute_list;
pub use plan::execute_plan;
pub use run::execute_run;
pub use status::execute_status;
pub use templates::execute_templates;

/// 共享工具函数：从 specs 目录中查找 feature 目录
/// 
/// 匹配规则：目录名格式为 "NNN-feature-slug"，提取后缀并精确匹配
/// 如果找到多个匹配，返回错误（不应该发生）
pub fn find_feature_dir(specs_dir: &std::path::Path, feature_slug: &str) -> anyhow::Result<PathBuf> {
    use std::fs;
    
    if !specs_dir.exists() {
        anyhow::bail!("❌ specs 目录不存在: {}", specs_dir.display());
    }

    let mut matches = Vec::new();
    
    for entry in fs::read_dir(specs_dir)? {
        let entry = entry?;
        let path = entry.path();
        
        if !path.is_dir() {
            continue;
        }
        
        if let Some(dir_name) = path.file_name().and_then(|n| n.to_str()) {
            // 提取 slug：NNN-feature-slug → feature-slug
            if let Some(extracted_slug) = extract_feature_slug(dir_name)
                && extracted_slug == feature_slug {
                    matches.push(path);
                }
        }
    }
    
    match matches.len() {
        0 => anyhow::bail!("❌ 未找到功能: {}", feature_slug),
        1 => Ok(matches.into_iter().next().unwrap()),
        n => anyhow::bail!(
            "❌ 发现 {} 个重复的功能目录: {}\n这是一个 bug，请手动清理重复目录",
            n,
            feature_slug
        ),
    }
}

/// 从目录名中提取 feature slug
/// 
/// 格式: "001-feature-slug" → "feature-slug"
fn extract_feature_slug(dir_name: &str) -> Option<&str> {
    // 查找第一个 '-' 的位置
    let dash_pos = dir_name.find('-')?;
    
    // 确保 '-' 前面都是数字
    let prefix = &dir_name[..dash_pos];
    if !prefix.chars().all(|c| c.is_ascii_digit()) {
        return None;
    }
    
    // 返回 '-' 后面的部分
    Some(&dir_name[dash_pos + 1..])
}

pub enum Command {
    Init {
        api_key: Option<String>,
        agent: Option<String>,
        interactive: bool,
        force: bool,
    },
    Plan {
        feature_slug: String,
        description: Option<String>,
        interactive: bool,
        repo: Option<PathBuf>,
    },
    Run {
        feature_slug: String,
        phase: Option<u8>,
        resume: bool,
        dry_run: bool,
        skip_review: bool,
        skip_test: bool,
        interactive: bool,
        repo: Option<PathBuf>,
    },
    Templates {
        verbose: bool,
    },
    List {
        all: bool,
        status: Option<String>,
    },
    Status {
        feature_slug: String,
    },
    Clean {
        dry_run: bool,
        all: bool,
    },
}

pub async fn execute_command(command: Command, config: &AppConfig) -> anyhow::Result<()> {
    match command {
        Command::Init {
            api_key,
            agent,
            interactive,
            force,
        } => execute_init(api_key, agent, interactive, force, config).await,
        Command::Plan {
            feature_slug,
            description,
            interactive,
            repo,
        } => execute_plan(feature_slug, description, interactive, repo, config).await,
        Command::Run {
            feature_slug,
            phase,
            resume,
            dry_run,
            skip_review,
            skip_test,
            interactive,
            repo,
        } => {
            execute_run(
                feature_slug,
                phase,
                resume,
                dry_run,
                skip_review,
                skip_test,
                interactive,
                repo,
                config,
            )
            .await
        }
        Command::Templates { verbose } => execute_templates(verbose, config).await,
        Command::List { all, status } => execute_list(all, status, config).await,
        Command::Status { feature_slug } => execute_status(feature_slug, config).await,
        Command::Clean { dry_run, all } => execute_clean(dry_run, all, config).await,
    }
}
