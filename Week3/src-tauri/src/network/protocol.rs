// ElevenLabs Scribe v2 WebSocket Protocol
//
// Protocol specification:
// - Connection: wss://api.elevenlabs.io/v1/speech-to-text/realtime
// - Authentication: xi-api-key header
// - Parameters: model_id=scribe_v2_realtime&encoding=pcm_16000

use serde::{Deserialize, Serialize};
use thiserror::Error;

#[derive(Debug, Error)]
pub enum ProtocolError {
    #[error("Serialization error: {0}")]
    SerializationError(String),

    #[error("Deserialization error: {0}")]
    DeserializationError(String),

    #[error("Invalid message type: {0}")]
    InvalidMessageType(String),

    #[error("Base64 encoding error: {0}")]
    Base64Error(String),
}

/// Client-to-server messages
#[derive(Debug, Clone, Serialize)]
#[serde(tag = "message_type", rename_all = "snake_case")]
pub enum ClientMessage {
    /// Send audio data chunk to server
    InputAudioChunk {
        /// Base64-encoded PCM i16 audio data
        audio_base_64: String,
    },
}

impl ClientMessage {
    /// Create an input audio chunk message from PCM i16 samples
    pub fn audio_chunk(samples: &[i16]) -> Result<Self, ProtocolError> {
        // Convert i16 samples to bytes
        let bytes: Vec<u8> = samples
            .iter()
            .flat_map(|&sample| sample.to_le_bytes())
            .collect();

        // Base64 encode
        let audio_base_64 = base64::engine::Engine::encode(
            &base64::engine::general_purpose::STANDARD,
            bytes
        );

        Ok(Self::InputAudioChunk { audio_base_64 })
    }

    /// Serialize to JSON string
    pub fn to_json(&self) -> Result<String, ProtocolError> {
        serde_json::to_string(self)
            .map_err(|e| ProtocolError::SerializationError(e.to_string()))
    }
}

/// Server-to-client messages
#[derive(Debug, Clone, Deserialize)]
#[serde(tag = "message_type", rename_all = "snake_case")]
pub enum ServerMessage {
    /// Session successfully started
    SessionStarted {
        /// Session ID assigned by server
        session_id: String,

        /// Session configuration
        config: SessionConfig,
    },

    /// Partial (real-time) transcript
    PartialTranscript {
        /// Partial transcription text
        text: String,

        /// Timestamp in milliseconds since epoch
        created_at_ms: u64,
    },

    /// Final committed transcript
    CommittedTranscript {
        /// Final transcription text
        text: String,

        /// Confidence score (0.0 - 1.0)
        confidence: f32,

        /// Timestamp in milliseconds since epoch
        created_at_ms: u64,
    },

    /// Input error from client
    InputError {
        /// Error message
        error_message: String,
    },
}

impl ServerMessage {
    /// Parse from JSON string
    pub fn from_json(json: &str) -> Result<Self, ProtocolError> {
        serde_json::from_str(json)
            .map_err(|e| ProtocolError::DeserializationError(e.to_string()))
    }

    /// Get the message type as a string
    pub fn message_type(&self) -> &'static str {
        match self {
            Self::SessionStarted { .. } => "session_started",
            Self::PartialTranscript { .. } => "partial_transcript",
            Self::CommittedTranscript { .. } => "committed_transcript",
            Self::InputError { .. } => "input_error",
        }
    }

    /// Check if this is a final transcript
    pub fn is_final(&self) -> bool {
        matches!(self, Self::CommittedTranscript { .. })
    }

    /// Extract text content if available
    pub fn text(&self) -> Option<&str> {
        match self {
            Self::PartialTranscript { text, .. } => Some(text),
            Self::CommittedTranscript { text, .. } => Some(text),
            _ => None,
        }
    }
}

/// Session configuration returned by server
#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct SessionConfig {
    /// Model ID
    pub model_id: String,

    /// Language code (e.g., "zh", "en", "auto")
    #[serde(default)]
    pub language_code: Option<String>,

    /// Audio encoding format
    #[serde(default)]
    pub encoding: Option<String>,
}

/// Connection configuration for establishing WebSocket
#[derive(Debug, Clone)]
pub struct ConnectionConfig {
    /// API endpoint
    pub endpoint: String,

    /// API key for authentication
    pub api_key: String,

    /// Model ID
    pub model_id: String,

    /// Language code
    pub language_code: String,

    /// Audio encoding
    pub encoding: String,
}

impl Default for ConnectionConfig {
    fn default() -> Self {
        Self {
            endpoint: "wss://api.elevenlabs.io/v1/speech-to-text/realtime".to_string(),
            api_key: String::new(),
            model_id: "scribe_v2_realtime".to_string(),
            language_code: "auto".to_string(),
            encoding: "pcm_16000".to_string(),
        }
    }
}

impl ConnectionConfig {
    /// Build the WebSocket URL with query parameters
    pub fn build_url(&self) -> String {
        format!(
            "{}?model_id={}&language_code={}&encoding={}",
            self.endpoint, self.model_id, self.language_code, self.encoding
        )
    }

    /// Get authentication header value
    pub fn auth_header(&self) -> (&'static str, &str) {
        ("xi-api-key", &self.api_key)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_client_message_serialization() {
        let samples = vec![100i16, -200, 300, -400];
        let message = ClientMessage::audio_chunk(&samples).expect("Failed to create message");

        let json = message.to_json().expect("Failed to serialize");
        assert!(json.contains("\"message_type\":\"input_audio_chunk\""));
        assert!(json.contains("\"audio_base_64\""));
    }

    #[test]
    fn test_server_message_session_started() {
        let json = r#"{
            "message_type": "session_started",
            "session_id": "test-session-123",
            "config": {
                "model_id": "scribe_v2_realtime",
                "language_code": "zh",
                "encoding": "pcm_16000"
            }
        }"#;

        let message = ServerMessage::from_json(json).expect("Failed to parse");

        match message {
            ServerMessage::SessionStarted {
                session_id,
                config,
            } => {
                assert_eq!(session_id, "test-session-123");
                assert_eq!(config.model_id, "scribe_v2_realtime");
            }
            _ => panic!("Expected SessionStarted message"),
        }
    }

    #[test]
    fn test_server_message_partial_transcript() {
        let json = r#"{
            "message_type": "partial_transcript",
            "text": "Hello Wor",
            "created_at_ms": 1706025600000
        }"#;

        let message = ServerMessage::from_json(json).expect("Failed to parse");

        match &message {
            ServerMessage::PartialTranscript { text, .. } => {
                assert_eq!(text, "Hello Wor");
            }
            _ => panic!("Expected PartialTranscript message"),
        }
        assert!(!message.is_final());
        assert_eq!(message.text(), Some("Hello Wor"));
    }

    #[test]
    fn test_server_message_committed_transcript() {
        let json = r#"{
            "message_type": "committed_transcript",
            "text": "Hello World",
            "confidence": 0.98,
            "created_at_ms": 1706025601000
        }"#;

        let message = ServerMessage::from_json(json).expect("Failed to parse");

        match &message {
            ServerMessage::CommittedTranscript {
                text, confidence, ..
            } => {
                assert_eq!(text, "Hello World");
                assert_eq!(*confidence, 0.98);
            }
            _ => panic!("Expected CommittedTranscript message"),
        }
        assert!(message.is_final());
        assert_eq!(message.text(), Some("Hello World"));
    }

    #[test]
    fn test_server_message_input_error() {
        let json = r#"{
            "message_type": "input_error",
            "error_message": "Invalid audio format"
        }"#;

        let message = ServerMessage::from_json(json).expect("Failed to parse");

        match &message {
            ServerMessage::InputError { error_message } => {
                assert_eq!(error_message, "Invalid audio format");
            }
            _ => panic!("Expected InputError message"),
        }
        assert!(!message.is_final());
        assert_eq!(message.text(), None);
    }

    #[test]
    fn test_connection_config_url_building() {
        let config = ConnectionConfig::default();
        let url = config.build_url();

        assert!(url.starts_with("wss://"));
        assert!(url.contains("model_id=scribe_v2_realtime"));
        assert!(url.contains("language_code=auto"));
        assert!(url.contains("encoding=pcm_16000"));
    }

    #[test]
    fn test_connection_config_auth_header() {
        let mut config = ConnectionConfig::default();
        config.api_key = "test-api-key-123".to_string();

        let (header_name, header_value) = config.auth_header();
        assert_eq!(header_name, "xi-api-key");
        assert_eq!(header_value, "test-api-key-123");
    }

    #[test]
    fn test_audio_chunk_encoding() {
        let samples = vec![0i16, i16::MAX, i16::MIN, 100, -200];
        let message = ClientMessage::audio_chunk(&samples).expect("Failed to create message");

        // Verify it serializes without error
        let json = message.to_json().expect("Failed to serialize");

        // Should contain base64 encoded data
        assert!(json.contains("audio_base_64"));
        assert!(!json.contains("null"));
    }
}
