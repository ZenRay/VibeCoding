// Connection state machine for managing WebSocket lifecycle

use std::time::{Duration, Instant};
use thiserror::Error;
use tracing;

#[derive(Debug, Error)]
pub enum StateError {
    #[error("Invalid state transition from {from} to {to}")]
    InvalidTransition {
        from: &'static str,
        to: &'static str,
    },

    #[error("Maximum reconnect attempts reached ({0})")]
    MaxReconnectAttemptsReached(u32),
}

/// Connection states
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ConnectionState {
    /// Not connected
    Disconnected,

    /// Attempting to establish connection
    Connecting,

    /// Connected and listening for speech
    Listening { session_id: String },

    /// Recording and processing audio
    Recording { started_at: Instant },

    /// Processing server response
    Processing,

    /// Committing final transcript
    Committing,

    /// Attempting to reconnect
    Reconnecting { attempt: u32 },

    /// Authentication failed (requires new API key)
    AuthenticationFailed,

    /// Network error occurred
    NetworkError { message: String },
}

impl ConnectionState {
    /// Get the state name as a string
    pub fn name(&self) -> &'static str {
        match self {
            Self::Disconnected => "disconnected",
            Self::Connecting => "connecting",
            Self::Listening { .. } => "listening",
            Self::Recording { .. } => "recording",
            Self::Processing => "processing",
            Self::Committing => "committing",
            Self::Reconnecting { .. } => "reconnecting",
            Self::AuthenticationFailed => "authentication_failed",
            Self::NetworkError { .. } => "network_error",
        }
    }

    /// Check if this is a terminal error state
    pub fn is_error(&self) -> bool {
        matches!(
            self,
            Self::AuthenticationFailed | Self::NetworkError { .. }
        )
    }

    /// Check if currently connected
    pub fn is_connected(&self) -> bool {
        matches!(
            self,
            Self::Listening { .. } | Self::Recording { .. } | Self::Processing | Self::Committing
        )
    }
}

/// State machine for managing connection lifecycle
pub struct StateMachine {
    state: ConnectionState,
    max_reconnect_attempts: u32,
    reconnect_backoff_base: Duration,
    max_backoff: Duration,
}

impl StateMachine {
    /// Create a new state machine
    pub fn new() -> Self {
        Self {
            state: ConnectionState::Disconnected,
            max_reconnect_attempts: 3,
            reconnect_backoff_base: Duration::from_secs(1),
            max_backoff: Duration::from_secs(8),
        }
    }

    /// Get the current state
    pub fn current_state(&self) -> &ConnectionState {
        &self.state
    }

    /// Transition to a new state
    pub fn transition_to(&mut self, new_state: ConnectionState) -> Result<(), StateError> {
        if !self.can_transition_to(&new_state) {
            return Err(StateError::InvalidTransition {
                from: self.state.name(),
                to: new_state.name(),
            });
        }

        tracing::info!(
            event = "state_transition",
            from = self.state.name(),
            to = new_state.name()
        );

        self.state = new_state;
        Ok(())
    }

    /// Check if transition to new state is valid
    fn can_transition_to(&self, new_state: &ConnectionState) -> bool {
        use ConnectionState::*;

        matches!(
            (&self.state, new_state),
            // Normal connection flow
            (Disconnected, Connecting) |
            (Connecting, Listening { .. }) |
            (Listening { .. }, Recording { .. }) |
            (Recording { .. }, Processing) |
            (Recording { .. }, Listening { .. }) | // User stops recording
            (Processing, Recording { .. }) | // Continue recording
            (Processing, Committing) |
            (Committing, Listening { .. }) |
            (Listening { .. }, Disconnected) |

            // Error transitions
            (Connecting, AuthenticationFailed) |
            (Connecting, NetworkError { .. }) |
            (Listening { .. }, NetworkError { .. }) |
            (Recording { .. }, NetworkError { .. }) |
            (Processing, NetworkError { .. }) |
            (Committing, NetworkError { .. }) |

            // Reconnection flow
            (NetworkError { .. }, Reconnecting { .. }) |
            (Reconnecting { .. }, Connecting) |
            (Reconnecting { .. }, Disconnected) |

            // Recovery from errors
            (AuthenticationFailed, Disconnected) |
            (NetworkError { .. }, Disconnected) |

            // Allow disconnection from any state
            (_, Disconnected)
        )
    }

    /// Attempt to reconnect (returns backoff duration)
    pub fn try_reconnect(&mut self) -> Result<Duration, StateError> {
        let attempt = match &self.state {
            ConnectionState::NetworkError { .. } => 1,
            ConnectionState::Reconnecting { attempt } => attempt + 1,
            _ => return Err(StateError::InvalidTransition {
                from: self.state.name(),
                to: "reconnecting",
            }),
        };

        if attempt > self.max_reconnect_attempts {
            return Err(StateError::MaxReconnectAttemptsReached(
                self.max_reconnect_attempts,
            ));
        }

        let backoff = self.calculate_backoff(attempt);

        self.state = ConnectionState::Reconnecting { attempt };

        tracing::info!(
            event = "reconnect_attempt",
            attempt = attempt,
            max_attempts = self.max_reconnect_attempts,
            backoff_ms = backoff.as_millis()
        );

        Ok(backoff)
    }

    /// Calculate exponential backoff duration
    fn calculate_backoff(&self, attempt: u32) -> Duration {
        let backoff = self.reconnect_backoff_base * 2u32.pow(attempt.saturating_sub(1));
        backoff.min(self.max_backoff)
    }

    /// Reset reconnection state
    pub fn reset_reconnect(&mut self) {
        if let ConnectionState::Reconnecting { .. } = self.state {
            self.state = ConnectionState::Disconnected;
        }
    }

    /// Configure reconnection parameters
    pub fn set_reconnect_config(&mut self, max_attempts: u32, base_backoff: Duration) {
        self.max_reconnect_attempts = max_attempts;
        self.reconnect_backoff_base = base_backoff;
    }
}

impl Default for StateMachine {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_state_machine_creation() {
        let sm = StateMachine::new();
        assert_eq!(sm.current_state(), &ConnectionState::Disconnected);
    }

    #[test]
    fn test_normal_connection_flow() {
        let mut sm = StateMachine::new();

        // Disconnected -> Connecting
        assert!(sm.transition_to(ConnectionState::Connecting).is_ok());

        // Connecting -> Listening
        assert!(sm
            .transition_to(ConnectionState::Listening {
                session_id: "test-123".to_string()
            })
            .is_ok());

        // Listening -> Recording
        assert!(sm
            .transition_to(ConnectionState::Recording {
                started_at: Instant::now()
            })
            .is_ok());

        // Recording -> Processing
        assert!(sm.transition_to(ConnectionState::Processing).is_ok());

        // Processing -> Committing
        assert!(sm.transition_to(ConnectionState::Committing).is_ok());

        // Committing -> Listening
        assert!(sm
            .transition_to(ConnectionState::Listening {
                session_id: "test-123".to_string()
            })
            .is_ok());

        // Listening -> Disconnected
        assert!(sm.transition_to(ConnectionState::Disconnected).is_ok());
    }

    #[test]
    fn test_invalid_transitions() {
        let mut sm = StateMachine::new();

        // Cannot go directly from Disconnected to Listening
        assert!(sm
            .transition_to(ConnectionState::Listening {
                session_id: "test".to_string()
            })
            .is_err());

        // Cannot go from Disconnected to Recording
        assert!(sm
            .transition_to(ConnectionState::Recording {
                started_at: Instant::now()
            })
            .is_err());
    }

    #[test]
    fn test_error_states() {
        let mut sm = StateMachine::new();

        sm.transition_to(ConnectionState::Connecting)
            .expect("Failed to transition");

        // Authentication failure from Connecting
        assert!(sm
            .transition_to(ConnectionState::AuthenticationFailed)
            .is_ok());
        assert!(sm.current_state().is_error());

        // Can recover from auth error
        assert!(sm.transition_to(ConnectionState::Disconnected).is_ok());
    }

    #[test]
    fn test_network_error_and_reconnect() {
        let mut sm = StateMachine::new();

        sm.transition_to(ConnectionState::Connecting)
            .expect("Failed");
        sm.transition_to(ConnectionState::Listening {
            session_id: "test".to_string(),
        })
        .expect("Failed");

        // Network error occurs
        assert!(sm
            .transition_to(ConnectionState::NetworkError {
                message: "Connection lost".to_string()
            })
            .is_ok());

        // Try reconnect
        let backoff = sm.try_reconnect().expect("Reconnect should succeed");
        assert_eq!(backoff, Duration::from_secs(1)); // First attempt

        // Verify state
        match sm.current_state() {
            ConnectionState::Reconnecting { attempt } => {
                assert_eq!(*attempt, 1);
            }
            _ => panic!("Expected Reconnecting state"),
        }

        // Try second reconnect
        let backoff2 = sm.try_reconnect().expect("Second reconnect should succeed");
        assert_eq!(backoff2, Duration::from_secs(2)); // Exponential backoff

        // Try third reconnect
        let backoff3 = sm.try_reconnect().expect("Third reconnect should succeed");
        assert_eq!(backoff3, Duration::from_secs(4));

        // Fourth attempt should fail (max 3 attempts)
        let result = sm.try_reconnect();
        assert!(result.is_err());
    }

    #[test]
    fn test_backoff_calculation() {
        let mut sm = StateMachine::new();

        // Need to be in a connected state first
        sm.transition_to(ConnectionState::Connecting).expect("Failed");
        sm.transition_to(ConnectionState::NetworkError {
            message: "Test".to_string(),
        })
        .expect("Failed");

        let backoff1 = sm.try_reconnect().expect("Should succeed");
        assert_eq!(backoff1, Duration::from_secs(1));

        let backoff2 = sm.try_reconnect().expect("Should succeed");
        assert_eq!(backoff2, Duration::from_secs(2));

        let backoff3 = sm.try_reconnect().expect("Should succeed");
        assert_eq!(backoff3, Duration::from_secs(4));
    }

    #[test]
    fn test_max_backoff_cap() {
        let mut sm = StateMachine::new();
        sm.set_reconnect_config(10, Duration::from_secs(1)); // Allow many attempts

        // Need to be in a connected state first
        sm.transition_to(ConnectionState::Connecting).expect("Failed");
        sm.transition_to(ConnectionState::NetworkError {
            message: "Test".to_string(),
        })
        .expect("Failed");

        // Keep reconnecting until we hit max backoff
        for _ in 0..5 {
            let _ = sm.try_reconnect();
        }

        // Should cap at 8 seconds (max_backoff)
        if let ConnectionState::Reconnecting { attempt } = sm.current_state() {
            let backoff = sm.calculate_backoff(*attempt);
            assert!(backoff <= Duration::from_secs(8));
        }
    }

    #[test]
    fn test_custom_reconnect_config() {
        let mut sm = StateMachine::new();
        sm.set_reconnect_config(5, Duration::from_millis(500));

        // Need to be in a connected state first
        sm.transition_to(ConnectionState::Connecting).expect("Failed");
        sm.transition_to(ConnectionState::NetworkError {
            message: "Test".to_string(),
        })
        .expect("Failed");

        let backoff = sm.try_reconnect().expect("Should succeed");
        assert_eq!(backoff, Duration::from_millis(500));
    }

    #[test]
    fn test_state_properties() {
        assert!(!ConnectionState::Disconnected.is_connected());
        assert!(!ConnectionState::Disconnected.is_error());

        assert!(ConnectionState::Listening {
            session_id: "test".to_string()
        }
        .is_connected());
        assert!(!ConnectionState::Listening {
            session_id: "test".to_string()
        }
        .is_error());

        assert!(!ConnectionState::AuthenticationFailed.is_connected());
        assert!(ConnectionState::AuthenticationFailed.is_error());

        assert!(!ConnectionState::NetworkError {
            message: "test".to_string()
        }
        .is_connected());
        assert!(ConnectionState::NetworkError {
            message: "test".to_string()
        }
        .is_error());
    }
}
