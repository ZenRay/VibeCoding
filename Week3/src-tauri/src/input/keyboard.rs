// Keyboard simulation module using enigo
//
// Provides keyboard-based text injection with support for:
// - UTF-8 characters (Chinese, emoji, etc.)
// - Controlled typing speed (5ms per character)
// - Platform-specific key mappings

use enigo::{Direction, Enigo, Key, Keyboard, Settings};
use std::thread;
use std::time::Duration;
use thiserror::Error;
use tracing::{debug, info};

/// Keyboard injection errors
#[derive(Debug, Error)]
pub enum KeyboardError {
    #[error("Failed to initialize keyboard controller")]
    InitializationFailed,

    #[error("Failed to type text: {0}")]
    TypingFailed(String),

    #[error("Empty text provided")]
    EmptyText,
}

/// Keyboard text injector
pub struct KeyboardInjector {
    enigo: Enigo,
    typing_delay_ms: u64,
}

impl KeyboardInjector {
    /// Create a new keyboard injector
    ///
    /// # Arguments
    /// * `typing_delay_ms` - Delay between each character in milliseconds (default: 5ms)
    pub fn new(typing_delay_ms: Option<u64>) -> Result<Self, KeyboardError> {
        let enigo = Enigo::new(&Settings::default())
            .map_err(|_| KeyboardError::InitializationFailed)?;

        Ok(Self {
            enigo,
            typing_delay_ms: typing_delay_ms.unwrap_or(5),
        })
    }

    /// Type text character by character with controlled speed
    ///
    /// # Arguments
    /// * `text` - The text to type
    ///
    /// # Returns
    /// * `Ok(())` if successful
    /// * `Err(KeyboardError)` if typing fails
    ///
    /// # Example
    /// ```ignore
    /// let mut injector = KeyboardInjector::new(None)?;
    /// injector.type_text("Hello, 世界! 🚀")?;
    /// ```
    pub fn type_text(&mut self, text: &str) -> Result<(), KeyboardError> {
        if text.is_empty() {
            return Err(KeyboardError::EmptyText);
        }

        info!(
            event = "keyboard_typing_start",
            text_length = text.len(),
            chars = text.chars().count(),
            delay_ms = self.typing_delay_ms
        );

        let char_count = text.chars().count();

        for (i, ch) in text.chars().enumerate() {
            // Type the character using text() method for better Unicode support
            if let Err(_) = self.enigo.text(&ch.to_string()) {
                return Err(KeyboardError::TypingFailed(format!(
                    "Failed to type character: {}",
                    ch
                )));
            }

            // Add delay between characters (except for the last one)
            if i < char_count - 1 {
                thread::sleep(Duration::from_millis(self.typing_delay_ms));
            }

            // Log progress every 10 characters
            if (i + 1) % 10 == 0 {
                debug!(
                    event = "keyboard_typing_progress",
                    chars_typed = i + 1,
                    total_chars = char_count
                );
            }
        }

        info!(
            event = "keyboard_typing_complete",
            chars_typed = char_count
        );

        Ok(())
    }

    /// Type text with line breaks
    ///
    /// # Arguments
    /// * `lines` - Vector of text lines to type
    pub fn type_lines(&mut self, lines: &[String]) -> Result<(), KeyboardError> {
        if lines.is_empty() {
            return Err(KeyboardError::EmptyText);
        }

        for (i, line) in lines.iter().enumerate() {
            self.type_text(line)?;

            // Press Enter after each line except the last
            if i < lines.len() - 1 {
                self.enigo
                    .key(Key::Return, Direction::Click)
                    .map_err(|_| KeyboardError::TypingFailed("Failed to press Return key".to_string()))?;
                thread::sleep(Duration::from_millis(self.typing_delay_ms));
            }
        }

        Ok(())
    }

    /// Set typing delay
    pub fn set_typing_delay(&mut self, delay_ms: u64) {
        self.typing_delay_ms = delay_ms;
    }

    /// Get current typing delay
    pub fn typing_delay(&self) -> u64 {
        self.typing_delay_ms
    }
}

impl Default for KeyboardInjector {
    fn default() -> Self {
        Self::new(None).expect("Failed to initialize default KeyboardInjector")
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    // Note: enigo requires an active X11/Wayland/Windows display server to initialize.
    // All tests requiring enigo are marked #[ignore] to allow headless testing.

    #[test]
    #[ignore]
    fn test_keyboard_injector_creation() {
        let injector = KeyboardInjector::new(Some(10));
        assert!(injector.is_ok());

        let injector = injector.unwrap();
        assert_eq!(injector.typing_delay(), 10);
    }

    #[test]
    #[ignore]
    fn test_empty_text_error() {
        let mut injector = KeyboardInjector::new(None).unwrap();
        let result = injector.type_text("");
        assert!(result.is_err());
        assert!(matches!(result.unwrap_err(), KeyboardError::EmptyText));
    }

    #[test]
    #[ignore]
    fn test_set_typing_delay() {
        let mut injector = KeyboardInjector::new(Some(5)).unwrap();
        assert_eq!(injector.typing_delay(), 5);

        injector.set_typing_delay(20);
        assert_eq!(injector.typing_delay(), 20);
    }

    // Note: The following test requires an active X11/Wayland session
    // and a text editor to receive input. It's marked as #[ignore]
    // to prevent CI failures.
    #[test]
    #[ignore]
    fn test_type_text_integration() {
        let mut injector = KeyboardInjector::new(Some(50)).unwrap();

        // Wait for user to focus a text editor
        println!("Please focus a text editor within 3 seconds...");
        thread::sleep(Duration::from_secs(3));

        let result = injector.type_text("Hello, World!");
        assert!(result.is_ok());
    }

    #[test]
    #[ignore]
    fn test_type_unicode() {
        let mut injector = KeyboardInjector::new(Some(50)).unwrap();

        println!("Please focus a text editor within 3 seconds...");
        thread::sleep(Duration::from_secs(3));

        let result = injector.type_text("你好世界 🚀");
        assert!(result.is_ok());
    }
}
