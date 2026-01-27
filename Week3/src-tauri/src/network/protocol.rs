use serde::{Deserialize, Serialize};
use base64::Engine;
use thiserror::Error;

#[derive(Debug, Error)]
pub enum ProtocolError {
    #[error("Serialization error: {0}")]
    SerializationError(String),
    #[error("Deserialization error: {0}")]
    DeserializationError(String),
}

#[derive(Debug, Clone)]
pub struct ConnectionConfig {
    pub endpoint: String,
    pub api_key: String,
    pub model_id: String,
    pub encoding: String,
}

impl ConnectionConfig {
    pub fn build_url(&self) -> String {
        format!(
            "{endpoint}?model_id={model_id}&encoding={encoding}",
            endpoint = self.endpoint,
            model_id = self.model_id,
            encoding = self.encoding
        )
    }
}

#[derive(Debug, Clone, Serialize)]
#[serde(tag = "message_type", rename_all = "snake_case")]
pub enum ClientMessage {
    InputAudioChunk { audio_base_64: String },
}

impl ClientMessage {
    pub fn audio_chunk(samples: &[i16]) -> Result<Self, ProtocolError> {
        let bytes: Vec<u8> = samples.iter().flat_map(|s| s.to_le_bytes()).collect();
        let audio_base_64 = base64::engine::general_purpose::STANDARD.encode(bytes);
        Ok(Self::InputAudioChunk { audio_base_64 })
    }

    pub fn to_json(&self) -> Result<String, ProtocolError> {
        serde_json::to_string(self).map_err(|e| ProtocolError::SerializationError(e.to_string()))
    }
}

#[derive(Debug, Clone, Deserialize)]
#[serde(tag = "message_type", rename_all = "snake_case")]
pub enum ServerMessage {
    SessionStarted { session_id: String },
    PartialTranscript { text: String },
    CommittedTranscript { text: String },
}

impl ServerMessage {
    pub fn from_json(input: &str) -> Result<Self, ProtocolError> {
        serde_json::from_str(input).map_err(|e| ProtocolError::DeserializationError(e.to_string()))
    }
}

#[cfg(test)]
mod tests {
    use super::{ClientMessage, ConnectionConfig, ServerMessage};

    #[test]
    fn connection_url_contains_params() {
        let config = ConnectionConfig {
            endpoint: "wss://example.test/rt".to_string(),
            api_key: "key".to_string(),
            model_id: "scribe".to_string(),
            encoding: "pcm_16000".to_string(),
        };
        let url = config.build_url();
        assert!(url.contains("model_id=scribe"));
        assert!(url.contains("encoding=pcm_16000"));
    }

    #[test]
    fn client_message_serializes() {
        let msg = match ClientMessage::audio_chunk(&[1, 2, 3]) {
            Ok(message) => message,
            Err(_) => {
                assert!(false, "encode failed");
                return;
            }
        };
        let json = match msg.to_json() {
            Ok(value) => value,
            Err(_) => {
                assert!(false, "json failed");
                return;
            }
        };
        assert!(json.contains("input_audio_chunk"));
    }

    #[test]
    fn server_message_parses() {
        let json = r#"{"message_type":"partial_transcript","text":"hello"}"#;
        let msg = match ServerMessage::from_json(json) {
            Ok(message) => message,
            Err(_) => {
                assert!(false, "parse failed");
                return;
            }
        };
        match msg {
            ServerMessage::PartialTranscript { text } => assert_eq!(text, "hello"),
            _ => panic!("unexpected message"),
        }
    }
}
