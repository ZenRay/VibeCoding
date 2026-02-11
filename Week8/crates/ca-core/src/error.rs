use thiserror::Error;

#[derive(Error, Debug)]
pub enum CoreError {
    #[error("Agent error: {0}")]
    Agent(String),

    #[error("Execution error: {0}")]
    Execution(String),

    #[error("Repository error: {0}")]
    Repository(String),

    #[error("Configuration error: {0}")]
    Config(String),

    #[error("IO error: {0}")]
    Io(#[from] std::io::Error),

    #[error("JSON error: {0}")]
    Json(#[from] serde_json::Error),

    #[error("YAML error: {0}")]
    Yaml(#[from] serde_yaml::Error),

    #[error("HTTP error: {0}")]
    Http(#[from] reqwest::Error),

    #[error("Other error: {0}")]
    Other(#[from] anyhow::Error),
}

pub type Result<T> = std::result::Result<T, CoreError>;
