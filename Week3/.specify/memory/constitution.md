<!--
Sync Impact Report:
Version: 1.0.0 (Initial Constitution)
Modified Principles: N/A (Initial creation)
Added Sections: All sections (Core Principles I-VII, Technology Standards, Development Workflow, Governance)
Removed Sections: N/A
Templates Requiring Updates:
  ✅ .specify/templates/plan-template.md - Constitution Check section placeholder ready
  ✅ .specify/templates/spec-template.md - User scenarios and requirements align with principles
  ✅ .specify/templates/tasks-template.md - Task categorization supports principle-driven development
Follow-up TODOs: None
-->

# ScribeFlow Desktop Voice System Constitution

**Project Root**: `~/Documents/VibeCoding/Week3`
**Specification**: `~/Documents/VibeCoding/specs/001-scribeflow-voice-system`
**Branch**: `001-scribeflow-voice-system`

## Core Principles

### I. Rust-First Safety & Performance (NON-NEGOTIABLE)

**Declaration**: All system-critical code MUST be written in Rust with zero `unsafe` blocks and zero use of `.unwrap()` or `.expect()`.

**Rationale**: Audio processing, real-time networking, and system integration require memory safety guarantees and predictable performance. Any garbage collection pause in the audio callback path causes audible artifacts. Rust's ownership model eliminates entire classes of bugs (data races, null pointer dereferences, buffer overflows) that are unacceptable in a system-level tool handling sensitive user input.

**Rules**:
- Rust 2024 edition MUST be used for all new code
- Audio processing threads MUST NOT allocate memory in callback paths
- All errors MUST be properly handled via `Result<T, E>` and propagated or logged
- WebSocket and audio streams MUST use async/await with tokio runtime
- Performance-critical paths MUST avoid mutex contention (prefer `ArcSwap` for config, `DashMap` for concurrent maps)

### II. Real-Time First Architecture

**Declaration**: System architecture MUST prioritize sub-200ms end-to-end latency for the voice-to-text-to-input pipeline.

**Rationale**: The user experience hinges on the perception of "instant" transcription. Any delay beyond 200ms feels laggy and breaks the natural flow of dictation. This requires careful engineering of every layer: audio capture, network transmission, text injection.

**Rules**:
- Audio MUST be captured with <10ms buffer windows
- WebSocket MUST maintain persistent connections (no cold-start per hotkey)
- Base64 encoding and JSON serialization MUST occur off the audio thread
- Text injection MUST complete within 50ms of receiving `committed_transcript` event
- All I/O operations MUST be non-blocking and use async/await patterns

### III. Privacy & Security by Design

**Declaration**: User voice data and transcribed text MUST be treated as highly sensitive. No data MUST be logged, cached, or transmitted except to the explicitly configured ASR endpoint.

**Rationale**: Voice dictation captures passwords, confidential communications, and personal information. A single privacy breach destroys user trust.

**Rules**:
- Audio buffers MUST be zeroed immediately after transmission
- API keys MUST be stored in system keychain (not plaintext config files)
- No transcription history MUST be persisted to disk without explicit user opt-in
- All network communication MUST use TLS/WSS
- Clipboard operations MUST restore previous content after paste injection
- macOS Accessibility API calls MUST be minimized and documented

### IV. Tauri v2 Plugin Architecture

**Declaration**: All system integration features (global hotkeys, clipboard, audio, text injection) MUST be implemented as Tauri plugins with explicit capability declarations.

**Rationale**: Tauri v2's permission model ensures the frontend cannot abuse system APIs. Plugins provide clear separation of concerns and enable independent testing of system integrations.

**Rules**:
- Every plugin MUST declare minimum required permissions in `capabilities/*.json`
- Frontend MUST NOT directly access Rust functions without ACL grants
- Plugins MUST expose both Tauri commands (frontend-invoked) and Rust APIs (backend-invoked)
- System tray, global shortcuts, and background execution MUST be configured declaratively
- Window management (overlay, focus handling) MUST respect platform-specific quirks (macOS App Nap, focus stealing)

### V. Test-Driven System Integration

**Declaration**: All system-level integrations (audio capture, WebSocket protocol, text injection) MUST have automated contract tests before implementation.

**Rationale**: System integration bugs are notoriously difficult to debug in production. Automated tests catch protocol violations, platform-specific issues, and regression early.

**Rules**:
- Audio pipeline tests MUST verify resampling accuracy (48kHz → 16kHz) within 0.1% error
- WebSocket tests MUST verify message sequencing (`session_started` → `partial_transcript` → `committed_transcript`)
- Text injection tests MUST verify focus management and clipboard restoration
- Permission checks (macOS Accessibility) MUST fail gracefully with user-actionable errors
- Integration tests MUST run on CI for macOS (primary target platform)

### VI. Minimal Dependencies, Maximum Auditability

**Declaration**: Every external dependency MUST be justified by necessity and verified via official documentation. Prefer standard library and well-audited crates.

**Rationale**: Audio and system access crates can introduce supply chain risks. Every dependency increases binary size and complicates security audits.

**Rules**:
- Always use latest stable versions of dependencies
- Verify crate APIs by visiting official documentation pages before use
- Prefer smaller, focused crates over large frameworks (e.g., `cpal` over `rodio`)
- Document why each dependency was chosen over alternatives in `Cargo.toml` comments
- Never use native async trait support (not `async_trait` crate)

### VII. Observability & Debuggability

**Declaration**: All state transitions (audio stream start/stop, WebSocket connection lifecycle, text injection attempts) MUST emit structured logs.

**Rationale**: When a user reports "it didn't work," logs are the only window into what happened. Structured logs enable filtering by component and correlation across the pipeline.

**Rules**:
- Use `tracing` crate with levels: ERROR (user-blocking), WARN (degraded), INFO (state changes), DEBUG (diagnostic)
- Every WebSocket event MUST log at INFO level with message type and truncated payload
- Audio buffer statistics (dropped frames, resampling errors) MUST be tracked and logged
- Text injection failures MUST log target application context (app name, window title if available)
- Logs MUST NOT contain full transcription text (privacy violation)

## Technology Standards

### Mandatory Stack

- **Framework**: Tauri v2 with Rust backend, system WebView frontend
- **Audio**: `cpal` v0.15+ for cross-platform audio I/O
- **Resampling**: `rubato` v0.14+ for high-quality 48kHz → 16kHz conversion
- **Networking**: `tokio-tungstenite` with `rustls` for WebSocket over TLS
- **ASR Service**: ElevenLabs Scribe v2 Realtime API (model: `scribe_v2_realtime`)
- **System Integration**: Platform-specific (macOS: Accessibility API via `enigo`, `active-win-pos-rs`)

### Prohibited Patterns

- **No Electron**: Tauri's native WebView reduces memory footprint by 10x
- **No Local Whisper**: Real-time requires <150ms latency; local inference cannot compete
- **No HTTP Polling**: WebSocket full-duplex is mandatory for streaming audio and receiving partial transcripts
- **No `.unwrap()` / `.expect()`**: All errors MUST be handled explicitly

### Performance Targets

- Cold start (app launch → ready for hotkey): <500ms
- Hotkey to first audio capture: <50ms
- Audio buffer latency: <10ms per chunk
- WebSocket round-trip (audio sent → partial transcript received): <150ms (network dependent)
- Text injection latency: <50ms
- Memory footprint (idle): <50MB
- Memory footprint (active transcription): <100MB

## Development Workflow

### Code Quality Gates

All pull requests MUST pass before merge:
1. `cargo clippy` with zero warnings
2. `cargo fmt --check` (code formatted)
3. `cargo test` (all unit and integration tests pass)
4. Manual test of audio capture → transcription → text injection on macOS
5. Verify no `.unwrap()`, `.expect()`, or `unsafe` introduced

### Documentation Requirements

- Every public function in Rust MUST have a doc comment explaining purpose and invariants
- Every Tauri plugin MUST have a README documenting required permissions and setup
- Architecture decisions (e.g., "Why persistent WebSocket?") MUST be documented in `docs/adr/`
- API protocol details (ElevenLabs message formats) MUST be captured in `docs/api-reference.md`

### Commit Conventions

- Conventional Commits format: `type(scope): description`
- Types: `feat`, `fix`, `perf`, `refactor`, `test`, `docs`, `chore`
- Scopes: `audio`, `network`, `injection`, `ui`, `build`
- Example: `feat(audio): implement 48kHz to 16kHz resampling with rubato`

## Governance

### Amendment Process

1. Proposed changes to this constitution MUST be documented in a PR to `.specify/memory/constitution.md`
2. Changes MUST include updated version number and rationale in Sync Impact Report
3. Changes MUST update dependent templates (plan, spec, tasks) in same PR
4. Amendment requires explicit approval from project maintainer
5. Migration plan required if changes affect existing code

### Versioning Policy

**Version format**: `MAJOR.MINOR.PATCH`

- **MAJOR**: Backward-incompatible governance change (e.g., removing a core principle, changing mandatory technology)
- **MINOR**: New principle added or existing principle materially expanded
- **PATCH**: Clarifications, wording improvements, typo fixes, non-semantic refinements

### Compliance Verification

- All PRs MUST reference which principles they uphold
- Code review MUST verify no principles are violated
- Complexity that violates principles MUST be justified in plan.md Complexity Tracking table
- Annual audit of codebase against constitution (check for `.unwrap()`, `unsafe`, etc.)

### Living Document

- This constitution supersedes all prior undocumented practices
- When ambiguity arises, constitution takes precedence over convenience
- Use `CLAUDE.md` for runtime development guidance (tool preferences, common commands)
- Use this constitution for governance and architectural invariants

**Version**: 1.0.0 | **Ratified**: 2026-01-24 | **Last Amended**: 2026-01-24
