# ScribeFlow - 当前状态

**Last Updated**: 2026-01-27  
**Branch**: `001-scribeflow-voice-system`  
**状态**: ✅ 核心功能完成，可发布 v0.1.0（有平台降级与环境依赖限制）

---

## ✅ 已完成（按需求）

### P1 即时听写
- 全局热键/按钮启动听写
- 实时语音转文本（partial + committed）
- 智能文本注入（键盘/剪贴板）
- 密码框/非编辑控件注入阻断（macOS + Linux best‑effort）

### P2 悬浮窗反馈
- 录音悬浮窗 + 波形（稳定布局）
- 录音下方实时显示转录结果
- 连接状态/通知提示

### P3 系统集成
- 托盘菜单（含 Start/Stop、Settings、About）
- 设置面板（API Key、语言、代理）
- Keyring + 加密文件降级存储
- 权限检查与引导

### P4 错误处理
- 断线重连（带退避）
- 结构化日志（脱敏）
- 错误提示与自动消退

---

## ⚠️ 现存限制/降级

1. **Wayland 自动注入**  
   Wayland 受限，无法可靠“自动输入到光标”，仅支持剪贴板模式（需要用户手动粘贴）。

2. **Wayland 全局热键**  
   在部分 Wayland 会话不可用，需使用 UI/托盘按钮作为替代入口。

3. **Linux 焦点控件检测（AT‑SPI）**  
   已接入 AT‑SPI 进行 best‑effort 识别，部分应用可能无法识别或误判。

4. **Windows 支持**  
   未进行完整测试（Tier 3）。

---

## 🧪 已执行测试

- `cargo test --manifest-path Week3/src-tauri/Cargo.toml` ✅

> 说明：涉及真实 API key 或显示服务器的测试仍依赖本地环境条件。

---

## 🔧 建议的下一步（可选）

- 在 Wayland 环境补充用户引导（提示需要粘贴或切换到 X11）。
- 若要扩展平台支持：增加 Windows 实测与修复清单。

