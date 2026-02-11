use thiserror::Error;

#[derive(Error, Debug)]
pub enum PromptError {
    #[error("Template error: {0}")]
    Template(String),

    #[error("Render error: {0}")]
    Render(String),

    #[error("IO error: {0}")]
    Io(#[from] std::io::Error),

    #[error("JSON error: {0}")]
    Json(#[from] serde_json::Error),

    #[error("MiniJinja error: {0}")]
    MiniJinja(#[from] minijinja::Error),

    #[error("Other error: {0}")]
    Other(#[from] anyhow::Error),
}

pub type Result<T> = std::result::Result<T, PromptError>;
