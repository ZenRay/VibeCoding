use std::path::PathBuf;
use std::sync::Arc;

use ca_core::{ClaudeAgent, ExecutionEngine, Phase, Repository};
use ca_pm::{ContextBuilder, ProjectInfo, PromptConfig, PromptManager};

use crate::config::AppConfig;

pub enum Command {
    Init {
        api_key: Option<String>,
        agent: String,
    },
    Run {
        task: String,
        repo: Option<String>,
        files: Vec<String>,
    },
    Templates {
        verbose: bool,
    },
    Tui {
        repo: Option<String>,
    },
}

pub async fn execute_command(command: Command, config: &AppConfig) -> anyhow::Result<()> {
    match command {
        Command::Init { api_key, agent } => execute_init(api_key, agent, config).await,
        Command::Run { task, repo, files } => execute_run(task, repo, files, config).await,
        Command::Templates { verbose } => execute_templates(verbose, config).await,
        Command::Tui { repo } => execute_tui(repo, config).await,
    }
}

async fn execute_init(
    api_key: Option<String>,
    agent: String,
    config: &AppConfig,
) -> anyhow::Result<()> {
    println!("🚀 初始化 Code Agent 配置...");

    let mut new_config = config.clone();

    // 更新 API 密钥
    if let Some(key) = api_key {
        new_config.agent.api_key = key;
    } else if new_config.agent.api_key.is_empty() {
        println!("⚠️  警告: 未设置 API 密钥");
        println!("   请使用 --api-key 参数或手动编辑配置文件");
    }

    // 更新 Agent 类型
    new_config.agent.agent_type = agent;

    // 保存配置
    new_config.save_default()?;

    println!("✅ 配置已保存到 ~/.code-agent/config.toml");
    println!("📝 Agent 类型: {}", new_config.agent.agent_type);
    println!("📝 模型: {}", new_config.agent.model);

    Ok(())
}

async fn execute_run(
    task: String,
    repo: Option<String>,
    files: Vec<String>,
    config: &AppConfig,
) -> anyhow::Result<()> {
    println!("🚀 执行任务: {}", task);

    // 验证 API 密钥
    if config.agent.api_key.is_empty() {
        anyhow::bail!("❌ 未配置 API 密钥,请先运行: code-agent init --api-key YOUR_KEY");
    }

    // 确定工作目录
    let repo_path = if let Some(path) = repo {
        PathBuf::from(path)
    } else if let Some(default) = &config.default_repo {
        default.clone()
    } else {
        std::env::current_dir()?
    };

    println!("📂 工作目录: {}", repo_path.display());

    // 创建 Repository
    let repository = Arc::new(Repository::new(&repo_path)?);

    // 创建 Agent
    let agent: Arc<dyn ca_core::Agent> = match config.agent.agent_type.as_str() {
        "claude" => {
            let mut claude =
                ClaudeAgent::new(config.agent.api_key.clone(), config.agent.model.clone())?;

            if let Some(url) = &config.agent.api_url {
                claude = claude.with_api_url(url.clone());
            }

            Arc::new(claude)
        }
        _ => {
            anyhow::bail!("❌ 不支持的 Agent 类型: {}", config.agent.agent_type);
        }
    };

    // 创建 ExecutionEngine
    let engine = ExecutionEngine::new(agent, repository.clone());

    // 验证连接
    println!("🔌 验证 Agent 连接...");
    if !engine.validate().await? {
        anyhow::bail!("❌ Agent 连接验证失败");
    }

    // 构建上下文
    let project_info = ProjectInfo {
        name: "Code Agent Task".to_string(),
        repo_path: repo_path.display().to_string(),
        primary_language: None,
        framework: None,
    };

    let mut context = ContextBuilder::new()
        .with_project_info(project_info)
        .add_instruction(task.clone());

    // 添加相关文件
    for file_path in &files {
        if let Ok(content) = repository.read_file(file_path) {
            context = context.add_file(file_path.clone(), content);
        }
    }

    let template_context = context.build()?;

    // 渲染提示词
    let prompt_config = PromptConfig {
        template_dir: config.prompt.template_dir.clone(),
        default_template: Some(config.prompt.default_template.clone()),
    };

    let prompt_manager = PromptManager::new(prompt_config)?;
    let prompt = prompt_manager.render_default(&template_context)?;

    // 执行任务
    println!("⚙️  开始执行...");
    let result = engine.execute_phase(Phase::ExecutePhase3, prompt).await?;

    // 显示结果
    if result.success {
        println!("✅ 任务执行成功!");
        println!("📝 修改文件数: {}", result.files_changed);
        println!("🔢 使用 tokens: {}", result.tokens_used);
        println!("\n{}", result.message);
    } else {
        println!("❌ 任务执行失败: {}", result.message);
    }

    Ok(())
}

async fn execute_templates(verbose: bool, config: &AppConfig) -> anyhow::Result<()> {
    println!("📋 可用模板:");

    let prompt_config = PromptConfig {
        template_dir: config.prompt.template_dir.clone(),
        default_template: Some(config.prompt.default_template.clone()),
    };

    let manager = PromptManager::new(prompt_config)?;
    let templates = manager.list_templates();

    if templates.is_empty() {
        println!("  (无模板)");
    } else {
        for template_name in templates {
            print!("  - {}", template_name);

            if template_name == config.prompt.default_template {
                print!(" (默认)");
            }

            println!();

            if verbose && let Some(template) = manager.get_template(template_name) {
                if let Some(desc) = &template.description {
                    println!("    描述: {}", desc);
                }
                println!("    内容预览:");
                let preview: String = template
                    .content
                    .lines()
                    .take(3)
                    .collect::<Vec<_>>()
                    .join("\n");
                println!("    {}", preview.replace('\n', "\n    "));
            }
        }
    }

    println!("\n📂 模板目录: {}", config.prompt.template_dir.display());

    Ok(())
}

async fn execute_tui(repo: Option<String>, config: &AppConfig) -> anyhow::Result<()> {
    println!("🖥️  启动 TUI 模式...");

    // 确定工作目录
    let repo_path = if let Some(path) = repo {
        PathBuf::from(path)
    } else if let Some(default) = &config.default_repo {
        default.clone()
    } else {
        std::env::current_dir()?
    };

    // 启动 TUI
    crate::ui::run_tui(&repo_path, config).await?;

    Ok(())
}
