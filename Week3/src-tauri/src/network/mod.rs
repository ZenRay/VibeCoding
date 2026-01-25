// Network communication module

pub mod client;
pub mod protocol;
pub mod state_machine;

pub use client::{ClientError, ScribeClient, WsStream};
pub use protocol::{ClientMessage, ConnectionConfig, ProtocolError, ServerMessage, SessionConfig};
pub use state_machine::{ConnectionState, StateError, StateMachine};
