use tauri::{AppHandle, Emitter, Manager};
use std::fs::{File, OpenOptions};
use std::io::{BufWriter, Write};
use tokio::time::{sleep, Duration};
use tracing::info;
use tokio::sync::Mutex;

use crate::audio::buffer::AudioBuffer;
use crate::audio::capture::{AudioCapture, CaptureError};
use crate::config::AppConfig;

#[derive(Default)]
pub struct AppState {
    is_recording: Mutex<bool>,
    config: Mutex<AppConfig>,
    capture: Mutex<Option<AudioCapture>>,
    wav_writer: Mutex<Option<hound::WavWriter<BufWriter<File>>>>,
}

impl AppState {
    pub fn new() -> Self {
        Self {
            is_recording: Mutex::new(false),
            config: Mutex::new(AppConfig::default()),
            capture: Mutex::new(None),
            wav_writer: Mutex::new(None),
        }
    }
}

pub async fn start_transcription(
    app_handle: AppHandle,
    state: &AppState,
) -> Result<(), String> {
    let mut recording = state.is_recording.lock().await;
    if *recording {
        return Ok(());
    }
    let mut capture_guard = state.capture.lock().await;
    let buffer = AudioBuffer::new(16_000);
    let mut capture = AudioCapture::new(buffer)
        .map_err(|e| format!("Failed to create audio capture: {e}"))?;
    capture
        .start()
        .map_err(|e| match e {
            CaptureError::StreamStartError(msg) => format!("Failed to start audio capture: {msg}"),
            other => format!("Failed to start audio capture: {other}"),
        })?;
    *capture_guard = Some(capture);
    *recording = true;
    info!(event = "recording_started");
    let _ = app_handle.emit(
        "recording_state_changed",
        serde_json::json!({ "is_recording": true }),
    );
    let app_handle_clone = app_handle.clone();
    let save_samples = std::env::var("SCRIBEFLOW_DEBUG_SAVE").ok().as_deref() == Some("1");
    let save_wav = std::env::var("SCRIBEFLOW_DEBUG_WAV").ok().as_deref() == Some("1");

    if save_wav {
        let spec = hound::WavSpec {
            channels: 1,
            sample_rate: capture_guard
                .as_ref()
                .map(|c| c.sample_rate())
                .unwrap_or(44100),
            bits_per_sample: 16,
            sample_format: hound::SampleFormat::Int,
        };
        if let Ok(writer) = hound::WavWriter::create("../audio_capture.wav", spec) {
            let mut wav_guard = state.wav_writer.lock().await;
            *wav_guard = Some(writer);
        }
    }
    tokio::spawn(async move {
        let mut saved_batches = 0u32;
        let mut saving_enabled = false;
        let mut output_samples = if save_samples {
            OpenOptions::new()
                .create(true)
                .append(true)
                .open("../audio_samples.csv")
                .ok()
        } else {
            None
        };
        let mut output_peaks = if save_samples {
            OpenOptions::new()
                .create(true)
                .append(true)
                .open("../audio_peaks.csv")
                .ok()
        } else {
            None
        };
        loop {
            let state_handle = app_handle_clone.state::<AppState>();
            let recording = state_handle.inner().is_recording.lock().await;
            if !*recording {
                break;
            }
            drop(recording);
            let capture_guard = state_handle.inner().capture.lock().await;
            if let Some(capture) = capture_guard.as_ref() {
                let mut buf = vec![0.0f32; 4096];
                let mut total_read = 0usize;
                let mut peak = 0.0f32;
                loop {
                    let read = capture.read_samples(&mut buf);
                    if read == 0 {
                        break;
                    }
                    total_read += read;
                    for sample in buf.iter().take(read) {
                        let abs = sample.abs();
                        if abs > peak {
                            peak = abs;
                        }
                    }
                    if peak > 1.0e-5 {
                        saving_enabled = true;
                    }
                    if let Some(file) = output_samples.as_mut() {
                        if saving_enabled && saved_batches < 50 {
                            for sample in buf.iter().take(read) {
                                let _ = writeln!(file, "{sample:.8e}");
                            }
                            saved_batches += 1;
                        }
                    }
                    if save_wav {
                        let mut wav_guard = state_handle.inner().wav_writer.lock().await;
                        if let Some(writer) = wav_guard.as_mut() {
                            for sample in buf.iter().take(read) {
                                let clamped = sample.clamp(-1.0, 1.0);
                                let value = (clamped * i16::MAX as f32) as i16;
                                let _ = writer.write_sample(value);
                            }
                        }
                    }
                }
                if total_read > 0 {
                    if let Some(file) = output_peaks.as_mut() {
                        let _ = writeln!(file, "{peak:.8e}");
                    }
                    let _ = app_handle_clone.emit(
                        "audio_level_update",
                        serde_json::json!({ "level": peak }),
                    );
                    info!(
                        event = "audio_level_update",
                        samples = total_read,
                        peak = peak
                    );
                }
            }
            sleep(Duration::from_millis(50)).await;
        }
    });
    Ok(())
}

pub async fn stop_transcription(
    app_handle: AppHandle,
    state: &AppState,
) -> Result<(), String> {
    let mut recording = state.is_recording.lock().await;
    if !*recording {
        return Err("Not recording".to_string());
    }
    let mut capture_guard = state.capture.lock().await;
    if let Some(mut capture) = capture_guard.take() {
        capture.stop();
    }
    let mut wav_guard = state.wav_writer.lock().await;
    if let Some(writer) = wav_guard.take() {
        let _ = writer.finalize();
    }
    *recording = false;
    let _ = app_handle.emit(
        "recording_state_changed",
        serde_json::json!({ "is_recording": false }),
    );
    Ok(())
}

pub async fn get_config(state: &AppState) -> AppConfig {
    state.config.lock().await.clone()
}

pub async fn save_config(state: &AppState, config: AppConfig) -> Result<(), String> {
    let mut current = state.config.lock().await;
    *current = config;
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::AppState;
    use crate::config::AppConfig;

    #[tokio::test]
    async fn state_starts_not_recording() {
        let state = AppState::new();
        let value = state.is_recording.lock().await;
        assert!(!*value);
    }

    #[tokio::test]
    async fn config_can_roundtrip() {
        let state = AppState::new();
        let updated = AppConfig {
            api_key: Some("key".to_string()),
            language: "en".to_string(),
            hotkey: "Cmd+Shift+\\".to_string(),
        };
        let _ = super::save_config(&state, updated.clone()).await;
        let stored = super::get_config(&state).await;
        assert_eq!(stored.api_key, updated.api_key);
        assert_eq!(stored.language, updated.language);
    }
}
