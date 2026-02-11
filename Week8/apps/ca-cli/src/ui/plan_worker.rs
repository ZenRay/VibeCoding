//! Plan Worker：在后台执行 plan 流程，通过 mpsc 向 TUI 发送事件。

use std::path::{Path, PathBuf};
use std::sync::Arc;

use ca_core::{
    Agent, ExecutionEngine, Phase, Repository, StateManager, TuiEvent, TuiEventHandler,
};
use ca_pm::{ContextBuilder, ProjectInfo, PromptConfig, PromptManager};
use tokio::sync::mpsc;

use crate::config::AppConfig;
use super::plan_app::UserMessage;

/// Plan Worker：接收用户消息，执行 plan 阶段，向 TUI 发送 TuiEvent。
pub async fn run_plan_worker(
    mut worker_rx: mpsc::Receiver<UserMessage>,
    ui_tx: mpsc::Sender<TuiEvent>,
    feature_slug: String,
    repo_path: PathBuf,
    config: AppConfig,
) -> anyhow::Result<()> {
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
                )
                .await
                {
                    let _ = ui_tx
                        .send(TuiEvent::Error(e.to_string()))
                        .await;
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
) -> anyhow::Result<()> {
    let specs_dir = repo_path.join("specs");
    std::fs::create_dir_all(&specs_dir)?;

    let feature_dir = create_feature_dir(&specs_dir, feature_slug)?;

    let repository = Arc::new(Repository::new(repo_path)?);
    let agent = create_agent(config)?;

    let event_handler = Box::new(TuiEventHandler::new(ui_tx.clone()));
    let mut engine = ExecutionEngine::new(agent, repository.clone())
        .with_event_handler(event_handler);

    if !engine.validate().await? {
        let _ = ui_tx
            .send(TuiEvent::Error("Agent 连接验证失败".to_string()))
            .await;
        return Ok(());
    }

    let project_info = build_project_info(repo_path)?;
    let prompt_config = PromptConfig {
        template_dir: config.prompt.template_dir.clone(),
        default_template: Some(config.prompt.default_template.clone()),
    };
    let mut prompt_manager = PromptManager::new(prompt_config)?;

    let template_dir = config
        .prompt
        .template_dir
        .join("plan")
        .join("feature_analysis");
    let task_template = prompt_manager.load_task_dir(&template_dir)?;

    let context = ContextBuilder::new()
        .with_project_info(project_info)
        .add_variable("feature_slug", feature_slug)?
        .add_variable("feature_description", feature_description)?
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
        let mut state_manager = StateManager::new(feature_slug, repo_path)?;
        state_manager.update_phase_status(0, ca_core::Status::Completed)?;
        state_manager.save()?;

        let status_path = feature_dir.join("status.md");
        let spec_file_path = feature_dir.join("spec.md");
        let spec_content = if spec_file_path.exists() {
            std::fs::read_to_string(&spec_file_path).unwrap_or_default()
        } else {
            String::new()
        };
        let status_doc = ca_core::StatusDocument::from_feature_state(
            state_manager.state(),
            &spec_content,
        );
        status_doc.save(&status_path)?;
    } else {
        let _ = ui_tx
            .send(TuiEvent::Error(format!("Plan 执行失败: {}", result.message)))
            .await;
    }

    Ok(())
}

fn create_feature_dir(specs_dir: &Path, feature_slug: &str) -> anyhow::Result<PathBuf> {
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
    Ok(feature_dir)
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
