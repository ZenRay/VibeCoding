# Tasks: ScribeFlow 桌面实时语音听写系统

**Input**: Design documents from `/specs/001-scribeflow-voice-system/`
**Project Root**: `~/Documents/VibeCoding/Week3` (源代码实现位置)
**Prerequisites**: plan.md, spec.md, research.md, data-model.md
**Branch**: `001-scribeflow-voice-system`

**Organization**: 任务按 7 个高层次阶段组织,每个任务涵盖完整功能模块。

## Format: `[ID] [P?] Description`

- **[P]**: 可并行执行 (不同文件,无依赖关系)
- 所有路径基于 `~/Documents/VibeCoding/Week3/` (Tauri 项目)

---

## Phase 1: 项目初始化与基础架构

**Purpose**: 搭建项目骨架,配置开发环境,完成 Tauri 基础设置

- [X] T001 初始化 Tauri v2 项目并配置基础架构
  - 在 `~/Documents/VibeCoding/Week3/` 创建 Tauri 项目
  - 配置 `src-tauri/Cargo.toml` 依赖: tauri 2.9, cpal 0.16, rubato 0.16.2, tokio-tungstenite 0.28, enigo 0.6.1, keyring 2.3
  - 配置 `package.json` 前端依赖: react 19.2, zustand 5.0.8, tailwindcss 4.1
  - 创建模块结构: `src-tauri/src/{audio,network,input,system,ui,config,utils}/mod.rs`
  - 配置 `tauri.conf.json`: 悬浮窗配置 (transparent, alwaysOnTop, center)
  - 配置 `capabilities/default.json`: 权限声明 (global-shortcut, clipboard-manager)
  - 配置 GitHub Actions CI: Rust 测试 + clippy lint
  - 验证: `npm run tauri dev` 启动成功,显示空白窗口

---

## Phase 2: 音频采集与重采样系统 (核心基础)

**Purpose**: 实现麦克风音频采集、环形缓冲区和 16kHz 重采样管道

- [X] T002 实现音频采集与重采样模块
  - **音频采集** (`src-tauri/src/audio/capture.rs`):
    - 使用 `cpal` 枚举默认输入设备
    - 配置音频流: 48kHz 单声道,10ms 缓冲区 (480 frames)
    - 实现零内存分配音频回调 (使用 `crossbeam::channel` 传递数据)
  - **环形缓冲区** (`src-tauri/src/audio/buffer.rs`):
    - 使用 `crossbeam::queue::ArrayQueue` 创建无锁队列 (容量 4800 samples = 100ms)
    - 实现 Producer-Consumer 模式 (音频线程 → Tokio 任务)
  - **重采样器** (`src-tauri/src/audio/resampler.rs`):
    - 使用 `rubato::FftFixedInOut` 实现 48kHz → 16kHz 重采样
    - 批量处理: 480 samples → 160 samples (10ms 块)
  - **单元测试** (`tests/unit/audio_resampler_test.rs`):
    - 测试重采样精度 (FFT 频谱分析,误差 <0.1%)
    - 测试环形缓冲区并发读写
  - 验证: `cargo test audio` 通过,音频采集延迟 <10ms

---

## Phase 3: WebSocket 客户端与协议实现

**Purpose**: 实现 ElevenLabs Scribe v2 WebSocket 通信和状态管理

- [X] T003 实现 WebSocket 客户端与协议状态机
  - **WebSocket 客户端** (`src-tauri/src/network/client.rs`):
    - 使用 `tokio-tungstenite` 建立 WSS 连接
    - 鉴权: HTTP Header `xi-api-key`
    - 查询参数: `model_id=scribe_v2_realtime&encoding=pcm_16000`
  - **协议定义** (`src-tauri/src/network/protocol.rs`):
    - 定义 Rust 结构体: `InputAudioChunk`, `SessionStarted`, `PartialTranscript`, `CommittedTranscript`
    - 实现 `serde` 序列化/反序列化
  - **状态机** (`src-tauri/src/network/state_machine.rs`):
    - 实现连接状态机: Idle → Connecting → Listening → Recording → Processing → Committing
    - 自动重连逻辑: 指数退避 (1s, 2s, 4s),最多 3 次重试
  - **集成测试** (`tests/integration/websocket_protocol_test.rs`):
    - Mock WebSocket 服务器模拟完整会话流程
    - 测试重连逻辑 (模拟连接断开)
  - 验证: `cargo test network` 通过,WebSocket 连接成功率 >99%

---

## Phase 4: 文本注入与系统集成 (P1 核心功能)

**Purpose**: 实现文本注入引擎、全局热键和权限管理 (完成 User Story 1)

- [ ] T004 实现文本注入系统与全局热键集成
  - **键盘模拟** (`src-tauri/src/input/keyboard.rs`):
    - 使用 `enigo` 模拟键盘输入,支持中文/emoji
    - 输入速度控制 (每字符 5ms 延迟)
  - **剪贴板注入** (`src-tauri/src/input/clipboard.rs`):
    - 使用 `tauri-plugin-clipboard-manager` 实现剪贴板操作
    - 流程: 保存原剪贴板 → 写入新内容 → 模拟 Cmd+V → 恢复原内容
  - **注入策略** (`src-tauri/src/input/injector.rs`):
    - 策略选择: 短文本 (<10 字符) 键盘模拟,长文本剪贴板粘贴
    - 活跃窗口检测 (使用 `active-win-pos-rs`)
    - macOS Accessibility API 密码框检测 (SecureTextField)
    - Linux 平台支持: X11 稳定,Wayland 强制剪贴板模式
  - **全局热键** (`src-tauri/src/system/hotkey.rs`):
    - 使用 `tauri-plugin-global-shortcut` 注册 `Cmd+Shift+\`
    - 回调触发 `start_transcription` Command
  - **权限管理** (`src-tauri/src/system/permissions.rs`):
    - 检测麦克风和 Accessibility 权限
    - 显示引导窗口 (Tauri Dialog)
  - **集成测试** (`tests/integration/text_injector_test.rs`):
    - 验证剪贴板恢复成功率 100%
    - 验证密码框检测准确率 >95%
  - 验证: 文本注入延迟 <50ms,热键响应 <50ms

---

## Phase 5: Tauri Commands 与端到端集成

**Purpose**: 实现前后端通信接口,完成核心转写流程 (User Story 1 完整实现)

- [ ] T005 实现 Tauri Commands 和端到端转写流程
  - **Tauri Commands** (`src-tauri/src/ui/commands.rs`):
    - `start_transcription()`: 启动音频采集 + WebSocket 连接
    - `stop_transcription()`: 停止采集
    - `save_config(config: AppConfig)`: 保存配置到 `tauri-plugin-store` 和 Keychain
    - `check_permissions()`: 返回权限状态
  - **Tauri Events** (后端 → 前端):
    - `audio_level_update { level: f32 }`: 音量更新 (50ms 间隔)
    - `partial_transcript { text: String }`: 部分转写
    - `committed_transcript { text: String }`: 最终转写
    - `connection_status { state: ConnectionState }`: 连接状态变化
    - `error { code, message }`: 错误通知
  - **全局状态管理** (`src-tauri/src/lib.rs`):
    - 使用 `DashMap` 管理会话状态
    - 使用 `ArcSwap` 管理配置 (AppConfig)
  - **配置存储** (`src-tauri/src/config/store.rs`):
    - API 密钥存储到 Keychain (macOS Keychain / Linux Secret Service / Linux 降级 AES-256-GCM 加密文件)
    - 其他配置存储到 `tauri-plugin-store` (JSON)
  - **集成测试** (`tests/integration/end_to_end_test.rs`):
    - 完整流程测试: 热键 → 采集 → 转写 → 注入
    - 测试端到端延迟 <200ms (良好网络环境)
  - 验证: P1 功能完整可用,延迟 <200ms,内存 <100MB

---

## Phase 6: 前端 UI 与悬浮窗实现 (P2 + P3 功能)

**Purpose**: 实现悬浮窗实时反馈、系统托盘和设置面板

- [ ] T006 实现前端 UI 组件和系统托盘
  - **悬浮窗组件** (`src/components/OverlayWindow.tsx`):
    - 固定位置在主显示器屏幕中央
    - 半透明背景 (CSS: `background: rgba(0,0,0,0.8)`)
    - 淡入淡出动画 (CSS transitions)
  - **波形可视化** (`src/components/WaveformVisualizer.tsx`):
    - Canvas 波形绘制,音量数据来自 `audio_level_update` 事件
    - 30fps 刷新率 (使用 `requestAnimationFrame`)
  - **转写文本显示** (`src/components/TranscriptDisplay.tsx`):
    - 实时显示 `partial_transcript` (覆盖前一个)
    - 显示 `committed_transcript` (标记为"已确认")
    - 文本淡入淡出动画
  - **状态管理** (`src/stores/transcriptStore.ts`):
    - 使用 Zustand 管理全局状态
    - 监听 Tauri Events (`src/hooks/useTauriEvents.ts`)
  - **系统托盘** (`src-tauri/src/ui/tray.rs`):
    - 托盘图标和菜单 ("设置", "关于", "退出")
    - 窗口隐藏逻辑 (关闭窗口不退出应用)
  - **设置面板** (`src/components/SettingsPanel.tsx`):
    - API 密钥输入框 (密码类型)
    - 快捷键配置,语言选择 (中文/英文/自动)
    - 保存按钮调用 `save_config` Command
  - 验证: 悬浮窗动画流畅 (30fps),托盘功能正常,配置持久化成功 (P2 + P3 完成)

---

## Phase 7: 错误处理、日志与优化 (P4 功能 + Polish)

**Purpose**: 实现网络异常处理、结构化日志和性能优化

- [ ] T007 实现错误处理、日志系统和最终优化
  - **网络错误处理**:
    - 连接失败 → 显示错误通知 (Toast)
    - 连接中断 → 剪贴板回退 + 自动重连 (最多 3 次)
    - API 限流 (429) → 显示配额不足提示
  - **错误通知组件** (React Toast 库):
    - 错误消息本地化,3 秒自动消失
  - **结构化日志** (`src-tauri/src/utils/logger.rs`):
    - 使用 `tracing` crate
    - 滚动文件日志 (`~/.scribeflow/logs/app.log`,最大 10MB,轮转 3 个文件)
    - 日志级别: ERROR, WARN, INFO, DEBUG
    - 隐私保护: 不记录完整转写文本,不记录 API 密钥
  - **性能优化**:
    - 音频采集线程优先级设置
    - WebSocket 消息批处理 (100ms 累积后发送)
    - 悬浮窗渲染优化 (Canvas 缓存)
  - **压力测试** (`tests/integration/stress_test.rs`):
    - 连续 1 小时转写 (验证无内存泄漏)
    - 100 次连续热键触发 (验证无资源泄漏)
  - **文档更新**:
    - 更新 `README.md`: 项目简介、安装指南、使用说明、截图
    - 生成 `CHANGELOG.md`: 版本 0.1.0 功能列表
  - 验证: 所有性能目标达成 (延迟 <200ms,内存 <100MB,CPU <15%),压力测试通过,P4 功能完成

---

## 依赖关系与执行顺序

### Phase 依赖

```
T001 (项目初始化)
 ↓
T002 (音频系统) [P] T003 (WebSocket)  ← 可并行执行
 ↓                ↓
T004 (文本注入) ← 依赖 T002, T003
 ↓
T005 (Tauri Commands) ← 依赖 T004 (核心功能完整)
 ↓
T006 (前端 UI) [P] T007 (错误处理)  ← 可并行执行
```

### User Story 映射

- **T001-T005**: User Story 1 (P1) - 全局热键触发即时听写
- **T006**: User Story 2 (P2) + User Story 3 (P3) - 悬浮窗 + 托盘配置
- **T007**: User Story 4 (P4) - 网络异常处理 + Polish

### 并行机会

- **T002 和 T003**: 音频系统和 WebSocket 客户端可并行开发 (不同模块)
- **T006 和 T007**: 前端 UI 和错误处理可并行开发 (前端 vs 后端)

---

## 实施策略

### MVP 优先 (仅 T001-T005)

1. 完成 T001: 项目初始化
2. 并行完成 T002 (音频) 和 T003 (WebSocket)
3. 完成 T004: 文本注入系统
4. 完成 T005: Tauri Commands 集成
5. **STOP 验证**: 命令行版本可用 (无 UI,通过日志验证转写和注入)
6. 用户可测试核心功能: 按热键 → 说话 → 文本自动插入

### 完整版本 (T001-T007)

1. 在 MVP 基础上完成 T006: 前端 UI (悬浮窗 + 托盘 + 设置)
2. 完成 T007: 错误处理和优化
3. **最终验证**: 完整桌面应用,所有 P1-P4 用户故事可用
4. 发布 v0.1.0

---

## 检查点

- **T001 完成**: 项目骨架搭建完成,`npm run tauri dev` 可启动
- **T002 完成**: 音频采集可用,`cargo test audio` 通过
- **T003 完成**: WebSocket 客户端可用,`cargo test network` 通过
- **T005 完成**: MVP 可用,核心转写功能工作 (User Story 1)
- **T006 完成**: 完整 UI 可用 (User Story 2 + 3)
- **T007 完成**: 生产就绪 (User Story 4),可发布 v0.1.0

---

## 注意事项

- 所有路径基于 `~/Documents/VibeCoding/Week3/`
- 使用 Rust 2024 edition,零 `unsafe` 代码,零 `.unwrap()`/`.expect()`
- 音频线程禁止内存分配和 I/O 操作
- API 密钥必须存储到系统 Keychain,不得明文保存
- 日志不得记录完整转写文本 (隐私保护)
- 每个 Task 完成后运行相关测试验证
- 遵循 `.specify/memory/constitution.md` 所有原则

---

**总任务数**: 7 个高层次任务
**估计时间**: 15-21 天
**MVP 范围**: T001-T005 (约 8-12 天)
**完整版本**: T001-T007 (约 15-21 天)
**下一步**: 执行 T001 初始化项目
