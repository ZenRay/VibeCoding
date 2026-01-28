use crate::audio::buffer::AudioBuffer;
use cpal::traits::{DeviceTrait, HostTrait, StreamTrait};
use cpal::{Device, Stream, StreamConfig};
use thiserror::Error;
use tracing::info;

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
    #[error("Unsupported sample format")]
    UnsupportedSampleFormat,
}

pub struct AudioCapture {
    device: Device,
    config: StreamConfig,
    stream: Option<Stream>,
    buffer: AudioBuffer,
    channels: usize,
}

impl AudioCapture {
    pub fn new(buffer: AudioBuffer) -> Result<Self, CaptureError> {
        let host = cpal::default_host();
        let device = host
            .default_input_device()
            .ok_or(CaptureError::NoDevice)?;

        let supported_config = device
            .default_input_config()
            .map_err(|e| CaptureError::ConfigError(e.to_string()))?;

        let config: StreamConfig = supported_config.into();

        let channels = config.channels as usize;
        Ok(Self {
            device,
            config,
            stream: None,
            buffer,
            channels,
        })
    }

    pub fn start(&mut self) -> Result<(), CaptureError> {
        let buffer = self.buffer.clone();
        let config = self.config.clone();
        let sample_rate = self.config.sample_rate.0;
        let channels = self.channels;
        let sample_format = self
            .device
            .default_input_config()
            .map_err(|e| CaptureError::ConfigError(e.to_string()))?
            .sample_format();

        let stream = match sample_format {
            cpal::SampleFormat::F32 => self
                .device
                .build_input_stream(
                    &config,
                    move |data: &[f32], _| {
                        if channels <= 1 {
                            buffer.push_batch(data);
                        } else {
                            for chunk in data.chunks_exact(channels) {
                                let sum: f32 = chunk.iter().sum();
                                let mono = sum / channels as f32;
                                if !buffer.push(mono) {
                                    break;
                                }
                            }
                        }
                    },
                    move |_err| {},
                    None,
                )
                .map_err(|e| CaptureError::StreamBuildError(e.to_string()))?,
            _ => return Err(CaptureError::UnsupportedSampleFormat),
        };

        stream
            .play()
            .map_err(|e| CaptureError::StreamStartError(e.to_string()))?;
        self.stream = Some(stream);
        info!(
            event = "audio_capture_started",
            sample_rate = sample_rate,
            channels = channels
        );
        Ok(())
    }

    pub fn stop(&mut self) {
        self.stream = None;
    }

    pub fn sample_rate(&self) -> u32 {
        self.config.sample_rate.0
    }

    pub fn read_samples(&self, output: &mut [f32]) -> usize {
        self.buffer.pop_batch(output)
    }
}
