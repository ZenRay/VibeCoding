// WebSocket client for ElevenLabs Scribe v2 API

use futures_util::{SinkExt, StreamExt};
use tokio::net::TcpStream;
use tokio_tungstenite::{
    connect_async, MaybeTlsStream, WebSocketStream,
    tungstenite::{
        client::IntoClientRequest,
        http::HeaderValue,
        Message,
        Error as TungsteniteError,
    },
};
use thiserror::Error;
use tracing;

use super::protocol::{ClientMessage, ConnectionConfig, ProtocolError, ServerMessage};

#[derive(Debug, Error)]
pub enum ClientError {
    #[error("WebSocket connection failed: {0}")]
    ConnectionFailed(String),

    #[error("WebSocket send error: {0}")]
    SendError(String),

    #[error("WebSocket receive error: {0}")]
    ReceiveError(String),

    #[error("Connection closed")]
    ConnectionClosed,

    #[error("Protocol error: {0}")]
    ProtocolError(#[from] ProtocolError),

    #[error("Invalid URL: {0}")]
    InvalidUrl(String),

    #[error("Authentication failed (401)")]
    AuthenticationFailed,

    #[error("Rate limit exceeded (429)")]
    RateLimitExceeded,

    #[error("Server error: {0}")]
    ServerError(String),
}

pub type WsStream = WebSocketStream<MaybeTlsStream<TcpStream>>;

/// WebSocket client for ElevenLabs Scribe API
pub struct ScribeClient {
    stream: Option<WsStream>,
    config: ConnectionConfig,
    session_id: Option<String>,
}

impl ScribeClient {
    /// Create a new client with the given configuration
    pub fn new(config: ConnectionConfig) -> Self {
        Self {
            stream: None,
            config,
            session_id: None,
        }
    }

    /// Connect to the WebSocket server
    pub async fn connect(&mut self) -> Result<(), ClientError> {
        // Build WebSocket URL
        let url = self.config.build_url();

        tracing::info!(
            event = "websocket_connecting",
            url = %url
        );

        // Create request with authentication header
        let mut request = url
            .into_client_request()
            .map_err(|e| ClientError::InvalidUrl(e.to_string()))?;

        let (header_name, header_value) = self.config.auth_header();
        request.headers_mut().insert(
            header_name,
            HeaderValue::from_str(header_value)
                .map_err(|e| ClientError::ConnectionFailed(e.to_string()))?,
        );

        // Establish WebSocket connection
        let (ws_stream, response) = connect_async(request)
            .await
            .map_err(|e| {
                match e {
                    tokio_tungstenite::tungstenite::Error::Http(resp) => {
                        let status = resp.status();
                        if status == 401 {
                            ClientError::AuthenticationFailed
                        } else if status == 429 {
                            ClientError::RateLimitExceeded
                        } else {
                            ClientError::ServerError(format!("HTTP {}", status))
                        }
                    }
                    _ => ClientError::ConnectionFailed(e.to_string())
                }
            })?;

        tracing::info!(
            event = "websocket_connected",
            status = response.status().as_u16()
        );

        self.stream = Some(ws_stream);

        Ok(())
    }

    /// Disconnect from the server
    pub async fn disconnect(&mut self) -> Result<(), ClientError> {
        if let Some(mut stream) = self.stream.take() {
            let _ = stream.send(Message::Close(None)).await;
            tracing::info!(event = "websocket_disconnected");
        }
        self.session_id = None;
        Ok(())
    }

    /// Send audio chunk to server
    pub async fn send_audio(&mut self, samples: &[i16]) -> Result<(), ClientError> {
        let message = ClientMessage::audio_chunk(samples)?;
        self.send_client_message(&message).await
    }

    /// Send a client message to the server
    async fn send_client_message(&mut self, message: &ClientMessage) -> Result<(), ClientError> {
        let stream = self
            .stream
            .as_mut()
            .ok_or(ClientError::ConnectionClosed)?;

        let json = message.to_json()?;

        stream
            .send(Message::Text(json.into()))
            .await
            .map_err(|e: TungsteniteError| ClientError::SendError(e.to_string()))?;

        Ok(())
    }

    /// Receive a server message
    pub async fn receive(&mut self) -> Result<ServerMessage, ClientError> {
        let stream = self
            .stream
            .as_mut()
            .ok_or(ClientError::ConnectionClosed)?;

        match stream.next().await {
            Some(Ok(Message::Text(text))) => {
                let message = ServerMessage::from_json(&text)?;

                // Store session ID if this is session_started
                if let ServerMessage::SessionStarted { ref session_id, .. } = message {
                    self.session_id = Some(session_id.clone());
                    tracing::info!(
                        event = "session_started",
                        session_id = %session_id
                    );
                }

                Ok(message)
            }
            Some(Ok(Message::Close(_))) => {
                tracing::warn!(event = "websocket_closed_by_server");
                Err(ClientError::ConnectionClosed)
            }
            Some(Ok(msg)) => {
                tracing::warn!(event = "unexpected_websocket_message", message_type = ?msg);
                Err(ClientError::ReceiveError(format!(
                    "Unexpected message type: {:?}",
                    msg
                )))
            }
            Some(Err(e)) => {
                let error_msg = format!("{}", e);
                tracing::error!(event = "websocket_receive_error", error = %error_msg);
                Err(ClientError::ReceiveError(error_msg))
            }
            None => {
                tracing::warn!(event = "websocket_stream_ended");
                Err(ClientError::ConnectionClosed)
            }
        }
    }

    /// Get the session ID (available after receiving session_started)
    pub fn session_id(&self) -> Option<&str> {
        self.session_id.as_deref()
    }

    /// Check if connected
    pub fn is_connected(&self) -> bool {
        self.stream.is_some()
    }

    /// Get the connection configuration
    pub fn config(&self) -> &ConnectionConfig {
        &self.config
    }
}

impl Drop for ScribeClient {
    fn drop(&mut self) {
        // Ensure we clean up the connection
        // Note: We can't use async in Drop, so just drop the stream
        // The WebSocket will be closed when the stream is dropped
        self.stream = None;
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_client_creation() {
        let config = ConnectionConfig::default();
        let client = ScribeClient::new(config);

        assert!(!client.is_connected());
        assert_eq!(client.session_id(), None);
    }

    #[tokio::test]
    #[ignore] // Requires valid API key and network
    async fn test_client_connect() {
        let mut config = ConnectionConfig::default();
        config.api_key = std::env::var("ELEVENLABS_API_KEY")
            .expect("ELEVENLABS_API_KEY not set");

        let mut client = ScribeClient::new(config);
        let result = client.connect().await;

        assert!(result.is_ok(), "Connection failed: {:?}", result.err());
        assert!(client.is_connected());
    }

    #[tokio::test]
    #[ignore] // Requires valid API key and network
    async fn test_client_session_flow() {
        let mut config = ConnectionConfig::default();
        config.api_key = std::env::var("ELEVENLABS_API_KEY")
            .expect("ELEVENLABS_API_KEY not set");

        let mut client = ScribeClient::new(config);
        client.connect().await.expect("Failed to connect");

        // Should receive session_started message
        match client.receive().await {
            Ok(ServerMessage::SessionStarted { .. }) => {
                assert!(client.session_id().is_some());
            }
            Ok(other) => panic!("Expected SessionStarted, got: {:?}", other),
            Err(e) => panic!("Failed to receive session_started: {}", e),
        }

        // Send some audio
        let samples = vec![0i16; 1600]; // 100ms @ 16kHz
        assert!(client.send_audio(&samples).await.is_ok());

        client.disconnect().await.expect("Failed to disconnect");
        assert!(!client.is_connected());
    }

    #[tokio::test]
    #[ignore] // Requires network connectivity to test
    async fn test_client_invalid_api_key() {
        let mut config = ConnectionConfig::default();
        config.api_key = "invalid-api-key".to_string();

        let mut client = ScribeClient::new(config);
        let result = client.connect().await;

        assert!(result.is_err());
        // Expected: AuthenticationFailed (401) or ConnectionFailed (network error)
    }
}
