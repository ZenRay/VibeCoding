#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use tauri::{AppHandle, State};
use tauri_app_lib::config::AppConfig;
use tauri_app_lib::ui::commands::{
    get_config as get_config_impl,
    save_config as save_config_impl,
    start_transcription as start_transcription_impl,
    stop_transcription as stop_transcription_impl,
    AppState,
};
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
async fn get_config_cmd(state: State<'_, AppState>) -> Result<AppConfig, String> {
    Ok(get_config_impl(state.inner()).await)
}

#[tauri::command]
async fn save_config_cmd(state: State<'_, AppState>, config: AppConfig) -> Result<(), String> {
    save_config_impl(state.inner(), config).await
}

fn main() {
    init_logger();
    let app_state = AppState::new();
    if let Err(err) = tauri::Builder::default()
        .manage(app_state)
        .setup(|app| {
            let icon = tauri::image::Image::new(&[0, 0, 0, 0], 1, 1);
            let _ = tauri::tray::TrayIconBuilder::new()
                .icon(icon)
                .build(app);
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            start_transcription,
            stop_transcription,
            get_config_cmd,
            save_config_cmd
        ])
        .run(tauri::generate_context!())
    {
        eprintln!("error while running tauri application: {err}");
    }
}
