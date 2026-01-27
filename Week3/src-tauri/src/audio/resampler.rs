use rubato::{FftFixedIn, Resampler};
use thiserror::Error;

#[derive(Debug, Error)]
pub enum ResamplerError {
    #[error("Resampler initialization failed: {0}")]
    InitError(String),
    #[error("Resample failed: {0}")]
    ProcessError(String),
}

pub struct ResamplerConfig {
    pub input_rate: usize,
    pub output_rate: usize,
    pub chunk_size: usize,
}

pub struct AudioResampler {
    inner: FftFixedIn<f32>,
}

impl AudioResampler {
    pub fn new(config: ResamplerConfig) -> Result<Self, ResamplerError> {
        let inner = FftFixedIn::<f32>::new(
            config.input_rate,
            config.output_rate,
            config.chunk_size,
            1,
            1,
        )
        .map_err(|e| ResamplerError::InitError(e.to_string()))?;
        Ok(Self { inner })
    }

    pub fn process(&mut self, input: &[f32]) -> Result<Vec<f32>, ResamplerError> {
        let output = self
            .inner
            .process(&[input.to_vec()], None)
            .map_err(|e| ResamplerError::ProcessError(e.to_string()))?;
        Ok(output
            .get(0)
            .cloned()
            .unwrap_or_default())
    }
}

#[cfg(test)]
mod tests {
    use super::{AudioResampler, ResamplerConfig};

    #[test]
    fn resampler_downsamples() {
        let mut resampler = match AudioResampler::new(ResamplerConfig {
            input_rate: 48000,
            output_rate: 16000,
            chunk_size: 480,
        }) {
            Ok(resampler) => resampler,
            Err(_) => {
                assert!(false, "resampler init failed");
                return;
            }
        };

        let input = vec![0.0f32; 480];
        let output = match resampler.process(&input) {
            Ok(out) => out,
            Err(_) => {
                assert!(false, "resample failed");
                return;
            }
        };
        assert!(!output.is_empty());
    }
}
