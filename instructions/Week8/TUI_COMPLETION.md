# Plan TUI 完成说明

**日期**: 2026-02-11  
**范围**: design.md Phase 6 / GAP_ANALYSIS Phase 4 — Plan 交互式 TUI

---

## 已完成内容

### 1. ca-core 扩展

- **TuiEvent::StatsUpdate**：新增 `{ turns, cost_usd }`，供 TUI 显示统计栏。

### 2. Plan TUI 应用 (`apps/ca-cli/src/ui/`)

| 文件 | 说明 |
|------|------|
| `plan_app.rs` | PlanApp 状态、3 区域布局 (标题/对话/输入/Stats)、非阻塞事件循环、UserMessage/UserMessage 处理、键盘 (Enter/Ctrl+C/↑↓) |
| `plan_worker.rs` | PlanWorker：接收 UserMessage::Input(描述)，执行 plan 流程 (创建 feature 目录、Engine+TuiEventHandler、PromptManager、execute_phase_with_config)，向 TUI 发送 TuiEvent |
| `mod.rs` | `execute_plan_tui()`：spawn_blocking(TUI) + tokio::spawn(Worker)，mpsc 双 channel，tokio::select! 等待任一方结束 |

### 3. 与 plan 命令集成

- **触发条件**：`code-agent plan <slug> --interactive` 且未传 `--description` 时，调用 `execute_plan_tui()`，不再走 stdin 交互。
- **行为**：进入全屏 TUI，输入功能描述并回车后，Worker 执行 plan 阶段，流式/工具/完成/统计通过 TuiEventHandler 推送到界面。

### 4. 设计对照

- ✅ 3 区域布局：Chat（对话）+ Input（输入）+ Stats（Turns/Cost）
- ✅ 非阻塞事件循环：100ms poll + `event_rx.try_recv()`
- ✅ 并发模型：TUI Task（spawn_blocking）+ Worker Task（tokio::spawn），mpsc 通信
- ✅ TUI → Worker：UserMessage (Input / Quit)
- ✅ Worker → TUI：TuiEvent (StreamText, ToolUse, ToolResult, Error, Complete, StatsUpdate)
- ✅ 键盘：Enter 发送、Ctrl+C/Esc 退出、↑↓ 历史

---

## 使用方式

```bash
code-agent plan my-feature --interactive
# 进入 TUI，输入功能描述后回车执行 plan
```

非交互或已提供描述时仍走原有 CLI 流程。

---

## 未实现（可选）

- **Run TUI**：design 中的 Run 进度 TUI 未实现，仍为 CLI 输出；可留作后续迭代。
- **对话历史持久化、滚动**：当前仅内存历史，未做滚动条/持久化。

---

## 测试与构建

- `cargo build -p ca-cli` 通过
- `cargo test -p ca-core -p ca-cli` 全部通过
