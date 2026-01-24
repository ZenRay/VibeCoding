// ScribeFlow - Desktop Real-time Voice Transcription System
// Copyright (c) 2026 ScribeFlow Team

// Module declarations
pub mod audio;
pub mod network;
pub mod input;
pub mod system;
pub mod ui;
pub mod config;
pub mod utils;

// Temporary greet command for initial testing
#[tauri::command]
fn greet(name: &str) -> String {
    format!("Hello, {}! ScribeFlow is initializing...", name)
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .plugin(tauri_plugin_global_shortcut::Builder::new().build())
        .plugin(tauri_plugin_clipboard_manager::init())
        .plugin(tauri_plugin_store::Builder::new().build())
        .invoke_handler(tauri::generate_handler![greet])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
