use enigo::{Enigo, Keyboard, Settings};

use crate::input::error::InputError;

pub struct KeyboardInjector;

impl KeyboardInjector {
    pub fn new() -> Self {
        Self
    }

    pub fn inject_text(&self, text: &str) -> Result<(), InputError> {
        if text.trim().is_empty() {
            return Err(InputError::EmptyText);
        }
        let mut enigo =
            Enigo::new(&Settings::default()).map_err(|e| InputError::Backend(e.to_string()))?;
        let _ = enigo.text(text).map_err(|e| InputError::Backend(e.to_string()))?;
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::KeyboardInjector;
    use crate::input::error::InputError;

    #[test]
    fn empty_text_is_error() {
        let injector = KeyboardInjector::new();
        let result = injector.inject_text("");
        assert!(matches!(result, Err(InputError::EmptyText)));
    }
}
