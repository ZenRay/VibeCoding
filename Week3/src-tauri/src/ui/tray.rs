use tauri::{Emitter, Manager};
use tauri::menu::{Menu, MenuItem, PredefinedMenuItem};
use tauri::tray::TrayIconBuilder;

const MENU_SETTINGS_ID: &str = "tray_settings";
const MENU_ABOUT_ID: &str = "tray_about";
const MENU_TOGGLE_ID: &str = "tray_toggle";
const MENU_COPY_ID: &str = "tray_copy";
const MENU_QUIT_ID: &str = "tray_quit";

pub fn setup_tray(app: &tauri::App) -> Result<(), String> {
    let settings = MenuItem::with_id(app, MENU_SETTINGS_ID, "Settings", true, None::<&str>)
        .map_err(|e| e.to_string())?;
    let about = MenuItem::with_id(app, MENU_ABOUT_ID, "About", true, None::<&str>)
        .map_err(|e| e.to_string())?;
    let toggle = MenuItem::with_id(app, MENU_TOGGLE_ID, "Start", true, None::<&str>)
        .map_err(|e| e.to_string())?;
    let copy = MenuItem::with_id(app, MENU_COPY_ID, "Copy Last Transcript", true, None::<&str>)
        .map_err(|e| e.to_string())?;
    let quit = MenuItem::with_id(app, MENU_QUIT_ID, "Quit", true, None::<&str>)
        .map_err(|e| e.to_string())?;
    let separator = PredefinedMenuItem::separator(app).map_err(|e| e.to_string())?;
    let menu = Menu::with_items(app, &[&toggle, &copy, &settings, &about, &separator, &quit])
        .map_err(|e| e.to_string())?;

    let icon = app
        .default_window_icon()
        .cloned()
        .unwrap_or_else(|| tauri::image::Image::new(&[0, 0, 0, 0], 1, 1));
    let app_handle = app.handle();
    TrayIconBuilder::new()
        .icon(icon)
        .menu(&menu)
        .on_menu_event(move |handle, event| {
            let id = event.id().as_ref();
            match id {
                MENU_TOGGLE_ID => {
                    let handle = handle.clone();
                    let toggle = toggle.clone();
                    tauri::async_runtime::spawn(async move {
                        let state = handle.state::<crate::ui::commands::AppState>();
                        let _ = crate::ui::commands::toggle_transcription(handle.clone(), state.inner()).await;
                        let is_recording = state.is_recording().await;
                        let label = if is_recording { "Stop" } else { "Start" };
                        let _ = toggle.set_text(label);
                    });
                }
                MENU_COPY_ID => {
                    let handle = handle.clone();
                    tauri::async_runtime::spawn(async move {
                        let state = handle.state::<crate::ui::commands::AppState>();
                        let _ = crate::ui::commands::copy_last_transcript(&handle, state.inner()).await;
                    });
                }
                MENU_SETTINGS_ID => {
                    let _ = handle.emit("open_settings", serde_json::json!({}));
                    if let Some(window) = handle.get_webview_window("main") {
                        let _ = window.show();
                        let _ = window.set_focus();
                    }
                }
                MENU_ABOUT_ID => {
                    let _ = handle.emit("open_about", serde_json::json!({}));
                    if let Some(window) = handle.get_webview_window("main") {
                        let _ = window.show();
                        let _ = window.set_focus();
                    }
                }
                MENU_QUIT_ID => {
                    handle.exit(0);
                }
                _ => {}
            }
        })
        .build(app_handle)
        .map_err(|e| e.to_string())?;

    Ok(())
}
