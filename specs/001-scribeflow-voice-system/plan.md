# Implementation Plan: ScribeFlow 桌面实时语音听写系统

**Branch**: `001-scribeflow-voice-system` | **Date**: 2026-01-24 | **Spec**: [spec.md](./spec.md)
**Project Root**: `~/Documents/VibeCoding/Week3`
**Implementation Location**: `~/Documents/VibeCoding/Week3` (源代码将在此创建)
**Spec Location**: `~/Documents/VibeCoding/specs/001-scribeflow-voice-system`

**Input**: Feature specification from `/specs/001-scribeflow-voice-system/spec.md`

## Summary

ScribeFlow 是一个基于 Tauri v2 和 ElevenLabs Scribe v2 API 的桌面实时语音听写工具。用户通过全局快捷键 (`Cmd+Shift+\`) 激活语音输入,系统实时将语音转换为文本并自动插入到当前活跃应用的光标位置。核心技术挑战包括:超低延迟音频处理管道(<200ms 端到端)、高精度音频重采样(48kHz → 16kHz)、跨应用文本注入、macOS 系统权限管理。

**技术方法**: 采用 Rust 后端处理音频采集和 WebSocket 通信,使用 React 前端实现悬浮窗 UI,通过 Tauri v2 插件系统集成系统级功能(全局热键、剪贴板、Accessibility API)。音频采集使用独立高优先级线程,通过 mpsc 通道传递数据到 Tokio 异步运行时,确保零内存分配的实时安全性。

## Technical Context

**Language/Version**: Rust 2024 edition (MSRV 1.77), TypeScript 5.3
**Primary Dependencies**:
- Backend: `tauri` 2.9, `cpal` 0.16, `rubato` 0.16.2, `tokio-tungstenite` 0.28, `enigo` 0.6.1, `keyring` 2.3
- Frontend: `@tauri-apps/api` 2.1, `react` 19.2, `zustand` 5.0.8
**Storage**:
- API 密钥: `keyring-rs` (macOS Keychain / Linux Secret Service / Windows Credential Manager)
- 用户配置: `tauri-plugin-store` (跨平台 JSON)
**Testing**: `cargo test` (Rust 单元测试 + 集成测试), Vitest (前端)
**Target Platform**:
- **Tier 1**: macOS 10.15+, Linux X11 (Ubuntu 22.04+, Fedora 38+)
- **Tier 2**: Linux Wayland (功能降级)
- **Tier 3**: Windows 11 (计划中)
**Project Type**: 桌面应用 (Tauri v2 跨平台架构)
**Performance Goals**:
- 端到端延迟 <200ms (语音停止 → 文本插入)
- 冷启动时间 <500ms (应用启动 → 可响应热键)
- 音频重采样精度误差 <0.1%
- WebSocket 连接成功率 >99%
**Constraints**:
- 内存占用 <50MB (空闲), <100MB (活跃转写)
- 音频采集线程禁止内存分配和 I/O 操作
- 零 `unsafe` 代码,零 `.unwrap()` / `.expect()`
- 所有音频流仅用于实时转写,不得持久化存储
**Scale/Scope**:
- 单用户桌面应用
- 7 个核心实体 (AudioStream, TranscriptionSession, TranscriptEvent, OverlayWindow, AppConfig, ActiveWindow, WebSocketConnection)
- 25 个功能需求 (FR-001 ~ FR-025)
- 4 个优先级用户故事 (P1~P4)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Rust-First Safety & Performance ✅

- [x] Rust 2024 edition used (MSRV 1.77)
- [x] Zero `unsafe` blocks (enforced by `cargo clippy`)
- [x] Zero `.unwrap()` / `.expect()` (enforced by CI gate)
- [x] Audio thread禁止内存分配 (使用预分配 ring buffer + mpsc channel)
- [x] 所有错误通过 `Result<T, E>` 处理和传播
- [x] 异步 I/O 使用 `tokio` runtime + `async/await`
- [x] 并发状态管理使用 `ArcSwap` (config) 和 `DashMap` (session state)

**Justification**: 音频处理和实时网络传输是核心功能,任何 GC 停顿或内存不安全都会导致音频爆音或数据竞争。

### Principle II: Real-Time First Architecture ✅

- [x] 音频缓冲区 <10ms (480 samples @ 48kHz)
- [x] WebSocket 持久连接 (预热策略,避免冷启动延迟)
- [x] Base64 编码和 JSON 序列化在独立 Tokio task 执行
- [x] 文本注入延迟 <50ms (预缓存活跃窗口信息)
- [x] 所有 I/O 非阻塞 (Tokio 异步运行时)

**Target**: 端到端延迟分解 - 音频采集 10ms + 重采样 5ms + 网络传输 50ms + 服务端处理 80ms + 文本注入 15ms = **160ms** (符合 <200ms 目标)

### Principle III: Privacy & Security by Design ✅

- [x] 音频缓冲区在传输后立即 `memset` 清零
- [x] API 密钥存储在 macOS Keychain (使用 `security` CLI 或 `keychain-services` crate)
- [x] 转写文本不持久化到磁盘 (除非用户明确启用历史记录功能)
- [x] 网络通信使用 WSS (TLS 1.3 加密)
- [x] 剪贴板操作保存并恢复原内容 (FR-008)
- [x] macOS Accessibility API 调用最小化 (仅用于焦点检测和文本注入)
- [x] 结构化日志不记录完整转写文本 (FR-025)

**Compliance**: 符合 GDPR 数据最小化原则,音频数据仅流式传输到 ElevenLabs,不在客户端或第三方存储。

### Principle IV: Tauri v2 Plugin Architecture ✅

- [x] 全局热键: `tauri-plugin-global-shortcut` 2.0
- [x] 剪贴板: `tauri-plugin-clipboard-manager` 2.1
- [x] 文件系统: `tauri-plugin-fs` 2.1 (配置读写)
- [x] 配置存储: `tauri-plugin-store` 2.1 (持久化)
- [x] 权限声明在 `capabilities/default.json`:
  - `global-shortcut:allow-register`
  - `clipboard-manager:allow-write-text`
  - `clipboard-manager:allow-read-text` (剪贴板恢复)
- [x] 系统托盘和窗口管理通过 `tauri::tray` 和 `tauri::window` API
- [x] macOS App Nap 防护通过 `NSApplicationActivationPolicyAccessory` + `macOSPrivateApi: true`

**Architecture Decision**: 所有系统集成通过 Tauri 插件和 Rust 后端 Commands,前端无法直接访问系统 API,符合最小权限原则。

### Principle V: Test-Driven System Integration ✅

- [x] 音频管道测试: 验证 48kHz → 16kHz 重采样误差 <0.1% (使用 FFT 频谱分析)
- [x] WebSocket 协议测试: 模拟 ElevenLabs API,验证消息序列 (`session_started` → `partial_transcript` → `committed_transcript`)
- [x] 文本注入测试: 验证焦点管理和剪贴板恢复成功率 100%
- [x] 权限检查测试: 模拟 macOS Accessibility 权限拒绝,验证错误提示
- [x] CI 集成: GitHub Actions 在 macOS runner 上运行集成测试

**Test Coverage Target**: >80% line coverage for Rust backend,>70% for React frontend。

### Principle VI: Minimal Dependencies, Maximum Auditability ✅

**Core Dependencies Justified**:

| Dependency | Version | Justification | Alternatives Rejected | Linux Support |
|------------|---------|---------------|----------------------|---------------|
| `cpal` | 0.16 | 唯一支持跨平台实时音频 I/O 的纯 Rust crate,活跃维护,<10ms 延迟 | `rodio` (仅播放), `portaudio-rs` (C bindings) | ✅ ALSA (需要 libasound2-dev) |
| `rubato` | 0.16.2 | 高质量 Sinc 重采样,SIMD 加速,real-time safe (无动态分配) | `dasp` (精度不足), `samplerate` (C bindings) | ✅ 完全跨平台 |
| `tokio-tungstenite` | 0.28 | 高性能异步 WebSocket,与 Tokio 深度集成,rustls TLS | `async-tungstenite` (维护不足), `websocket` (同步阻塞) | ✅ 完全跨平台 |
| `enigo` | 0.6.1 | 跨平台键盘模拟,支持 Rust 2024 edition,X11/Wayland 支持 | `autopilot` (API 不稳定), `rdev` (仅监听) | ✅ X11 稳定 / ⚠️ Wayland 实验性 |
| `keyring` | 2.3 | 跨平台密钥存储,支持 Keychain/Secret Service/Credential Manager | 平台特定 API (难以维护) | ✅ Secret Service支持 |

**Binary Size Optimization**:
- 使用 `strip = true` 和 `lto = true` (Release 构建)
- 预期二进制大小 <10MB (Tauri) vs >150MB (Electron)

### Principle VII: Observability & Debuggability ✅

**Structured Logging Strategy** (使用 `tracing` crate):

```rust
// 音频采集开始
tracing::info!(
    event = "audio_capture_started",
    sample_rate = 48000,
    channels = 1,
    buffer_size_ms = 10
);

// WebSocket 连接
tracing::info!(
    event = "websocket_connected",
    session_id = %session_id,
    model = "scribe_v2_realtime"
);

// 转写事件 (不记录完整文本)
tracing::info!(
    event = "transcript_received",
    type = "committed",
    text_length = text.len(),
    confidence = 0.98
);

// 错误场景
tracing::error!(
    event = "text_injection_failed",
    reason = "password_field_detected",
    app_name = "Safari"
);
```

**Log Output**:
- Development: stdout (RUST_LOG=debug)
- Production: 滚动文件日志 `~/.scribeflow/logs/app.log` (最大 10MB,轮转 3 个文件)

---

### ✅ Constitution Compliance Summary

**Status**: **PASS** - All 7 core principles satisfied.

**Zero Violations**: 项目设计完全符合宪法要求,无需复杂性豁免。

**Re-evaluation Trigger**: Phase 1 design.md 完成后重新审查,确保数据模型和 API contracts 未引入新的复杂性或依赖。

## Project Structure

### Project Locations

**重要说明**: 本项目采用分离的文档和代码目录结构:

- **项目根目录**: `~/Documents/VibeCoding/Week3` (源代码位置)
- **规范文档**: `~/Documents/VibeCoding/specs/001-scribeflow-voice-system` (设计文档)
- **共享配置**: `~/Documents/VibeCoding/Week3/.specify` (工具和模板)

### Documentation (this feature)

**完整路径**: `~/Documents/VibeCoding/specs/001-scribeflow-voice-system/`

```text
specs/001-scribeflow-voice-system/
├── spec.md              # 功能规范 (已完成)
├── design.md            # 详细设计文档 (已完成,v1.2.0)
├── plan.md              # 本文件 (实施计划)
├── research.md          # Phase 0 输出 (技术调研和决策)
├── data-model.md        # Phase 1 输出 (实体关系和状态机)
├── quickstart.md        # Phase 1 输出 (开发环境搭建)
├── contracts/           # Phase 1 输出 (WebSocket 协议契约)
│   ├── elevenlabs-websocket-protocol.md
│   ├── tauri-commands.md
│   └── test-scenarios.md
├── tasks.md             # Phase 2 输出 (/speckit.tasks 生成)
└── checklists/          # 质量检查清单
    └── requirements.md
```

### Source Code (Week3 directory)

**完整路径**: `~/Documents/VibeCoding/Week3/`

**注意**: 源代码将在 Week3 目录下创建,使用 Tauri 标准结构

```text
~/Documents/VibeCoding/Week3/
├── src-tauri/                    # Rust 后端
│   ├── src/
│   │   ├── main.rs               # 应用入口
│   │   ├── lib.rs                # Tauri Builder 配置
│   │   ├── audio/                # 音频处理模块
│   │   │   ├── mod.rs
│   │   │   ├── capture.rs        # cpal 音频采集
│   │   │   ├── resampler.rs      # rubato 重采样器
│   │   │   └── buffer.rs         # 环形缓冲区
│   │   ├── network/              # 网络通信模块
│   │   │   ├── mod.rs
│   │   │   ├── client.rs         # WebSocket 客户端
│   │   │   ├── protocol.rs       # Scribe v2 协议
│   │   │   └── state_machine.rs # 连接状态机
│   │   ├── input/                # 文本注入模块
│   │   │   ├── mod.rs
│   │   │   ├── injector.rs       # 注入策略选择
│   │   │   ├── keyboard.rs       # enigo 键盘模拟
│   │   │   └── clipboard.rs      # 剪贴板操作
│   │   ├── system/               # 系统集成模块
│   │   │   ├── mod.rs
│   │   │   ├── hotkey.rs         # 全局热键
│   │   │   ├── window.rs         # 活跃窗口追踪
│   │   │   └── permissions.rs    # macOS 权限检查
│   │   ├── ui/                   # UI 交互模块
│   │   │   ├── mod.rs
│   │   │   ├── tray.rs           # 系统托盘
│   │   │   └── commands.rs       # Tauri Commands
│   │   ├── config/               # 配置管理模块
│   │   │   ├── mod.rs
│   │   │   └── store.rs          # 配置持久化
│   │   └── utils/
│   │       ├── mod.rs
│   │       ├── logger.rs         # tracing 日志配置
│   │       └── crypto.rs         # API Key 加密
│   ├── Cargo.toml
│   ├── capabilities/
│   │   └── default.json          # 权限声明
│   └── icons/                    # 应用图标
├── src/                          # React 前端
│   ├── App.tsx                   # 根组件
│   ├── main.tsx                  # 入口
│   ├── components/
│   │   ├── OverlayWindow.tsx     # 悬浮窗组件
│   │   ├── WaveformVisualizer.tsx # 波形动画
│   │   ├── TranscriptDisplay.tsx # 转写文本显示
│   │   └── SettingsPanel.tsx     # 设置面板
│   ├── stores/
│   │   └── transcriptStore.ts    # Zustand 状态管理
│   ├── hooks/
│   │   └── useTauriEvents.ts     # Tauri 事件监听
│   └── styles/
│       └── globals.css           # TailwindCSS 样式
├── tests/                        # 测试目录
│   ├── unit/                     # Rust 单元测试
│   │   ├── audio_resampler_test.rs
│   │   ├── websocket_protocol_test.rs
│   │   └── text_injector_test.rs
│   ├── integration/              # Rust 集成测试
│   │   ├── end_to_end_test.rs
│   │   └── permission_test.rs
│   └── frontend/                 # 前端测试
│       └── OverlayWindow.test.tsx
├── .github/
│   └── workflows/
│       └── ci.yml                # GitHub Actions CI
├── package.json                  # Node.js 依赖
├── tsconfig.json                 # TypeScript 配置
├── tailwind.config.js            # TailwindCSS 配置
└── README.md                     # 项目 README

```

**Structure Decision**: 采用标准 Tauri v2 应用结构,Rust 后端 (`src-tauri/`) 和 React 前端 (`src/`) 分离。Rust 模块按功能领域组织 (audio, network, input, system, ui, config),每个模块独立可测试。前端采用组件化设计,Zustand 管理全局状态,通过 Tauri Events 与后端通信。

---

## Implementation Phases

### Phase 0: Research & Technical Decisions (研究与技术决策)

**目标**: 解决所有技术不确定性,验证关键假设,生成 `research.md`。

**Duration**: 1-2 天

#### 0.1 WebSocket 协议验证

**Research Question**: ElevenLabs Scribe v2 Realtime API 的完整协议规范是什么?如何处理连接生命周期、错误场景和重连逻辑?

**Tasks**:
1. 阅读 [ElevenLabs Scribe v2 文档](https://elevenlabs.io/docs/cookbooks/speech-to-text/streaming)
2. 使用 `wscat` 或 Python `websockets` 库手动测试协议:
   - 握手流程 (xi-api-key header vs token query param)
   - `session_started` 事件结构
   - `input_audio_chunk` 消息格式 (base64 编码验证)
   - `partial_transcript` 和 `committed_transcript` 事件时序
   - `input_error` 错误消息
   - 空闲超时和心跳机制
3. 文档化协议状态机:
   ```
   Idle → Connecting → Listening → Recording → Processing → Committing → Idle
   ```
4. 确定重连策略:
   - 指数退避 (1s, 2s, 4s)
   - 最大重试次数 3 次
   - 是否需要 Ping/Pong 心跳?

**Output**: `research.md` 第 1 节 "WebSocket 协议规范与状态机"

#### 0.2 音频采集与重采样最佳实践

**Research Question**: 如何使用 `cpal` 实现 <10ms 延迟的音频采集?如何使用 `rubato` 实现高质量 48kHz → 16kHz 重采样?

**Tasks**:
1. 阅读 [cpal 文档](https://docs.rs/cpal/) 和 [示例代码](https://github.com/RustAudio/cpal/tree/master/examples)
2. 验证 macOS CoreAudio 配置:
   - 默认输入设备枚举
   - 原生采样率检测 (通常 48kHz)
   - 缓冲区大小设置 (目标 480 frames = 10ms @ 48kHz)
3. 测试 `rubato` 重采样器选项:
   - `FftFixedInOut`: 高质量 Sinc 插值,SIMD 加速
   - `FastFixedIn`: 低延迟但精度略低
   - 性能基准测试: 输入 480 samples (10ms),输出 160 samples (16kHz),测量 CPU 占用
4. 验证 ring buffer 设计:
   - 使用 `crossbeam::queue::ArrayQueue` (无锁,预分配)
   - 容量设置为 100ms 数据 (4800 samples @ 48kHz)

**Output**: `research.md` 第 2 节 "音频采集与重采样实现"

#### 0.3 macOS 系统集成策略

**Research Question**: 如何在 macOS 上实现全局热键、文本注入和权限检查?

**Tasks**:
1. 验证 `tauri-plugin-global-shortcut` 2.0:
   - 注册 `Cmd+Shift+\` 快捷键
   - 事件回调触发测试
   - 是否会与系统快捷键冲突?(如 Spotlight)
2. 测试 `enigo` 0.6.1 键盘模拟:
   - 在 VS Code、Chrome、TextEdit 中模拟输入
   - 特殊字符处理 (中文、emoji)
   - 输入速度控制 (避免"幽灵打字"效果)
3. 验证 `tauri-plugin-clipboard-manager`:
   - 读取当前剪贴板内容
   - 写入新内容
   - 恢复原内容 (时间窗口测试)
   - 模拟 `Cmd+V` 粘贴
4. 使用 `active-win-pos-rs` 获取活跃窗口:
   - 应用名称和窗口标题
   - 焦点元素类型检测 (需要 Accessibility API)
5. macOS 权限流程:
   - 麦克风权限: `AVFoundation` 或 `cpal` 自动请求
   - Accessibility 权限: 使用 `macos-accessibility-client` crate 检测,引导用户授权
   - Screen Recording 权限 (仅在需要窗口标题时)

**Output**: `research.md` 第 3 节 "macOS 系统集成和权限管理"

#### 0.4 Tauri v2 架构决策

**Research Question**: 如何设计 Tauri 前后端通信?如何防止 macOS App Nap 挂起后台进程?

**Tasks**:
1. 阅读 [Tauri v2 IPC 文档](https://v2.tauri.app/develop/inter-process-communication/)
2. 设计 Tauri Commands (前端 → 后端):
   - `start_transcription()`: 启动音频采集和 WebSocket 连接
   - `stop_transcription()`: 停止采集
   - `save_config(config: AppConfig)`: 保存配置
   - `check_permissions()`: 检查权限状态
3. 设计 Tauri Events (后端 → 前端):
   - `audio_level_update { level: f32 }`: 音量更新 (50ms 间隔)
   - `partial_transcript { text: String }`: 部分转写
   - `committed_transcript { text: String }`: 最终转写
   - `connection_status { state: ConnectionState }`: 连接状态变化
   - `error { message: String }`: 错误通知
4. 验证 macOS App Nap 防护:
   ```rust
   #[cfg(target_os = "macos")]
   unsafe {
       let app = cocoa::appkit::NSApplication::sharedApplication(cocoa::base::nil);
       app.setActivationPolicy_(cocoa::appkit::NSApplicationActivationPolicyAccessory);
   }
   ```
5. 配置 `tauri.conf.json`:
   ```json
   {
     "macOSPrivateApi": true,
     "windows": [
       {
         "label": "overlay",
         "decorations": false,
         "transparent": true,
         "alwaysOnTop": true,
         "acceptFirstMouse": false,
         "focusable": false
       }
     ]
   }
   ```

**Output**: `research.md` 第 4 节 "Tauri v2 架构和 IPC 设计"

#### 0.5 性能基准与瓶颈分析

**Research Question**: 端到端延迟 <200ms 是否可行?哪些环节是瓶颈?

**Tasks**:
1. 延迟分解测量:
   - 音频采集: cpal 回调延迟 (预期 10ms)
   - 重采样: rubato 处理时间 (预期 <5ms)
   - Base64 编码: 1600 bytes 编码时间 (预期 <1ms)
   - WebSocket 发送: 本地测量 (预期 <2ms)
   - 网络往返: ping 测试到 ElevenLabs API (预期 50-100ms)
   - 服务端处理: Scribe v2 承诺 <150ms
   - 文本注入: enigo 模拟输入延迟 (预期 <15ms)
2. 内存占用测量:
   - Tauri WebView: ~15MB (固定)
   - Rust 运行时: ~10MB
   - 音频缓冲区: 5MB (100ms @ 48kHz)
   - 总计: ~30MB 空闲,~80MB 活跃 (符合 <100MB 目标)
3. CPU 占用基准:
   - 空闲状态: <1%
   - 活跃转写: <15% (单核)

**Output**: `research.md` 第 5 节 "性能基准与优化策略"

#### 0.6 错误处理与降级策略

**Research Question**: 如何优雅处理网络错误、权限错误和 API 限流?

**Tasks**:
1. 定义错误类型:
   ```rust
   #[derive(Debug, thiserror::Error)]
   pub enum ScribeFlowError {
       #[error("Audio device not available")]
       AudioDeviceError,
       #[error("WebSocket connection failed: {0}")]
       WebSocketError(String),
       #[error("API authentication failed")]
       AuthError,
       #[error("Permission denied: {0}")]
       PermissionError(String),
   }
   ```
2. 网络错误降级:
   - 连接失败 → 显示错误,不启动采集
   - 连接中断 → 复制已转写文本到剪贴板,自动重连
   - API 限流 (429) → 显示配额不足提示
3. 权限错误处理:
   - 麦克风拒绝 → 显示引导窗口,无法使用核心功能
   - Accessibility 拒绝 → 可以显示转写结果,但无法注入文本

**Output**: `research.md` 第 6 节 "错误处理与用户反馈"

---

**Phase 0 Deliverable**: `research.md` (包含 6 个决策章节,每个章节包含决策、依据和替代方案)

---

### Phase 1: Design & Contracts (设计与契约)

**目标**: 生成数据模型、API 契约和快速启动指南。

**Duration**: 2-3 天

**Prerequisites**: `research.md` 完成,所有技术不确定性解决。

#### 1.1 Data Model Definition

**Task**: 从 spec.md 提取 7 个核心实体,定义 Rust 数据结构和状态机。

**Output**: `data-model.md`

**Content**:

```markdown
# Data Model: ScribeFlow

## Entity: AudioStream

**Purpose**: 表示从麦克风采集的实时音频数据流。

**Rust Structure**:
```rust
pub struct AudioStream {
    pub device: cpal::Device,
    pub config: cpal::StreamConfig,
    pub sample_rate: u32,           // 原生采样率 (通常 48000)
    pub channels: u16,              // 单声道 (1)
    pub buffer_size: usize,         // 缓冲区大小 (480 frames = 10ms)
    pub stream: Option<cpal::Stream>,
}
```

**Lifecycle**:
- Created: 用户按下热键,`audio::capture::start()` 调用
- Active: cpal 回调持续推送音频数据到 ring buffer
- Destroyed: 用户停止转写或错误发生

**Validation Rules**:
- `sample_rate` 必须在 16000-48000 范围内
- `channels` 必须为 1 (单声道)
- `buffer_size` 必须是 2 的幂次方

---

## Entity: TranscriptionSession

**Purpose**: 表示一次完整的语音输入过程。

**Rust Structure**:
```rust
pub struct TranscriptionSession {
    pub session_id: String,              // 由 ElevenLabs 服务端生成
    pub state: SessionState,
    pub started_at: Instant,
    pub ended_at: Option<Instant>,
    pub partial_texts: Vec<String>,      // 临时存储 partial transcripts
    pub committed_texts: Vec<String>,    // 最终转写文本
}

#[derive(Debug, Clone, PartialEq)]
pub enum SessionState {
    Idle,
    Connecting,
    Listening { session_id: String },
    Recording { start_time: Instant },
    Processing,
    Committing,
    Error { message: String },
}
```

**State Transitions**:
```
Idle → Connecting → Listening → Recording → Processing → Committing → Idle
           ↓           ↓            ↓           ↓            ↓
        Error ←────────┴────────────┴───────────┴────────────┘
```

**Validation Rules**:
- `session_id` 必须非空 (由服务端生成后验证)
- `state` 转换必须遵循状态机规则
- `committed_texts` 一旦添加不可修改 (immutable append-only)

---

(继续定义其他 5 个实体: TranscriptEvent, OverlayWindow, AppConfig, ActiveWindow, WebSocketConnection)


#### 1.2 API Contracts Generation

**Task**: 定义 WebSocket 协议契约、Tauri Commands 契约和测试场景。

**Output**: `contracts/` 目录

**1.2.1 WebSocket Protocol Contract**

文件: `contracts/elevenlabs-websocket-protocol.md`


# ElevenLabs Scribe v2 Realtime WebSocket Protocol

## Connection

**Endpoint**: `wss://api.elevenlabs.io/v1/speech-to-text/realtime`

**Authentication**:
- Method 1 (Recommended): HTTP Header `xi-api-key: <API_KEY>`
- Method 2: Query Parameter `?token=<API_KEY>`

**Query Parameters**:
- `model_id`: `scribe_v2_realtime` (required)
- `language_code`: `en` | `zh` | `auto` (optional, default: auto)
- `encoding`: `pcm_16000` (required, 16kHz PCM)

## Client → Server Messages

### 1. input_audio_chunk

**Description**: 发送音频数据块。

**Format**:
```json
{
  "message_type": "input_audio_chunk",
  "audio_base_64": "<BASE64_ENCODED_PCM_I16>"
}
```

**Rust Implementation**:
```rust
#[derive(Serialize)]
struct InputAudioChunk {
    message_type: String,  // 固定为 "input_audio_chunk"
    audio_base_64: String,
}
```

**Validation**:
- `audio_base_64` 必须是有效的 Base64 字符串
- 解码后数据长度必须是 2 的倍数 (i16 samples)
- 推荐每 100ms 发送一次 (1600 bytes = 800 samples @ 16kHz)

## Server → Client Messages

### 1. session_started

**Description**: 会话初始化成功。

**Format**:
```json
{
  "message_type": "session_started",
  "session_id": "uuid-v4",
  "config": {
    "model_id": "scribe_v2_realtime",
    "language_code": "zh"
  }
}
```

**Rust Implementation**:
```rust
#[derive(Deserialize)]
struct SessionStarted {
    message_type: String,
    session_id: String,
    config: SessionConfig,
}
```

### 2. partial_transcript

**Description**: 实时部分转写结果。

**Format**:
```json
{
  "message_type": "partial_transcript",
  "text": "你好世",
  "created_at_ms": 1706025600000
}
```

**Handling**:
- 更新悬浮窗显示 (非阻塞)
- 不触发文本注入
- 覆盖前一个 partial transcript

### 3. committed_transcript

**Description**: 最终确定的转写文本。

**Format**:
```json
{
  "message_type": "committed_transcript",
  "text": "你好世界",
  "confidence": 0.98,
  "created_at_ms": 1706025601500
}
```

**Handling**:
- 触发文本注入逻辑
- 更新悬浮窗显示为"已确认"状态
- 记录到 `TranscriptionSession.committed_texts`

### 4. input_error

**Description**: 客户端发送的数据格式错误。

**Format**:
```json
{
  "message_type": "input_error",
  "error_message": "Invalid audio format"
}
```

**Handling**:
- 停止音频采集
- 显示错误提示
- 记录错误日志

## Error Scenarios

| Error Type | Cause | Client Handling |
|------------|-------|-----------------|
| 401 Unauthorized | API key invalid | 显示"API 密钥无效",引导用户更新 |
| 429 Too Many Requests | Rate limit | 显示"配额不足",等待 60s 后重试 |
| 1006 Abnormal Closure | Network issue | 自动重连 (指数退避) |
| 1011 Internal Error | Server error | 显示"服务暂时不可用",60s 后重试 |

## Test Scenarios

见 `contracts/test-scenarios.md`
```

**1.2.2 Tauri Commands Contract**

文件: `contracts/tauri-commands.md`

```markdown
# Tauri Commands API

## Command: start_transcription

**Description**: 启动音频采集和 WebSocket 连接。

**Signature**:
```rust
#[tauri::command]
async fn start_transcription(
    state: tauri::State<'_, AppState>
) -> Result<(), String>
```

**Frontend Invocation**:
```typescript
import { invoke } from '@tauri-apps/api/core';

try {
  await invoke('start_transcription');
  console.log('Transcription started');
} catch (error) {
  console.error('Failed to start:', error);
}
```

**Behavior**:
1. 检查 macOS Accessibility 权限 → 如未授权,返回错误
2. 枚举音频设备 → 如无可用设备,返回错误
3. 启动 cpal 音频流
4. 建立 WebSocket 连接到 ElevenLabs
5. 触发 `connection_status` 事件通知前端

**Error Codes**:
- `PERMISSION_DENIED`: 权限不足
- `AUDIO_DEVICE_ERROR`: 音频设备不可用
- `WEBSOCKET_ERROR`: 网络连接失败

---

(继续定义其他 Commands: stop_transcription, save_config, check_permissions)
```

**1.2.3 Test Scenarios**

文件: `contracts/test-scenarios.md`

```markdown
# Test Scenarios

## Scenario 1: Happy Path - Complete Transcription Flow

**Steps**:
1. 用户按下 `Cmd+Shift+\` 热键
2. 系统显示悬浮窗"正在连接..."
3. WebSocket 连接成功,收到 `session_started` 事件
4. 悬浮窗更新为"正在听"
5. 用户说"Hello World"
6. 系统收到 3 个 `partial_transcript`:
   - "Hel"
   - "Hello"
   - "Hello Wor"
7. 系统收到 1 个 `committed_transcript`: "Hello World"
8. 文本插入到活跃应用 (TextEdit)
9. 悬浮窗淡出

**Expected Result**:
- TextEdit 中出现 "Hello World"
- 端到端延迟 <200ms
- 悬浮窗动画流畅 (30fps)

**Validation**:
```rust
#[tokio::test]
async fn test_happy_path_transcription() {
    // Mock WebSocket server
    // Simulate audio input
    // Verify text injection
}
```

## Scenario 2: Network Failure Mid-Transcription

**Steps**:
1. 用户开始说话,已转写 "Hello Wo..."
2. 网络连接突然断开 (模拟断网)
3. 系统检测到 WebSocket 关闭
4. 系统将 "Hello Wo" 复制到剪贴板
5. 显示通知 "网络中断,已转写内容已复制到剪贴板"
6. 自动尝试重连 (最多 3 次)

**Expected Result**:
- 剪贴板包含 "Hello Wo"
- 通知显示 3 秒后消失
- 如网络恢复,自动重连成功

**Validation**:
```rust
#[tokio::test]
async fn test_network_failure_clipboard_fallback() {
    // Simulate connection drop
    // Verify clipboard content
    // Verify notification
}
```

---

(继续定义其他场景: 密码框检测、权限拒绝、长时间连续说话、剪贴板恢复)
```

#### 1.3 Quickstart Guide

**Task**: 编写开发环境搭建指南。

**Output**: `quickstart.md`

```markdown
# QuickStart: ScribeFlow Development

## Prerequisites

- **macOS**: 10.15+ (Catalina or later)
- **Rust**: 1.77+ ([Install via rustup](https://rustup.rs/))
- **Node.js**: 18+ LTS ([Install via nvm](https://github.com/nvm-sh/nvm))
- **Xcode Command Line Tools**: `xcode-select --install`
- **ElevenLabs API Key**: [Get free trial](https://elevenlabs.io/)

## Setup Steps

### 1. Clone Repository

```bash
git clone https://github.com/your-org/scribeflow.git
cd scribeflow
git checkout 001-scribeflow-voice-system
```

### 2. Install Dependencies

```bash
# Install Rust dependencies
cd src-tauri
cargo build

# Install Node.js dependencies
cd ..
npm install
```

### 3. Configure API Key

```bash
# Create .env file (NOT committed to git)
echo "ELEVENLABS_API_KEY=your_api_key_here" > .env
```

### 4. Grant Permissions (macOS)

1. **Microphone Permission**: Will be requested on first run
2. **Accessibility Permission**:
   - Open "System Preferences > Security & Privacy > Accessibility"
   - Click the lock to make changes
   - Add ScribeFlow to the list (after first build)

### 5. Run Development Server

```bash
npm run tauri dev
```

This will:
- Compile Rust backend
- Start Vite dev server for React frontend
- Launch ScribeFlow in development mode

### 6. Build for Production

```bash
npm run tauri build

# Output:
# - macOS: src-tauri/target/release/bundle/macos/ScribeFlow.app
# - DMG: src-tauri/target/release/bundle/dmg/ScribeFlow.dmg
```

## Testing

### Unit Tests (Rust)

```bash
cd src-tauri
cargo test
```

### Integration Tests

```bash
cargo test --test end_to_end_test
```

### Frontend Tests

```bash
npm run test
```

## Common Issues

### Issue: "Audio device not found"

**Solution**: Check microphone connection in "System Preferences > Sound > Input"

### Issue: "Permission denied for Accessibility"

**Solution**: Grant Accessibility permission as described in Step 4

### Issue: "WebSocket connection failed"

**Solution**: Verify API key in `.env` file and network connection

## Development Workflow

1. **Feature Branch**: `git checkout -b feature/your-feature`
2. **Code**: Modify Rust backend (`src-tauri/src/`) or React frontend (`src/`)
3. **Test**: `cargo test` + `npm run test`
4. **Lint**: `cargo clippy` + `npm run lint`
5. **Format**: `cargo fmt` + `npm run format`
6. **Commit**: `git commit -m "feat(scope): description"`
7. **Push**: `git push origin feature/your-feature`

## Debugging

### Rust Backend Logs

```bash
RUST_LOG=debug npm run tauri dev
```

### Frontend Console

Open DevTools: `Cmd+Option+I` in the app window

### WebSocket Traffic

Use [wscat](https://github.com/websockets/wscat) to inspect WebSocket messages:

```bash
npm install -g wscat
wscat -c "wss://api.elevenlabs.io/v1/speech-to-text/realtime?model_id=scribe_v2_realtime" \
  -H "xi-api-key: your_key"
```

## Resources

- [Tauri v2 Documentation](https://v2.tauri.app/)
- [cpal Audio Guide](https://docs.rs/cpal/)
- [ElevenLabs API Reference](https://elevenlabs.io/docs/api-reference/speech-to-text/v-1-speech-to-text-realtime)
```

#### 1.4 Update Agent Context

**Task**: 运行 `.specify/scripts/bash/update-agent-context.sh claude` 更新 AI 助手上下文。

```bash
cd /home/ray/Documents/VibeCoding
.specify/scripts/bash/update-agent-context.sh claude
```

**Expected Output**:
- 更新 `.claude/context.md` (如存在)
- 添加本项目使用的技术栈: Tauri v2, cpal, rubato, tokio-tungstenite, ElevenLabs Scribe v2

---

**Phase 1 Deliverables**:
- `data-model.md` (7 个实体定义)
- `contracts/elevenlabs-websocket-protocol.md`
- `contracts/tauri-commands.md`
- `contracts/test-scenarios.md`
- `quickstart.md`
- 更新的 agent 上下文文件

---

### Phase 2: Core Audio & Network Implementation (核心音频和网络实现)

**目标**: 实现 P1 功能 - 全局热键触发即时听写 (不含悬浮窗 UI)。

**Duration**: 5-7 天

**Prerequisites**: Phase 1 完成,数据模型和契约已定义。

#### 2.1 Audio Capture Module

**Tasks**:
1. 实现 `src-tauri/src/audio/capture.rs`:
   - 枚举音频设备
   - 配置 cpal 流 (48kHz, 单声道, 10ms 缓冲)
   - 音频回调函数 (零内存分配)
   - 错误处理 (设备断开、缓冲区溢出)
2. 实现 `src-tauri/src/audio/buffer.rs`:
   - Ring buffer (使用 `crossbeam::queue::ArrayQueue`)
   - 容量: 4800 samples (100ms @ 48kHz)
3. 实现 `src-tauri/src/audio/resampler.rs`:
   - 使用 `rubato::FftFixedInOut`
   - 48kHz → 16kHz (3:1 ratio)
   - 批量处理: 480 samples → 160 samples
4. 单元测试:
   - 测试重采样精度 (FFT 频谱对比,误差 <0.1%)
   - 测试 ring buffer 并发读写

**Acceptance Criteria**:
- `cargo test audio` 全部通过
- 音频采集延迟 <10ms (使用 tracing 测量)
- 重采样 CPU 占用 <3% (单核)

#### 2.2 WebSocket Client Module

**Tasks**:
1. 实现 `src-tauri/src/network/client.rs`:
   - 使用 `tokio-tungstenite` 建立 WSS 连接
   - 握手 Header: `xi-api-key`
   - 查询参数: `model_id=scribe_v2_realtime&encoding=pcm_16000`
2. 实现 `src-tauri/src/network/protocol.rs`:
   - 定义 Rust 结构体 (InputAudioChunk, SessionStarted, PartialTranscript, CommittedTranscript)
   - 序列化/反序列化 (使用 `serde_json`)
3. 实现 `src-tauri/src/network/state_machine.rs`:
   - 连接状态机 (Idle → Connecting → Listening → Recording → ...)
   - 自动重连逻辑 (指数退避,最多 3 次)
4. 集成测试:
   - Mock WebSocket server (使用 `tokio-tungstenite` 的 `accept_async`)
   - 模拟完整会话流程 (session_started → partial → committed)
   - 测试重连逻辑 (模拟连接断开)

**Acceptance Criteria**:
- `cargo test network` 全部通过
- WebSocket 连接成功率 >99% (100 次测试)
- 重连逻辑正确 (最多 3 次,指数退避)

#### 2.3 Text Injection Module

**Tasks**:
1. 实现 `src-tauri/src/input/keyboard.rs`:
   - 使用 `enigo` 模拟键盘输入
   - 特殊字符处理 (中文、emoji)
   - 输入速度控制 (每字符 5ms 延迟)
2. 实现 `src-tauri/src/input/clipboard.rs`:
   - 使用 `tauri-plugin-clipboard-manager`
   - 读取当前剪贴板内容
   - 写入新内容
   - 恢复原内容
   - 模拟 `Cmd+V` 粘贴
3. 实现 `src-tauri/src/input/injector.rs`:
   - 注入策略选择:
     - 短文本 (<10 字符): 键盘模拟
     - 长文本 (>=10 字符): 剪贴板粘贴
   - 焦点检测 (使用 `active-win-pos-rs`)
   - 安全检查 (密码框检测,使用 Accessibility API)
4. 集成测试:
   - 在 TextEdit 中测试键盘模拟
   - 在 VS Code 中测试剪贴板粘贴
   - 测试剪贴板恢复成功率 (100 次测试,成功率 100%)

**Acceptance Criteria**:
- `cargo test input` 全部通过
- 文本注入延迟 <50ms
- 剪贴板恢复成功率 100%
- 密码框检测准确率 >95%

#### 2.4 Global Hotkey Integration

**Tasks**:
1. 配置 `tauri-plugin-global-shortcut`:
   - 注册 `Cmd+Shift+\` 快捷键
   - 回调函数触发 `start_transcription` Command
2. 实现 `src-tauri/src/system/hotkey.rs`:
   - 热键事件监听
   - 状态管理 (避免重复触发)
3. 集成测试:
   - 模拟热键按下
   - 验证 `start_transcription` 被调用

**Acceptance Criteria**:
- 热键响应延迟 <50ms
- 无冲突 (与系统快捷键或其他应用)

#### 2.5 End-to-End Integration

**Tasks**:
1. 实现 `src-tauri/src/lib.rs`:
   - Tauri Builder 配置
   - 注册 Commands 和 Plugins
   - 初始化全局状态 (AppState)
2. 实现 Tauri Commands:
   - `start_transcription()`: 启动音频采集 + WebSocket 连接
   - `stop_transcription()`: 停止采集
3. 实现 Tauri Events:
   - `connection_status`: 连接状态变化
   - `partial_transcript`: 部分转写
   - `committed_transcript`: 最终转写
4. 集成测试:
   - 完整流程测试 (热键 → 采集 → 转写 → 注入)
   - 测试端到端延迟 (目标 <200ms)

**Acceptance Criteria**:
- 端到端集成测试通过
- 延迟 <200ms (在良好网络环境下)
- 内存占用 <100MB (活跃转写时)

---

**Phase 2 Deliverables**:
- 完整的 P1 功能 (全局热键触发即时听写)
- 所有单元测试和集成测试通过 (`cargo test`)
- 基本可用的命令行版本 (无 UI)

---

### Phase 3: UI & Configuration (用户界面和配置)

**目标**: 实现 P2 悬浮窗和 P3 配置管理。

**Duration**: 4-5 天

**Prerequisites**: Phase 2 完成,核心功能可用。

#### 3.1 Overlay Window Component

**Tasks**:
1. 实现 `src/components/OverlayWindow.tsx`:
   - 固定位置在屏幕中央 (使用 Tauri Window API)
   - 半透明背景 (CSS: `background: rgba(0,0,0,0.8)`)
   - 显示/隐藏动画 (CSS transitions)
2. 实现 `src/components/WaveformVisualizer.tsx`:
   - Canvas 波形绘制
   - 音量数据来自 `audio_level_update` 事件
   - 30fps 刷新率
3. 实现 `src/components/TranscriptDisplay.tsx`:
   - 显示 `partial_transcript` (实时更新)
   - 显示 `committed_transcript` (标记为"已确认")
   - 文本淡入淡出动画
4. 状态管理:
   - 使用 Zustand (`src/stores/transcriptStore.ts`)
   - 监听 Tauri Events (`src/hooks/useTauriEvents.ts`)

**Acceptance Criteria**:
- 悬浮窗固定在屏幕中央
- 波形动画流畅 (30fps)
- 文本实时更新无延迟

#### 3.2 System Tray

**Tasks**:
1. 实现 `src-tauri/src/ui/tray.rs`:
   - 托盘图标 (使用 `tauri::tray::TrayIconBuilder`)
   - 菜单项: "设置"、"关于"、"退出"
   - 菜单事件处理
2. 实现窗口隐藏逻辑:
   - 关闭窗口时隐藏 (不退出应用)
   - 退出菜单项完全退出

**Acceptance Criteria**:
- 托盘图标显示正常
- 菜单功能正常
- 窗口关闭不退出应用

#### 3.3 Settings Panel

**Tasks**:
1. 实现 `src/components/SettingsPanel.tsx`:
   - API 密钥输入框 (密码类型)
   - 快捷键配置 (显示当前快捷键)
   - 语言选择 (中文/英文/自动检测)
   - 保存按钮
2. 实现 `src-tauri/src/config/store.rs`:
   - 使用 `tauri-plugin-store` 持久化配置
   - API 密钥存储到 macOS Keychain
3. 实现 Tauri Command:
   - `save_config(config: AppConfig)`
   - `load_config() -> AppConfig`

**Acceptance Criteria**:
- 配置正确保存和加载
- API 密钥存储到 Keychain (不以明文形式保存)
- 应用重启后配置保留

#### 3.4 Permission Management

**Tasks**:
1. 实现 `src-tauri/src/system/permissions.rs`:
   - 检测麦克风权限
   - 检测 Accessibility 权限
   - 显示引导窗口 (Tauri Dialog)
2. 实现 Tauri Command:
   - `check_permissions() -> PermissionStatus`
3. 前端权限引导:
   - 首次启动时显示权限检查
   - 如未授权,显示引导步骤

**Acceptance Criteria**:
- 权限检查正确
- 引导窗口显示清晰
- 用户授权后功能正常

---

**Phase 3 Deliverables**:
- 完整的 P2 功能 (悬浮窗实时反馈)
- 完整的 P3 功能 (系统托盘和配置管理)
- 用户体验完整的桌面应用

---

### Phase 4: Error Handling & Polish (错误处理和优化)

**目标**: 实现 P4 网络异常处理,优化性能,完善日志和文档。

**Duration**: 3-4 天

**Prerequisites**: Phase 3 完成,核心功能和 UI 可用。

#### 4.1 Network Error Handling

**Tasks**:
1. 实现网络错误降级:
   - 连接失败 → 显示错误通知
   - 连接中断 → 剪贴板回退 + 自动重连
   - API 限流 (429) → 显示配额不足
2. 实现错误通知组件:
   - Toast 通知 (使用 React Toast 库)
   - 错误消息本地化
3. 集成测试:
   - 模拟网络断开
   - 验证剪贴板回退
   - 验证自动重连

**Acceptance Criteria**:
- 所有错误场景有用户反馈
- 自动重连成功率 >90%
- 剪贴板回退功能正常

#### 4.2 Logging & Observability

**Tasks**:
1. 配置 `tracing` crate:
   - 日志级别: ERROR, WARN, INFO, DEBUG
   - 滚动文件日志 (`~/.scribeflow/logs/app.log`)
   - 最大文件大小 10MB,轮转 3 个文件
2. 添加结构化日志:
   - 音频采集事件
   - WebSocket 生命周期
   - 文本注入事件
   - 错误事件
3. 隐私保护:
   - 日志不记录完整转写文本 (仅记录长度和置信度)
   - 日志不记录 API 密钥

**Acceptance Criteria**:
- 日志文件正常生成
- 日志包含足够调试信息
- 无隐私泄漏

#### 4.3 Performance Optimization

**Tasks**:
1. 性能基准测试:
   - 端到端延迟测量 (目标 <200ms)
   - 内存占用测量 (目标 <100MB)
   - CPU 占用测量 (目标 <15%)
2. 优化点:
   - 音频采集线程优先级设置
   - WebSocket 消息批处理
   - 悬浮窗渲染优化 (Canvas 缓存)
3. 压力测试:
   - 连续 1 小时转写 (验证无内存泄漏)
   - 100 次连续热键触发 (验证无资源泄漏)

**Acceptance Criteria**:
- 所有性能目标达成
- 压力测试通过

#### 4.4 Documentation & CI

**Tasks**:
1. 更新 README.md:
   - 项目简介
   - 安装指南
   - 使用说明
   - 截图/GIF
2. 配置 GitHub Actions CI:
   - Rust 单元测试
   - Rust 集成测试
   - Clippy lint
   - 代码格式检查
3. 生成 CHANGELOG.md:
   - 版本 0.1.0 功能列表

**Acceptance Criteria**:
- README.md 完整且清晰
- CI 通过所有检查
- CHANGELOG.md 记录所有功能

---

**Phase 4 Deliverables**:
- 完整的 P4 功能 (网络异常处理)
- 优化的性能和稳定性
- 完善的日志和文档
- 可发布的 v0.1.0 版本

---

## Risk Analysis

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **ElevenLabs API 延迟超出预期** | Medium | High | Phase 0 提前测试真实延迟,如超过 150ms,考虑调整端到端目标或联系 ElevenLabs 技术支持 |
| **macOS Accessibility API 权限被拒绝** | Medium | High | 提供清晰的引导步骤,如用户拒绝,降级为"仅显示转写结果"模式 |
| **音频重采样精度不足** | Low | Medium | Phase 0 测试 rubato 多种重采样器,如精度不足,考虑使用 `SincFixedIn` (高质量但 CPU 占用更高) |
| **文本注入在某些应用不工作** | Medium | Medium | Phase 2 测试主流应用 (VS Code, Chrome, Word),如失败,提供黑名单配置或剪贴板回退 |
| **内存泄漏或资源泄漏** | Low | High | Phase 4 压力测试,使用 `valgrind` (Linux) 或 Instruments (macOS) 检测泄漏 |
| **跨平台兼容性问题** | Low | Medium | 初期仅支持 macOS,Phase 5 (未来) 扩展到 Windows 和 Linux |

## Success Metrics

| Metric | Target | Measurement Method |
|--------|--------|--------------------|
| **端到端延迟** | <200ms | 使用 tracing 测量,从热键按下到文本插入完成 |
| **WebSocket 连接成功率** | >99% | 100 次连接测试,记录失败次数 |
| **音频重采样精度** | 误差 <0.1% | FFT 频谱分析,对比 48kHz 和 16kHz 频谱 |
| **内存占用 (空闲)** | <50MB | Activity Monitor 测量 |
| **内存占用 (活跃)** | <100MB | 活跃转写时 Activity Monitor 测量 |
| **剪贴板恢复成功率** | 100% | 100 次测试,验证剪贴板内容恢复 |
| **文本注入准确率** | 100% | 10 次连续测试,验证文本插入到正确应用 |
| **密码框检测准确率** | >95% | 20 个不同应用的密码框测试 |

## Timeline Summary

| Phase | Duration | Key Deliverables |
|-------|----------|------------------|
| **Phase 0: Research** | 1-2 days | research.md (6 个决策章节) |
| **Phase 1: Design & Contracts** | 2-3 days | data-model.md, contracts/, quickstart.md |
| **Phase 2: Core Implementation** | 5-7 days | P1 功能 (音频采集、WebSocket、文本注入) |
| **Phase 3: UI & Configuration** | 4-5 days | P2 悬浮窗 + P3 配置管理 |
| **Phase 4: Error Handling & Polish** | 3-4 days | P4 网络异常处理 + 性能优化 + 文档 |
| **Total** | **15-21 days** | v0.1.0 可发布版本 |

---

## Next Steps

1. **Review this plan**: 确认所有技术决策和阶段划分合理
2. **Run `/speckit.tasks`**: 生成详细的任务列表 (tasks.md)
3. **Start Phase 0**: 执行技术调研,解决所有不确定性
4. **Re-evaluate Constitution Check**: Phase 1 完成后重新审查,确保无违规

---

**Plan Version**: 1.0.0
**Created**: 2026-01-24
**Author**: ScribeFlow Planning Agent
**Status**: Ready for Review
