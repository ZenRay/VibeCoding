// Text injection strategy selector
//
// Provides intelligent text injection with:
// - Automatic strategy selection (keyboard vs clipboard)
// - Active window detection
// - Password field detection and blocking
// - Platform-specific optimizations

use super::clipboard::{ClipboardInjector, ClipboardManager};
use super::keyboard::KeyboardInjector;
use thiserror::Error;
use tracing::{info, warn};

/// Text injection errors
#[derive(Debug, Error)]
pub enum InjectionError {
    #[error("Keyboard injection failed: {0}")]
    KeyboardFailed(String),

    #[error("Clipboard injection failed: {0}")]
    ClipboardFailed(String),

    #[error("Active window detection failed: {0}")]
    WindowDetectionFailed(String),

    #[error("Text injection blocked: {0}")]
    InjectionBlocked(String),

    #[error("Empty text provided")]
    EmptyText,
}

/// Text injection method
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum InjectionMethod {
    /// Direct keyboard simulation (character by character)
    Keyboard,

    /// Clipboard-based paste (Cmd+V/Ctrl+V)
    Clipboard,
}

/// Text injection strategy configuration
#[derive(Debug, Clone)]
pub struct InjectionStrategy {
    /// Short text threshold (characters)
    /// Text shorter than this uses keyboard simulation
    /// Text equal or longer uses clipboard paste
    pub short_text_threshold: usize,

    /// Whether to preserve original clipboard content
    pub preserve_clipboard: bool,

    /// Whether to detect and block password fields
    pub block_password_fields: bool,

    /// Keyboard typing delay (milliseconds per character)
    pub keyboard_delay_ms: u64,
}

impl Default for InjectionStrategy {
    fn default() -> Self {
        Self {
            short_text_threshold: 10,
            preserve_clipboard: true,
            block_password_fields: true,
            keyboard_delay_ms: 5,
        }
    }
}

/// Main text injector that orchestrates injection strategies
pub struct TextInjector {
    keyboard_injector: KeyboardInjector,
    clipboard_injector: ClipboardInjector,
    strategy: InjectionStrategy,
}

impl TextInjector {
    /// Create a new text injector with default strategy
    pub fn new() -> Result<Self, InjectionError> {
        Self::with_strategy(InjectionStrategy::default())
    }

    /// Create a new text injector with custom strategy
    pub fn with_strategy(strategy: InjectionStrategy) -> Result<Self, InjectionError> {
        let keyboard_injector = KeyboardInjector::new(Some(strategy.keyboard_delay_ms))
            .map_err(|e| InjectionError::KeyboardFailed(e.to_string()))?;

        let clipboard_injector = ClipboardInjector::new(strategy.preserve_clipboard)
            .map_err(|e| InjectionError::ClipboardFailed(e.to_string()))?;

        Ok(Self {
            keyboard_injector,
            clipboard_injector,
            strategy,
        })
    }

    /// Inject text using automatic strategy selection
    ///
    /// # Arguments
    /// * `text` - The text to inject
    /// * `clipboard_manager` - Clipboard manager instance
    ///
    /// # Returns
    /// * `Ok(InjectionMethod)` - The method used for injection
    /// * `Err(InjectionError)` - If injection fails
    ///
    /// # Strategy Selection
    /// 1. Check active window and focus element
    /// 2. Block injection if password field detected
    /// 3. Select method based on text length and element type:
    ///    - Short text (<threshold): Keyboard simulation
    ///    - Long text (>=threshold): Clipboard paste
    ///    - Code editor: Always keyboard (preserves formatting)
    pub fn inject_text(
        &mut self,
        text: &str,
        clipboard_manager: &dyn ClipboardManager,
    ) -> Result<InjectionMethod, InjectionError> {
        if text.is_empty() {
            return Err(InjectionError::EmptyText);
        }

        info!(
            event = "text_injection_start",
            text_length = text.len(),
            chars = text.chars().count()
        );

        // Get active window information
        let active_window = match self.get_active_window() {
            Ok(window) => window,
            Err(e) => {
                warn!(
                    event = "active_window_detection_failed",
                    error = %e,
                    "Proceeding with default injection method"
                );
                // Default to keyboard for safety
                return self.inject_via_keyboard(text);
            }
        };

        info!(
            event = "active_window_detected",
            app_name = %active_window.app_name,
            focus_element = ?active_window.focus_element
        );

        // Check for password field
        if self.strategy.block_password_fields
            && active_window.focus_element == FocusElementType::SecureTextField
        {
            let msg = format!(
                "Text injection blocked: password field detected in {}",
                active_window.app_name
            );
            warn!(event = "injection_blocked", reason = "password_field");
            return Err(InjectionError::InjectionBlocked(msg));
        }

        // Select injection method
        let method = self.select_injection_method(text, &active_window);

        info!(
            event = "injection_method_selected",
            method = ?method,
            text_length = text.len()
        );

        // Execute injection
        match method {
            InjectionMethod::Keyboard => self.inject_via_keyboard(text),
            InjectionMethod::Clipboard => self.inject_via_clipboard(text, clipboard_manager),
        }
    }

    /// Select injection method based on text and active window
    fn select_injection_method(&self, text: &str, window: &ActiveWindowInfo) -> InjectionMethod {
        let char_count = text.chars().count();

        // Code editors: always use keyboard to preserve indentation
        if window.focus_element == FocusElementType::CodeEditor {
            return InjectionMethod::Keyboard;
        }

        // Short text: use keyboard
        if char_count < self.strategy.short_text_threshold {
            return InjectionMethod::Keyboard;
        }

        // Long text: use clipboard
        InjectionMethod::Clipboard
    }

    /// Inject text via keyboard simulation
    fn inject_via_keyboard(&mut self, text: &str) -> Result<InjectionMethod, InjectionError> {
        self.keyboard_injector
            .type_text(text)
            .map_err(|e| InjectionError::KeyboardFailed(e.to_string()))?;

        info!(event = "text_injected", method = "keyboard");
        Ok(InjectionMethod::Keyboard)
    }

    /// Inject text via clipboard paste
    fn inject_via_clipboard(
        &mut self,
        text: &str,
        clipboard_manager: &dyn ClipboardManager,
    ) -> Result<InjectionMethod, InjectionError> {
        self.clipboard_injector
            .inject_text(text, clipboard_manager)
            .map_err(|e| InjectionError::ClipboardFailed(e.to_string()))?;

        info!(event = "text_injected", method = "clipboard");
        Ok(InjectionMethod::Clipboard)
    }

    /// Get active window information
    ///
    /// This is a simplified version. Full implementation would use:
    /// - active-win-pos-rs for window detection
    /// - macOS Accessibility API for focus element detection
    fn get_active_window(&self) -> Result<ActiveWindowInfo, InjectionError> {
        // TODO: Implement using active-win-pos-rs
        // For now, return a mock active window
        Ok(ActiveWindowInfo {
            app_name: "Unknown".to_string(),
            focus_element: FocusElementType::TextField,
        })
    }

    /// Update injection strategy
    pub fn set_strategy(&mut self, strategy: InjectionStrategy) {
        self.keyboard_injector
            .set_typing_delay(strategy.keyboard_delay_ms);
        self.clipboard_injector
            .set_preserve_clipboard(strategy.preserve_clipboard);
        self.strategy = strategy;
    }

    /// Get current strategy
    pub fn strategy(&self) -> &InjectionStrategy {
        &self.strategy
    }
}

impl Default for TextInjector {
    fn default() -> Self {
        Self::new().expect("Failed to create default TextInjector")
    }
}

/// Active window information
#[derive(Debug, Clone)]
struct ActiveWindowInfo {
    /// Application name
    app_name: String,

    /// Type of focused element
    focus_element: FocusElementType,
}

/// Focus element type
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
enum FocusElementType {
    /// Regular text field (safe to inject)
    TextField,

    /// Secure text field / password field (block injection)
    SecureTextField,

    /// Rich text editor
    RichTextEditor,

    /// Code editor (prefer keyboard injection)
    CodeEditor,

    /// Non-editable area (block injection)
    NonEditable,

    /// Unknown type (default to text field behavior)
    Unknown,
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::input::clipboard::ClipboardManager;

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
    // All tests requiring TextInjector are marked #[ignore] to allow headless testing.

    #[test]
    #[ignore]
    fn test_text_injector_creation() {
        let injector = TextInjector::new();
        assert!(injector.is_ok());

        let injector = injector.unwrap();
        assert_eq!(injector.strategy().short_text_threshold, 10);
        assert!(injector.strategy().preserve_clipboard);
    }

    #[test]
    #[ignore]
    fn test_custom_strategy() {
        let strategy = InjectionStrategy {
            short_text_threshold: 20,
            preserve_clipboard: false,
            block_password_fields: true,
            keyboard_delay_ms: 10,
        };

        let injector = TextInjector::with_strategy(strategy);
        assert!(injector.is_ok());

        let injector = injector.unwrap();
        assert_eq!(injector.strategy().short_text_threshold, 20);
        assert!(!injector.strategy().preserve_clipboard);
    }

    #[test]
    #[ignore]
    fn test_empty_text_error() {
        let mut injector = TextInjector::new().unwrap();
        let clipboard = MockClipboard::new();

        let result = injector.inject_text("", &clipboard);
        assert!(result.is_err());
        assert!(matches!(result.unwrap_err(), InjectionError::EmptyText));
    }

    #[test]
    #[ignore]
    fn test_method_selection_short_text() {
        let injector = TextInjector::new().unwrap();
        let window = ActiveWindowInfo {
            app_name: "TextEdit".to_string(),
            focus_element: FocusElementType::TextField,
        };

        let method = injector.select_injection_method("Short", &window);
        assert_eq!(method, InjectionMethod::Keyboard);
    }

    #[test]
    #[ignore]
    fn test_method_selection_long_text() {
        let injector = TextInjector::new().unwrap();
        let window = ActiveWindowInfo {
            app_name: "TextEdit".to_string(),
            focus_element: FocusElementType::TextField,
        };

        let method = injector.select_injection_method("This is a much longer text that exceeds the threshold", &window);
        assert_eq!(method, InjectionMethod::Clipboard);
    }

    #[test]
    #[ignore]
    fn test_method_selection_code_editor() {
        let injector = TextInjector::new().unwrap();
        let window = ActiveWindowInfo {
            app_name: "VS Code".to_string(),
            focus_element: FocusElementType::CodeEditor,
        };

        // Even long text should use keyboard in code editor
        let method = injector.select_injection_method(
            "function example() { return 'very long code'; }",
            &window,
        );
        assert_eq!(method, InjectionMethod::Keyboard);
    }
}
