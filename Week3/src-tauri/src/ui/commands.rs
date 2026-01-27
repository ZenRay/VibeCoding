use tauri::{AppHandle, Emitter, Manager};
use tauri_plugin_global_shortcut::{GlobalShortcutExt, Shortcut};
use std::fs::{File, OpenOptions};
use std::io::{BufWriter, Write};
use tokio::time::{sleep, Duration};
use tracing::{info, warn};
use tokio::net::{lookup_host, TcpStream};
use url::Url;
use std::time::Instant;
use tokio::sync::Mutex;

use crate::audio::buffer::AudioBuffer;
use crate::audio::capture::{AudioCapture, CaptureError};
use crate::audio::resampler::{AudioResampler, ResamplerConfig};
use crate::config::store as config_store;
use crate::config::AppConfig;
use crate::input::injector::TextInjector;
use crate::network::client::ScribeClient;
use crate::network::protocol::{ConnectionConfig, ServerMessage};

#[derive(Default)]
pub struct AppState {
    is_recording: Mutex<bool>,
    config: Mutex<AppConfig>,
    capture: Mutex<Option<AudioCapture>>,
    wav_writer: Mutex<Option<hound::WavWriter<BufWriter<File>>>>,
    session_cancel: Mutex<Option<tokio::sync::watch::Sender<bool>>>,
}

impl AppState {
    pub fn new() -> Self {
        Self {
            is_recording: Mutex::new(false),
            config: Mutex::new(AppConfig::default()),
            capture: Mutex::new(None),
            wav_writer: Mutex::new(None),
            session_cancel: Mutex::new(None),
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
    let config = config_store::load_config(&app_handle);
    let api_key = config
        .api_key
        .clone()
        .ok_or_else(|| "API key not configured".to_string())?;
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

    let (cancel_tx, cancel_rx) = tokio::sync::watch::channel(false);
    {
        let mut cancel_guard = state.session_cancel.lock().await;
        *cancel_guard = Some(cancel_tx);
    }

    let input_rate = capture_guard
        .as_ref()
        .map(|c| c.sample_rate())
        .unwrap_or(44100) as usize;
    let input_chunk = (input_rate / 100) as usize;
    let mut resampler = AudioResampler::new(ResamplerConfig {
        input_rate,
        output_rate: 16000,
        chunk_size: input_chunk,
    })
    .map_err(|e| format!("{e}"))?;

    let ws_config = ConnectionConfig {
        endpoint: "wss://api.elevenlabs.io/v1/speech-to-text/realtime".to_string(),
        api_key,
        model_id: "scribe_v2_realtime".to_string(),
        audio_format: "pcm_16000".to_string(),
        sample_rate: 16_000,
        commit_strategy: "vad".to_string(),
        language_code: if config.language == "auto" {
            None
        } else {
            Some(config.language.clone())
        },
    };
    let _ = app_handle.emit(
        "connection_status",
        serde_json::json!({ "state": "connecting" }),
    );
    info!(event = "ws_task_spawned");
    let (audio_tx, audio_rx) = tokio::sync::mpsc::channel::<Vec<i16>>(8);
    let app_handle_clone = app_handle.clone();
    let save_samples = std::env::var("SCRIBEFLOW_DEBUG_SAVE").ok().as_deref() == Some("1");
    let save_wav = std::env::var("SCRIBEFLOW_DEBUG_WAV").ok().as_deref() == Some("1");
    let cancel_rx_audio = cancel_rx.clone();

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
        let mut last_level_log = Instant::now();
        let mut last_drop_log = Instant::now();
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
            if *cancel_rx_audio.borrow() {
                break;
            }
            let state_handle = app_handle_clone.state::<AppState>();
            let recording = state_handle.inner().is_recording.lock().await;
            if !*recording {
                break;
            }
            drop(recording);
            let capture_guard = state_handle.inner().capture.lock().await;
            if let Some(capture) = capture_guard.as_ref() {
                let mut buf = vec![0.0f32; input_chunk.max(1)];
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
                    let resampled = match resampler.process(&buf[..read]) {
                        Ok(data) => data,
                        Err(_) => Vec::new(),
                    };
                    if !resampled.is_empty() {
                        let pcm: Vec<i16> = resampled
                            .iter()
                            .map(|s| (s.clamp(-1.0, 1.0) * i16::MAX as f32) as i16)
                            .collect();
                        if audio_tx.try_send(pcm).is_err() && last_drop_log.elapsed() >= Duration::from_secs(5) {
                            warn!(event = "audio_drop", reason = "ws_queue_full");
                            last_drop_log = Instant::now();
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
                    if last_level_log.elapsed() >= Duration::from_secs(2) {
                        info!(
                            event = "audio_level_update",
                            samples = total_read,
                            peak = peak
                        );
                        last_level_log = Instant::now();
                    }
                }
            }
            sleep(Duration::from_millis(50)).await;
        }
    });

    let mut cancel_rx_ws = cancel_rx.clone();
    let ws_endpoint = ws_config.endpoint.clone();
    tokio::spawn(async move {
        let mut ws_client = ScribeClient::new(ws_config);
        info!(event = "ws_connect_start");
        if let Ok(url) = Url::parse(&ws_endpoint) {
            if let Some(host) = url.host_str() {
                let port = url.port_or_known_default().unwrap_or(443);
                match lookup_host((host, port)).await {
                    Ok(addrs) => {
                        let resolved: Vec<String> = addrs.map(|addr| addr.to_string()).collect();
                        info!(event = "ws_dns_resolved", host = host, port = port, addrs = ?resolved);
                    }
                    Err(err) => {
                        warn!(event = "ws_dns_error", host = host, error = %err);
                    }
                }
                match tokio::time::timeout(Duration::from_secs(3), TcpStream::connect((host, port))).await {
                    Ok(Ok(_)) => {
                        info!(event = "ws_tcp_connect_ok", host = host, port = port);
                    }
                    Ok(Err(err)) => {
                        warn!(event = "ws_tcp_connect_error", host = host, port = port, error = %err);
                    }
                    Err(_) => {
                        warn!(event = "ws_tcp_connect_timeout", host = host, port = port);
                    }
                }
            }
        }
        match tokio::time::timeout(Duration::from_secs(10), ws_client.connect()).await {
            Ok(Ok(())) => {
                let _ = app_handle.emit(
                    "connection_status",
                    serde_json::json!({ "state": "connected" }),
                );
                info!(event = "ws_connected");
            }
            Ok(Err(err)) => {
                warn!(event = "ws_connect_error", error = %err);
                let _ = app_handle.emit(
                    "connection_status",
                    serde_json::json!({ "state": "failed" }),
                );
                return;
            }
            Err(_) => {
                warn!(event = "ws_connect_timeout");
                let _ = app_handle.emit(
                    "connection_status",
                    serde_json::json!({ "state": "failed" }),
                );
                return;
            }
        }
        let mut audio_rx = audio_rx;
        loop {
            tokio::select! {
                _ = cancel_rx_ws.changed() => {
                    if *cancel_rx_ws.borrow() {
                        break;
                    }
                }
                pcm = audio_rx.recv() => {
                    if let Some(pcm) = pcm {
                        if let Err(err) = ws_client.send_audio(&pcm).await {
                            warn!(event = "ws_send_error", error = %err);
                        }
                    } else {
                        break;
                    }
                }
                message = ws_client.receive() => {
                    match message {
                        Ok(message) => match message {
                            ServerMessage::SessionStarted { session_id } => {
                                info!(event = "session_started", session_id = session_id);
                            }
                            ServerMessage::PartialTranscript { text } => {
                                let _ = app_handle.emit(
                                    "partial_transcript",
                                    serde_json::json!({ "text": text }),
                                );
                                info!(event = "partial_transcript", text = text);
                            }
                            ServerMessage::CommittedTranscript { text } => {
                                let _ = app_handle.emit(
                                    "committed_transcript",
                                    serde_json::json!({ "text": text }),
                                );
                                info!(event = "committed_transcript", text = text);
                                let app_handle_inject = app_handle.clone();
                                let text_clone = text.clone();
                                tokio::task::spawn_blocking(move || {
                                    let injector = TextInjector::new();
                                    let _ = injector.inject(&app_handle_inject, &text_clone);
                                });
                            }
                            ServerMessage::Error {
                                message_type,
                                message,
                            } => {
                                warn!(
                                    event = "scribe_error",
                                    message_type = message_type,
                                    message = message
                                );
                            }
                            ServerMessage::Unknown { message_type, .. } => {
                                warn!(event = "unknown_message", message_type = message_type);
                            }
                        },
                        Err(err) => {
                            warn!(event = "ws_receive_error", error = %err);
                        }
                    }
                }
            }
        }
        info!(event = "ws_task_exit");
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
    let cancel = state.session_cancel.lock().await.take();
    if let Some(cancel_tx) = cancel {
        let _ = cancel_tx.send(true);
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

pub async fn toggle_transcription(
    app_handle: AppHandle,
    state: &AppState,
) -> Result<(), String> {
    let is_recording = {
        let guard = state.is_recording.lock().await;
        *guard
    };
    if is_recording {
        stop_transcription(app_handle, state).await
    } else {
        start_transcription(app_handle, state).await
    }
}

pub async fn get_config(app_handle: &AppHandle, state: &AppState) -> AppConfig {
    let config = config_store::load_config(app_handle);
    let mut current = state.config.lock().await;
    *current = config.clone();
    config
}

pub async fn save_config(
    app_handle: &AppHandle,
    state: &AppState,
    config: AppConfig,
) -> Result<(), String> {
    config_store::save_config(app_handle, &config)?;
    let shortcut_manager = app_handle.global_shortcut();
    shortcut_manager
        .unregister_all()
        .map_err(|e| format!("Failed to unregister hotkeys: {e}"))?;
    let shortcut: Shortcut = config
        .hotkey
        .parse()
        .map_err(|e| format!("Invalid hotkey: {e}"))?;
    shortcut_manager
        .on_shortcut(shortcut, move |handle, _shortcut, _event| {
            let app_handle = handle.clone();
            tauri::async_runtime::spawn(async move {
                let state = app_handle.state::<AppState>();
                let _ = toggle_transcription(app_handle.clone(), state.inner()).await;
            });
        })
        .map_err(|e| format!("Failed to register hotkey: {e}"))?;
    let mut current = state.config.lock().await;
    *current = config;
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::AppState;

    #[tokio::test]
    async fn state_starts_not_recording() {
        let state = AppState::new();
        let value = state.is_recording.lock().await;
        assert!(!*value);
    }

}
