use active_win_pos_rs::{get_active_window, ActiveWindow};
use tauri::{AppHandle, Emitter};
#[cfg(target_os = "macos")]
use std::process::Command;

use crate::input::clipboard::ClipboardInjector;
use crate::input::error::InputError;
use crate::input::keyboard::KeyboardInjector;

const CLIPBOARD_THRESHOLD: usize = 120;

pub struct TextInjector {
    keyboard: KeyboardInjector,
    clipboard: ClipboardInjector,
}

impl TextInjector {
    pub fn new() -> Self {
        Self {
            keyboard: KeyboardInjector::new(),
            clipboard: ClipboardInjector::new(),
        }
    }

    pub fn inject(&self, app_handle: &AppHandle, text: &str) -> Result<(), InputError> {
        if text.trim().is_empty() {
            return Err(InputError::EmptyText);
        }
        if !has_display() {
            return Err(InputError::InjectionBlocked(
                "display not available for injection".to_string(),
            ));
        }
        if is_wayland() {
            return self.clipboard.inject_text(app_handle, text);
        }
        if let Ok(window) = get_active_window() {
            if let Some(reason) = should_block_injection(&window) {
                return Err(InputError::InjectionBlocked(reason));
            }
        } else {
            let _ = app_handle.emit(
                "notification",
                serde_json::json!({
                    "message": "Active window not detected; inserting into current focus"
                }),
            );
        }
        if text.chars().count() >= CLIPBOARD_THRESHOLD {
            self.clipboard.inject_text(app_handle, text)
        } else {
            self.keyboard.inject_text(text)
        }
    }
}

fn has_display() -> bool {
    std::env::var("DISPLAY").is_ok() || std::env::var("WAYLAND_DISPLAY").is_ok()
}

fn is_wayland() -> bool {
    std::env::var("XDG_SESSION_TYPE")
        .map(|value| value.eq_ignore_ascii_case("wayland"))
        .unwrap_or(false)
        || std::env::var("WAYLAND_DISPLAY").is_ok()
}

fn should_block_injection(window: &ActiveWindow) -> Option<String> {
    let title = window.title.to_lowercase();
    let app = window.app_name.to_lowercase();
    let sensitive_keywords = [
        "password",
        "passcode",
        "pin",
        "密碼",
        "密码",
        "senha",
        "пароль",
        "암호",
    ];
    let sensitive_apps = ["1password", "bitwarden", "keepass", "lastpass"];
    if sensitive_keywords.iter().any(|keyword| title.contains(keyword)) {
        return Some(format!("sensitive window title: {}", window.title));
    }
    if sensitive_apps.iter().any(|keyword| app.contains(keyword)) {
        return Some(format!("sensitive app: {}", window.app_name));
    }
    #[cfg(target_os = "macos")]
    if let Some((role, subrole)) = macos_focused_element_info() {
        if subrole.eq_ignore_ascii_case("AXSecureTextField") {
            return Some("secure text field focused".to_string());
        }
        let allowed_roles = ["AXTextField", "AXTextArea", "AXSearchField"];
        if !allowed_roles.iter().any(|item| role.eq_ignore_ascii_case(item)) {
            return Some(format!("non-editable focus: {role}"));
        }
    }
    None
}

#[cfg(target_os = "macos")]
fn macos_focused_element_info() -> Option<(String, String)> {
    let script = r#"
        tell application "System Events"
            tell (first application process whose frontmost is true)
                set focusedElement to value of attribute "AXFocusedUIElement"
                if focusedElement is missing value then return ""
                set theRole to role of focusedElement
                set theSubrole to subrole of focusedElement
                return theRole & "|" & theSubrole
            end tell
        end tell
    "#;
    let output = Command::new("osascript")
        .arg("-e")
        .arg(script)
        .output()
        .ok()?;
    if !output.status.success() {
        return None;
    }
    let text = String::from_utf8_lossy(&output.stdout).trim().to_string();
    if text.is_empty() {
        return None;
    }
    let mut parts = text.splitn(2, '|');
    let role = parts.next()?.trim().to_string();
    let subrole = parts.next().unwrap_or("").trim().to_string();
    Some((role, subrole))
}

