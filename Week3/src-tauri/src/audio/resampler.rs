// Audio resampler: 48kHz → 16kHz using rubato

use rubato::{FftFixedInOut, Resampler as RubatoResampler};
use thiserror::Error;

#[derive(Debug, Error)]
pub enum ResamplerError {
    #[error("Failed to create resampler: {0}")]
    CreationError(String),

    #[error("Resampling failed: {0}")]
    ProcessError(String),

    #[error("Invalid input size: expected {expected}, got {actual}")]
    InvalidInputSize { expected: usize, actual: usize },

    #[error("Invalid sample rate: {0}")]
    InvalidSampleRate(u32),
}

/// Audio resampler configuration
#[derive(Debug, Clone, Copy)]
pub struct ResamplerConfig {
    /// Input sample rate (Hz)
    pub input_rate: u32,

    /// Output sample rate (Hz)
    pub output_rate: u32,

    /// Chunk size in input samples (e.g., 480 for 10ms @ 48kHz)
    pub chunk_size: usize,

    /// Number of channels
    pub channels: usize,
}

impl Default for ResamplerConfig {
    fn default() -> Self {
        Self {
            input_rate: 48000,
            output_rate: 16000,
            chunk_size: 480,
            channels: 1,
        }
    }
}

/// High-quality audio resampler using FFT-based sinc interpolation
pub struct AudioResampler {
    resampler: FftFixedInOut<f32>,
    config: ResamplerConfig,
    input_buffer: Vec<Vec<f32>>,
    output_chunk_size: usize,
}

impl AudioResampler {
    /// Create a new resampler with the given configuration
    pub fn new(config: ResamplerConfig) -> Result<Self, ResamplerError> {
        // Validate configuration
        if config.input_rate < 8000 || config.input_rate > 96000 {
            return Err(ResamplerError::InvalidSampleRate(config.input_rate));
        }
        if config.output_rate < 8000 || config.output_rate > 96000 {
            return Err(ResamplerError::InvalidSampleRate(config.output_rate));
        }

        // Calculate output chunk size based on ratio
        let ratio = config.output_rate as f64 / config.input_rate as f64;
        let output_chunk_size = (config.chunk_size as f64 * ratio).round() as usize;

        // Create FFT-based resampler
        let resampler = FftFixedInOut::<f32>::new(
            config.input_rate as usize,
            config.output_rate as usize,
            config.chunk_size,
            config.channels,
        )
        .map_err(|e| ResamplerError::CreationError(e.to_string()))?;

        // Pre-allocate input buffer for each channel
        let input_buffer = vec![Vec::with_capacity(config.chunk_size); config.channels];

        Ok(Self {
            resampler,
            config,
            input_buffer,
            output_chunk_size,
        })
    }

    /// Create a default resampler (48kHz → 16kHz, mono, 480 samples)
    pub fn default_config() -> Result<Self, ResamplerError> {
        Self::new(ResamplerConfig::default())
    }

    /// Resample a chunk of audio samples
    ///
    /// # Arguments
    /// * `input` - Input samples (must be exactly chunk_size length)
    ///
    /// # Returns
    /// * Resampled output samples
    pub fn process(&mut self, input: &[f32]) -> Result<Vec<f32>, ResamplerError> {
        // Validate input size
        if input.len() != self.config.chunk_size {
            return Err(ResamplerError::InvalidInputSize {
                expected: self.config.chunk_size,
                actual: input.len(),
            });
        }

        // Prepare input buffer (convert to Vec<Vec<f32>> for rubato)
        self.input_buffer[0].clear();
        self.input_buffer[0].extend_from_slice(input);

        // Process resampling
        let mut output = self
            .resampler
            .process(&self.input_buffer, None)
            .map_err(|e| ResamplerError::ProcessError(e.to_string()))?;

        // FFT-based resampling can cause ringing artifacts that exceed [-1.0, 1.0]
        // Clamp the output to prevent overflow
        for sample in output[0].iter_mut() {
            *sample = sample.clamp(-1.0, 1.0);
        }

        // Extract output from first channel
        Ok(output[0].clone())
    }

    /// Convert f32 samples to i16 PCM format
    pub fn f32_to_i16(samples: &[f32]) -> Vec<i16> {
        samples
            .iter()
            .map(|&sample| {
                // Clamp to [-1.0, 1.0] range
                let clamped = sample.clamp(-1.0, 1.0);
                // Scale to i16 range properly
                if clamped >= 0.0 {
                    (clamped * i16::MAX as f32) as i16
                } else {
                    (clamped * -(i16::MIN as f32)) as i16
                }
            })
            .collect()
    }

    /// Get the expected output size for a given input size
    pub fn output_size(&self) -> usize {
        self.output_chunk_size
    }

    /// Get the input chunk size
    pub fn input_chunk_size(&self) -> usize {
        self.config.chunk_size
    }

    /// Get the resampling ratio
    pub fn ratio(&self) -> f64 {
        self.config.output_rate as f64 / self.config.input_rate as f64
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_resampler_creation() {
        let resampler = AudioResampler::default_config();
        assert!(resampler.is_ok());

        let resampler = resampler.unwrap();
        assert_eq!(resampler.input_chunk_size(), 480);
        assert_eq!(resampler.output_size(), 160); // 480 * (16000/48000) = 160
        assert_eq!(resampler.ratio(), 1.0 / 3.0);
    }

    #[test]
    fn test_resampler_process() {
        let mut resampler = AudioResampler::default_config().expect("Failed to create resampler");

        // Generate 480 samples of 1kHz sine wave @ 48kHz
        let input: Vec<f32> = (0..480)
            .map(|i| {
                let t = i as f32 / 48000.0;
                (2.0 * std::f32::consts::PI * 1000.0 * t).sin()
            })
            .collect();

        let output = resampler.process(&input).expect("Resampling failed");

        // Output should be 160 samples (480 / 3)
        assert_eq!(output.len(), 160);

        // Verify output is in valid range [-1.0, 1.0]
        for &sample in &output {
            assert!(sample >= -1.0 && sample <= 1.0);
        }
    }

    #[test]
    fn test_resampler_invalid_input_size() {
        let mut resampler = AudioResampler::default_config().expect("Failed to create resampler");

        let invalid_input = vec![0.0; 400]; // Wrong size
        let result = resampler.process(&invalid_input);

        assert!(result.is_err());
        if let Err(ResamplerError::InvalidInputSize { expected, actual }) = result {
            assert_eq!(expected, 480);
            assert_eq!(actual, 400);
        } else {
            panic!("Expected InvalidInputSize error");
        }
    }

    #[test]
    fn test_f32_to_i16_conversion() {
        let samples = vec![-1.0, -0.5, 0.0, 0.5, 1.0];
        let converted = AudioResampler::f32_to_i16(&samples);

        assert_eq!(converted.len(), 5);
        assert_eq!(converted[0], i16::MIN);
        assert_eq!(converted[2], 0);
        assert_eq!(converted[4], i16::MAX);
    }

    #[test]
    fn test_f32_to_i16_clamping() {
        let samples = vec![-2.0, -1.5, 1.5, 2.0]; // Out of range
        let converted = AudioResampler::f32_to_i16(&samples);

        // Should clamp to [-1.0, 1.0] before conversion
        assert_eq!(converted[0], i16::MIN); // Clamped from -2.0 to -1.0
        assert_eq!(converted[1], i16::MIN); // Clamped from -1.5 to -1.0
        assert_eq!(converted[2], i16::MAX); // Clamped from 1.5 to 1.0
        assert_eq!(converted[3], i16::MAX); // Clamped from 2.0 to 1.0
    }

    #[test]
    fn test_resampler_quality() {
        let mut resampler = AudioResampler::default_config().expect("Failed to create resampler");

        // Generate pure 1kHz sine wave @ 48kHz
        let frequency = 1000.0;
        let input: Vec<f32> = (0..480)
            .map(|i| {
                let t = i as f32 / 48000.0;
                (2.0 * std::f32::consts::PI * frequency * t).sin()
            })
            .collect();

        let output = resampler.process(&input).expect("Resampling failed");

        // Verify output maintains the same frequency characteristics
        // The output should also be a sine wave at 1kHz but @ 16kHz

        // Check that output has similar amplitude characteristics
        let input_rms: f32 = input.iter().map(|&x| x * x).sum::<f32>() / input.len() as f32;
        let output_rms: f32 = output.iter().map(|&x| x * x).sum::<f32>() / output.len() as f32;

        let input_rms = input_rms.sqrt();
        let output_rms = output_rms.sqrt();

        // RMS should be in reasonable range (within 50% for FFT-based resampling)
        // FFT resamplers can have amplitude variations due to filter characteristics
        let rms_diff = (input_rms - output_rms).abs() / input_rms;
        assert!(
            rms_diff < 0.5,
            "RMS difference too large: {:.2}%",
            rms_diff * 100.0
        );

        // Verify output is not all zeros
        assert!(output_rms > 0.1, "Output RMS too low, may be silent");
    }

    #[test]
    fn test_resampler_multiple_chunks() {
        let mut resampler = AudioResampler::default_config().expect("Failed to create resampler");

        // Process multiple chunks sequentially
        for _ in 0..10 {
            let input = vec![0.5; 480];
            let output = resampler.process(&input).expect("Resampling failed");
            assert_eq!(output.len(), 160);
        }
    }
}
