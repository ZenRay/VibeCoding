//! Plan Worker：在后台执行 plan 流程，通过 mpsc 向 TUI 发送事件。

use std::path::{Path, PathBuf};
use std::sync::Arc;

use ca_core::{
    Agent, ExecutionEngine, Phase, Repository, StateManager, TuiEvent, TuiEventHandler,
    WorktreeManager,
};
use ca_pm::{ContextBuilder, ProjectInfo, PromptConfig, PromptManager};
use tokio::sync::mpsc;

use super::plan_app::UserMessage;
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

/// Plan Worker：接收用户消息，执行 plan 阶段，向 TUI 发送 TuiEvent。
pub async fn run_plan_worker(
    mut worker_rx: mpsc::Receiver<UserMessage>,
    ui_tx: mpsc::Sender<TuiEvent>,
    feature_slug: String,
    repo_path: PathBuf,
    config: AppConfig,
) -> anyhow::Result<()> {
    // ✅ 只在 Worker 启动时检查一次 feature 是否存在
    let specs_dir = repo_path.join("specs");
    std::fs::create_dir_all(&specs_dir)?;
    let (feature_dir, _is_existing) = create_feature_dir(&specs_dir, &feature_slug)?;
    
    // 注意：不再在这里发送 StreamText 通知
    // TUI 会通过 PlanApp::new() 的参数来显示提示
    
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
    
    // 处理用户输入
    while let Some(msg) = worker_rx.recv().await {
        match msg {
            UserMessage::Quit => break,
            UserMessage::Input(feature_description) => {
                if let Err(e) = run_one_plan(
                    &feature_slug,
                    &repo_path,
                    &feature_description,
                    &config,
                    ui_tx.clone(),
                    &feature_dir,
                    &feature_dir_name,
                    feature_number,
                )
                .await
                {
                    let _ = ui_tx.send(TuiEvent::Error(e.to_string())).await;
                }
            }
        }
    }
    Ok(())
}

async fn run_one_plan(
    feature_slug: &str,
    repo_path: &Path,
    feature_description: &str,
    config: &AppConfig,
    ui_tx: mpsc::Sender<TuiEvent>,
    feature_dir: &Path,
    feature_dir_name: &str,
    feature_number: u32,
) -> anyhow::Result<()> {
    // ✅ 不再检测 feature 是否存在，直接使用传入的参数
    
    let worktree_manager = WorktreeManager::new(repo_path).map_err(|e| anyhow::anyhow!("{}", e))?;
    let working_dir = if worktree_manager.is_git_repo() {
        match worktree_manager.create_worktree(feature_slug, feature_number, None) {
            Ok(p) => p,
            Err(_) => repo_path.to_path_buf(),
        }
    } else {
        repo_path.to_path_buf()
    };

    let repository = Arc::new(Repository::new(&working_dir)?);
    let agent = create_agent(config)?;

    let event_handler = Box::new(TuiEventHandler::new(ui_tx.clone()));
    let mut engine =
        ExecutionEngine::new(agent, repository.clone()).with_event_handler(event_handler);

    if !engine.validate().await? {
        let _ = ui_tx
            .send(TuiEvent::Error("Agent 连接验证失败".to_string()))
            .await;
        return Ok(());
    }

    let project_info = build_project_info(&working_dir)?;
    let template_base = get_template_base_dir(config);
    let prompt_config = PromptConfig {
        template_dir: template_base.clone(),
        default_template: Some(config.prompt.default_template.clone()),
    };
    let mut prompt_manager = PromptManager::new(prompt_config)?;

    let template_dir = template_base.join("plan").join("feature_analysis");
    let task_template = prompt_manager.load_task_dir(&template_dir)?;

    // 构建 context（移除 is_existing 判断，简化为统一的创建模式）
    let context = ContextBuilder::new()
        .with_project_info(project_info)
        .add_variable("feature_slug", feature_slug)?
        .add_variable("feature_description", feature_description)?
        .add_variable("mode", "create")?
        .build()?;

    let (system_prompt, user_prompt) = prompt_manager.render_task(&task_template, &context)?;

    let result = engine
        .execute_phase_with_config(
            Phase::Plan,
            &task_template.config,
            system_prompt,
            user_prompt,
        )
        .await?;

    let _ = ui_tx
        .send(TuiEvent::StatsUpdate {
            turns: result.turns as u32,
            cost_usd: result.cost_usd,
        })
        .await;

    if result.success {
        let mut state_manager = StateManager::new(feature_dir_name, &working_dir)?;
        state_manager.update_phase_status(0, ca_core::Status::Completed)?;
        state_manager.save()?;

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
    } else {
        let _ = ui_tx
            .send(TuiEvent::Error(format!(
                "Plan 执行失败: {}",
                result.message
            )))
            .await;
    }

    Ok(())
}

fn create_feature_dir(
    specs_dir: &Path, 
    feature_slug: &str
) -> anyhow::Result<(PathBuf, bool)> {
    // 1. 检查 feature slug 是否已存在
    if let Some(existing) = find_existing_feature(specs_dir, feature_slug)? {
        // Feature 已存在，直接返回现有目录（不在这里发送通知）
        return Ok((existing, true)); // (path, is_existing = true)
    }

    // 2. 创建新的功能目录
    let mut counter = 1;
    let feature_dir = loop {
        let dir_name = format!("{:03}-{}", counter, feature_slug);
        let dir_path = specs_dir.join(&dir_name);

        if !dir_path.exists() {
            std::fs::create_dir_all(&dir_path)?;
            let state_dir = dir_path.join(".ca-state");
            std::fs::create_dir_all(&state_dir)?;
            std::fs::create_dir_all(state_dir.join("backups"))?;
            break dir_path;
        }

        counter += 1;
        if counter > 999 {
            anyhow::bail!("功能编号超出范围 (max: 999)");
        }
    };
    
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

fn build_project_info(repo_path: &Path) -> anyhow::Result<ProjectInfo> {
    let project_name = repo_path
        .file_name()
        .and_then(|n| n.to_str())
        .unwrap_or("project")
        .to_string();
    let primary_language = detect_primary_language(repo_path);
    let framework = detect_framework(repo_path);
    Ok(ProjectInfo {
        name: project_name,
        repo_path: repo_path.display().to_string(),
        primary_language,
        framework,
    })
}

fn detect_primary_language(repo_path: &Path) -> Option<String> {
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

fn detect_framework(repo_path: &Path) -> Option<String> {
    if repo_path.join("Cargo.toml").exists() {
        None
    } else if let Ok(content) = std::fs::read_to_string(repo_path.join("package.json")) {
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
