# Tauri Commands API 规范

**版本**: 1.0.0
**日期**: 2026-01-24
**Tauri 版本**: v2.9.5

本文档定义了 ScribeFlow 前端 (React/TypeScript) 与后端 (Rust) 之间的 Tauri Commands API 契约。

---

## 目录

1. [Commands 概述](#commands-概述)
2. [转写控制 Commands](#转写控制-commands)
3. [配置管理 Commands](#配置管理-commands)
4. [权限检查 Commands](#权限检查-commands)
5. [Tauri Events (后端 → 前端)](#tauri-events-后端--前端)
6. [TypeScript 类型定义](#typescript-类型定义)
7. [错误处理](#错误处理)

---

## Commands 概述

### 命名约定

- **snake_case**: Rust 函数名使用 snake_case (如 `start_transcription`)
- **调用方式**: 前端通过 `invoke('command_name', { args })` 调用
- **返回值**: 所有 Commands 返回 `Result<T, String>`,错误以字符串形式传递

### 权限声明

所有 Commands 必须在 `src-tauri/capabilities/default.json` 中声明权限:

```json
{
  "identifier": "default",
  "description": "Default capabilities for ScribeFlow",
  "windows": ["main", "overlay"],
  "permissions": [
    "core:window:allow-show",
    "core:window:allow-hide",
    "global-shortcut:allow-register",
    "clipboard-manager:allow-read-text",
    "clipboard-manager:allow-write-text"
  ]
}
```

---

## 转写控制 Commands

### 1. start_transcription

**描述**: 启动音频采集和 WebSocket 连接,开始语音转写。

**Rust 签名**:

```rust
#[tauri::command]
async fn start_transcription(
    state: tauri::State<'_, AppState>,
    app: tauri::AppHandle,
) -> Result<(), String>
```

**前端调用**:

```typescript
import { invoke } from '@tauri-apps/api/core';

try {
  await invoke('start_transcription');
  console.log('Transcription started successfully');
} catch (error) {
  console.error('Failed to start transcription:', error);
  // error 是字符串类型的错误消息
}
```

**行为流程**:

1. 检查 macOS Accessibility 权限
2. 检查麦克风权限
3. 枚举音频输入设备
4. 启动 cpal 音频流
5. 建立 WebSocket 连接到 ElevenLabs
6. 触发 `connection_status` 事件通知前端状态变化

**可能的错误**:

| 错误码 | 错误消息 | 原因 | 用户操作 |
|-------|---------|------|---------|
| `PERMISSION_DENIED` | "需要辅助功能权限" | Accessibility 权限未授权 | 前往系统设置授权 |
| `AUDIO_DEVICE_ERROR` | "未检测到麦克风设备" | 音频设备不可用 | 检查麦克风连接 |
| `WEBSOCKET_ERROR` | "网络连接失败" | 无法连接到 ElevenLabs API | 检查网络和 API 密钥 |
| `ALREADY_RUNNING` | "转写会话已在运行中" | 重复调用 | 先调用 `stop_transcription` |

**Rust 实现示例**:

```rust
use tauri::{State, AppHandle, Manager};

#[derive(Default)]
pub struct AppState {
    pub session: Arc<Mutex<Option<TranscriptionSession>>>,
    pub audio: Arc<Mutex<Option<AudioStream>>>,
    pub websocket: Arc<Mutex<Option<WebSocketConnection>>>,
}

#[tauri::command]
async fn start_transcription(
    state: State<'_, AppState>,
    app: AppHandle,
) -> Result<(), String> {
    // 1. 检查权限
    if !check_accessibility_permission() {
        return Err("PERMISSION_DENIED: 需要辅助功能权限".to_string());
    }

    // 2. 检查是否已在运行
    let mut session = state.session.lock().await;
    if session.is_some() {
        return Err("ALREADY_RUNNING: 转写会话已在运行中".to_string());
    }

    // 3. 启动音频采集
    let audio_stream = audio::capture::start()
        .await
        .map_err(|e| format!("AUDIO_DEVICE_ERROR: {}", e))?;

    // 4. 建立 WebSocket 连接
    let api_key = keychain::get_api_key()
        .map_err(|e| format!("CONFIG_ERROR: {}", e))?;

    let ws_client = network::client::connect(&api_key)
        .await
        .map_err(|e| format!("WEBSOCKET_ERROR: {}", e))?;

    // 5. 创建会话
    let mut new_session = TranscriptionSession::new();
    new_session.audio_stream = Some(audio_stream);
    new_session.websocket_conn = Some(ws_client);

    *session = Some(new_session);

    // 6. 触发状态事件
    app.emit("connection_status", ConnectionStatus::Connecting)
        .map_err(|e| format!("EVENT_ERROR: {}", e))?;

    tracing::info!("Transcription started");

    Ok(())
}
```

---

### 2. stop_transcription

**描述**: 停止音频采集和 WebSocket 连接,结束当前转写会话。

**Rust 签名**:

```rust
#[tauri::command]
async fn stop_transcription(
    state: tauri::State<'_, AppState>,
    app: tauri::AppHandle,
) -> Result<(), String>
```

**前端调用**:

```typescript
try {
  await invoke('stop_transcription');
  console.log('Transcription stopped');
} catch (error) {
  console.error('Failed to stop:', error);
}
```

**行为流程**:

1. 停止 cpal 音频流
2. 断开 WebSocket 连接 (发送 Close frame)
3. 清理会话状态
4. 触发 `connection_status` 事件 (Disconnected)

**可能的错误**:

| 错误码 | 错误消息 | 原因 |
|-------|---------|------|
| `NOT_RUNNING` | "当前没有运行中的转写会话" | 未调用 `start_transcription` |

**Rust 实现示例**:

```rust
#[tauri::command]
async fn stop_transcription(
    state: State<'_, AppState>,
    app: AppHandle,
) -> Result<(), String> {
    let mut session = state.session.lock().await;

    if let Some(mut s) = session.take() {
        // 停止音频采集
        if let Some(mut audio) = s.audio_stream.take() {
            audio.stop().map_err(|e| format!("AUDIO_ERROR: {}", e))?;
        }

        // 断开 WebSocket
        if let Some(mut ws) = s.websocket_conn.take() {
            ws.disconnect().await.map_err(|e| format!("WEBSOCKET_ERROR: {}", e))?;
        }

        // 触发事件
        app.emit("connection_status", ConnectionStatus::Disconnected)
            .map_err(|e| format!("EVENT_ERROR: {}", e))?;

        tracing::info!("Transcription stopped");

        Ok(())
    } else {
        Err("NOT_RUNNING: 当前没有运行中的转写会话".to_string())
    }
}
```

---

## 配置管理 Commands

### 3. save_config

**描述**: 保存用户配置到持久化存储,API 密钥存储到 macOS Keychain。

**Rust 签名**:

```rust
#[tauri::command]
async fn save_config(
    config: AppConfig,
    state: tauri::State<'_, AppState>,
) -> Result<(), String>
```

**前端调用**:

```typescript
import { invoke } from '@tauri-apps/api/core';

interface AppConfig {
  apiKey: string;
  globalHotkey: {
    modifiers: string[];
    key: string;
  };
  language: 'en' | 'zh' | 'auto';
  injectionStrategy: {
    shortTextThreshold: number;
    preserveClipboard: boolean;
  };
  enableWaveform: boolean;
  overlayOpacity: number;
}

const config: AppConfig = {
  apiKey: 'sk_xxx',
  globalHotkey: {
    modifiers: ['Cmd', 'Shift'],
    key: 'Backslash',
  },
  language: 'zh',
  injectionStrategy: {
    shortTextThreshold: 10,
    preserveClipboard: true,
  },
  enableWaveform: true,
  overlayOpacity: 0.85,
};

try {
  await invoke('save_config', { config });
  console.log('Config saved');
} catch (error) {
  console.error('Failed to save config:', error);
}
```

**行为流程**:

1. 验证配置有效性 (`validate()`)
2. 提取 API 密钥,存储到 macOS Keychain
3. 其他配置存储到 `tauri-plugin-store` (JSON 文件)
4. 触发 `config_updated` 事件

**可能的错误**:

| 错误码 | 错误消息 | 原因 |
|-------|---------|------|
| `INVALID_CONFIG` | "配置验证失败: ..." | 配置不符合验证规则 |
| `KEYCHAIN_ERROR` | "无法保存到钥匙串" | macOS Keychain 访问失败 |
| `STORE_ERROR` | "无法写入配置文件" | 文件系统权限问题 |

**Rust 实现示例**:

```rust
use serde::{Deserialize, Serialize};
use tauri_plugin_store::StoreExt;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AppConfig {
    pub api_key: String,
    pub global_hotkey: HotkeyConfig,
    pub language: String,
    pub injection_strategy: InjectionStrategy,
    pub enable_waveform: bool,
    pub overlay_opacity: f32,
}

#[tauri::command]
async fn save_config(
    config: AppConfig,
    state: State<'_, AppState>,
    app: AppHandle,
) -> Result<(), String> {
    // 1. 验证配置
    config.validate()
        .map_err(|e| format!("INVALID_CONFIG: {}", e))?;

    // 2. 保存 API 密钥到 Keychain
    keychain::save_api_key(&config.api_key)
        .map_err(|e| format!("KEYCHAIN_ERROR: {}", e))?;

    // 3. 保存其他配置到 Store
    let store = app.store("config.json")
        .map_err(|e| format!("STORE_ERROR: {}", e))?;

    let config_without_key = AppConfig {
        api_key: String::new(), // 不存储 API 密钥到文件
        ..config
    };

    store.set("config", serde_json::to_value(config_without_key).unwrap());
    store.save()
        .map_err(|e| format!("STORE_ERROR: {}", e))?;

    // 4. 触发事件
    app.emit("config_updated", ())
        .map_err(|e| format!("EVENT_ERROR: {}", e))?;

    tracing::info!("Config saved successfully");

    Ok(())
}
```

---

### 4. load_config

**描述**: 从持久化存储加载用户配置,API 密钥从 macOS Keychain 读取。

**Rust 签名**:

```rust
#[tauri::command]
async fn load_config(
    state: tauri::State<'_, AppState>,
    app: tauri::AppHandle,
) -> Result<AppConfig, String>
```

**前端调用**:

```typescript
try {
  const config = await invoke<AppConfig>('load_config');
  console.log('Config loaded:', config);
  // config.apiKey 将是空字符串 (安全考虑,不返回 API 密钥)
} catch (error) {
  console.error('Failed to load config:', error);
  // 如果配置不存在,返回默认配置
}
```

**行为流程**:

1. 从 `tauri-plugin-store` 读取配置 JSON
2. 从 macOS Keychain 读取 API 密钥
3. 合并返回完整配置 (但 API 密钥字段为空,安全考虑)

**可能的错误**:

| 错误码 | 错误消息 | 原因 |
|-------|---------|------|
| `CONFIG_NOT_FOUND` | "配置文件不存在" | 首次启动,尚未保存配置 |
| `PARSE_ERROR` | "配置文件格式错误" | JSON 解析失败 |

**Rust 实现示例**:

```rust
#[tauri::command]
async fn load_config(
    state: State<'_, AppState>,
    app: AppHandle,
) -> Result<AppConfig, String> {
    let store = app.store("config.json")
        .map_err(|e| format!("STORE_ERROR: {}", e))?;

    // 读取配置
    let config: AppConfig = store.get("config")
        .ok_or("CONFIG_NOT_FOUND: 配置文件不存在".to_string())
        .and_then(|v| serde_json::from_value(v)
            .map_err(|e| format!("PARSE_ERROR: {}", e)))?;

    // 不返回 API 密钥 (安全考虑)
    let safe_config = AppConfig {
        api_key: String::new(),
        ..config
    };

    Ok(safe_config)
}
```

---

## 权限检查 Commands

### 5. check_permissions

**描述**: 检查 macOS 权限状态 (麦克风、Accessibility)。

**Rust 签名**:

```rust
#[tauri::command]
fn check_permissions() -> Result<PermissionStatus, String>
```

**前端调用**:

```typescript
interface PermissionStatus {
  microphone: boolean;
  accessibility: boolean;
  screenRecording: boolean; // 可选,仅用于窗口标题
}

try {
  const status = await invoke<PermissionStatus>('check_permissions');
  console.log('Microphone:', status.microphone);
  console.log('Accessibility:', status.accessibility);

  if (!status.accessibility) {
    // 显示引导 UI
    showPermissionGuide();
  }
} catch (error) {
  console.error('Failed to check permissions:', error);
}
```

**行为流程**:

1. 检查麦克风权限 (通过 cpal 或 AVFoundation)
2. 检查 Accessibility 权限 (通过 `macos-accessibility-client`)
3. 可选: 检查 Screen Recording 权限

**Rust 实现示例**:

```rust
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PermissionStatus {
    pub microphone: bool,
    pub accessibility: bool,
    pub screen_recording: bool,
}

#[tauri::command]
fn check_permissions() -> Result<PermissionStatus, String> {
    use macos_accessibility_client::accessibility;

    let status = PermissionStatus {
        microphone: check_microphone_permission(),
        accessibility: accessibility::application_is_trusted(),
        screen_recording: check_screen_recording_permission(),
    };

    tracing::info!(
        "Permission check: microphone={}, accessibility={}, screen_recording={}",
        status.microphone,
        status.accessibility,
        status.screen_recording
    );

    Ok(status)
}

fn check_microphone_permission() -> bool {
    // macOS 麦克风权限检查
    // 实现省略...
    true
}

fn check_screen_recording_permission() -> bool {
    // macOS Screen Recording 权限检查
    // 实现省略...
    false
}
```

---

### 6. request_accessibility_permission

**描述**: 请求 Accessibility 权限 (显示系统弹窗引导)。

**Rust 签名**:

```rust
#[tauri::command]
fn request_accessibility_permission() -> Result<(), String>
```

**前端调用**:

```typescript
try {
  await invoke('request_accessibility_permission');
  console.log('Permission request dialog shown');
} catch (error) {
  console.error('Failed to request permission:', error);
}
```

**Rust 实现示例**:

```rust
#[tauri::command]
fn request_accessibility_permission() -> Result<(), String> {
    use macos_accessibility_client::accessibility;

    // 显示系统权限请求弹窗
    let _ = accessibility::application_is_trusted_with_prompt();

    Ok(())
}
```

---

## Tauri Events (后端 → 前端)

### Event 列表

| Event 名称 | Payload 类型 | 触发时机 | 描述 |
|-----------|-------------|---------|------|
| `audio_level_update` | `{ level: number }` | 每 50ms | 音量级别更新 (0.0 ~ 1.0) |
| `partial_transcript` | `{ text: string }` | 实时 | 部分转写结果 |
| `committed_transcript` | `{ text: string, confidence: number }` | VAD 检测停顿后 | 最终转写结果 |
| `connection_status` | `string` | 状态变化时 | 连接状态: "connecting", "connected", "disconnected", "error" |
| `error` | `{ code: string, message: string }` | 错误发生时 | 错误通知 |
| `config_updated` | `null` | 配置保存后 | 配置已更新 |

### 前端监听示例

```typescript
import { listen } from '@tauri-apps/api/event';

// 监听音量更新
const unlistenAudioLevel = await listen<{ level: number }>('audio_level_update', (event) => {
  console.log('Audio level:', event.payload.level);
  updateWaveform(event.payload.level);
});

// 监听部分转写
const unlistenPartial = await listen<{ text: string }>('partial_transcript', (event) => {
  console.log('Partial:', event.payload.text);
  updateOverlayText(event.payload.text, false);
});

// 监听最终转写
const unlistenCommitted = await listen<{ text: string; confidence: number }>('committed_transcript', (event) => {
  console.log('Committed:', event.payload.text, event.payload.confidence);
  updateOverlayText(event.payload.text, true);
});

// 监听连接状态
const unlistenStatus = await listen<string>('connection_status', (event) => {
  console.log('Connection status:', event.payload);
  setConnectionState(event.payload);
});

// 监听错误
const unlistenError = await listen<{ code: string; message: string }>('error', (event) => {
  console.error('Error:', event.payload.code, event.payload.message);
  showErrorNotification(event.payload);
});

// 清理监听器
window.addEventListener('beforeunload', () => {
  unlistenAudioLevel();
  unlistenPartial();
  unlistenCommitted();
  unlistenStatus();
  unlistenError();
});
```

### Rust 触发事件示例

```rust
use tauri::{Manager, AppHandle};

// 触发音量更新事件
app.emit("audio_level_update", serde_json::json!({ "level": 0.75 }))
    .map_err(|e| format!("EVENT_ERROR: {}", e))?;

// 触发转写事件
app.emit("committed_transcript", serde_json::json!({
    "text": "你好世界",
    "confidence": 0.98
})).map_err(|e| format!("EVENT_ERROR: {}", e))?;

// 触发错误事件
app.emit("error", serde_json::json!({
    "code": "WEBSOCKET_ERROR",
    "message": "网络连接失败"
})).map_err(|e| format!("EVENT_ERROR: {}", e))?;
```

---

## TypeScript 类型定义

### 完整类型定义文件

```typescript
// src/types/tauri.ts

/**
 * 应用配置
 */
export interface AppConfig {
  /** API 密钥 (加载时为空,仅保存时提供) */
  apiKey: string;

  /** 全局快捷键配置 */
  globalHotkey: HotkeyConfig;

  /** 首选语言 */
  language: 'en' | 'zh' | 'auto';

  /** 文本注入策略 */
  injectionStrategy: InjectionStrategy;

  /** 是否启用波形可视化 */
  enableWaveform: boolean;

  /** 悬浮窗透明度 (0.0 ~ 1.0) */
  overlayOpacity: number;
}

/**
 * 快捷键配置
 */
export interface HotkeyConfig {
  /** 修饰键 (Cmd, Shift, Alt, Ctrl) */
  modifiers: string[];

  /** 主键 */
  key: string;
}

/**
 * 注入策略配置
 */
export interface InjectionStrategy {
  /** 短文本阈值 (字符数) */
  shortTextThreshold: number;

  /** 是否保存原剪贴板内容 */
  preserveClipboard: boolean;
}

/**
 * 权限状态
 */
export interface PermissionStatus {
  /** 麦克风权限 */
  microphone: boolean;

  /** Accessibility 权限 */
  accessibility: boolean;

  /** Screen Recording 权限 (可选) */
  screenRecording: boolean;
}

/**
 * 连接状态
 */
export type ConnectionState =
  | 'disconnected'
  | 'connecting'
  | 'connected'
  | 'error'
  | 'reconnecting';

/**
 * 错误 Payload
 */
export interface ErrorPayload {
  /** 错误码 */
  code: string;

  /** 错误消息 */
  message: string;
}

/**
 * 音量更新 Payload
 */
export interface AudioLevelPayload {
  /** 音量级别 (0.0 ~ 1.0) */
  level: number;
}

/**
 * 部分转写 Payload
 */
export interface PartialTranscriptPayload {
  /** 部分转写文本 */
  text: string;
}

/**
 * 最终转写 Payload
 */
export interface CommittedTranscriptPayload {
  /** 最终转写文本 */
  text: string;

  /** 置信度 (0.0 ~ 1.0) */
  confidence: number;
}
```

---

## 错误处理

### 错误码规范

| 错误码前缀 | 类型 | 示例 | 处理方式 |
|----------|------|------|---------|
| `PERMISSION_` | 权限错误 | `PERMISSION_DENIED` | 显示引导 UI |
| `AUDIO_` | 音频错误 | `AUDIO_DEVICE_ERROR` | 检查设备连接 |
| `WEBSOCKET_` | 网络错误 | `WEBSOCKET_ERROR` | 自动重连 |
| `CONFIG_` | 配置错误 | `CONFIG_NOT_FOUND` | 使用默认配置 |
| `ALREADY_` | 状态冲突 | `ALREADY_RUNNING` | 提示用户 |
| `NOT_` | 状态缺失 | `NOT_RUNNING` | 忽略或提示 |

### 前端错误处理模式

```typescript
import { invoke } from '@tauri-apps/api/core';

async function startTranscription() {
  try {
    await invoke('start_transcription');
    toast.success('语音输入已启动');
  } catch (error) {
    const errorMessage = error as string;

    if (errorMessage.includes('PERMISSION_DENIED')) {
      showPermissionGuide();
    } else if (errorMessage.includes('AUDIO_DEVICE_ERROR')) {
      toast.error('未检测到麦克风设备');
    } else if (errorMessage.includes('WEBSOCKET_ERROR')) {
      toast.error('网络连接失败,请检查网络');
    } else if (errorMessage.includes('ALREADY_RUNNING')) {
      toast.info('语音输入已在运行中');
    } else {
      toast.error(`启动失败: ${errorMessage}`);
    }
  }
}
```

---

## 总结

### Commands 统计

| 类别 | Commands 数量 |
|------|-------------|
| 转写控制 | 2 |
| 配置管理 | 2 |
| 权限检查 | 2 |
| **总计** | **6** |

### Events 统计

| 类别 | Events 数量 |
|------|-----------|
| 实时数据 | 3 (audio_level, partial, committed) |
| 状态通知 | 2 (connection_status, error) |
| 配置 | 1 (config_updated) |
| **总计** | **6** |

### 关键要点

1. **类型安全**: 所有 Payloads 都有明确的 TypeScript 类型定义
2. **错误处理**: 统一的错误码规范,便于前端分类处理
3. **事件驱动**: 后端状态变化通过 Events 通知前端,避免轮询
4. **权限管理**: 显式的权限检查 Commands,提升用户体验
5. **配置隔离**: API 密钥存储在 Keychain,不通过前端传递

---

**API 版本**: 1.0.0
**最后更新**: 2026-01-24
**状态**: Complete
