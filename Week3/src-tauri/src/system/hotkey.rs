// Global hotkey registration module
//
// Provides global hotkey support using tauri-plugin-global-shortcut
// - Default: Cmd+Shift+\ (macOS) / Ctrl+Shift+\ (Linux/Windows)
// - Customizable through configuration
// - Event-driven callback system

use thiserror::Error;
use tracing::{error, info, warn};

/// Hotkey registration errors
#[derive(Debug, Error)]
pub enum HotkeyError {
    #[error("Failed to register hotkey: {0}")]
    RegistrationFailed(String),

    #[error("Failed to unregister hotkey: {0}")]
    UnregistrationFailed(String),

    #[error("Hotkey already registered: {0}")]
    AlreadyRegistered(String),

    #[error("Invalid hotkey format: {0}")]
    InvalidFormat(String),
}

/// Hotkey configuration
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct HotkeyConfig {
    /// Modifier keys (e.g., ["CommandOrControl", "Shift"])
    pub modifiers: Vec<String>,

    /// Main key (e.g., "Backslash")
    pub key: String,
}

impl HotkeyConfig {
    /// Create default hotkey configuration
    ///
    /// Default: Cmd+Shift+\ (macOS) / Ctrl+Shift+\ (Linux/Windows)
    pub fn default() -> Self {
        Self {
            modifiers: vec!["CommandOrControl".to_string(), "Shift".to_string()],
            key: "Backslash".to_string(),
        }
    }

    /// Create custom hotkey configuration
    pub fn new(modifiers: Vec<String>, key: String) -> Result<Self, HotkeyError> {
        // Validate modifiers
        for modifier in &modifiers {
            if !Self::is_valid_modifier(modifier) {
                return Err(HotkeyError::InvalidFormat(format!(
                    "Invalid modifier: {}",
                    modifier
                )));
            }
        }

        // Validate key
        if key.is_empty() {
            return Err(HotkeyError::InvalidFormat(
                "Key cannot be empty".to_string(),
            ));
        }

        Ok(Self { modifiers, key })
    }

    /// Convert to shortcut string format
    ///
    /// Example: "CommandOrControl+Shift+Backslash"
    pub fn to_shortcut_string(&self) -> String {
        let mut parts = self.modifiers.clone();
        parts.push(self.key.clone());
        parts.join("+")
    }

    /// Validate modifier key
    fn is_valid_modifier(modifier: &str) -> bool {
        matches!(
            modifier,
            "CommandOrControl"
                | "Command"
                | "Cmd"
                | "Control"
                | "Ctrl"
                | "Alt"
                | "Option"
                | "Shift"
                | "Super"
                | "Meta"
        )
    }
}

impl std::fmt::Display for HotkeyConfig {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{}", self.to_shortcut_string())
    }
}

/// Global hotkey manager
///
/// Manages registration and lifecycle of global hotkeys using
/// tauri-plugin-global-shortcut
pub struct HotkeyManager {
    current_hotkey: Option<HotkeyConfig>,
    registered: bool,
}

impl HotkeyManager {
    /// Create a new hotkey manager
    pub fn new() -> Self {
        Self {
            current_hotkey: None,
            registered: false,
        }
    }

    /// Register a global hotkey
    ///
    /// # Arguments
    /// * `config` - Hotkey configuration
    /// * `app_handle` - Tauri app handle
    ///
    /// # Returns
    /// * `Ok(())` if registration successful
    /// * `Err(HotkeyError)` if registration fails
    ///
    /// # Note
    /// This is a placeholder implementation. The actual registration
    /// will be done in the Tauri setup using tauri-plugin-global-shortcut
    pub fn register<R: tauri::Runtime>(
        &mut self,
        config: HotkeyConfig,
        app_handle: &tauri::AppHandle<R>,
    ) -> Result<(), HotkeyError> {
        // Check if already registered
        if self.registered {
            if let Some(current) = &self.current_hotkey {
                if current == &config {
                    return Err(HotkeyError::AlreadyRegistered(config.to_string()));
                }
                // Unregister current before registering new one
                self.unregister(app_handle)?;
            }
        }

        let shortcut_str = config.to_shortcut_string();

        info!(
            event = "hotkey_registration_start",
            shortcut = %shortcut_str
        );

        // TODO: Actual registration using tauri-plugin-global-shortcut
        // Example:
        // use tauri_plugin_global_shortcut::GlobalShortcutExt;
        // app_handle.global_shortcut().register(&shortcut_str)
        //     .map_err(|e| HotkeyError::RegistrationFailed(e.to_string()))?;

        self.current_hotkey = Some(config);
        self.registered = true;

        info!(
            event = "hotkey_registered",
            shortcut = %shortcut_str
        );

        Ok(())
    }

    /// Unregister current hotkey
    ///
    /// # Arguments
    /// * `app_handle` - Tauri app handle
    ///
    /// # Returns
    /// * `Ok(())` if unregistration successful
    /// * `Err(HotkeyError)` if unregistration fails
    pub fn unregister<R: tauri::Runtime>(
        &mut self,
        _app_handle: &tauri::AppHandle<R>,
    ) -> Result<(), HotkeyError> {
        if !self.registered {
            return Ok(());
        }

        if let Some(config) = &self.current_hotkey {
            let shortcut_str = config.to_shortcut_string();

            info!(
                event = "hotkey_unregistration_start",
                shortcut = %shortcut_str
            );

            // TODO: Actual unregistration using tauri-plugin-global-shortcut
            // Example:
            // use tauri_plugin_global_shortcut::GlobalShortcutExt;
            // app_handle.global_shortcut().unregister(&shortcut_str)
            //     .map_err(|e| HotkeyError::UnregistrationFailed(e.to_string()))?;

            info!(
                event = "hotkey_unregistered",
                shortcut = %shortcut_str
            );
        }

        self.current_hotkey = None;
        self.registered = false;

        Ok(())
    }

    /// Check if a hotkey is currently registered
    pub fn is_registered(&self) -> bool {
        self.registered
    }

    /// Get current hotkey configuration
    pub fn current_hotkey(&self) -> Option<&HotkeyConfig> {
        self.current_hotkey.as_ref()
    }
}

impl Default for HotkeyManager {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_default_hotkey_config() {
        let config = HotkeyConfig::default();
        assert_eq!(config.modifiers, vec!["CommandOrControl", "Shift"]);
        assert_eq!(config.key, "Backslash");
        assert_eq!(
            config.to_shortcut_string(),
            "CommandOrControl+Shift+Backslash"
        );
    }

    #[test]
    fn test_custom_hotkey_config() {
        let config =
            HotkeyConfig::new(vec!["Control".to_string()], "Space".to_string());
        assert!(config.is_ok());

        let config = config.unwrap();
        assert_eq!(config.to_shortcut_string(), "Control+Space");
    }

    #[test]
    fn test_invalid_modifier() {
        let config = HotkeyConfig::new(
            vec!["InvalidModifier".to_string()],
            "A".to_string(),
        );
        assert!(config.is_err());
    }

    #[test]
    fn test_empty_key() {
        let config = HotkeyConfig::new(vec!["Control".to_string()], String::new());
        assert!(config.is_err());
    }

    #[test]
    fn test_hotkey_manager_creation() {
        let manager = HotkeyManager::new();
        assert!(!manager.is_registered());
        assert!(manager.current_hotkey().is_none());
    }

    #[test]
    fn test_hotkey_config_equality() {
        let config1 = HotkeyConfig::default();
        let config2 = HotkeyConfig::default();
        assert_eq!(config1, config2);

        let config3 =
            HotkeyConfig::new(vec!["Control".to_string()], "A".to_string()).unwrap();
        assert_ne!(config1, config3);
    }

    #[test]
    fn test_valid_modifiers() {
        let valid_modifiers = vec![
            "CommandOrControl",
            "Command",
            "Cmd",
            "Control",
            "Ctrl",
            "Alt",
            "Option",
            "Shift",
            "Super",
            "Meta",
        ];

        for modifier in valid_modifiers {
            let config = HotkeyConfig::new(
                vec![modifier.to_string()],
                "A".to_string(),
            );
            assert!(config.is_ok(), "Modifier {} should be valid", modifier);
        }
    }
}
