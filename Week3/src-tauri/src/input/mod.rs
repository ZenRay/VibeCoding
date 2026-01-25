// Input module - Text injection system
//
// This module provides text injection capabilities through:
// - Keyboard simulation (character-by-character typing)
// - Clipboard-based paste (for longer text)
// - Intelligent strategy selection based on context

pub mod clipboard;
pub mod injector;
pub mod keyboard;

// Re-exports for convenience
pub use clipboard::{ClipboardError, ClipboardInjector, ClipboardManager, TauriClipboardManager};
pub use injector::{InjectionError, InjectionMethod, InjectionStrategy, TextInjector};
pub use keyboard::{KeyboardError, KeyboardInjector};
