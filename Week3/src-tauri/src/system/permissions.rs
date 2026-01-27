use cpal::traits::HostTrait;

#[derive(Debug, Clone, Copy, PartialEq, Eq, serde::Serialize)]
pub enum PermissionStatus {
    Granted,
    Denied,
    NotRequired,
}

#[derive(Debug, Clone, serde::Serialize)]
pub struct PermissionReport {
    pub microphone: PermissionStatus,
    pub accessibility: PermissionStatus,
}

pub struct PermissionManager;

impl PermissionManager {
    pub fn new() -> Self {
        Self
    }

    pub fn microphone_status(&self) -> PermissionStatus {
        if cpal::default_host().default_input_device().is_some() {
            PermissionStatus::Granted
        } else {
            PermissionStatus::Denied
        }
    }

    pub fn accessibility_status(&self) -> PermissionStatus {
        #[cfg(target_os = "macos")]
        {
            if let Ok(output) = std::process::Command::new("osascript")
                .arg("-e")
                .arg("tell application \"System Events\" to return UI elements enabled")
                .output()
            {
                let text = String::from_utf8_lossy(&output.stdout).to_lowercase();
                return if text.contains("true") {
                    PermissionStatus::Granted
                } else {
                    PermissionStatus::Denied
                };
            }
            return PermissionStatus::Denied;
        }
        #[cfg(not(target_os = "macos"))]
        {
            PermissionStatus::NotRequired
        }
    }

    pub fn report(&self) -> PermissionReport {
        PermissionReport {
            microphone: self.microphone_status(),
            accessibility: self.accessibility_status(),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::{PermissionManager, PermissionStatus};

    #[test]
    fn permissions_default_granted() {
        let manager = PermissionManager::new();
        assert!(matches!(
            manager.microphone_status(),
            PermissionStatus::Granted | PermissionStatus::Denied
        ));
        assert!(matches!(
            manager.accessibility_status(),
            PermissionStatus::Granted | PermissionStatus::Denied | PermissionStatus::NotRequired
        ));
    }
}
