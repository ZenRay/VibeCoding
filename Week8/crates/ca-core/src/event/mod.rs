//! 事件处理器模块
//!
//! 提供了流式输出和 TUI 更新的事件处理机制。

use std::io::{self, Write};
use tokio::sync::mpsc;

/// 事件处理器 trait
///
/// 用于实时流式输出和 TUI 更新,支持在 Agent 执行过程中接收各种事件通知。
pub trait EventHandler: Send + Sync {
    /// 处理流式文本输出
    ///
    /// 当 Agent 生成文本内容时调用,支持实时显示。
    fn on_text(&mut self, text: &str);

    /// 处理工具调用事件
    ///
    /// 当 Agent 调用工具时通知,包含工具名称和输入参数。
    fn on_tool_use(&mut self, tool: &str, input: &serde_json::Value);

    /// 处理工具结果事件
    ///
    /// 当工具执行完成并返回结果时调用。
    fn on_tool_result(&mut self, result: &str);

    /// 处理错误事件
    ///
    /// 当执行过程中发生错误时调用。
    fn on_error(&mut self, error: &str);

    /// 处理完成事件
    ///
    /// 当整个执行流程完成时调用。
    fn on_complete(&mut self);
}

/// CLI 事件处理器
///
/// 直接输出到 stdout 的简单实现,适用于命令行界面。
/// 所有输出都会立即刷新到终端。
pub struct CliEventHandler;

impl CliEventHandler {
    /// 创建新的 CLI 事件处理器
    pub fn new() -> Self {
        Self
    }
}

impl Default for CliEventHandler {
    fn default() -> Self {
        Self::new()
    }
}

impl EventHandler for CliEventHandler {
    fn on_text(&mut self, text: &str) {
        print!("{}", text);
        io::stdout().flush().ok();
    }

    fn on_tool_use(&mut self, tool: &str, input: &serde_json::Value) {
        println!("\n🔧 调用工具: {}", tool);
        if let Ok(pretty) = serde_json::to_string_pretty(input) {
            println!("   输入: {}", pretty);
        }
        io::stdout().flush().ok();
    }

    fn on_tool_result(&mut self, result: &str) {
        let truncated = if result.len() > 200 {
            format!("{}... ({} 字符)", &result[..200], result.len())
        } else {
            result.to_string()
        };
        println!("   结果: {}", truncated);
        io::stdout().flush().ok();
    }

    fn on_error(&mut self, error: &str) {
        eprintln!("❌ 错误: {}", error);
        io::stderr().flush().ok();
    }

    fn on_complete(&mut self) {
        println!("\n✅ 执行完成");
        io::stdout().flush().ok();
    }
}

/// TUI 事件
///
/// 用于通过 channel 发送到 TUI 应用的事件类型。
#[derive(Debug, Clone)]
pub enum TuiEvent {
    /// 流式文本
    StreamText(String),
    /// 工具调用
    ToolUse {
        tool: String,
        input: serde_json::Value,
    },
    /// 工具结果
    ToolResult(String),
    /// 错误
    Error(String),
    /// 完成
    Complete,
    /// 统计更新 (轮次、成本等)
    StatsUpdate {
        turns: u32,
        cost_usd: f64,
    },
}

/// TUI 事件处理器
///
/// 通过 mpsc channel 发送事件到 TUI 应用的实现。
/// 适用于基于 ratatui 的交互式界面。
pub struct TuiEventHandler {
    tx: mpsc::Sender<TuiEvent>,
}

impl TuiEventHandler {
    /// 创建新的 TUI 事件处理器
    ///
    /// # 参数
    ///
    /// * `tx` - 用于发送事件的 channel sender
    pub fn new(tx: mpsc::Sender<TuiEvent>) -> Self {
        Self { tx }
    }
}

impl EventHandler for TuiEventHandler {
    fn on_text(&mut self, text: &str) {
        let _ = self.tx.try_send(TuiEvent::StreamText(text.to_string()));
    }

    fn on_tool_use(&mut self, tool: &str, input: &serde_json::Value) {
        let _ = self.tx.try_send(TuiEvent::ToolUse {
            tool: tool.to_string(),
            input: input.clone(),
        });
    }

    fn on_tool_result(&mut self, result: &str) {
        let _ = self.tx.try_send(TuiEvent::ToolResult(result.to_string()));
    }

    fn on_error(&mut self, error: &str) {
        let _ = self.tx.try_send(TuiEvent::Error(error.to_string()));
    }

    fn on_complete(&mut self) {
        let _ = self.tx.try_send(TuiEvent::Complete);
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_cli_event_handler_creation() {
        let handler = CliEventHandler::new();
        let _handler2 = CliEventHandler::default();

        // 测试基本创建
        assert_eq!(std::mem::size_of_val(&handler), 0); // ZST (Zero-Sized Type)
    }

    #[tokio::test]
    async fn test_tui_event_handler() {
        let (tx, mut rx) = mpsc::channel(10);
        let mut handler = TuiEventHandler::new(tx);

        // 测试文本事件
        handler.on_text("test text");
        if let Some(event) = rx.recv().await {
            match event {
                TuiEvent::StreamText(text) => assert_eq!(text, "test text"),
                _ => panic!("Expected StreamText event"),
            }
        }

        // 测试工具调用事件
        let input = serde_json::json!({"key": "value"});
        handler.on_tool_use("Read", &input);
        if let Some(event) = rx.recv().await {
            match event {
                TuiEvent::ToolUse { tool, input: i } => {
                    assert_eq!(tool, "Read");
                    assert_eq!(i, input);
                }
                _ => panic!("Expected ToolUse event"),
            }
        }

        // 测试完成事件
        handler.on_complete();
        if let Some(event) = rx.recv().await {
            match event {
                TuiEvent::Complete => {}
                _ => panic!("Expected Complete event"),
            }
        }
    }

    #[test]
    fn test_event_handler_trait_object() {
        let handler: Box<dyn EventHandler> = Box::new(CliEventHandler::new());
        
        // 测试 trait object 可以正常使用
        let _ = handler;
    }
}
