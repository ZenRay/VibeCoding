// Ring buffer for audio samples using lock-free queue

use crossbeam::queue::ArrayQueue;
use std::sync::Arc;
use thiserror::Error;

/// Ring buffer capacity: 100ms @ 48kHz = 4800 samples
const BUFFER_CAPACITY: usize = 4800;

#[derive(Debug, Error)]
pub enum BufferError {
    #[error("Buffer is full, cannot push more samples")]
    BufferFull,

    #[error("Buffer is empty, no samples available")]
    BufferEmpty,
}

/// Lock-free ring buffer for audio samples
pub struct AudioBuffer {
    queue: Arc<ArrayQueue<f32>>,
}

impl AudioBuffer {
    /// Create a new audio buffer with default capacity (100ms @ 48kHz)
    pub fn new() -> Self {
        Self {
            queue: Arc::new(ArrayQueue::new(BUFFER_CAPACITY)),
        }
    }

    /// Create a new audio buffer with custom capacity
    pub fn with_capacity(capacity: usize) -> Self {
        Self {
            queue: Arc::new(ArrayQueue::new(capacity)),
        }
    }

    /// Push a sample into the buffer (non-blocking)
    /// Returns error if buffer is full
    pub fn push(&self, sample: f32) -> Result<(), BufferError> {
        self.queue.push(sample).map_err(|_| BufferError::BufferFull)
    }

    /// Push multiple samples into the buffer
    /// Returns the number of samples successfully pushed
    pub fn push_batch(&self, samples: &[f32]) -> usize {
        let mut count = 0;
        for &sample in samples {
            if self.push(sample).is_ok() {
                count += 1;
            } else {
                break;
            }
        }
        count
    }

    /// Pop a sample from the buffer (non-blocking)
    /// Returns None if buffer is empty
    pub fn pop(&self) -> Option<f32> {
        self.queue.pop()
    }

    /// Pop multiple samples from the buffer
    /// Fills the output buffer with available samples
    /// Returns the number of samples popped
    pub fn pop_batch(&self, output: &mut [f32]) -> usize {
        let mut count = 0;
        for slot in output.iter_mut() {
            if let Some(sample) = self.pop() {
                *slot = sample;
                count += 1;
            } else {
                break;
            }
        }
        count
    }

    /// Get the number of samples currently in the buffer
    pub fn len(&self) -> usize {
        self.queue.len()
    }

    /// Check if the buffer is empty
    pub fn is_empty(&self) -> bool {
        self.queue.is_empty()
    }

    /// Get the total capacity of the buffer
    pub fn capacity(&self) -> usize {
        self.queue.capacity()
    }

    /// Get a clone of the internal Arc for sharing across threads
    pub fn clone_arc(&self) -> Arc<ArrayQueue<f32>> {
        Arc::clone(&self.queue)
    }
}

impl Default for AudioBuffer {
    fn default() -> Self {
        Self::new()
    }
}

impl Clone for AudioBuffer {
    fn clone(&self) -> Self {
        Self {
            queue: Arc::clone(&self.queue),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_buffer_push_pop() {
        let buffer = AudioBuffer::new();

        // Push a sample
        assert!(buffer.push(1.0).is_ok());
        assert_eq!(buffer.len(), 1);

        // Pop the sample
        assert_eq!(buffer.pop(), Some(1.0));
        assert_eq!(buffer.len(), 0);
        assert!(buffer.is_empty());
    }

    #[test]
    fn test_buffer_batch_operations() {
        let buffer = AudioBuffer::new();
        let samples = vec![1.0, 2.0, 3.0, 4.0, 5.0];

        // Push batch
        let pushed = buffer.push_batch(&samples);
        assert_eq!(pushed, 5);
        assert_eq!(buffer.len(), 5);

        // Pop batch
        let mut output = vec![0.0; 3];
        let popped = buffer.pop_batch(&mut output);
        assert_eq!(popped, 3);
        assert_eq!(output, vec![1.0, 2.0, 3.0]);
        assert_eq!(buffer.len(), 2);
    }

    #[test]
    fn test_buffer_full() {
        let buffer = AudioBuffer::with_capacity(2);

        assert!(buffer.push(1.0).is_ok());
        assert!(buffer.push(2.0).is_ok());

        // Buffer is full
        assert!(buffer.push(3.0).is_err());
    }

    #[test]
    fn test_buffer_empty() {
        let buffer = AudioBuffer::new();

        assert!(buffer.is_empty());
        assert_eq!(buffer.pop(), None);
    }

    #[test]
    fn test_buffer_concurrent_access() {
        use std::thread;

        let buffer = AudioBuffer::new();
        let buffer_clone = buffer.clone();

        // Producer thread
        let producer = thread::spawn(move || {
            for i in 0..100 {
                let _ = buffer_clone.push(i as f32);
            }
        });

        // Wait for producer
        producer.join().expect("Producer thread panicked");

        // Consumer thread
        let consumer = thread::spawn(move || {
            let mut count = 0;
            while !buffer.is_empty() {
                if buffer.pop().is_some() {
                    count += 1;
                }
            }
            count
        });

        let consumed = consumer.join().expect("Consumer thread panicked");
        assert_eq!(consumed, 100);
    }
}
