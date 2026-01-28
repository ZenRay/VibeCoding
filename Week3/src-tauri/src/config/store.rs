use tauri::{AppHandle, Manager};
use tauri_plugin_store::StoreExt;

use crate::config::{default_hotkey, AppConfig};
use aes_gcm::{Aes256Gcm, Nonce};
use aes_gcm::aead::{Aead, KeyInit};
use base64::Engine;
use rand::RngCore;
use sha2::{Digest, Sha256};

const STORE_NAME: &str = "config.json";
const KEYRING_SERVICE: &str = "io.scribeflow.api";
const KEYRING_USER: &str = "elevenlabs_api_key";
const FALLBACK_FILE: &str = "api_key.enc";

pub fn load_config(app: &AppHandle) -> AppConfig {
    let store = match app.store(STORE_NAME) {
        Ok(store) => store,
        Err(_) => return AppConfig::default(),
    };
    let value = store.get("app_config");
    let mut config = value
        .and_then(|v| serde_json::from_value(v).ok())
        .unwrap_or_else(AppConfig::default);
    if let Ok(Some(api_key)) = load_api_key(app) {
        config.api_key = Some(api_key);
    }
    if config.hotkey.trim().is_empty() {
        config.hotkey = default_hotkey();
    }
    if !cfg!(target_os = "macos") && config.hotkey == "Cmd+Shift+\\" {
        config.hotkey = default_hotkey();
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
            "hotkey": config.hotkey.clone(),
            "proxy_url": config.proxy_url.clone()
        }),
    );
    store
        .save()
        .map_err(|e| format!("Failed to save config: {e}"))?;
    if let Some(api_key) = config.api_key.as_deref() {
        save_api_key(app, api_key)?;
    } else {
        let _ = delete_fallback_key(app);
    }
    Ok(())
}

pub fn save_api_key(app: &AppHandle, api_key: &str) -> Result<(), String> {
    let entry = keyring::Entry::new(KEYRING_SERVICE, KEYRING_USER)
        .map_err(|e| format!("Keyring entry error: {e}"))?;
    match entry.set_password(api_key) {
        Ok(()) => Ok(()),
        Err(err) => {
            let _ = save_fallback_key(app, api_key);
            Err(format!("Keyring save error: {err}"))
        }
    }
}

pub fn load_api_key(app: &AppHandle) -> Result<Option<String>, String> {
    let entry = keyring::Entry::new(KEYRING_SERVICE, KEYRING_USER)
        .map_err(|e| format!("Keyring entry error: {e}"))?;
    match entry.get_password() {
        Ok(value) => Ok(Some(value)),
        Err(keyring::Error::NoEntry) => load_fallback_key(app),
        Err(_) => load_fallback_key(app),
    }
}

fn derive_key() -> [u8; 32] {
    let machine_id = std::fs::read_to_string("/etc/machine-id").unwrap_or_default();
    let user = std::env::var("USER").unwrap_or_default();
    let mut hasher = Sha256::new();
    hasher.update(machine_id.as_bytes());
    hasher.update(user.as_bytes());
    let digest = hasher.finalize();
    let mut key = [0u8; 32];
    key.copy_from_slice(&digest[..32]);
    key
}

fn fallback_path(app: &AppHandle) -> Result<std::path::PathBuf, String> {
    let dir = app
        .path()
        .app_data_dir()
        .map_err(|e| format!("Failed to resolve app data dir: {e}"))?;
    std::fs::create_dir_all(&dir).map_err(|e| format!("Failed to create app data dir: {e}"))?;
    Ok(dir.join(FALLBACK_FILE))
}

fn save_fallback_key(app: &AppHandle, api_key: &str) -> Result<(), String> {
    let path = fallback_path(app)?;
    let key = derive_key();
    let cipher = Aes256Gcm::new_from_slice(&key).map_err(|e| format!("Cipher init error: {e}"))?;
    let mut nonce_bytes = [0u8; 12];
    rand::thread_rng().fill_bytes(&mut nonce_bytes);
    let nonce = Nonce::from_slice(&nonce_bytes);
    let ciphertext = cipher
        .encrypt(nonce, api_key.as_bytes())
        .map_err(|e| format!("Encrypt error: {e}"))?;
    let payload = serde_json::json!({
        "nonce": base64::engine::general_purpose::STANDARD.encode(nonce_bytes),
        "ciphertext": base64::engine::general_purpose::STANDARD.encode(ciphertext),
    });
    std::fs::write(&path, payload.to_string())
        .map_err(|e| format!("Fallback write error: {e}"))?;
    Ok(())
}

fn load_fallback_key(app: &AppHandle) -> Result<Option<String>, String> {
    let path = fallback_path(app)?;
    if !path.exists() {
        return Ok(None);
    }
    let data = std::fs::read_to_string(&path)
        .map_err(|e| format!("Fallback read error: {e}"))?;
    let value: serde_json::Value =
        serde_json::from_str(&data).map_err(|e| format!("Fallback parse error: {e}"))?;
    let nonce_b64 = value.get("nonce").and_then(|v| v.as_str()).unwrap_or("");
    let cipher_b64 = value.get("ciphertext").and_then(|v| v.as_str()).unwrap_or("");
    if nonce_b64.is_empty() || cipher_b64.is_empty() {
        return Ok(None);
    }
    let nonce_bytes = base64::engine::general_purpose::STANDARD
        .decode(nonce_b64)
        .map_err(|e| format!("Fallback decode error: {e}"))?;
    let cipher_bytes = base64::engine::general_purpose::STANDARD
        .decode(cipher_b64)
        .map_err(|e| format!("Fallback decode error: {e}"))?;
    let key = derive_key();
    let cipher = Aes256Gcm::new_from_slice(&key).map_err(|e| format!("Cipher init error: {e}"))?;
    let nonce = Nonce::from_slice(&nonce_bytes);
    let plaintext = cipher
        .decrypt(nonce, cipher_bytes.as_ref())
        .map_err(|e| format!("Decrypt error: {e}"))?;
    Ok(Some(String::from_utf8_lossy(&plaintext).to_string()))
}

fn delete_fallback_key(app: &AppHandle) -> Result<(), String> {
    let path = fallback_path(app)?;
    if path.exists() {
        let _ = std::fs::remove_file(path);
    }
    Ok(())
}
