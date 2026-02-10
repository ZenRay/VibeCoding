//! TUI 模块：Plan 交互式界面 (3 区域布局 + Worker 并发)。

mod plan_app;
mod plan_worker;

pub use plan_app::run_plan_tui_blocking;
pub use plan_worker::run_plan_worker;

use std::path::PathBuf;
use tokio::sync::mpsc;

use crate::config::AppConfig;

/// 启动 Plan TUI：TUI Task (阻塞线程) + Worker Task (async)，通过 mpsc 通信。
pub async fn execute_plan_tui(
    feature_slug: String,
    repo_path: PathBuf,
    config: AppConfig,
) -> anyhow::Result<()> {
    let (ui_tx, ui_rx) = mpsc::channel(100);
    let (worker_tx, worker_rx) = mpsc::channel(100);

    let slug = feature_slug.clone();
    let path = repo_path.clone();

    let ui_handle = tokio::task::spawn_blocking(move || {
        run_plan_tui_blocking(ui_rx, worker_tx, slug, &path)
    });

    let worker_handle = tokio::spawn(async move {
        run_plan_worker(worker_rx, ui_tx, feature_slug, repo_path, config).await
    });

    tokio::select! {
        ui_res = ui_handle => {
            match ui_res {
                Ok(Ok(())) => {}
                Ok(Err(e)) => tracing::error!("TUI 错误: {:?}", e),
                Err(e) => tracing::error!("TUI task 异常: {:?}", e),
            }
        }
        worker_res = worker_handle => {
            if let Err(e) = worker_res {
                tracing::error!("Worker task 异常: {:?}", e);
            }
        }
    }

    Ok(())
}
