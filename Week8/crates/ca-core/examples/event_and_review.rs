//! EventHandler 和 KeywordMatcher 使用示例

use ca_core::{CliEventHandler, EventHandler, KeywordMatcher};
use tokio::sync::mpsc;

fn main() {
    println!("=== EventHandler 示例 ===\n");
    demo_cli_event_handler();

    println!("\n=== KeywordMatcher 示例 ===\n");
    demo_keyword_matcher();
}

fn demo_cli_event_handler() {
    println!("1. CLI EventHandler (直接输出):");
    let mut handler = CliEventHandler::new();

    handler.on_text("正在处理请求...\n");
    handler.on_tool_use(
        "Read",
        &serde_json::json!({
            "path": "/path/to/file.rs"
        }),
    );
    handler.on_tool_result("文件内容: fn main() { ... }");
    handler.on_complete();

    println!("\n2. TUI EventHandler (通过 channel):");
    println!("   (需要在异步上下文中使用,见 demo_tui_event_handler)");
}

fn demo_keyword_matcher() {
    println!("1. Review Matcher:");
    let review_matcher = KeywordMatcher::for_review();

    let test_cases = vec![
        ("APPROVED", "单行匹配"),
        ("Verdict: APPROVED", "前缀匹配"),
        ("**APPROVED**", "特殊格式"),
        ("NEEDS_CHANGES", "失败关键词"),
        ("代码看起来不错", "无匹配"),
    ];

    for (output, description) in test_cases {
        match review_matcher.check(output) {
            Some(true) => println!("   ✅ {} - {}", description, output),
            Some(false) => println!("   ❌ {} - {}", description, output),
            None => println!("   ❓ {} - {}", description, output),
        }
    }

    println!("\n2. Verification Matcher:");
    let verification_matcher = KeywordMatcher::for_verification();

    let test_cases = vec![
        ("VERIFIED", "验证通过"),
        ("[VERIFIED]", "特殊格式"),
        ("Result: FAILED", "验证失败"),
        ("测试运行中...", "无匹配"),
    ];

    for (output, description) in test_cases {
        match verification_matcher.check(output) {
            Some(true) => println!("   ✅ {} - {}", description, output),
            Some(false) => println!("   ❌ {} - {}", description, output),
            None => println!("   ❓ {} - {}", description, output),
        }
    }

    println!("\n3. 真实场景模拟:");
    simulate_review_cycle();
}

fn simulate_review_cycle() {
    let matcher = KeywordMatcher::for_review();

    let review_outputs = vec![
        r#"
# Code Review

## 发现的问题
1. 缺少错误处理
2. 测试覆盖不足

Verdict: NEEDS_CHANGES
        "#,
        r#"
# Code Review (迭代 2)

## 检查结果
- ✅ 错误处理已添加
- ✅ 测试覆盖率达标
- ✅ 文档完整

**APPROVED**
        "#,
    ];

    for (i, output) in review_outputs.iter().enumerate() {
        println!("   迭代 {}:", i + 1);
        match matcher.check(output) {
            Some(true) => println!("      结果: ✅ 审查通过,进入下一阶段"),
            Some(false) => println!("      结果: ⚠️  需要修复,继续迭代"),
            None => println!("      结果: ❓ 无法确定,需要人工介入"),
        }
    }
}

// 异步示例 (仅作展示,实际需要在 #[tokio::main] 中运行)
#[allow(dead_code)]
async fn demo_tui_event_handler() {
    use ca_core::TuiEventHandler;

    let (tx, mut rx) = mpsc::channel(100);
    let mut handler = TuiEventHandler::new(tx);

    // 模拟事件发送
    handler.on_text("开始执行任务...\n");
    handler.on_tool_use("Write", &serde_json::json!({"path": "test.rs"}));
    handler.on_complete();

    // TUI 应用会从 rx 接收事件
    while let Some(event) = rx.recv().await {
        println!("   TUI 收到事件: {:?}", event);
    }
}
