use crossbeam::queue::ArrayQueue;
use std::sync::Arc;

#[derive(Clone)]
pub struct AudioBuffer {
    queue: Arc<ArrayQueue<f32>>,
}

impl AudioBuffer {
    pub fn new(capacity: usize) -> Self {
        Self {
            queue: Arc::new(ArrayQueue::new(capacity)),
        }
    }

    pub fn push(&self, sample: f32) -> bool {
        self.queue.push(sample).is_ok()
    }

    pub fn push_batch(&self, samples: &[f32]) -> usize {
        let mut pushed = 0;
        for &sample in samples {
            if self.queue.push(sample).is_ok() {
                pushed += 1;
            } else {
                break;
            }
        }
        pushed
    }

    pub fn pop_batch(&self, output: &mut [f32]) -> usize {
        let mut count = 0;
        for slot in output.iter_mut() {
            if let Some(sample) = self.queue.pop() {
                *slot = sample;
                count += 1;
            } else {
                break;
            }
        }
        count
    }

    pub fn len(&self) -> usize {
        self.queue.len()
    }
}

#[cfg(test)]
mod tests {
    use super::AudioBuffer;

    #[test]
    fn buffer_push_pop_roundtrip() {
        let buffer = AudioBuffer::new(4);
        assert!(buffer.push(0.25));
        assert!(buffer.push(0.5));

        let mut out = [0.0f32; 2];
        let read = buffer.pop_batch(&mut out);
        assert_eq!(read, 2);
        assert_eq!(out, [0.25, 0.5]);
    }
}
