use std::thread::sleep;
use std::time::Duration;
use std::io::Write;
use std::process::{Command, Stdio};

use enigo::{Direction, Enigo, Key, Keyboard, Settings};
use tauri::{AppHandle, Emitter};
use tauri_plugin_clipboard_manager::ClipboardExt;

use crate::input::error::InputError;

pub struct ClipboardInjector;

impl ClipboardInjector {
    pub fn new() -> Self {
        Self
    }

    pub fn inject_text(&self, app_handle: &AppHandle, text: &str) -> Result<(), InputError> {
        if text.trim().is_empty() {
            return Err(InputError::EmptyText);
        }
        let clipboard = app_handle.clipboard();
        if is_wayland() {
            if !try_wl_copy(text) {
                return Err(InputError::ClipboardWriteFailed(
                    "Wayland clipboard copy failed (wl-copy unavailable or failed)".to_string(),
                ));
            }
            let _ = app_handle.emit(
                "notification",
                serde_json::json!({
                    "message": "Text copied to clipboard. Paste manually (Ctrl+V). Clipboard not restored on Wayland."
                }),
            );
            return Ok(());
        }
        let previous = clipboard
            .read_text()
            .map_err(|e| InputError::ClipboardReadFailed(e.to_string()))?;
        clipboard
            .write_text(text.to_string())
            .map_err(|e| InputError::ClipboardWriteFailed(e.to_string()))?;
        sleep(Duration::from_millis(20));
        let mut enigo =
            Enigo::new(&Settings::default()).map_err(|e| InputError::Backend(e.to_string()))?;
        paste_with_enigo(&mut enigo);
        sleep(Duration::from_millis(20));
        let _ = clipboard.write_text(previous);
        Ok(())
    }
}

fn paste_with_enigo(enigo: &mut Enigo) {
    #[cfg(target_os = "macos")]
    {
        let _ = enigo.key(Key::Meta, Direction::Press);
        let _ = enigo.key(Key::Unicode('v'), Direction::Click);
        let _ = enigo.key(Key::Meta, Direction::Release);
    }
    #[cfg(not(target_os = "macos"))]
    {
        let _ = enigo.key(Key::Control, Direction::Press);
        let _ = enigo.key(Key::Unicode('v'), Direction::Click);
        let _ = enigo.key(Key::Control, Direction::Release);
    }
}

fn try_wl_copy(text: &str) -> bool {
    let mut child = match Command::new("wl-copy")
        .stdin(Stdio::piped())
        .spawn()
    {
        Ok(child) => child,
        Err(_) => return false,
    };
    if let Some(mut stdin) = child.stdin.take() {
        if stdin.write_all(text.as_bytes()).is_err() {
            return false;
        }
    }
    child.wait().is_ok()
}

fn is_wayland() -> bool {
    std::env::var("XDG_SESSION_TYPE")
        .map(|value| value.eq_ignore_ascii_case("wayland"))
        .unwrap_or(false)
        || std::env::var("WAYLAND_DISPLAY").is_ok()
}
