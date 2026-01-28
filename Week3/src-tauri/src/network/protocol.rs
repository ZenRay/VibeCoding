use serde::Serialize;
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
    pub audio_format: String,
    pub sample_rate: u32,
    pub commit_strategy: String,
    pub language_code: Option<String>,
    pub proxy_url: Option<String>,
}

impl ConnectionConfig {
    pub fn build_url(&self) -> String {
        let mut url = format!(
            "{endpoint}?model_id={model_id}&audio_format={audio_format}&commit_strategy={commit_strategy}",
            endpoint = self.endpoint,
            model_id = self.model_id,
            audio_format = self.audio_format,
            commit_strategy = self.commit_strategy
        );
        if let Some(language) = &self.language_code {
            url.push_str("&language_code=");
            url.push_str(language);
        }
        url
    }
}

#[derive(Debug, Clone, Serialize)]
#[serde(tag = "message_type", rename_all = "snake_case")]
pub enum ClientMessage {
    InputAudioChunk {
        audio_base_64: String,
        sample_rate: u32,
        #[serde(skip_serializing_if = "Option::is_none")]
        commit: Option<bool>,
        #[serde(skip_serializing_if = "Option::is_none")]
        previous_text: Option<String>,
    },
}

impl ClientMessage {
    pub fn audio_chunk(samples: &[i16], sample_rate: u32) -> Result<Self, ProtocolError> {
        let bytes: Vec<u8> = samples.iter().flat_map(|s| s.to_le_bytes()).collect();
        let audio_base_64 = base64::engine::general_purpose::STANDARD.encode(bytes);
        Ok(Self::InputAudioChunk {
            audio_base_64,
            sample_rate,
            commit: None,
            previous_text: None,
        })
    }

    pub fn to_json(&self) -> Result<String, ProtocolError> {
        serde_json::to_string(self).map_err(|e| ProtocolError::SerializationError(e.to_string()))
    }
}

#[derive(Debug, Clone)]
pub enum ServerMessage {
    SessionStarted { session_id: String },
    PartialTranscript { text: String },
    CommittedTranscript { text: String },
    Error { message_type: String, message: String },
    Unknown { message_type: String, raw: serde_json::Value },
}

impl ServerMessage {
    pub fn from_json(input: &str) -> Result<Self, ProtocolError> {
        let value: serde_json::Value =
            serde_json::from_str(input).map_err(|e| ProtocolError::DeserializationError(e.to_string()))?;
        let message_type = value
            .get("message_type")
            .and_then(|v| v.as_str())
            .unwrap_or("unknown")
            .to_string();
        match message_type.as_str() {
            "session_started" => {
                let session_id = value
                    .get("session_id")
                    .and_then(|v| v.as_str())
                    .ok_or_else(|| {
                        ProtocolError::DeserializationError("missing session_id".to_string())
                    })?;
                Ok(Self::SessionStarted {
                    session_id: session_id.to_string(),
                })
            }
            "partial_transcript" => {
                let text = value
                    .get("text")
                    .and_then(|v| v.as_str())
                    .ok_or_else(|| {
                        ProtocolError::DeserializationError("missing text".to_string())
                    })?;
                Ok(Self::PartialTranscript {
                    text: text.to_string(),
                })
            }
            "committed_transcript" | "committed_transcript_with_timestamps" => {
                let text = value
                    .get("text")
                    .and_then(|v| v.as_str())
                    .ok_or_else(|| {
                        ProtocolError::DeserializationError("missing text".to_string())
                    })?;
                Ok(Self::CommittedTranscript {
                    text: text.to_string(),
                })
            }
            other if other.ends_with("_error") => {
                let message = value
                    .get("message")
                    .and_then(|v| v.as_str())
                    .unwrap_or("unknown error")
                    .to_string();
                Ok(Self::Error {
                    message_type: other.to_string(),
                    message,
                })
            }
            other => Ok(Self::Unknown {
                message_type: other.to_string(),
                raw: value,
            }),
        }
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
            audio_format: "pcm_16000".to_string(),
            sample_rate: 16_000,
            commit_strategy: "vad".to_string(),
            language_code: None,
            proxy_url: None,
        };
        let url = config.build_url();
        assert!(url.contains("model_id=scribe"));
        assert!(url.contains("audio_format=pcm_16000"));
        assert!(url.contains("commit_strategy=vad"));
    }

    #[test]
    fn client_message_serializes() {
        let msg = match ClientMessage::audio_chunk(&[1, 2, 3], 16_000) {
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
