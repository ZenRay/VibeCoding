// Clipboard-based text injection module
//
// Provides clipboard-based text injection with:
// - Save/restore clipboard content
// - Simulate Cmd+V/Ctrl+V paste
// - Cross-platform support (macOS/Linux/Windows)

use enigo::{Direction, Enigo, Key, Keyboard, Settings};
use std::thread;
use std::time::Duration;
use thiserror::Error;
use tracing::{debug, info, warn};

/// Clipboard injection errors
#[derive(Debug, Error)]
pub enum ClipboardError {
    #[error("Failed to read clipboard content")]
    ReadFailed,

    #[error("Failed to write clipboard content")]
    WriteFailed,

    #[error("Failed to simulate paste command")]
    PasteFailed,

    #[error("Empty text provided")]
    EmptyText,

    #[error("Clipboard restoration failed")]
    RestorationFailed,
}

/// Clipboard text injector
///
/// This injector uses the system clipboard to inject text:
/// 1. Save current clipboard content
/// 2. Write new text to clipboard
/// 3. Simulate Cmd+V (macOS) or Ctrl+V (Linux/Windows)
/// 4. Restore original clipboard content
pub struct ClipboardInjector {
    enigo: Enigo,
    preserve_clipboard: bool,
}

impl ClipboardInjector {
    /// Create a new clipboard injector
    ///
    /// # Arguments
    /// * `preserve_clipboard` - Whether to save and restore original clipboard content
    pub fn new(preserve_clipboard: bool) -> Result<Self, ClipboardError> {
        let enigo = Enigo::new(&Settings::default())
            .map_err(|_| ClipboardError::PasteFailed)?;

        Ok(Self {
            enigo,
            preserve_clipboard,
        })
    }

    /// Inject text via clipboard paste
    ///
    /// # Arguments
    /// * `text` - The text to inject
    /// * `app_handle` - Tauri app handle for clipboard access
    ///
    /// # Returns
    /// * `Ok(())` if successful
    /// * `Err(ClipboardError)` if injection fails
    ///
    /// # Process
    /// 1. Save original clipboard content (if preserve_clipboard is true)
    /// 2. Write text to clipboard
    /// 3. Simulate Cmd+V/Ctrl+V
    /// 4. Wait for paste to complete
    /// 5. Restore original clipboard (if preserve_clipboard is true)
    pub fn inject_text(
        &mut self,
        text: &str,
        clipboard_manager: &dyn ClipboardManager,
    ) -> Result<(), ClipboardError> {
        if text.is_empty() {
            return Err(ClipboardError::EmptyText);
        }

        info!(
            event = "clipboard_injection_start",
            text_length = text.len(),
            preserve = self.preserve_clipboard
        );

        // Step 1: Save original clipboard content
        let original_content = if self.preserve_clipboard {
            match clipboard_manager.read_text() {
                Ok(content) => {
                    debug!(
                        event = "clipboard_saved",
                        length = content.len()
                    );
                    Some(content)
                }
                Err(e) => {
                    warn!(
                        event = "clipboard_save_failed",
                        error = %e,
                        "Proceeding without backup"
                    );
                    None
                }
            }
        } else {
            None
        };

        // Step 2: Write text to clipboard
        clipboard_manager
            .write_text(text)
            .map_err(|_| ClipboardError::WriteFailed)?;

        debug!(event = "clipboard_written", text_length = text.len());

        // Step 3: Simulate paste command
        // Wait a bit for clipboard to be ready
        thread::sleep(Duration::from_millis(50));

        self.simulate_paste()?;

        // Step 4: Wait for paste to complete
        thread::sleep(Duration::from_millis(100));

        // Step 5: Restore original clipboard
        if let Some(original) = original_content {
            match clipboard_manager.write_text(&original) {
                Ok(_) => {
                    debug!(
                        event = "clipboard_restored",
                        length = original.len()
                    );
                }
                Err(e) => {
                    warn!(
                        event = "clipboard_restore_failed",
                        error = %e,
                        "Original content may be lost"
                    );
                    return Err(ClipboardError::RestorationFailed);
                }
            }
        }

        info!(event = "clipboard_injection_complete");

        Ok(())
    }

    /// Simulate paste keyboard shortcut
    ///
    /// - macOS: Cmd+V
    /// - Linux/Windows: Ctrl+V
    fn simulate_paste(&mut self) -> Result<(), ClipboardError> {
        #[cfg(target_os = "macos")]
        {
            self.enigo
                .key(Key::Meta, Direction::Press)
                .map_err(|_| ClipboardError::PasteFailed)?;
            self.enigo
                .key(Key::Unicode('v'), Direction::Click)
                .map_err(|_| ClipboardError::PasteFailed)?;
            self.enigo
                .key(Key::Meta, Direction::Release)
                .map_err(|_| ClipboardError::PasteFailed)?;
        }

        #[cfg(not(target_os = "macos"))]
        {
            self.enigo
                .key(Key::Control, Direction::Press)
                .map_err(|_| ClipboardError::PasteFailed)?;
            self.enigo
                .key(Key::Unicode('v'), Direction::Click)
                .map_err(|_| ClipboardError::PasteFailed)?;
            self.enigo
                .key(Key::Control, Direction::Release)
                .map_err(|_| ClipboardError::PasteFailed)?;
        }

        debug!(event = "paste_command_simulated");

        Ok(())
    }

    /// Set clipboard preservation behavior
    pub fn set_preserve_clipboard(&mut self, preserve: bool) {
        self.preserve_clipboard = preserve;
    }

    /// Get clipboard preservation setting
    pub fn preserves_clipboard(&self) -> bool {
        self.preserve_clipboard
    }
}

impl Default for ClipboardInjector {
    fn default() -> Self {
        Self::new(true).expect("Failed to create default ClipboardInjector")
    }
}

/// Trait for clipboard access
///
/// This trait abstracts clipboard operations to allow
/// testing without requiring actual clipboard access.
pub trait ClipboardManager {
    fn read_text(&self) -> Result<String, String>;
    fn write_text(&self, text: &str) -> Result<(), String>;
}

/// Tauri clipboard manager implementation
pub struct TauriClipboardManager<'a, R: tauri::Runtime> {
    app_handle: &'a tauri::AppHandle<R>,
}

impl<'a, R: tauri::Runtime> TauriClipboardManager<'a, R> {
    pub fn new(app_handle: &'a tauri::AppHandle<R>) -> Self {
        Self { app_handle }
    }
}

impl<'a, R: tauri::Runtime> ClipboardManager for TauriClipboardManager<'a, R> {
    fn read_text(&self) -> Result<String, String> {
        // Note: Actual implementation will use tauri-plugin-clipboard-manager
        // For now, return empty string as placeholder
        // TODO: Implement using app_handle.clipboard().read_text()
        Ok(String::new())
    }

    fn write_text(&self, _text: &str) -> Result<(), String> {
        // Note: Actual implementation will use tauri-plugin-clipboard-manager
        // TODO: Implement using app_handle.clipboard().write_text(text)
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    struct MockClipboard {
        content: std::cell::RefCell<String>,
    }

    impl MockClipboard {
        fn new() -> Self {
            Self {
                content: std::cell::RefCell::new(String::new()),
            }
        }
    }

    impl ClipboardManager for MockClipboard {
        fn read_text(&self) -> Result<String, String> {
            Ok(self.content.borrow().clone())
        }

        fn write_text(&self, text: &str) -> Result<(), String> {
            *self.content.borrow_mut() = text.to_string();
            Ok(())
        }
    }

    // Note: enigo requires an active X11/Wayland/Windows display server to initialize.
    // All tests requiring enigo are marked #[ignore] to allow headless testing.

    #[test]
    #[ignore]
    fn test_clipboard_injector_creation() {
        let injector = ClipboardInjector::new(true);
        assert!(injector.is_ok());
        assert!(injector.unwrap().preserves_clipboard());

        let injector = ClipboardInjector::new(false);
        assert!(injector.is_ok());
        assert!(!injector.unwrap().preserves_clipboard());
    }

    #[test]
    #[ignore]
    fn test_empty_text_error() {
        let mut injector = ClipboardInjector::new(true).unwrap();
        let clipboard = MockClipboard::new();

        let result = injector.inject_text("", &clipboard);
        assert!(result.is_err());
        assert!(matches!(result.unwrap_err(), ClipboardError::EmptyText));
    }

    #[test]
    #[ignore]
    fn test_clipboard_preservation() {
        let injector = ClipboardInjector::new(true);
        assert!(injector.is_ok());
        let clipboard = MockClipboard::new();

        // Set initial clipboard content
        clipboard.write_text("Original content").unwrap();

        // Note: This test will fail without actual clipboard/UI integration
        // It's here to demonstrate the expected behavior
        // Inject new text
        // let _ = injector.inject_text("New text", &clipboard);

        // Verify original content is restored (after paste simulation)
        // This would need actual integration testing
    }

    #[test]
    #[ignore]
    fn test_set_preserve_clipboard() {
        let mut injector = ClipboardInjector::new(true).unwrap();
        assert!(injector.preserves_clipboard());

        injector.set_preserve_clipboard(false);
        assert!(!injector.preserves_clipboard());
    }
}
