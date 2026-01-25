// System permissions management module
//
// Provides permission checking and user guidance for:
// - macOS Accessibility API (required for keyboard injection and active window detection)
// - Microphone access (required for audio capture)
// - Cross-platform support with graceful degradation

use thiserror::Error;
use tracing::{error, info, warn};

/// Permission-related errors
#[derive(Debug, Error)]
pub enum PermissionError {
    #[error("Permission check failed: {0}")]
    CheckFailed(String),

    #[error("Permission denied: {0}")]
    Denied(String),

    #[error("Platform not supported: {0}")]
    PlatformNotSupported(String),
}

/// Permission status
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum PermissionStatus {
    /// Permission granted
    Granted,

    /// Permission denied
    Denied,

    /// Permission not determined (user hasn't been asked yet)
    NotDetermined,

    /// Platform doesn't require this permission
    NotRequired,

    /// Unable to determine permission status
    Unknown,
}

/// All required permissions
#[derive(Debug, Clone)]
pub struct AppPermissions {
    /// Accessibility permission (macOS only)
    pub accessibility: PermissionStatus,

    /// Microphone permission
    pub microphone: PermissionStatus,
}

/// Permission manager for checking and requesting permissions
pub struct PermissionManager {
    current_permissions: AppPermissions,
}

impl PermissionManager {
    /// Create a new permission manager
    pub fn new() -> Self {
        Self {
            current_permissions: AppPermissions {
                accessibility: PermissionStatus::Unknown,
                microphone: PermissionStatus::Unknown,
            },
        }
    }

    /// Check all required permissions
    ///
    /// # Returns
    /// * `Ok(AppPermissions)` with current status of all permissions
    /// * `Err(PermissionError)` if checking fails
    pub fn check_all_permissions(&mut self) -> Result<AppPermissions, PermissionError> {
        info!(event = "permissions_check_start");

        // Check accessibility permission (macOS only)
        self.current_permissions.accessibility = self.check_accessibility_permission()?;

        // Check microphone permission
        self.current_permissions.microphone = self.check_microphone_permission()?;

        info!(
            event = "permissions_checked",
            accessibility = ?self.current_permissions.accessibility,
            microphone = ?self.current_permissions.microphone
        );

        Ok(self.current_permissions.clone())
    }

    /// Check macOS Accessibility permission
    ///
    /// This permission is required for:
    /// - Keyboard simulation (text injection)
    /// - Active window detection
    /// - Focus element detection (password field blocking)
    ///
    /// # Platform Support
    /// - macOS: Required (uses Accessibility API)
    /// - Linux: Not required (X11/Wayland security model differs)
    /// - Windows: Not required
    fn check_accessibility_permission(&self) -> Result<PermissionStatus, PermissionError> {
        #[cfg(target_os = "macos")]
        {
            info!(event = "accessibility_check_start", platform = "macos");

            // TODO: Implement using macOS Accessibility API
            // Example code for reference (requires cocoa/core-foundation crates):
            //
            // use core_foundation::base::TCFType;
            // use core_foundation::dictionary::CFDictionary;
            // use core_graphics::access::AXIsProcessTrusted;
            //
            // let trusted = unsafe { AXIsProcessTrusted() };
            //
            // if trusted {
            //     Ok(PermissionStatus::Granted)
            // } else {
            //     Ok(PermissionStatus::Denied)
            // }

            // Placeholder: Return NotDetermined to trigger guidance
            warn!(
                event = "accessibility_check_placeholder",
                message = "Using placeholder implementation"
            );

            Ok(PermissionStatus::NotDetermined)
        }

        #[cfg(not(target_os = "macos"))]
        {
            info!(
                event = "accessibility_not_required",
                platform = std::env::consts::OS
            );
            Ok(PermissionStatus::NotRequired)
        }
    }

    /// Check microphone permission
    ///
    /// This permission is required for audio capture.
    ///
    /// # Platform Support
    /// - macOS: Required (uses AVFoundation permission check)
    /// - Linux: Not required (ALSA/PulseAudio don't have permission system)
    /// - Windows: Not required (WASAPI doesn't have permission system)
    fn check_microphone_permission(&self) -> Result<PermissionStatus, PermissionError> {
        #[cfg(target_os = "macos")]
        {
            info!(event = "microphone_check_start", platform = "macos");

            // TODO: Implement using macOS AVFoundation
            // Example code for reference (requires cocoa crate):
            //
            // use cocoa::foundation::NSString;
            // use objc::runtime::{Class, Object};
            // use objc::{class, msg_send, sel, sel_impl};
            //
            // let av_capture_device_class = class!(AVCaptureDevice);
            // let media_type_audio = NSString::alloc(nil).init_str("vide");
            // let status: i64 = unsafe {
            //     msg_send![av_capture_device_class,
            //         authorizationStatusForMediaType: media_type_audio]
            // };
            //
            // match status {
            //     3 => Ok(PermissionStatus::Granted),     // AVAuthorizationStatusAuthorized
            //     2 => Ok(PermissionStatus::Denied),      // AVAuthorizationStatusDenied
            //     0 => Ok(PermissionStatus::NotDetermined), // AVAuthorizationStatusNotDetermined
            //     _ => Ok(PermissionStatus::Unknown),
            // }

            // Placeholder: Return NotDetermined to trigger guidance
            warn!(
                event = "microphone_check_placeholder",
                message = "Using placeholder implementation"
            );

            Ok(PermissionStatus::NotDetermined)
        }

        #[cfg(not(target_os = "macos"))]
        {
            info!(
                event = "microphone_not_required",
                platform = std::env::consts::OS
            );
            Ok(PermissionStatus::NotRequired)
        }
    }

    /// Check if all required permissions are granted
    ///
    /// # Returns
    /// * `true` if all required permissions are granted or not required
    /// * `false` if any required permission is denied or not determined
    pub fn all_permissions_granted(&self) -> bool {
        let accessibility_ok = matches!(
            self.current_permissions.accessibility,
            PermissionStatus::Granted | PermissionStatus::NotRequired
        );

        let microphone_ok = matches!(
            self.current_permissions.microphone,
            PermissionStatus::Granted | PermissionStatus::NotRequired
        );

        accessibility_ok && microphone_ok
    }

    /// Get list of missing permissions that need to be granted
    ///
    /// # Returns
    /// * Vector of permission names that are denied or not determined
    pub fn get_missing_permissions(&self) -> Vec<String> {
        let mut missing = Vec::new();

        if matches!(
            self.current_permissions.accessibility,
            PermissionStatus::Denied | PermissionStatus::NotDetermined
        ) {
            missing.push("Accessibility".to_string());
        }

        if matches!(
            self.current_permissions.microphone,
            PermissionStatus::Denied | PermissionStatus::NotDetermined
        ) {
            missing.push("Microphone".to_string());
        }

        missing
    }

    /// Get current permissions
    pub fn current_permissions(&self) -> &AppPermissions {
        &self.current_permissions
    }

    /// Generate user guidance message for missing permissions
    ///
    /// # Returns
    /// * Markdown-formatted guidance text with platform-specific instructions
    pub fn generate_guidance_message(&self) -> String {
        let missing = self.get_missing_permissions();

        if missing.is_empty() {
            return "All permissions granted. You're ready to use ScribeFlow!".to_string();
        }

        let mut message = String::from("# Permissions Required\n\n");
        message.push_str("ScribeFlow needs the following permissions to function:\n\n");

        #[cfg(target_os = "macos")]
        {
            if matches!(
                self.current_permissions.accessibility,
                PermissionStatus::Denied | PermissionStatus::NotDetermined
            ) {
                message.push_str("## Accessibility Permission\n\n");
                message.push_str("Required for keyboard text injection and active window detection.\n\n");
                message.push_str("**How to grant:**\n");
                message.push_str("1. Open System Settings > Privacy & Security > Accessibility\n");
                message.push_str("2. Find 'ScribeFlow' in the list\n");
                message.push_str("3. Toggle the switch to enable\n");
                message.push_str("4. Restart ScribeFlow\n\n");
            }

            if matches!(
                self.current_permissions.microphone,
                PermissionStatus::Denied | PermissionStatus::NotDetermined
            ) {
                message.push_str("## Microphone Permission\n\n");
                message.push_str("Required for voice input capture.\n\n");
                message.push_str("**How to grant:**\n");
                message.push_str("1. Open System Settings > Privacy & Security > Microphone\n");
                message.push_str("2. Find 'ScribeFlow' in the list\n");
                message.push_str("3. Toggle the switch to enable\n");
                message.push_str("4. Restart ScribeFlow\n\n");
            }
        }

        #[cfg(target_os = "linux")]
        {
            message.push_str("## Linux Platform Notes\n\n");
            message.push_str("- **Microphone**: Ensure your user has access to audio devices\n");
            message.push_str("  - Check: `groups | grep audio`\n");
            message.push_str("  - Add to audio group: `sudo usermod -aG audio $USER`\n");
            message.push_str("- **X11**: Keyboard injection requires X11 session (Wayland support limited)\n\n");
        }

        message.push_str("---\n\n");
        message.push_str("After granting permissions, please restart ScribeFlow.");

        message
    }

    /// Open system preferences to the relevant permission page
    ///
    /// # Arguments
    /// * `permission_type` - Type of permission to open settings for
    ///
    /// # Platform Support
    /// - macOS: Opens System Settings to specific privacy pane
    /// - Linux: Not implemented (opens general settings)
    /// - Windows: Not implemented
    pub fn open_permission_settings(
        &self,
        _permission_type: PermissionType,
    ) -> Result<(), PermissionError> {
        #[cfg(target_os = "macos")]
        {
            let url = match permission_type {
                PermissionType::Accessibility => {
                    "x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility"
                }
                PermissionType::Microphone => {
                    "x-apple.systempreferences:com.apple.preference.security?Privacy_Microphone"
                }
            };

            info!(
                event = "opening_system_settings",
                permission_type = ?permission_type,
                url = url
            );

            // TODO: Implement using Tauri shell plugin
            // Example:
            // use tauri::api::shell;
            // shell::open(&app_handle, url, None)
            //     .map_err(|e| PermissionError::CheckFailed(e.to_string()))?;

            Ok(())
        }

        #[cfg(not(target_os = "macos"))]
        {
            warn!(
                event = "open_settings_not_supported",
                platform = std::env::consts::OS
            );
            Err(PermissionError::PlatformNotSupported(
                "Opening system settings is only supported on macOS".to_string(),
            ))
        }
    }
}

impl Default for PermissionManager {
    fn default() -> Self {
        Self::new()
    }
}

/// Permission types
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum PermissionType {
    /// Accessibility permission
    Accessibility,

    /// Microphone permission
    Microphone,
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_permission_manager_creation() {
        let manager = PermissionManager::new();
        assert_eq!(manager.current_permissions.accessibility, PermissionStatus::Unknown);
        assert_eq!(manager.current_permissions.microphone, PermissionStatus::Unknown);
    }

    #[test]
    fn test_permission_status_equality() {
        assert_eq!(PermissionStatus::Granted, PermissionStatus::Granted);
        assert_ne!(PermissionStatus::Granted, PermissionStatus::Denied);
    }

    #[test]
    fn test_all_permissions_granted_when_unknown() {
        let manager = PermissionManager::new();
        assert!(!manager.all_permissions_granted());
    }

    #[test]
    fn test_get_missing_permissions() {
        let mut manager = PermissionManager::new();
        manager.current_permissions.accessibility = PermissionStatus::Denied;
        manager.current_permissions.microphone = PermissionStatus::NotDetermined;

        let missing = manager.get_missing_permissions();
        assert_eq!(missing.len(), 2);
        assert!(missing.contains(&"Accessibility".to_string()));
        assert!(missing.contains(&"Microphone".to_string()));
    }

    #[test]
    fn test_no_missing_permissions_when_granted() {
        let mut manager = PermissionManager::new();
        manager.current_permissions.accessibility = PermissionStatus::Granted;
        manager.current_permissions.microphone = PermissionStatus::Granted;

        let missing = manager.get_missing_permissions();
        assert_eq!(missing.len(), 0);
    }

    #[test]
    fn test_no_missing_permissions_when_not_required() {
        let mut manager = PermissionManager::new();
        manager.current_permissions.accessibility = PermissionStatus::NotRequired;
        manager.current_permissions.microphone = PermissionStatus::NotRequired;

        let missing = manager.get_missing_permissions();
        assert_eq!(missing.len(), 0);
        assert!(manager.all_permissions_granted());
    }

    #[test]
    fn test_guidance_message_generation() {
        let mut manager = PermissionManager::new();
        manager.current_permissions.accessibility = PermissionStatus::NotDetermined;
        manager.current_permissions.microphone = PermissionStatus::NotDetermined;

        let guidance = manager.generate_guidance_message();
        assert!(guidance.contains("Permissions Required"));
        assert!(guidance.len() > 100); // Should have substantial content
    }

    #[test]
    fn test_guidance_message_when_all_granted() {
        let mut manager = PermissionManager::new();
        manager.current_permissions.accessibility = PermissionStatus::Granted;
        manager.current_permissions.microphone = PermissionStatus::Granted;

        let guidance = manager.generate_guidance_message();
        assert!(guidance.contains("All permissions granted"));
    }

    #[test]
    fn test_permission_type_equality() {
        assert_eq!(PermissionType::Accessibility, PermissionType::Accessibility);
        assert_ne!(PermissionType::Accessibility, PermissionType::Microphone);
    }
}
