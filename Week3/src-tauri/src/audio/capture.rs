// Audio capture using cpal

use cpal::traits::{DeviceTrait, HostTrait, StreamTrait};
use cpal::{Device, Stream, StreamConfig};
use thiserror::Error;
use tracing;

use super::buffer::AudioBuffer;

#[derive(Debug, Error)]
pub enum CaptureError {
    #[error("No audio input device available")]
    NoDevice,

    #[error("Failed to get device configuration: {0}")]
    ConfigError(String),

    #[error("Failed to build audio stream: {0}")]
    StreamBuildError(String),

    #[error("Failed to start audio stream: {0}")]
    StreamStartError(String),

    #[error("Unsupported channel count: {0} (only mono supported)")]
    UnsupportedChannelCount(u16),

    #[error("Unsupported sample rate: {0} (must be between 16kHz and 96kHz)")]
    UnsupportedSampleRate(u32),
}

/// Audio capture configuration
#[derive(Debug, Clone)]
pub struct CaptureConfig {
    /// Sample rate (Hz)
    pub sample_rate: u32,

    /// Number of channels (must be 1 for mono)
    pub channels: u16,

    /// Buffer size in frames (e.g., 480 for 10ms @ 48kHz)
    pub buffer_size: usize,
}

impl Default for CaptureConfig {
    fn default() -> Self {
        Self {
            sample_rate: 48000,
            channels: 1,
            buffer_size: 480,
        }
    }
}

/// Audio stream state
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum StreamState {
    Idle,
    Starting,
    Running,
    Paused,
    Error,
}

/// Audio capture manager
pub struct AudioCapture {
    device: Device,
    config: StreamConfig,
    capture_config: CaptureConfig,
    stream: Option<Stream>,
    buffer: AudioBuffer,
    state: StreamState,
}

impl AudioCapture {
    /// Create a new audio capture instance with the default device
    pub fn new() -> Result<Self, CaptureError> {
        Self::with_config(CaptureConfig::default())
    }

    /// Create a new audio capture instance with custom configuration
    pub fn with_config(capture_config: CaptureConfig) -> Result<Self, CaptureError> {
        // Get default audio host
        let host = cpal::default_host();

        // Get default input device
        let device = host
            .default_input_device()
            .ok_or(CaptureError::NoDevice)?;

        tracing::info!(
            event = "audio_device_selected",
            device_name = device.name().ok().as_deref().unwrap_or("unknown")
        );

        // Get supported configuration
        let supported_config = device
            .default_input_config()
            .map_err(|e| CaptureError::ConfigError(e.to_string()))?;

        // Get native sample rate and channels
        let native_rate = supported_config.sample_rate().0;
        let native_channels = supported_config.channels();

        tracing::info!(
            event = "audio_config_detected",
            sample_rate = native_rate,
            channels = native_channels,
            sample_format = ?supported_config.sample_format()
        );

        // Create stream config
        let config: StreamConfig = supported_config.into();

        // Create audio buffer (100ms capacity)
        let buffer = AudioBuffer::new();

        Ok(Self {
            device,
            config,
            capture_config,
            stream: None,
            buffer,
            state: StreamState::Idle,
        })
    }

    /// Start audio capture
    pub fn start(&mut self) -> Result<(), CaptureError> {
        if self.state == StreamState::Running {
            tracing::warn!("Audio capture already running");
            return Ok(());
        }

        self.state = StreamState::Starting;

        // Clone buffer for use in the audio callback
        let buffer = self.buffer.clone();
        let channels = self.config.channels;

        // Build input stream
        let stream = self
            .device
            .build_input_stream(
                &self.config,
                move |data: &[f32], _: &cpal::InputCallbackInfo| {
                    // Audio callback - MUST be real-time safe (no allocations, no I/O)
                    if channels == 1 {
                        // Mono: direct copy
                        let pushed = buffer.push_batch(data);
                        if pushed < data.len() {
                            tracing::warn!(
                                event = "audio_buffer_overflow",
                                dropped_samples = data.len() - pushed
                            );
                        }
                    } else {
                        // Stereo or multichannel: convert to mono by averaging channels
                        let ch = channels as usize;
                        for chunk in data.chunks_exact(ch) {
                            let mono_sample: f32 = chunk.iter().sum::<f32>() / ch as f32;
                            if buffer.push(mono_sample).is_err() {
                                tracing::warn!(event = "audio_buffer_overflow");
                                break;
                            }
                        }
                    }
                },
                move |err| {
                    tracing::error!(event = "audio_stream_error", error = %err);
                },
                None, // Use default timeout
            )
            .map_err(|e| CaptureError::StreamBuildError(e.to_string()))?;

        // Start the stream
        stream
            .play()
            .map_err(|e| CaptureError::StreamStartError(e.to_string()))?;

        tracing::info!(
            event = "audio_capture_started",
            sample_rate = self.config.sample_rate.0,
            channels = self.config.channels,
            buffer_size_ms = (self.capture_config.buffer_size as f64
                / self.config.sample_rate.0 as f64
                * 1000.0)
        );

        self.stream = Some(stream);
        self.state = StreamState::Running;

        Ok(())
    }

    /// Stop audio capture
    pub fn stop(&mut self) -> Result<(), CaptureError> {
        if self.state == StreamState::Idle {
            tracing::warn!("Audio capture already stopped");
            return Ok(());
        }

        // Drop the stream to stop capture
        self.stream = None;
        self.state = StreamState::Idle;

        tracing::info!(event = "audio_capture_stopped");

        Ok(())
    }

    /// Read samples from the buffer
    ///
    /// # Arguments
    /// * `output` - Buffer to fill with samples
    ///
    /// # Returns
    /// * Number of samples read
    pub fn read_samples(&self, output: &mut [f32]) -> usize {
        self.buffer.pop_batch(output)
    }

    /// Check if enough samples are available for processing
    pub fn has_samples(&self, count: usize) -> bool {
        self.buffer.len() >= count
    }

    /// Get the number of samples currently available in the buffer
    pub fn available_samples(&self) -> usize {
        self.buffer.len()
    }

    /// Get the current stream state
    pub fn state(&self) -> StreamState {
        self.state
    }

    /// Get the capture configuration
    pub fn config(&self) -> &CaptureConfig {
        &self.capture_config
    }

    /// Get the native sample rate
    pub fn sample_rate(&self) -> u32 {
        self.config.sample_rate.0
    }

    /// Get the number of channels
    pub fn channels(&self) -> u16 {
        self.config.channels
    }

    /// Get the buffer
    pub fn buffer(&self) -> &AudioBuffer {
        &self.buffer
    }
}

impl Default for AudioCapture {
    fn default() -> Self {
        Self::new().expect("Failed to create default audio capture")
    }
}

impl Drop for AudioCapture {
    fn drop(&mut self) {
        let _ = self.stop();
    }
}

/// List all available audio input devices
pub fn list_input_devices() -> Result<Vec<String>, CaptureError> {
    let host = cpal::default_host();
    let devices = host
        .input_devices()
        .map_err(|e| CaptureError::ConfigError(e.to_string()))?;

    let mut device_names = Vec::new();
    for device in devices {
        if let Ok(name) = device.name() {
            device_names.push(name);
        }
    }

    Ok(device_names)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_capture_creation() {
        // This test may fail in CI environments without audio devices
        match AudioCapture::new() {
            Ok(capture) => {
                assert_eq!(capture.state(), StreamState::Idle);
                // Device may be mono (1) or stereo (2), both are acceptable
                assert!(capture.channels() >= 1 && capture.channels() <= 2);
                assert!(capture.sample_rate() >= 16000);
            }
            Err(CaptureError::NoDevice) => {
                // Expected in CI/headless environments
                println!("No audio device available (expected in CI)");
            }
            Err(e) => panic!("Unexpected error: {}", e),
        }
    }

    #[test]
    fn test_list_devices() {
        match list_input_devices() {
            Ok(devices) => {
                println!("Available input devices:");
                for (i, device) in devices.iter().enumerate() {
                    println!("  {}. {}", i + 1, device);
                }
            }
            Err(e) => {
                println!("Failed to list devices: {} (expected in CI)", e);
            }
        }
    }

    #[test]
    fn test_buffer_operations() {
        if let Ok(capture) = AudioCapture::new() {
            // Buffer should be empty initially
            assert_eq!(capture.available_samples(), 0);
            assert!(!capture.has_samples(1));

            let mut output = vec![0.0; 100];
            let read = capture.read_samples(&mut output);
            assert_eq!(read, 0);
        }
    }

    #[test]
    #[ignore] // Requires actual audio device and user interaction
    fn test_capture_start_stop() {
        let mut capture = AudioCapture::new().expect("No audio device");

        // Start capture
        assert!(capture.start().is_ok());
        assert_eq!(capture.state(), StreamState::Running);

        // Wait a bit to capture some audio
        std::thread::sleep(std::time::Duration::from_millis(100));

        // Should have some samples now
        assert!(capture.available_samples() > 0);

        // Stop capture
        assert!(capture.stop().is_ok());
        assert_eq!(capture.state(), StreamState::Idle);
    }

    #[test]
    #[ignore] // Requires actual audio device
    fn test_capture_read_samples() {
        let mut capture = AudioCapture::new().expect("No audio device");

        capture.start().expect("Failed to start capture");

        // Wait for samples
        std::thread::sleep(std::time::Duration::from_millis(200));

        // Read samples
        let mut buffer = vec![0.0; 480];
        let read = capture.read_samples(&mut buffer);

        assert!(read > 0, "Should have captured some samples");
        assert!(read <= 480);

        // Verify samples are in valid range
        for &sample in buffer.iter().take(read) {
            assert!(
                sample >= -1.0 && sample <= 1.0,
                "Sample out of range: {}",
                sample
            );
        }

        capture.stop().expect("Failed to stop capture");
    }
}
