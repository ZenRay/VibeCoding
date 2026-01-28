# ScribeFlow (Week3)

基于 Tauri v2 + React 的桌面实时语音听写应用（ElevenLabs Scribe v2）。

## 功能概览

- 实时转写（partial + committed）
- 悬浮窗 + 波形显示
- 系统托盘（Start/Stop、Settings、About）
- 文本注入（键盘/剪贴板）
- API Key 安全存储（Keyring + 加密文件降级）

## 环境要求

- Rust 1.77+
- Node.js 20.19+（推荐使用 nvm）
- macOS 10.15+ / Linux (Ubuntu 22.04+，X11 推荐)

## 开发

```bash
npm run tauri dev
```

## 构建

```bash
npm run tauri build
```

## 测试

```bash
cargo test --manifest-path src-tauri/Cargo.toml
npm test
```

## 已知限制

- Wayland：热键与自动注入受限，需使用托盘按钮并手动粘贴
- Windows：尚未完整验证（Tier 3）

## 相关文档

- `specs/001-scribeflow-voice-system/CURRENT_STATUS.md`
- `specs/001-scribeflow-voice-system/quickstart.md`
