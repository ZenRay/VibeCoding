#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use tauri::{AppHandle, Emitter, Manager, State, WindowEvent};
use tauri_plugin_global_shortcut::{GlobalShortcutExt, Shortcut};
use serde_json::json;
use tauri_app_lib::config::AppConfig;
use tauri_app_lib::config::store::load_config;
use tauri_app_lib::ui::commands::{
    check_connectivity as check_connectivity_impl,
    check_permissions as check_permissions_impl,
    get_hotkey_status as get_hotkey_status_impl,
    get_config as get_config_impl,
    save_config as save_config_impl,
    start_transcription as start_transcription_impl,
    stop_transcription as stop_transcription_impl,
    toggle_transcription as toggle_transcription_impl,
    AppState,
};
use tauri_app_lib::ui::tray::setup_tray;
use tauri_app_lib::utils::logger::init_logger;

#[tauri::command]
async fn start_transcription(
    app_handle: AppHandle,
    state: State<'_, AppState>,
) -> Result<(), String> {
    start_transcription_impl(app_handle, state.inner()).await
}

#[tauri::command]
async fn stop_transcription(
    app_handle: AppHandle,
    state: State<'_, AppState>,
) -> Result<(), String> {
    stop_transcription_impl(app_handle, state.inner()).await
}

#[tauri::command]
async fn get_config_cmd(
    app_handle: AppHandle,
    state: State<'_, AppState>,
) -> Result<AppConfig, String> {
    Ok(get_config_impl(&app_handle, state.inner()).await)
}

#[tauri::command]
async fn save_config_cmd(
    app_handle: AppHandle,
    state: State<'_, AppState>,
    config: AppConfig,
) -> Result<(), String> {
    save_config_impl(&app_handle, state.inner(), config).await
}

#[tauri::command]
async fn check_connectivity_cmd(app_handle: AppHandle) -> Result<(), String> {
    check_connectivity_impl(app_handle).await
}

#[tauri::command]
async fn check_permissions_cmd(app_handle: AppHandle) -> Result<tauri_app_lib::system::permissions::PermissionReport, String> {
    check_permissions_impl(app_handle).await
}

#[tauri::command]
async fn get_hotkey_status_cmd(app_handle: AppHandle) -> Result<tauri_app_lib::ui::commands::HotkeyStatus, String> {
    get_hotkey_status_impl(app_handle).await
}

fn main() {
    let _ = rustls::crypto::aws_lc_rs::default_provider().install_default();
    init_logger();
    let app_state = AppState::new();
    if let Err(err) = tauri::Builder::default()
        .manage(app_state)
        .plugin(tauri_plugin_store::Builder::default().build())
        .plugin(tauri_plugin_clipboard_manager::init())
        .plugin(tauri_plugin_global_shortcut::Builder::default().build())
        .setup(|app| {
            setup_tray(app)?;
            let app_handle = app.handle();
            let config = load_config(&app_handle);
            let shortcut: Shortcut = config
                .hotkey
                .parse()
                .map_err(|err| format!("Invalid hotkey: {err}"))?;
            app_handle
                .global_shortcut()
                .on_shortcut(shortcut, move |handle, _shortcut, _event| {
                    let app_handle = handle.clone();
                    tauri::async_runtime::spawn(async move {
                        let state = app_handle.state::<AppState>();
                        let _ =
                            toggle_transcription_impl(app_handle.clone(), state.inner()).await;
                    });
                })
                .map_err(|err| err.to_string())?;
            let is_wayland = std::env::var("XDG_SESSION_TYPE")
                .map(|value| value.eq_ignore_ascii_case("wayland"))
                .unwrap_or(false)
                || std::env::var("WAYLAND_DISPLAY").is_ok();
            if is_wayland {
                let _ = app.emit(
                    "hotkey_status",
                    json!({
                        "supported": false,
                        "reason": "Wayland does not support global shortcuts"
                    }),
                );
            } else {
                let _ = app.emit("hotkey_status", json!({ "supported": true }));
            }
            if let Some(window) = app.get_webview_window("main") {
                let _ = window.hide();
            }
            Ok(())
        })
        .on_window_event(|window, event| {
            if let WindowEvent::CloseRequested { api, .. } = event {
                let _ = window.hide();
                api.prevent_close();
            }
        })
        .invoke_handler(tauri::generate_handler![
            start_transcription,
            stop_transcription,
            get_config_cmd,
            save_config_cmd,
            check_connectivity_cmd,
            check_permissions_cmd,
            get_hotkey_status_cmd
        ])
        .run(tauri::generate_context!())
    {
        eprintln!("error while running tauri application: {err}");
    }
}
