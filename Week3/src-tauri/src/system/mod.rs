// System integration module
//
// Provides system-level functionality:
// - Global hotkey registration and management
// - macOS Accessibility and microphone permission checking
// - Platform-specific system integration

pub mod hotkey;
pub mod permissions;

// Re-exports for convenience
pub use hotkey::{HotkeyConfig, HotkeyError, HotkeyManager};
pub use permissions::{AppPermissions, PermissionError, PermissionManager, PermissionStatus, PermissionType};
