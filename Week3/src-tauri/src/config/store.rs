use tauri::AppHandle;
use tauri_plugin_store::StoreExt;

use crate::config::AppConfig;

const STORE_NAME: &str = "config.json";
const KEYRING_SERVICE: &str = "io.scribeflow.api";
const KEYRING_USER: &str = "elevenlabs_api_key";

pub fn load_config(app: &AppHandle) -> AppConfig {
    let store = match app.store(STORE_NAME) {
        Ok(store) => store,
        Err(_) => return AppConfig::default(),
    };
    let value = store.get("app_config");
    let mut config = value
        .and_then(|v| serde_json::from_value(v).ok())
        .unwrap_or_else(AppConfig::default);
    if let Ok(Some(api_key)) = load_api_key() {
        config.api_key = Some(api_key);
    }
    config
}

pub fn save_config(app: &AppHandle, config: &AppConfig) -> Result<(), String> {
    let store = app
        .store(STORE_NAME)
        .map_err(|e| format!("Failed to open config store: {e}"))?;
    store.set(
        "app_config".to_string(),
        serde_json::json!({
            "api_key": null,
            "language": config.language.clone(),
            "hotkey": config.hotkey.clone()
        }),
    );
    store
        .save()
        .map_err(|e| format!("Failed to save config: {e}"))?;
    if let Some(api_key) = config.api_key.as_deref() {
        save_api_key(api_key)?;
    }
    Ok(())
}

pub fn save_api_key(api_key: &str) -> Result<(), String> {
    let entry = keyring::Entry::new(KEYRING_SERVICE, KEYRING_USER)
        .map_err(|e| format!("Keyring entry error: {e}"))?;
    entry
        .set_password(api_key)
        .map_err(|e| format!("Keyring save error: {e}"))?;
    Ok(())
}

pub fn load_api_key() -> Result<Option<String>, String> {
    let entry = keyring::Entry::new(KEYRING_SERVICE, KEYRING_USER)
        .map_err(|e| format!("Keyring entry error: {e}"))?;
    match entry.get_password() {
        Ok(value) => Ok(Some(value)),
        Err(keyring::Error::NoEntry) => Ok(None),
        Err(err) => Err(format!("Keyring load error: {err}")),
    }
}
