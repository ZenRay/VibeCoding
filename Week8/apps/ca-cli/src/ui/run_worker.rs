//! Run Worker：在后台执行 Run 流程 (Phase 1-7)，通过 mpsc 向 TUI 发送事件。

use std::path::PathBuf;
use std::sync::Arc;

use ca_core::{
    ExecutionEngine, Repository, StateManager, Status, TuiEvent, TuiEventHandler, WorktreeManager,
};
use ca_pm::{PromptConfig, PromptManager};
use tokio::sync::mpsc;

use crate::commands::run::{
    execute_execute_phase, execute_fix_phase, execute_observer_phase, execute_planning_phase,
    execute_review_phase, execute_verification_phase, find_feature_dir, get_phase_name,
};
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
        if path.exists() && path.join("run/phase1_observer/user.jinja").exists() {
            return path.clone();
        }
    }

    // 如果都不存在，回退到用户配置目录
    config.prompt.template_dir.clone()
}

/// Run Worker：执行 7 个 Phase，向 TUI 发送 TuiEvent。
pub async fn run_run_worker(
    ui_tx: mpsc::Sender<TuiEvent>,
    feature_slug: String,
    repo_path: PathBuf,
    config: AppConfig,
    dry_run: bool,
    skip_review: bool,
    skip_test: bool,
) -> anyhow::Result<()> {
    let feature_dir = find_feature_dir(&repo_path, &feature_slug)?;
    let feature_dir_name = feature_dir
        .file_name()
        .and_then(|n| n.to_str())
        .unwrap_or(&feature_slug)
        .to_string();

    let worktree_manager = WorktreeManager::new(&repo_path).map_err(|e| anyhow::anyhow!("{}", e))?;
    let working_dir = if worktree_manager.is_git_repo()
        && worktree_manager.worktree_exists(&feature_dir_name).unwrap_or(false)
    {
        worktree_manager.worktree_path(&feature_dir_name)
    } else {
        repo_path.clone()
    };

    let mut state_manager = StateManager::new(&feature_dir_name, &working_dir)?;

    let specs_dir = working_dir.join("specs");
    let spec_file = feature_dir.join("spec.md");
    let spec_content = if spec_file.exists() {
        std::fs::read_to_string(&spec_file).unwrap_or_default()
    } else {
        String::new()
    };

    let status_hook = Arc::new(ca_core::StatusDocumentHook::new(specs_dir, spec_content));
    state_manager.add_hook(status_hook);

    let repository = Arc::new(Repository::new(&working_dir)?);
    let agent = create_agent(&config)?;

    let event_handler = Box::new(TuiEventHandler::new(ui_tx.clone()));
    let mut engine =
        ExecutionEngine::new(agent, repository.clone()).with_event_handler(event_handler);

    if !engine.validate().await? {
        let _ = ui_tx
            .send(TuiEvent::Error("Agent 连接验证失败".to_string()))
            .await;
        return Ok(());
    }

    let template_base = get_template_base_dir(&config);
    let prompt_config = PromptConfig {
        template_dir: template_base,
        default_template: None,
    };
    let mut prompt_manager = PromptManager::new(prompt_config)?;

    for phase_num in 1..=7 {
        let phase_name = get_phase_name(phase_num).to_string();

        let _ = ui_tx
            .send(TuiEvent::PhaseStart(phase_num, phase_name.clone()))
            .await;

        if skip_review && phase_num == 5 {
            state_manager.update_phase_status(phase_num, Status::Completed)?;
            send_phase_complete(&ui_tx, &state_manager, phase_num).await;
            continue;
        }

        if skip_test && phase_num == 7 {
            state_manager.update_phase_status(phase_num, Status::Completed)?;
            send_phase_complete(&ui_tx, &state_manager, phase_num).await;
            continue;
        }

        state_manager.start_phase_with_default_name(phase_num)?;

        let result: anyhow::Result<()> = match phase_num {
            1 => {
                execute_observer_phase(
                    &mut engine,
                    &mut state_manager,
                    &mut prompt_manager,
                    &feature_dir,
                    &working_dir,
                    dry_run,
                )
                .await
            }
            2 => {
                execute_planning_phase(
                    &mut engine,
                    &mut state_manager,
                    &mut prompt_manager,
                    &feature_dir,
                    &working_dir,
                    dry_run,
                )
                .await
            }
            3 | 4 => {
                execute_execute_phase(
                    &mut engine,
                    &mut state_manager,
                    &mut prompt_manager,
                    &feature_dir,
                    &working_dir,
                    phase_num,
                    dry_run,
                )
                .await
            }
            5 => {
                execute_review_phase(
                    &mut engine,
                    &mut state_manager,
                    &mut prompt_manager,
                    &feature_dir,
                    &working_dir,
                    dry_run,
                    true, // tui_mode: 自动继续，不读 stdin
                )
                .await
            }
            6 => {
                execute_fix_phase(
                    &mut engine,
                    &mut state_manager,
                    &mut prompt_manager,
                    &feature_dir,
                    &working_dir,
                    dry_run,
                )
                .await
            }
            7 => {
                execute_verification_phase(
                    &mut engine,
                    &mut state_manager,
                    &mut prompt_manager,
                    &feature_dir,
                    &working_dir,
                    dry_run,
                )
                .await
            }
            _ => anyhow::bail!("无效的 phase 编号: {}", phase_num),
        };

        match result {
            Ok(()) => {
                state_manager.update_phase_status(phase_num, Status::Completed)?;
                state_manager.save()?;
                send_phase_complete(&ui_tx, &state_manager, phase_num).await;
            }
            Err(e) => {
                let err_msg = e.to_string();
                let _ = ui_tx
                    .send(TuiEvent::PhaseFailed(phase_num, err_msg.clone()))
                    .await;
                let _ = ui_tx.send(TuiEvent::Error(err_msg)).await;
                return Err(e);
            }
        }
    }

    let _ = ui_tx.send(TuiEvent::Complete).await;

    Ok(())
}

async fn send_phase_complete(
    ui_tx: &mpsc::Sender<TuiEvent>,
    state_manager: &StateManager,
    phase_num: u8,
) {
    let state = state_manager.state();
    let turns = state.cost_summary.total_tokens_input;
    let cost_usd = state.cost_summary.total_cost_usd;
    let _ = ui_tx.send(TuiEvent::PhaseComplete(phase_num)).await;
    let _ = ui_tx.send(TuiEvent::StatsUpdate { turns, cost_usd }).await;
}

fn create_agent(config: &AppConfig) -> anyhow::Result<Arc<dyn ca_core::Agent>> {
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
