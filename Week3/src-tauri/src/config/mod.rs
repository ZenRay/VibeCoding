pub mod store;

use serde::{Deserialize, Serialize};

pub const CONFIG_MODULE_NAME: &str = "config";

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AppConfig {
    pub api_key: Option<String>,
    pub language: String,
    pub hotkey: String,
}

impl Default for AppConfig {
    fn default() -> Self {
        Self {
            api_key: None,
            language: "auto".to_string(),
            hotkey: "Cmd+Shift+\\".to_string(),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::AppConfig;

    #[test]
    fn default_config_has_hotkey() {
        let config = AppConfig::default();
        assert!(!config.hotkey.trim().is_empty());
    }
}
