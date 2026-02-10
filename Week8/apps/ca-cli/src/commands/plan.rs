//! Plan 命令实现
//!
//! 功能规划和 specs 文档生成

use std::path::{Path, PathBuf};
use std::sync::Arc;

use ca_core::{Agent, ExecutionEngine, Phase, Repository, StateManager};
use ca_pm::{ContextBuilder, ProjectInfo, PromptConfig, PromptManager};

use crate::config::AppConfig;

/// 执行 plan 命令
pub async fn execute_plan(
    feature_slug: String,
    description: Option<String>,
    interactive: bool,
    repo: Option<PathBuf>,
    config: &AppConfig,
) -> anyhow::Result<()> {
    println!("📋 规划功能: {}", feature_slug);
    println!();

    // 确定工作目录
    let repo_path = if let Some(path) = repo {
        path
    } else if let Some(default) = &config.default_repo {
        default.clone()
    } else {
        std::env::current_dir()?
    };

    println!("📂 工作目录: {}", repo_path.display());

    // 创建 Repository
    let repository = Arc::new(Repository::new(&repo_path)?);

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

    // 创建 specs 目录
    let specs_dir = repo_path.join("specs");
    std::fs::create_dir_all(&specs_dir)?;

    // 创建功能目录
    let feature_dir = create_feature_dir(&specs_dir, &feature_slug)?;
    println!("📁 Specs 目录: {}", feature_dir.display());

    // 初始化状态管理
    let mut state_manager = StateManager::new(&feature_slug, &repo_path)?;

    // 创建 Agent
    let agent = create_agent(config)?;

    // 创建 ExecutionEngine
    let engine = ExecutionEngine::new(agent, repository.clone());

    // 验证连接
    println!("🔌 验证 Agent 连接...");
    if !engine.validate().await? {
        anyhow::bail!("❌ Agent 连接验证失败");
    }
    println!("✅ 连接成功");
    println!();

    // 构建项目信息
    let project_info = build_project_info(&repo_path)?;

    // 构建 Prompt 上下文
    let context = ContextBuilder::new()
        .with_project_info(project_info)
        .add_variable("feature_slug", feature_slug.clone())?
        .add_variable("feature_description", feature_description.clone())?
        .build()?;

    // 渲染 Prompt
    let prompt_config = PromptConfig {
        template_dir: config.prompt.template_dir.clone(),
        default_template: None,
    };
    let prompt_manager = PromptManager::new(prompt_config)?;
    let user_prompt = prompt_manager.render("plan/feature_analysis", &context)?;

    // 执行 Plan 阶段
    println!("⚙️  开始分析功能...");
    let result = engine.execute_phase(Phase::Plan, user_prompt).await?;

    if result.success {
        println!("✅ 功能分析完成!");
        println!();

        // 更新状态
        state_manager.update_phase_status(0, ca_core::Status::Completed)?;
        state_manager.save()?;

        // 显示生成的文件
        println!("📄 生成的文档:");
        for file in &["spec.md", "design.md", "plan.md", "tasks.md"] {
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
fn create_feature_dir(specs_dir: &Path, feature_slug: &str) -> anyhow::Result<PathBuf> {
    // 查找下一个可用的编号
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

    // 创建 .ca-state 子目录
    let state_dir = feature_dir.join(".ca-state");
    std::fs::create_dir_all(&state_dir)?;
    std::fs::create_dir_all(state_dir.join("backups"))?;

    Ok(feature_dir)
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
    } else if repo_path.join("requirements.txt").exists() || repo_path.join("pyproject.toml").exists() {
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
    use ca_core::{AgentConfig, AgentFactory, AgentType, ClaudeAgent};

    let agent_type = match config.agent.agent_type.as_str() {
        "claude" => AgentType::Claude,
        "cursor" => AgentType::Cursor,
        "copilot" => AgentType::Copilot,
        _ => anyhow::bail!("不支持的 Agent 类型: {}", config.agent.agent_type),
    };

    // 对于 Claude,直接创建实例
    if agent_type == AgentType::Claude {
        let agent = ClaudeAgent::new(config.agent.api_key.clone(), config.agent.model.clone())?;
        return Ok(Arc::new(agent));
    }

    // 其他类型使用工厂
    let agent_config = AgentConfig {
        agent_type,
        api_key: config.agent.api_key.clone(),
        model: Some(config.agent.model.clone()),
        api_url: config.agent.api_url.clone(),
    };

    let _boxed_agent = AgentFactory::create(agent_config)?;
    
    // 需要从 Box转换为 Arc - 这里需要特殊处理
    // 由于 AgentFactory 返回 Box,我们需要重新实现
    anyhow::bail!("当前仅支持 Claude Agent")
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
