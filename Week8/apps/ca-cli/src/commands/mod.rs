use std::path::PathBuf;

use crate::config::AppConfig;

mod init;
mod plan;
mod run;
mod list;
mod status;
mod clean;
mod templates;

pub use init::execute_init;
pub use plan::execute_plan;
pub use run::execute_run;
pub use list::execute_list;
pub use status::execute_status;
pub use clean::execute_clean;
pub use templates::execute_templates;

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
