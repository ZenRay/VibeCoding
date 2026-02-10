use std::path::PathBuf;

use ca_pm::{PromptConfig, PromptManager};

use crate::config::AppConfig;

mod init;
mod plan;
mod run;
mod list;
mod status;
mod clean;

pub use init::execute_init;
pub use plan::execute_plan;
pub use run::execute_run;
pub use list::execute_list;
pub use status::execute_status;
pub use clean::execute_clean;

pub enum Command {
    Init {
        api_key: Option<String>,
        agent: Option<String>,
        interactive: bool,
        force: bool,
    },
    Plan {
        feature_slug: String,
        description: Option<String>,
        interactive: bool,
        repo: Option<PathBuf>,
    },
    Run {
        feature_slug: String,
        phase: Option<u8>,
        resume: bool,
        dry_run: bool,
        skip_review: bool,
        skip_test: bool,
        repo: Option<PathBuf>,
    },
    Templates {
        verbose: bool,
    },
    List {
        all: bool,
        status: Option<String>,
    },
    Status {
        feature_slug: String,
    },
    Clean {
        dry_run: bool,
        all: bool,
    },
}

pub async fn execute_command(command: Command, config: &AppConfig) -> anyhow::Result<()> {
    match command {
        Command::Init { api_key, agent, interactive, force } => {
            execute_init(api_key, agent, interactive, force, config).await
        }
        Command::Plan { feature_slug, description, interactive, repo } => {
            execute_plan(feature_slug, description, interactive, repo, config).await
        }
        Command::Run { feature_slug, phase, resume, dry_run, skip_review, skip_test, repo } => {
            execute_run(feature_slug, phase, resume, dry_run, skip_review, skip_test, repo, config).await
        }
        Command::Templates { verbose } => execute_templates(verbose, config).await,
        Command::List { all, status } => {
            execute_list(all, status, config).await
        }
        Command::Status { feature_slug } => {
            execute_status(feature_slug, config).await
        }
        Command::Clean { dry_run, all } => {
            execute_clean(dry_run, all, config).await
        }
    }
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
