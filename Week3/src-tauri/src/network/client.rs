use crate::network::protocol::{ClientMessage, ConnectionConfig, ProtocolError, ServerMessage};
use futures_util::{SinkExt, StreamExt};
use thiserror::Error;
use tokio::net::TcpStream;
use tokio_tungstenite::{connect_async, MaybeTlsStream, WebSocketStream};

#[derive(Debug, Error)]
pub enum ClientError {
    #[error("WebSocket connection failed: {0}")]
    ConnectionFailed(String),
    #[error("WebSocket send error: {0}")]
    SendError(String),
    #[error("WebSocket receive error: {0}")]
    ReceiveError(String),
    #[error("Protocol error: {0}")]
    ProtocolError(#[from] ProtocolError),
}

pub type WsStream = WebSocketStream<MaybeTlsStream<TcpStream>>;

pub struct ScribeClient {
    stream: Option<WsStream>,
    config: ConnectionConfig,
}

impl ScribeClient {
    pub fn new(config: ConnectionConfig) -> Self {
        Self {
            stream: None,
            config,
        }
    }

    pub async fn connect(&mut self) -> Result<(), ClientError> {
        let url = self.config.build_url();
        let (stream, _response) = connect_async(url)
            .await
            .map_err(|e| ClientError::ConnectionFailed(e.to_string()))?;
        self.stream = Some(stream);
        Ok(())
    }

    pub async fn send_audio(&mut self, samples: &[i16]) -> Result<(), ClientError> {
        let message = ClientMessage::audio_chunk(samples)?;
        self.send_message(&message).await
    }

    async fn send_message(&mut self, message: &ClientMessage) -> Result<(), ClientError> {
        let stream = self
            .stream
            .as_mut()
            .ok_or_else(|| ClientError::SendError("Not connected".to_string()))?;
        let json = message.to_json()?;
        stream
            .send(tokio_tungstenite::tungstenite::Message::Text(json.into()))
            .await
            .map_err(|e| ClientError::SendError(e.to_string()))?;
        Ok(())
    }

    pub async fn receive(&mut self) -> Result<ServerMessage, ClientError> {
        let stream = self
            .stream
            .as_mut()
            .ok_or_else(|| ClientError::ReceiveError("Not connected".to_string()))?;
        match stream.next().await {
            Some(Ok(tokio_tungstenite::tungstenite::Message::Text(text))) => {
                Ok(ServerMessage::from_json(&text)?)
            }
            Some(Ok(_)) => Err(ClientError::ReceiveError("Unsupported message".to_string())),
            Some(Err(e)) => Err(ClientError::ReceiveError(e.to_string())),
            None => Err(ClientError::ReceiveError("Stream closed".to_string())),
        }
    }
}
