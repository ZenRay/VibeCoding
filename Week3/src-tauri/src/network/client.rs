use crate::network::protocol::{ClientMessage, ConnectionConfig, ProtocolError, ServerMessage};
use base64::Engine;
use futures_util::{SinkExt, StreamExt};
use tokio::io::{AsyncReadExt, AsyncWriteExt};
use thiserror::Error;
use tokio::net::TcpStream;
use tokio_tungstenite::{
    connect_async, client_async_tls_with_config, MaybeTlsStream, WebSocketStream,
    tungstenite::{client::IntoClientRequest, http::HeaderValue},
};
use url::Url;

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
    #[error("Invalid URL: {0}")]
    InvalidUrl(String),
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
        let mut request = url
            .into_client_request()
            .map_err(|e| ClientError::InvalidUrl(e.to_string()))?;
        request.headers_mut().insert(
            "xi-api-key",
            HeaderValue::from_str(&self.config.api_key)
                .map_err(|e| ClientError::ConnectionFailed(e.to_string()))?,
        );
        if let Some(proxy_url) = self.config.proxy_url.as_ref().and_then(|value| Url::parse(value).ok()) {
            return self.connect_via_proxy(request, proxy_url).await;
        }
        let request_for_direct = request.clone();
        match tokio::time::timeout(std::time::Duration::from_secs(6), connect_async(request_for_direct)).await {
            Ok(Ok((stream, _response))) => {
                self.stream = Some(stream);
                return Ok(());
            }
            Ok(Err(err)) => {
                if let Some(proxy_url) = proxy_from_env() {
                    return self.connect_via_proxy(request, proxy_url).await;
                }
                return Err(ClientError::ConnectionFailed(err.to_string()));
            }
            Err(_) => {
                if let Some(proxy_url) = proxy_from_env() {
                    return self.connect_via_proxy(request, proxy_url).await;
                }
                return Err(ClientError::ConnectionFailed("Direct connect timeout".to_string()));
            }
        }
    }

    pub async fn send_audio(&mut self, samples: &[i16]) -> Result<(), ClientError> {
        let message = ClientMessage::audio_chunk(samples, self.config.sample_rate)?;
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

fn proxy_from_env() -> Option<Url> {
    let candidates = [
        "ALL_PROXY",
        "HTTPS_PROXY",
        "HTTP_PROXY",
        "all_proxy",
        "https_proxy",
        "http_proxy",
    ];
    for key in candidates {
        if let Ok(value) = std::env::var(key) {
            if value.trim().is_empty() {
                continue;
            }
            if let Ok(url) = Url::parse(value.trim()) {
                return Some(url);
            }
        }
    }
    None
}

impl ScribeClient {
    async fn connect_via_proxy(
        &mut self,
        request: tokio_tungstenite::tungstenite::http::Request<()>,
        proxy_url: Url,
    ) -> Result<(), ClientError> {
        let scheme = proxy_url.scheme();
        match scheme {
            "socks5" | "socks5h" => {
                let host = proxy_url
                    .host_str()
                    .ok_or_else(|| ClientError::ConnectionFailed("Proxy host missing".to_string()))?;
                let port = proxy_url.port_or_known_default().unwrap_or(1080);
                let target = request
                    .uri()
                    .host()
                    .ok_or_else(|| ClientError::InvalidUrl("Target host missing".to_string()))?;
                let target_port = request
                    .uri()
                    .port_u16()
                    .unwrap_or(443);
                let stream = tokio_socks::tcp::Socks5Stream::connect(
                    (host, port),
                    (target, target_port),
                )
                .await
                .map_err(|e| ClientError::ConnectionFailed(e.to_string()))?
                .into_inner();
                let (ws_stream, _response) =
                    client_async_tls_with_config(request, stream, None, None)
                        .await
                        .map_err(|e| ClientError::ConnectionFailed(e.to_string()))?;
                self.stream = Some(ws_stream);
                Ok(())
            }
            "http" | "https" => {
                let proxy_host = proxy_url
                    .host_str()
                    .ok_or_else(|| ClientError::ConnectionFailed("Proxy host missing".to_string()))?;
                let proxy_port = proxy_url.port_or_known_default().unwrap_or(8080);
                let target_host = request
                    .uri()
                    .host()
                    .ok_or_else(|| ClientError::InvalidUrl("Target host missing".to_string()))?;
                let target_port = request.uri().port_u16().unwrap_or(443);
                let mut stream = TcpStream::connect((proxy_host, proxy_port))
                    .await
                    .map_err(|e| ClientError::ConnectionFailed(e.to_string()))?;
                let mut connect_request = format!(
                    "CONNECT {target}:{port} HTTP/1.1\r\nHost: {target}:{port}\r\n",
                    target = target_host,
                    port = target_port
                );
                if let Some(auth) = proxy_basic_auth(&proxy_url) {
                    connect_request.push_str(&format!("Proxy-Authorization: Basic {auth}\r\n"));
                }
                connect_request.push_str("\r\n");
                stream
                    .write_all(connect_request.as_bytes())
                    .await
                    .map_err(|e| ClientError::ConnectionFailed(e.to_string()))?;
                let mut response = Vec::new();
                let mut buf = [0u8; 1024];
                loop {
                    let read = stream
                        .read(&mut buf)
                        .await
                        .map_err(|e| ClientError::ConnectionFailed(e.to_string()))?;
                    if read == 0 {
                        break;
                    }
                    response.extend_from_slice(&buf[..read]);
                    if response.windows(4).any(|w| w == b"\r\n\r\n") {
                        break;
                    }
                    if response.len() > 8192 {
                        break;
                    }
                }
                let response_str = String::from_utf8_lossy(&response);
                if !response_str.starts_with("HTTP/1.1 200")
                    && !response_str.starts_with("HTTP/1.0 200")
                {
                    return Err(ClientError::ConnectionFailed(format!(
                        "Proxy CONNECT failed: {response_str}"
                    )));
                }
                let (ws_stream, _response) =
                    client_async_tls_with_config(request, stream, None, None)
                        .await
                        .map_err(|e| ClientError::ConnectionFailed(e.to_string()))?;
                self.stream = Some(ws_stream);
                Ok(())
            }
            _ => Err(ClientError::ConnectionFailed(format!(
                "Unsupported proxy scheme: {scheme}"
            ))),
        }
    }
}

fn proxy_basic_auth(proxy_url: &Url) -> Option<String> {
    let user = proxy_url.username();
    if user.is_empty() {
        return None;
    }
    let password = proxy_url.password().unwrap_or("");
    let raw = format!("{user}:{password}");
    Some(base64::engine::general_purpose::STANDARD.encode(raw.as_bytes()))
}
