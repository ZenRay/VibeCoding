use thiserror::Error;

#[derive(Debug, Error)]
pub enum InputError {
    #[error("Text is empty")]
    EmptyText,
    #[error("Injection blocked: {0}")]
    InjectionBlocked(String),
    #[error("Clipboard unavailable")]
    ClipboardUnavailable,
    #[error("Clipboard read failed: {0}")]
    ClipboardReadFailed(String),
    #[error("Clipboard write failed: {0}")]
    ClipboardWriteFailed(String),
    #[error("Input backend error: {0}")]
    Backend(String),
}
