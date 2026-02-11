//! TUI 模块：Plan 和 Run 交互式界面。

mod plan_app;
mod plan_worker;
mod run_app;
mod run_worker;

pub use plan_app::run_plan_tui_blocking;
pub use plan_worker::run_plan_worker;
pub use run_app::run_run_tui_blocking;
pub use run_worker::run_run_worker;

use std::path::PathBuf;
use tokio::sync::mpsc;

use crate::config::AppConfig;

/// 启动 Plan TUI：TUI Task (阻塞线程) + Worker Task (async)，通过 mpsc 通信。
pub async fn execute_plan_tui(
    feature_slug: String,
    repo_path: PathBuf,
    config: AppConfig,
) -> anyhow::Result<()> {
    // TUI 模式下禁用 tracing 日志输出（避免干扰 TUI 界面）
    disable_tracing_output();
    
    let (ui_tx, ui_rx) = mpsc::channel(100);
    let (worker_tx, worker_rx) = mpsc::channel(100);

    let slug = feature_slug.clone();
    let path = repo_path.clone();

    let ui_handle =
        tokio::task::spawn_blocking(move || run_plan_tui_blocking(ui_rx, worker_tx, slug, &path));

    let worker_handle = tokio::spawn(async move {
        run_plan_worker(worker_rx, ui_tx, feature_slug, repo_path, config).await
    });

    tokio::select! {
        ui_res = ui_handle => {
            match ui_res {
                Ok(Ok(())) => {}
                Ok(Err(e)) => eprintln!("TUI 错误: {:?}", e),
                Err(e) => eprintln!("TUI task 异常: {:?}", e),
            }
        }
        worker_res = worker_handle => {
            if let Err(e) = worker_res {
                eprintln!("Worker task 异常: {:?}", e);
            }
        }
    }

    Ok(())
}

/// 启动 Run TUI：TUI Task (阻塞线程) + RunWorker Task (async)，通过 mpsc 通信。
pub async fn execute_run_tui(
    feature_slug: String,
    repo_path: PathBuf,
    config: AppConfig,
    dry_run: bool,
    skip_review: bool,
    skip_test: bool,
) -> anyhow::Result<()> {
    // TUI 模式下禁用 tracing 日志输出（避免干扰 TUI 界面）
    disable_tracing_output();
    
    let (ui_tx, ui_rx) = mpsc::channel(100);

    let slug = feature_slug.clone();
    let path = repo_path.clone();

    let ui_handle = tokio::task::spawn_blocking(move || run_run_tui_blocking(ui_rx, slug, &path));

    let worker_handle = tokio::spawn(async move {
        run_run_worker(
            ui_tx,
            feature_slug,
            repo_path,
            config,
            dry_run,
            skip_review,
            skip_test,
        )
        .await
    });

    tokio::select! {
        ui_res = ui_handle => {
            match ui_res {
                Ok(Ok(())) => {}
                Ok(Err(e)) => eprintln!("TUI 错误: {:?}", e),
                Err(e) => eprintln!("TUI task 异常: {:?}", e),
            }
        }
        worker_res = worker_handle => {
            if let Err(e) = worker_res {
                eprintln!("Worker task 异常: {:?}", e);
            }
        }
    }

    Ok(())
}

/// 禁用 tracing 日志输出（TUI 模式下使用）
fn disable_tracing_output() {
    use tracing_subscriber::{fmt, EnvFilter};
    
    // 方法 1: 尝试创建一个输出到 /dev/null 的 subscriber（Unix）
    #[cfg(unix)]
    {
        if let Ok(null_file) = std::fs::OpenOptions::new()
            .write(true)
            .open("/dev/null")
        {
            let subscriber = fmt()
                .with_writer(move || null_file.try_clone().unwrap())
                .with_env_filter(EnvFilter::new("off"))
                .finish();
            
            let _ = tracing::subscriber::set_global_default(subscriber);
            return;
        }
    }
    
    // 方法 2: 创建一个静默的 subscriber
    let subscriber = fmt()
        .with_writer(std::io::sink)  // 输出到空设备
        .with_env_filter(EnvFilter::new("off"))
        .finish();
    
    let _ = tracing::subscriber::set_global_default(subscriber);
}
