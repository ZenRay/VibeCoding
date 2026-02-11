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

    /// API base URL (用于 OpenRouter, Azure, 等第三方服务)
    /// 示例: https://openrouter.ai/api/v1
    #[arg(long, global = true)]
    api_url: Option<String>,

    /// 模型名称 (覆盖默认模型)
    #[arg(long, global = true)]
    model: Option<String>,

    /// API 密钥 (覆盖环境变量)
    #[arg(long, global = true)]
    api_key: Option<String>,
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

        /// 强制重新初始化 (覆盖已有文件)
        #[arg(short, long)]
        force: bool,
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
        /// 功能名称 (slug)
        feature_slug: String,

        /// 执行特定阶段 (1-7)
        #[arg(long)]
        phase: Option<u8>,

        /// 从中断处恢复
        #[arg(long)]
        resume: bool,

        /// 模拟执行,不修改文件
        #[arg(long)]
        dry_run: bool,

        /// 跳过代码审查
        #[arg(long)]
        skip_review: bool,

        /// 跳过测试验证
        #[arg(long)]
        skip_test: bool,

        /// 交互式 TUI 模式
        #[arg(short, long)]
        interactive: bool,

        /// 工作目录
        #[arg(short, long)]
        repo: Option<std::path::PathBuf>,
    },

    /// 列出可用模板
    Templates {
        /// 显示详细信息
        #[arg(short, long)]
        verbose: bool,
    },

    /// 列出所有功能及状态
    List {
        /// 显示所有功能 (包括已完成的)
        #[arg(long)]
        all: bool,

        /// 按状态筛选
        #[arg(long, value_name = "STATUS")]
        status: Option<String>,
    },

    /// 查看功能详细状态
    Status {
        /// 功能名称 (slug)
        feature_slug: String,
    },

    /// 清理已完成功能的 worktree (仅 .trees/，specs/ 永久保留)
    Clean {
        /// 试运行,不实际删除
        #[arg(long)]
        dry_run: bool,

        /// 显示所有功能 (包括跳过的)
        #[arg(short, long)]
        all: bool,
    },
}

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    let cli = Cli::parse();

    // 检查是否是交互模式（决定是否初始化日志）
    let is_interactive = match &cli.command {
        Commands::Plan { interactive, .. } => *interactive,
        Commands::Run { interactive, .. } => *interactive,
        _ => false,
    };

    // 只在非交互模式下初始化日志（TUI 模式不需要日志输出）
    if !is_interactive {
        init_logging(cli.verbose);
    }

    // 加载配置
    let mut config = if let Some(config_path) = cli.config {
        AppConfig::load_from_file(&config_path)?
    } else {
        AppConfig::load_default()?
    };

    // 将命令行参数合并到配置 (CLI 参数优先级更高)
    // 优先级: CLI 参数 > 环境变量 > 配置文件默认值
    
    // API Key: CLI 参数 > 环境变量
    if let Some(api_key) = cli.api_key {
        config.agent.api_key = api_key;
    } else if config.agent.api_key.is_empty() {
        // 配置文件中没有 API key，从环境变量加载
        if let Ok(key) = ca_core::Config::load_api_key(&ca_core::AgentType::Claude) {
            config.agent.api_key = key;
        }
    }
    
    // API URL: CLI 参数 > 环境变量
    if let Some(api_url) = cli
        .api_url
        .or_else(|| std::env::var("ANTHROPIC_BASE_URL").ok())
    {
        config.agent.api_url = Some(api_url);
    }
    
    // Model: CLI 参数 > 环境变量
    if let Some(model) = cli.model {
        config.agent.model = model;
    }

    // 执行命令
    match cli.command {
        Commands::Init {
            api_key,
            agent,
            interactive,
            force,
        } => {
            execute_command(
                Command::Init {
                    api_key,
                    agent,
                    interactive,
                    force,
                },
                &config,
            )
            .await?;
        }
        Commands::Plan {
            feature_slug,
            description,
            interactive,
            repo,
        } => {
            execute_command(
                Command::Plan {
                    feature_slug,
                    description,
                    interactive,
                    repo,
                },
                &config,
            )
            .await?;
        }
        Commands::Run {
            feature_slug,
            phase,
            resume,
            dry_run,
            skip_review,
            skip_test,
            interactive,
            repo,
        } => {
            execute_command(
                Command::Run {
                    feature_slug,
                    phase,
                    resume,
                    dry_run,
                    skip_review,
                    skip_test,
                    interactive,
                    repo,
                },
                &config,
            )
            .await?;
        }
        Commands::Templates { verbose } => {
            execute_command(Command::Templates { verbose }, &config).await?;
        }
        Commands::List { all, status } => {
            execute_command(Command::List { all, status }, &config).await?;
        }
        Commands::Status { feature_slug } => {
            execute_command(Command::Status { feature_slug }, &config).await?;
        }
        Commands::Clean { dry_run, all } => {
            execute_command(Command::Clean { dry_run, all }, &config).await?;
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
