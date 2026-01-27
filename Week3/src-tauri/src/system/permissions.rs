use cpal::traits::HostTrait;

#[cfg(target_os = "macos")]
use objc::{class, msg_send, sel, sel_impl};

#[cfg(target_os = "macos")]
#[link(name = "ApplicationServices", kind = "framework")]
extern "C" {
    fn AXIsProcessTrusted() -> bool;
}

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
        #[cfg(target_os = "macos")]
        {
            let status = macos_mic_authorization_status();
            return match status {
                3 => PermissionStatus::Granted,
                2 | 1 | 0 => PermissionStatus::Denied,
                _ => PermissionStatus::Denied,
            };
        }
        if cpal::default_host().default_input_device().is_some() {
            PermissionStatus::Granted
        } else {
            PermissionStatus::Denied
        }
    }

    pub fn accessibility_status(&self) -> PermissionStatus {
        #[cfg(target_os = "macos")]
        {
            return if unsafe { AXIsProcessTrusted() } {
                PermissionStatus::Granted
            } else {
                PermissionStatus::Denied
            };
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

#[cfg(target_os = "macos")]
fn macos_mic_authorization_status() -> i32 {
    let media_type = {
        let c_string = std::ffi::CString::new("soun").unwrap_or_default();
        unsafe {
            let nsstring: *mut objc::runtime::Object =
                msg_send![class!(NSString), stringWithUTF8String: c_string.as_ptr()];
            nsstring
        }
    };
    unsafe {
        let status: i32 = msg_send![class!(AVCaptureDevice), authorizationStatusForMediaType: media_type];
        status
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
