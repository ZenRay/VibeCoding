use tauri::{Emitter, Manager};
use tauri::menu::{Menu, MenuItem, PredefinedMenuItem};
use tauri::tray::TrayIconBuilder;

const MENU_SETTINGS_ID: &str = "tray_settings";
const MENU_ABOUT_ID: &str = "tray_about";
const MENU_QUIT_ID: &str = "tray_quit";

pub fn setup_tray(app: &tauri::App) -> Result<(), String> {
    let settings = MenuItem::with_id(app, MENU_SETTINGS_ID, "Settings", true, None::<&str>)
        .map_err(|e| e.to_string())?;
    let about = MenuItem::with_id(app, MENU_ABOUT_ID, "About", true, None::<&str>)
        .map_err(|e| e.to_string())?;
    let quit = MenuItem::with_id(app, MENU_QUIT_ID, "Quit", true, None::<&str>)
        .map_err(|e| e.to_string())?;
    let separator = PredefinedMenuItem::separator(app).map_err(|e| e.to_string())?;
    let menu = Menu::with_items(app, &[&settings, &about, &separator, &quit])
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
                MENU_SETTINGS_ID => {
                    let _ = handle.emit("open_settings", serde_json::json!({}));
                    if let Some(window) = handle.get_webview_window("main") {
                        let _ = window.show();
                        let _ = window.set_focus();
                    }
                }
                MENU_ABOUT_ID => {
                    let _ = handle.emit("open_about", serde_json::json!({}));
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
