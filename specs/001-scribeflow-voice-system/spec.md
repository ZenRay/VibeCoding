# Feature Specification: ScribeFlow 桌面实时语音听写系统

**Feature Branch**: `001-scribeflow-voice-system`
**Created**: 2026-01-24
**Status**: Draft
**Project Root**: `~/Documents/VibeCoding/Week3`
**Spec Location**: `~/Documents/VibeCoding/specs/001-scribeflow-voice-system`
**Input**: User description: "根据 @Week3/instuctions/project.md 生成一个本项目的计划和 research。根据你了解的知识,构建一个详细的设计文文档,放在 specs/design.md文件中,输出为中文,使用 mermaid绘制架构,设计,组件、流程等图:表并详细说明。"

## Clarifications

### Session 2026-01-24

- Q: Overlay window positioning strategy - Should it follow cursor position, be fixed at screen center, use smart adaptive positioning, or be user-configurable? → A: Fixed screen center - Overlay always appears at the center of the primary display
- Q: API connection failure user experience - When WebSocket disconnects during active transcription, how should already-transcribed text be delivered to the user? → A: Clipboard only - Copy partial transcription to clipboard, notify user to paste manually

## User Scenarios & Testing *(mandatory)*

### User Story 1 - 全局热键触发即时听写 (Priority: P1)

用户在任何应用程序（如文档编辑器、邮件客户端、IDE）中工作时,按下全局快捷键（默认 `Cmd+Shift+\`）即可激活语音听写。用户说话时,系统实时将语音转换为文本并自动插入到当前光标位置,无需切换应用窗口或进行任何额外操作。

**Why this priority**: 这是系统的核心价值主张。即时、无缝的语音输入体验是用户选择使用该工具的首要原因,必须首先实现才能验证产品可行性。

**Independent Test**: 可以通过以下步骤独立测试：
1. 启动应用并保持后台运行
2. 打开任意文本编辑器（如记事本）并将光标放在文本区域
3. 按下 `Cmd+Shift+\` 快捷键
4. 说出"Hello World"
5. 验证"Hello World"文本自动出现在光标位置

**Acceptance Scenarios**:

1. **Given** 应用已启动并在后台运行,用户在文本编辑器中工作, **When** 用户按下 `Cmd+Shift+\` 并说出一段话, **Then** 系统显示悬浮窗提示"正在听",并在用户停顿后将转写文本插入到光标位置
2. **Given** 用户正在进行语音输入, **When** 用户说话过程中, **Then** 悬浮窗实时显示部分转写结果(partial transcript),让用户看到系统正在处理
3. **Given** 语音转写完成, **When** 系统收到最终转写文本(committed transcript), **Then** 文本立即插入到当前活跃应用的光标位置,整个过程延迟小于 200ms
4. **Given** 用户在密码输入框或终端等敏感区域, **When** 用户按下快捷键, **Then** 系统检测到非文本编辑区域并提示用户当前位置不适合语音输入(安全保护)

---

### User Story 2 - 悬浮窗实时反馈与可视化 (Priority: P2)

用户在语音输入过程中,屏幕上会出现一个透明悬浮窗,实时显示转写进度、音量波形和部分识别结果。这让用户清楚知道系统正在监听,并能及时发现识别错误。

**Why this priority**: 实时反馈提升用户信心和体验。虽然不是核心功能,但对于建立用户信任至关重要。在 P1 功能稳定后实现。

**Independent Test**: 可以通过以下步骤独立测试:
1. 激活语音输入
2. 在说话时观察悬浮窗是否显示波形动画
3. 验证部分转写文本是否实时更新
4. 检查悬浮窗是否固定显示在主显示器的屏幕中央位置

**Acceptance Scenarios**:

1. **Given** 用户激活语音输入, **When** 语音服务连接成功, **Then** 主显示器屏幕中央出现固定位置的半透明悬浮窗,显示"正在听"提示
2. **Given** 悬浮窗已显示, **When** 用户开始说话, **Then** 悬浮窗显示音量波形动画,波形高度反映音量大小
3. **Given** 语音识别服务返回部分转写结果, **When** 收到 `partial_transcript` 事件, **Then** 悬浮窗文本区域实时更新显示当前识别的文字(如"hel" → "hello")
4. **Given** 语音识别完成, **When** 收到 `committed_transcript` 事件, **Then** 悬浮窗显示最终文本并在 500ms 后自动淡出消失

---

### User Story 3 - 系统托盘管理与配置 (Priority: P3)

用户可以通过系统托盘图标管理应用,包括查看运行状态、打开设置界面、配置全局快捷键、输入 API 密钥,以及退出应用。应用常驻后台,不占用 Dock 或任务栏空间。

**Why this priority**: 配置管理是必要的辅助功能,但不影响核心听写体验。在核心功能稳定后添加,以支持用户个性化设置。

**Independent Test**: 可以通过以下步骤独立测试:
1. 启动应用,验证系统托盘出现图标
2. 点击托盘图标,验证菜单显示"设置"和"退出"选项
3. 点击"设置",验证弹出配置窗口
4. 在配置窗口输入 API 密钥并保存
5. 验证应用重启后配置保留

**Acceptance Scenarios**:

1. **Given** 应用启动, **When** 应用初始化完成, **Then** 系统托盘区域显示应用图标,主窗口自动隐藏
2. **Given** 用户点击托盘图标, **When** 菜单展开, **Then** 显示"设置"、"关于"和"退出"三个菜单项
3. **Given** 用户选择"设置"菜单项, **When** 设置窗口打开, **Then** 显示 API 密钥输入框、快捷键配置和语言选择等设置项
4. **Given** 用户在设置中输入有效的 ElevenLabs API 密钥, **When** 用户点击"保存", **Then** 密钥安全存储到系统钥匙串(macOS Keychain),不以明文形式保存
5. **Given** 用户点击"退出"菜单项, **When** 确认退出, **Then** 应用完全退出,停止所有后台服务和音频采集

---

### User Story 4 - 网络异常与降级处理 (Priority: P4)

当网络不稳定或 ElevenLabs 服务不可用时,系统能够优雅处理错误,向用户提示网络问题,并在网络恢复后自动重连,无需重启应用。

**Why this priority**: 容错处理提升可靠性,但在核心功能验证前不是首要任务。可在后期优化阶段实现。

**Independent Test**: 可以通过以下步骤独立测试:
1. 启动应用并确保正常工作
2. 断开网络连接
3. 尝试激活语音输入
4. 验证系统显示"网络连接失败"错误提示
5. 恢复网络连接
6. 再次激活语音输入,验证自动重连成功

**Acceptance Scenarios**:

1. **Given** 用户激活语音输入, **When** WebSocket 连接失败(网络不可达或服务端错误), **Then** 悬浮窗显示"网络连接失败,请检查网络"错误提示,并在 3 秒后自动消失
2. **Given** WebSocket 连接在语音输入过程中断开, **When** 检测到连接中断, **Then** 系统立即停止音频采集,将已转写的文本复制到剪贴板,显示通知"网络中断,已转写内容已复制到剪贴板",并尝试自动重连(最多重试 3 次)
3. **Given** 网络在断开后恢复, **When** 用户再次激活语音输入, **Then** 系统自动重新建立 WebSocket 连接,无需用户手动操作
4. **Given** API 密钥无效或配额耗尽, **When** 服务端返回鉴权错误, **Then** 系统显示"API 密钥无效或配额不足"错误,并引导用户打开设置界面更新密钥

---

### Edge Cases

- **边界条件 1**: 用户在语音输入过程中切换到另一个应用窗口
  - **处理**: 系统检测到活跃窗口变化,将转写文本插入到新的活跃窗口光标位置
  - **注意**: 需要在文本插入前重新获取活跃窗口信息,避免文本插入到错误位置

- **边界条件 2**: 用户在终端、密码框等特殊输入区域激活语音输入
  - **处理**: 通过 macOS Accessibility API 检测焦点元素类型,如果检测到安全文本框(SecureTextField)或非编辑区域,则显示警告提示,不执行文本注入

- **边界条件 3**: 用户剪贴板中有重要内容,系统需要使用剪贴板注入文本
  - **处理**: 在使用剪贴板粘贴策略前,先读取并缓存当前剪贴板内容,文本注入完成后立即恢复原有剪贴板内容,确保不破坏用户数据

- **边界条件 4**: 多个用户同时在不同设备上使用相同 API 密钥
  - **处理**: 这由 ElevenLabs 服务端处理,客户端不受影响。如果触发速率限制,返回错误提示用户

- **边界条件 5**: 用户长时间连续说话(超过 30 秒)
  - **处理**: 系统持续发送音频流,服务端会自动分段处理。客户端收到多个 `committed_transcript` 事件时,逐段插入文本,中间用空格分隔

- **边界条件 6**: macOS 缺少 Accessibility 权限
  - **处理**: 应用启动时检测权限状态。如果未授权,显示引导窗口,指示用户前往"系统偏好设置 > 安全性与隐私 > 辅助功能"添加应用到信任列表

- **边界条件 7**: 麦克风权限被拒绝
  - **处理**: 首次激活语音输入时请求麦克风权限。如果用户拒绝,显示错误提示并引导用户前往系统设置授权

- **边界条件 8**: Linux Wayland 环境下运行
  - **处理**: 检测到 Wayland 显示服务器时,显示功能限制提示,自动降级为剪贴板注入模式,禁用密码框检测功能

- **边界条件 9**: Linux 系统未安装 Secret Service (GNOME Keyring/KWallet)
  - **处理**: 检测到 Secret Service 不可用时,降级为加密文件存储 (使用 AES-256-GCM),显示安全警告建议用户安装密钥管理器

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: 系统 MUST 在用户按下全局快捷键时激活语音监听,默认快捷键为 `Cmd+Shift+\`(macOS)
- **FR-002**: 系统 MUST 在用户激活语音输入后的 50ms 内开始采集麦克风音频
- **FR-003**: 系统 MUST 将采集的音频实时流式传输到 ElevenLabs Scribe v2 API,使用 WebSocket 协议
- **FR-004**: 系统 MUST 在收到 `partial_transcript` 事件时,在悬浮窗中实时显示部分转写文本
- **FR-005**: 系统 MUST 在收到 `committed_transcript` 事件时,将最终转写文本插入到当前活跃应用的光标位置
- **FR-006**: 文本插入 MUST 在收到 `committed_transcript` 事件后 50ms 内完成
- **FR-007**: 系统 MUST 支持两种文本注入策略:键盘模拟(短文本)和剪贴板粘贴(长文本)
- **FR-008**: 使用剪贴板注入时,系统 MUST 先保存原有剪贴板内容,注入完成后立即恢复
- **FR-009**: 系统 MUST 在应用启动时检测 macOS Accessibility 权限,如未授权则引导用户授权
- **FR-010**: 系统 MUST 在应用启动时检测麦克风权限,首次使用时请求权限
- **FR-011**: 系统 MUST 在系统托盘显示应用图标,提供"设置"和"退出"菜单
- **FR-012**: 系统 MUST 提供设置界面,允许用户配置 API 密钥、快捷键和语言偏好
- **FR-013**: API 密钥 MUST 存储在系统安全存储中,不得以明文形式保存到配置文件
  - macOS: Keychain Services
  - Linux: Secret Service (GNOME Keyring / KWallet)
  - 降级: 加密文件存储 (AES-256-GCM) 如系统密钥管理器不可用
- **FR-014**: 系统 MUST 在悬浮窗显示音量波形动画,实时反映麦克风音量
- **FR-015**: 系统 MUST 将采集的音频从原生采样率(通常 48kHz)重采样到 16kHz,以符合 Scribe v2 要求
- **FR-016**: 系统 MUST 在音频采集线程中避免内存分配和网络 I/O,通过消息通道传递音频数据到异步任务
- **FR-017**: 系统 MUST 在 WebSocket 连接失败时显示错误提示,并支持自动重连(最多 3 次)
- **FR-017a**: 系统 MUST 在 WebSocket 连接在活跃转写过程中断开时,将已转写的部分文本复制到系统剪贴板,并显示通知提示用户手动粘贴
- **FR-018**: 系统 MUST 在检测到 API 密钥无效或配额不足时,显示错误并引导用户更新密钥
- **FR-019**: 系统 MUST 在用户关闭主窗口时隐藏窗口而非退出应用,保持后台运行
- **FR-020**: 系统 MUST 在文本注入前获取当前活跃窗口信息,确保文本插入到正确应用
- **FR-021**: 系统 MUST 检测焦点元素类型,对于密码框或非编辑区域显示警告而非插入文本
  - macOS: 使用 Accessibility API (AXUIElement)
  - Linux X11: 使用 AT-SPI 协议 (尽力而为)
  - Linux Wayland: 功能受限,显示通用警告由用户判断
- **FR-022**: 系统 MUST 支持中文和英文语音识别,通过配置指定 `language_code` 参数
- **FR-023**: 系统 MUST 在后台常驻时内存占用不超过 100MB(活跃转写时)
- **FR-024**: 系统 MUST 在冷启动(应用启动到可响应快捷键)耗时不超过 500ms
- **FR-025**: 系统 MUST 记录所有状态转换和错误到结构化日志,但不得记录完整转写文本(隐私保护)

### Key Entities

- **AudioStream**: 音频流,表示从麦克风采集的实时音频数据。关键属性包括采样率(原生 48kHz,目标 16kHz)、通道数(单声道)、缓冲区大小(10ms 块)。

- **TranscriptionSession**: 转写会话,表示一次完整的语音输入过程。关键属性包括会话 ID(由服务端生成)、会话状态(Connecting/Active/Ended)、开始时间、结束时间。

- **TranscriptEvent**: 转写事件,表示服务端推送的转写结果。类型包括 `partial_transcript`(部分结果)和 `committed_transcript`(最终结果)。关键属性包括事件类型、文本内容、置信度、时间戳。

- **OverlayWindow**: 悬浮窗,表示显示实时反馈的 UI 窗口。关键属性包括位置(固定在主显示器中央)、可见性(显示/隐藏)、内容(文本和波形)、透明度。

- **AppConfig**: 应用配置,表示用户的个性化设置。关键属性包括 API 密钥(引用钥匙串)、全局快捷键组合、首选语言、文本注入策略(键盘/剪贴板阈值)。

- **ActiveWindow**: 活跃窗口,表示当前用户正在操作的应用窗口。关键属性包括应用名称、窗口标题、焦点元素类型(文本框/密码框/其他)。

- **WebSocketConnection**: WebSocket 连接,表示与 ElevenLabs 服务的网络连接。关键属性包括连接状态(Disconnected/Connecting/Connected/Error)、上次心跳时间、重连次数。

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 用户从按下快捷键到开始听到音频采集反馈(悬浮窗显示)的延迟不超过 100ms
- **SC-002**: 语音转写的端到端延迟(用户停止说话到文本插入完成)不超过 200ms(网络延迟 <50ms 时)
- **SC-003**: 系统在空闲状态(仅后台运行,未激活语音输入)时内存占用不超过 50MB
- **SC-004**: 系统在活跃转写状态时内存占用不超过 100MB
- **SC-005**: 应用冷启动时间(从启动到托盘图标显示并可响应快捷键)不超过 500ms
- **SC-006**: 音频重采样精度误差不超过 0.1%(48kHz → 16kHz)
- **SC-007**: 在网络正常条件下,WebSocket 连接成功率达到 99%
- **SC-008**: 系统在连续 1 小时语音输入测试中不出现崩溃或内存泄漏
- **SC-009**: 用户在首次使用时,从启动应用到完成首次语音输入的总时长不超过 3 分钟(包括权限授权和 API 配置)
- **SC-010**: 悬浮窗 UI 渲染帧率保持在 30fps 以上,确保波形动画流畅
- **SC-011**: 剪贴板恢复成功率达到 100%(即使用剪贴板注入后,原有内容必须完整恢复)
- **SC-012**: 在 10 次连续语音输入测试中,文本插入到正确应用窗口的准确率达到 100%
- **SC-013**: 系统能够正确识别并拒绝在密码框等安全区域进行文本注入,准确率达到 95%
- **SC-014**: 用户通过托盘菜单退出应用后,所有后台进程完全终止,无残留进程

### Assumptions

1. **目标平台**:
   - **Tier 1 (完全支持)**: macOS 10.15+ 和 Linux X11 (Ubuntu 22.04+, Fedora 38+)
   - **Tier 2 (尽力支持)**: Linux Wayland (功能降级 - 强制剪贴板注入,无窗口检测)
   - **Tier 3 (计划中)**: Windows 11 (v2.0)
2. **网络环境**: 假设用户具有稳定的互联网连接,往返延迟(RTT)小于 100ms。离线模式不在当前范围内。
3. **API 访问**: 假设用户已注册 ElevenLabs 账户并获得有效的 API 密钥。免费试用额度足够初期测试。
4. **硬件要求**: 假设用户设备配备麦克风(内置或外接)且正常工作。不支持蓝牙音频设备(延迟过高)。
   - **Linux**: 需要 ALSA 驱动支持,推荐配置 PulseAudio 进行音频混合。
5. **语言支持**: 初期重点支持英文和中文。其他语言通过 ElevenLabs API 的自动检测功能支持,但未经充分测试。
6. **隐私政策**: 系统不存储、不记录、不传输任何语音数据或转写文本到非 ElevenLabs 服务器。所有音频流仅用于实时转写,转写完成后立即丢弃。
7. **系统权限**: 假设用户愿意授予应用必要权限。如果用户拒绝,应用核心功能无法使用。
   - **macOS**: 需要麦克风权限和 Accessibility 权限
   - **Linux X11**: 需要麦克风权限,文本注入无需特殊权限 (通过 XTest 扩展)
   - **Linux Wayland**: 需要麦克风权限,键盘模拟需要 libei 支持 (GNOME 46+) 或降级为剪贴板注入
8. **文本编辑器兼容性**: 系统优先保证在主流应用(VS Code、Word、Chrome、Slack)中的兼容性。部分特殊应用(如某些 Java Swing 应用)可能存在兼容性问题。
9. **性能基准**: 所有延迟和性能指标基于 2020 年后的 MacBook Pro(M1 芯片或更新)测试。旧设备可能无法达到相同性能。
10. **配额管理**: 系统不主动管理 API 配额。当配额耗尽时,依赖服务端错误提示用户。未来可考虑添加本地配额监控。
