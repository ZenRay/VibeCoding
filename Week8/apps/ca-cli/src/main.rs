use clap::{Parser, Subcommand};

mod commands;
mod config;
mod ui;

use commands::{Command, execute_command};
use config::AppConfig;

#[derive(Parser)]
#[command(name = "code-agent")]
#[command(author, version, about, long_about = None)]
#[command(propagate_version = true)]
struct Cli {
    #[command(subcommand)]
    command: Commands,

    /// 配置文件路径
    #[arg(short, long)]
    config: Option<String>,

    /// 详细日志
    #[arg(short, long)]
    verbose: bool,
}

#[derive(Subcommand)]
enum Commands {
    /// 初始化配置
    Init {
        /// API 密钥
        #[arg(long)]
        api_key: Option<String>,

        /// Agent 类型 (claude, copilot, cursor)
        #[arg(long)]
        agent: Option<String>,

        /// 交互式配置向导
        #[arg(short, long)]
        interactive: bool,
    },

    /// 规划功能并生成 specs
    Plan {
        /// 功能名称 (slug)
        feature_slug: String,

        /// 功能描述
        #[arg(short, long)]
        description: Option<String>,

        /// 交互式模式
        #[arg(short, long)]
        interactive: bool,

        /// 工作目录
        #[arg(short, long)]
        repo: Option<std::path::PathBuf>,
    },

    /// 执行任务
    Run {
        /// 任务描述
        task: String,

        /// 工作目录
        #[arg(short, long)]
        repo: Option<String>,

        /// 相关文件(可以指定多个)
        #[arg(short, long)]
        files: Vec<String>,
    },

    /// 列出可用模板
    Templates {
        /// 显示详细信息
        #[arg(short, long)]
        verbose: bool,
    },

    /// 交互式 TUI 模式
    Tui {
        /// 工作目录
        #[arg(short, long)]
        repo: Option<String>,
    },
}

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    let cli = Cli::parse();

    // 初始化日志
    init_logging(cli.verbose);

    // 加载配置
    let config = if let Some(config_path) = cli.config {
        AppConfig::load_from_file(&config_path)?
    } else {
        AppConfig::load_default()?
    };

    // 执行命令
    match cli.command {
        Commands::Init { api_key, agent, interactive } => {
            execute_command(Command::Init { api_key, agent, interactive }, &config).await?;
        }
        Commands::Plan { feature_slug, description, interactive, repo } => {
            execute_command(Command::Plan { feature_slug, description, interactive, repo }, &config).await?;
        }
        Commands::Run { task, repo, files } => {
            execute_command(Command::Run { task, repo, files }, &config).await?;
        }
        Commands::Templates { verbose } => {
            execute_command(Command::Templates { verbose }, &config).await?;
        }
        Commands::Tui { repo } => {
            execute_command(Command::Tui { repo }, &config).await?;
        }
    }

    Ok(())
}

fn init_logging(verbose: bool) {
    use tracing_subscriber::{EnvFilter, fmt};

    let filter = if verbose {
        EnvFilter::new("debug")
    } else {
        EnvFilter::new("info")
    };

    fmt().with_env_filter(filter).with_target(false).init();
}
