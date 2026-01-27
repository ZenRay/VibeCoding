#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum PermissionStatus {
    Granted,
    Denied,
    NotRequired,
}

pub struct PermissionManager;

impl PermissionManager {
    pub fn new() -> Self {
        Self
    }

    pub fn microphone_status(&self) -> PermissionStatus {
        PermissionStatus::Granted
    }

    pub fn accessibility_status(&self) -> PermissionStatus {
        PermissionStatus::Granted
    }
}

#[cfg(test)]
mod tests {
    use super::{PermissionManager, PermissionStatus};

    #[test]
    fn permissions_default_granted() {
        let manager = PermissionManager::new();
        assert_eq!(manager.microphone_status(), PermissionStatus::Granted);
        assert_eq!(manager.accessibility_status(), PermissionStatus::Granted);
    }
}
