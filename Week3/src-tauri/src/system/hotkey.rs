use thiserror::Error;

#[derive(Debug, Error)]
pub enum HotkeyError {
    #[error("Hotkey string is empty")]
    Empty,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct HotkeyConfig {
    pub value: String,
}

impl HotkeyConfig {
    pub fn new(value: String) -> Result<Self, HotkeyError> {
        if value.trim().is_empty() {
            return Err(HotkeyError::Empty);
        }
        Ok(Self { value })
    }
}

impl Default for HotkeyConfig {
    fn default() -> Self {
        Self {
            value: if cfg!(target_os = "macos") {
                "Cmd+Shift+\\".to_string()
            } else {
                "Ctrl+Shift+\\".to_string()
            },
        }
    }
}

#[cfg(test)]
mod tests {
    use super::{HotkeyConfig, HotkeyError};

    #[test]
    fn empty_hotkey_rejected() {
        let result = HotkeyConfig::new("".to_string());
        assert!(matches!(result, Err(HotkeyError::Empty)));
    }

    #[test]
    fn default_hotkey_non_empty() {
        let config = HotkeyConfig::default();
        assert!(!config.value.trim().is_empty());
    }
}
