use thiserror::Error;

#[derive(Debug, Error)]
pub enum InputError {
    #[error("Text is empty")]
    EmptyText,
}

pub struct ClipboardInjector;

impl ClipboardInjector {
    pub fn new() -> Self {
        Self
    }

    pub fn inject_text(&self, text: &str) -> Result<(), InputError> {
        if text.trim().is_empty() {
            return Err(InputError::EmptyText);
        }
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::{ClipboardInjector, InputError};

    #[test]
    fn empty_text_is_error() {
        let injector = ClipboardInjector::new();
        let result = injector.inject_text("   ");
        assert!(matches!(result, Err(InputError::EmptyText)));
    }
}
