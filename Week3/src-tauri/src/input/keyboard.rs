use crate::input::clipboard::InputError;

pub struct KeyboardInjector;

impl KeyboardInjector {
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
    use super::KeyboardInjector;
    use crate::input::clipboard::InputError;

    #[test]
    fn empty_text_is_error() {
        let injector = KeyboardInjector::new();
        let result = injector.inject_text("");
        assert!(matches!(result, Err(InputError::EmptyText)));
    }
}
