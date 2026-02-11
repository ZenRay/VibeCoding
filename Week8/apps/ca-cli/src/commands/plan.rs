//! Plan 命令实现
//!
//! 功能规划和 specs 文档生成

use std::path::{Path, PathBuf};
use std::sync::Arc;

use ca_core::{Agent, ExecutionEngine, Phase, Repository, StateManager, WorktreeManager};
use ca_pm::{ContextBuilder, ProjectInfo, PromptConfig, PromptManager};

use crate::config::AppConfig;

/// 获取模板基础目录
/// 优先使用项目内置模板，如果不存在则使用用户配置目录
fn get_template_base_dir(config: &AppConfig) -> PathBuf {
    // 尝试多个可能的内置模板位置
    let possible_paths = [
        // 1. 当前目录下（开发时）
        PathBuf::from("crates/ca-pm/templates"),
        // 2. 可执行文件所在目录的相对路径（已安装）
        std::env::current_exe()
            .ok()
            .and_then(|exe| exe.parent().map(|p| p.to_path_buf()))
            .map(|exe_dir| exe_dir.join("../../../crates/ca-pm/templates"))
            .unwrap_or_default(),
        // 3. 项目根目录（如果通过 cargo run 运行）
        PathBuf::from(env!("CARGO_MANIFEST_DIR"))
            .parent()
            .and_then(|p| p.parent())
            .map(|root| root.join("crates/ca-pm/templates"))
            .unwrap_or_default(),
    ];

    // 尝试每个路径
    for path in &possible_paths {
        if path.exists() && path.join("plan/feature_analysis/user.jinja").exists() {
            return path.clone();
        }
    }

    // 如果都不存在，回退到用户配置目录
    config.prompt.template_dir.clone()
}

/// 执行 plan 命令
pub async fn execute_plan(
    feature_slug: String,
    description: Option<String>,
    interactive: bool,
    repo: Option<PathBuf>,
    config: &AppConfig,
) -> anyhow::Result<()> {
    // 确定工作目录
    let repo_path = if let Some(path) = repo {
        path
    } else if let Some(default) = &config.default_repo {
        default.clone()
    } else {
        std::env::current_dir()?
    };

    // 交互模式且未提供 description → 启动 TUI
    if interactive && description.is_none() {
        return crate::ui::execute_plan_tui(feature_slug, repo_path, config.clone()).await;
    }

    println!("📋 规划功能: {}", feature_slug);
    println!();
    println!("📂 工作目录: {}", repo_path.display());

    // 创建 specs 目录
    let specs_dir = repo_path.join("specs");
    std::fs::create_dir_all(&specs_dir)?;

    // 创建或获取功能目录（CLI 模式不允许重复）
    let (feature_dir, is_existing) = create_feature_dir(&specs_dir, &feature_slug, false)?;
    
    if is_existing {
        // 这种情况不应该发生（因为 update_existing=false），但保留处理
        anyhow::bail!(
            "❌ Feature '{}' 已存在，请使用 'code-agent run {}' 继续开发",
            feature_slug, feature_slug
        );
    }
    
    let feature_dir_name = feature_dir
        .file_name()
        .and_then(|n| n.to_str())
        .unwrap_or(&feature_slug)
        .to_string();
    let feature_number = feature_dir_name
        .split('-')
        .next()
        .and_then(|s| s.parse::<u32>().ok())
        .unwrap_or(1);

    println!("📁 Specs 目录: {}", feature_dir.display());

    // 检查是否使用 worktree (仅 git 仓库)
    let worktree_manager =
        WorktreeManager::new(&repo_path).map_err(|e| anyhow::anyhow!("{}", e))?;
    let working_dir = if worktree_manager.is_git_repo() {
        match worktree_manager.create_worktree(&feature_slug, feature_number, None) {
            Ok(worktree_path) => {
                println!("✅ 创建 worktree: {}", worktree_path.display());
                worktree_path
            }
            Err(e) => {
                println!("ℹ️  无法创建 worktree ({}), 使用主目录", e);
                repo_path.clone()
            }
        }
    } else {
        println!("ℹ️  非 git 仓库，使用主目录");
        repo_path.clone()
    };

    // 创建 Repository (在 working_dir 中操作)
    let repository = Arc::new(Repository::new(&working_dir)?);

    // 获取功能描述
    let feature_description = if let Some(desc) = description {
        desc
    } else if interactive {
        get_feature_description()?
    } else {
        anyhow::bail!("请提供功能描述 (--description) 或使用交互模式 (--interactive)");
    };

    println!("📝 功能描述: {}", feature_description);
    println!();

    // 初始化状态管理 (使用 feature_dir_name 作为 specs 路径)
    let mut state_manager = StateManager::new(&feature_dir_name, &working_dir)?;

    // 添加 Status Document Hook
    let specs_dir = working_dir.join("specs");
    let spec_content = String::new(); // 初始为空，plan 完成后会更新
    let status_hook =
        std::sync::Arc::new(ca_core::StatusDocumentHook::new(specs_dir, spec_content));
    state_manager.add_hook(status_hook);

    // 创建 Agent
    let agent = create_agent(config)?;

    // 创建 ExecutionEngine
    let mut engine = ExecutionEngine::new(agent, repository.clone());

    // 验证连接
    println!("🔌 验证 Agent 连接...");
    if !engine.validate().await? {
        anyhow::bail!("❌ Agent 连接验证失败");
    }
    println!("✅ 连接成功");
    println!();

    // 构建项目信息
    let project_info = build_project_info(&working_dir)?;

    // 构建 Prompt 上下文
    let context = ContextBuilder::new()
        .with_project_info(project_info)
        .add_variable("feature_slug", feature_slug.clone())?
        .add_variable("feature_description", feature_description.clone())?
        .build()?;

    // 渲染 Prompt (使用新的 3 文件结构)
    // 优先使用项目内置模板
    let template_base = get_template_base_dir(config);

    let prompt_config = PromptConfig {
        template_dir: template_base.clone(),
        default_template: None,
    };
    let mut prompt_manager = PromptManager::new(prompt_config)?;

    // 加载 plan 模板 (使用 3 文件结构)
    let template_dir = template_base.join("plan/feature_analysis");
    let task_template = prompt_manager.load_task_dir(&template_dir)?;

    // 渲染提示词
    let (system_prompt, user_prompt) = prompt_manager.render_task(&task_template, &context)?;

    // 执行 Plan 阶段
    println!("⚙️  开始分析功能...");
    let result = engine
        .execute_phase_with_config(
            Phase::Plan,
            &task_template.config,
            system_prompt,
            user_prompt,
        )
        .await?;

    if result.success {
        println!("✅ 功能分析完成!");
        println!();

        // 更新状态
        state_manager.update_phase_status(0, ca_core::Status::Completed)?;
        state_manager.save()?;

        // 创建初始 status.md
        let status_path = feature_dir.join("status.md");
        let spec_file_path = feature_dir.join("spec.md");
        let spec_content = if spec_file_path.exists() {
            std::fs::read_to_string(&spec_file_path).unwrap_or_default()
        } else {
            String::new()
        };

        let status_doc =
            ca_core::StatusDocument::from_feature_state(state_manager.state(), &spec_content);
        status_doc.save(&status_path)?;

        println!("📊 状态文件: {}", status_path.display());

        // 显示生成的文件
        println!("📄 生成的文档:");
        for file in &["spec.md", "design.md", "plan.md", "tasks.md", "status.md"] {
            let file_path = feature_dir.join(file);
            if file_path.exists() {
                println!("  ✓ {}", file);
            } else {
                println!("  - {} (待生成)", file);
            }
        }
        println!();

        // 创建初始 state.yml
        let state_file = feature_dir.join("state.yml");
        state_manager.save()?;
        println!("📊 状态文件: {}", state_file.display());
        println!();

        println!("🎉 功能规划完成!");
        println!();
        println!("下一步:");
        println!("  code-agent run {}", feature_slug);
        if worktree_manager.is_git_repo() {
            println!();
            println!("💡 提示: specs/ 目录已通过软链接共享，功能历史永久保留");
        }
    } else {
        println!("❌ 功能分析失败: {}", result.message);
        anyhow::bail!("Plan 执行失败");
    }

    Ok(())
}

/// 交互式获取功能描述
fn get_feature_description() -> anyhow::Result<String> {
    use std::io::{self, Write};

    println!("请描述要实现的功能:");
    println!("(提示: 越详细越好，可以包含技术细节、约束条件等)");
    println!();
    print!("> ");
    io::stdout().flush()?;

    let mut description = String::new();
    io::stdin().read_line(&mut description)?;
    let description = description.trim().to_string();

    if description.is_empty() {
        anyhow::bail!("功能描述不能为空");
    }

    Ok(description)
}

/// 创建功能目录
fn create_feature_dir(specs_dir: &Path, feature_slug: &str, update_existing: bool) -> anyhow::Result<(PathBuf, bool)> {
    // 1. 检查 feature slug 是否已存在
    if let Some(existing) = find_existing_feature(specs_dir, feature_slug)? {
        if update_existing {
            // 允许更新现有 feature
            return Ok((existing, true)); // (path, is_existing)
        } else {
            // CLI 模式下，拒绝重复创建
            anyhow::bail!(
                "❌ Feature '{}' 已存在于 {}\n\n提示:\n  • 使用 'code-agent status {}' 查看状态\n  • 使用 'code-agent run {}' 继续开发\n  • 或使用不同的 feature slug",
                feature_slug,
                existing.display(),
                feature_slug,
                feature_slug
            );
        }
    }

    // 2. 查找下一个可用的编号并创建新目录
    let mut counter = 1;
    let feature_dir = loop {
        let dir_name = format!("{:03}-{}", counter, feature_slug);
        let dir_path = specs_dir.join(&dir_name);

        if !dir_path.exists() {
            std::fs::create_dir_all(&dir_path)?;
            break dir_path;
        }

        counter += 1;
        if counter > 999 {
            anyhow::bail!("功能编号超出范围 (max: 999)");
        }
    };

    // 3. 创建 .ca-state 子目录
    let state_dir = feature_dir.join(".ca-state");
    std::fs::create_dir_all(&state_dir)?;
    std::fs::create_dir_all(state_dir.join("backups"))?;

    Ok((feature_dir, false)) // (path, is_existing = false)
}

/// 查找已存在的 feature 目录
fn find_existing_feature(specs_dir: &Path, feature_slug: &str) -> anyhow::Result<Option<PathBuf>> {
    if !specs_dir.exists() {
        return Ok(None);
    }

    for entry in std::fs::read_dir(specs_dir)? {
        let entry = entry?;
        let path = entry.path();

        if path.is_dir()
            && let Some(dir_name) = path.file_name().and_then(|n| n.to_str()) {
                // 提取 slug：001-feature-slug → feature-slug
                if let Some(dash_pos) = dir_name.find('-') {
                    let prefix = &dir_name[..dash_pos];
                    // 确保前缀是数字
                    if prefix.chars().all(|c| c.is_ascii_digit()) {
                        let extracted_slug = &dir_name[dash_pos + 1..];
                        if extracted_slug == feature_slug {
                            return Ok(Some(path));
                        }
                    }
                }
            }
    }

    Ok(None)
}

/// 构建项目信息
fn build_project_info(repo_path: &Path) -> anyhow::Result<ProjectInfo> {
    // 尝试检测项目信息
    let project_name = repo_path
        .file_name()
        .and_then(|n| n.to_str())
        .unwrap_or("project")
        .to_string();

    // 检测主要编程语言
    let primary_language = detect_primary_language(repo_path);

    // 检测框架
    let framework = detect_framework(repo_path);

    Ok(ProjectInfo {
        name: project_name,
        repo_path: repo_path.display().to_string(),
        primary_language,
        framework,
    })
}

/// 检测主要编程语言
fn detect_primary_language(repo_path: &Path) -> Option<String> {
    // 简单的启发式检测
    if repo_path.join("Cargo.toml").exists() {
        Some("Rust".to_string())
    } else if repo_path.join("package.json").exists() {
        Some("JavaScript/TypeScript".to_string())
    } else if repo_path.join("go.mod").exists() {
        Some("Go".to_string())
    } else if repo_path.join("requirements.txt").exists()
        || repo_path.join("pyproject.toml").exists()
    {
        Some("Python".to_string())
    } else {
        None
    }
}

/// 检测框架
fn detect_framework(repo_path: &Path) -> Option<String> {
    // 检测常见框架
    if repo_path.join("Cargo.toml").exists() {
        // Rust: 检查是否有 tauri, actix, etc.
        None // 需要解析 Cargo.toml
    } else if let Ok(content) = std::fs::read_to_string(repo_path.join("package.json")) {
        // JavaScript/TypeScript
        if content.contains("\"next\"") {
            Some("Next.js".to_string())
        } else if content.contains("\"react\"") {
            Some("React".to_string())
        } else if content.contains("\"vue\"") {
            Some("Vue".to_string())
        } else {
            None
        }
    } else {
        None
    }
}

/// 创建 Agent
fn create_agent(config: &AppConfig) -> anyhow::Result<Arc<dyn Agent>> {
    use ca_core::{AgentConfig, AgentFactory, AgentType};

    let agent_type = match config.agent.agent_type.as_str() {
        "claude" => AgentType::Claude,
        "cursor" => AgentType::Cursor,
        "copilot" => AgentType::Copilot,
        _ => anyhow::bail!("不支持的 Agent 类型: {}", config.agent.agent_type),
    };

    let agent_config = AgentConfig {
        agent_type,
        api_key: config.agent.api_key.clone(),
        model: Some(config.agent.model.clone()),
        api_url: config.agent.api_url.clone(),
    };

    AgentFactory::create(agent_config).map_err(Into::into)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_detect_primary_language_rust() {
        let temp_dir = std::env::temp_dir().join("test-rust-project");
        std::fs::create_dir_all(&temp_dir).unwrap();
        std::fs::write(temp_dir.join("Cargo.toml"), "").unwrap();

        let lang = detect_primary_language(&temp_dir);
        assert_eq!(lang, Some("Rust".to_string()));

        std::fs::remove_dir_all(&temp_dir).ok();
    }

    #[test]
    fn test_detect_primary_language_nodejs() {
        let temp_dir = std::env::temp_dir().join("test-node-project");
        std::fs::create_dir_all(&temp_dir).unwrap();
        std::fs::write(temp_dir.join("package.json"), "{}").unwrap();

        let lang = detect_primary_language(&temp_dir);
        assert_eq!(lang, Some("JavaScript/TypeScript".to_string()));

        std::fs::remove_dir_all(&temp_dir).ok();
    }
}
