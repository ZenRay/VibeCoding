# 测试场景规范: ScribeFlow

**版本**: 1.0.0
**日期**: 2026-01-24
**测试框架**: Rust `cargo test` + TypeScript Vitest

本文档定义了 ScribeFlow 的所有测试场景,包括单元测试、集成测试和端到端测试。

---

## 目录

1. [测试策略](#测试策略)
2. [单元测试场景](#单元测试场景)
3. [集成测试场景](#集成测试场景)
4. [端到端测试场景](#端到端测试场景)
5. [性能测试场景](#性能测试场景)
6. [边界条件测试](#边界条件测试)

---

## 测试策略

### 测试金字塔

```
        /\
       /  \  E2E Tests (5%)
      /----\
     /      \  Integration Tests (20%)
    /--------\
   /          \  Unit Tests (75%)
  /____________\
```

### 测试覆盖率目标

| 层级 | 目标覆盖率 | 测试数量 |
|------|----------|---------|
| **Unit Tests** | >80% | ~50 个 |
| **Integration Tests** | >70% | ~15 个 |
| **E2E Tests** | 关键路径 100% | ~8 个 |

### 测试环境

- **Platform**: macOS 10.15+ (GitHub Actions macOS runner)
- **Rust**: 1.77+ (stable)
- **Node.js**: 18 LTS
- **Mock Services**: Mock ElevenLabs WebSocket server

---

## 单元测试场景

### 1. 音频重采样精度测试

**测试目标**: 验证 rubato 重采样器的精度符合 <0.1% 误差要求。

**测试方法**: FFT 频谱分析

**Rust 测试代码**:

```rust
#[cfg(test)]
mod tests {
    use super::*;
    use rubato::{FftFixedInOut, Resampler};

    #[test]
    fn test_resampler_accuracy() {
        // 生成 1kHz 正弦波 @ 48kHz
        let sample_rate_in = 48000;
        let sample_rate_out = 16000;
        let duration_ms = 100;
        let frequency = 1000.0;

        let samples_in = (sample_rate_in * duration_ms / 1000) as usize;
        let input: Vec<f32> = (0..samples_in)
            .map(|i| {
                let t = i as f32 / sample_rate_in as f32;
                (2.0 * std::f32::consts::PI * frequency * t).sin()
            })
            .collect();

        // 创建重采样器
        let mut resampler = FftFixedInOut::<f32>::new(
            sample_rate_in as usize,
            sample_rate_out as usize,
            samples_in,
            1,
        ).unwrap();

        // 重采样
        let output = resampler.process(&[input], None).unwrap();

        // FFT 频谱分析
        let fft_result = perform_fft(&output[0]);
        let peak_frequency = find_peak_frequency(&fft_result, sample_rate_out as f32);

        // 验证频率误差 <0.1%
        let error = (peak_frequency - frequency).abs() / frequency;
        assert!(
            error < 0.001,
            "Resampling error {:.4}% exceeds 0.1%",
            error * 100.0
        );
    }

    fn perform_fft(samples: &[f32]) -> Vec<f32> {
        // FFT 实现 (使用 rustfft crate)
        // 实现省略...
        vec![]
    }

    fn find_peak_frequency(fft_result: &[f32], sample_rate: f32) -> f32 {
        // 查找峰值频率
        // 实现省略...
        1000.0
    }
}
```

**验收标准**:
- ✅ 频率误差 <0.1%
- ✅ SNR (信噪比) >80dB
- ✅ 测试执行时间 <100ms

---

### 2. Ring Buffer 并发读写测试

**测试目标**: 验证无锁 ring buffer 在高并发场景下的正确性。

**Rust 测试代码**:

```rust
use crossbeam::queue::ArrayQueue;
use std::sync::Arc;
use std::thread;

#[test]
fn test_ring_buffer_concurrent() {
    let buffer = Arc::new(ArrayQueue::new(1000));
    let buffer_clone = buffer.clone();

    // Producer 线程
    let producer = thread::spawn(move || {
        for i in 0..1000 {
            while buffer_clone.push(i).is_err() {
                thread::yield_now();
            }
        }
    });

    // Consumer 线程
    let consumer = thread::spawn(move || {
        let mut received = Vec::new();
        for _ in 0..1000 {
            loop {
                if let Some(value) = buffer.pop() {
                    received.push(value);
                    break;
                }
                thread::yield_now();
            }
        }
        received
    });

    producer.join().unwrap();
    let received = consumer.join().unwrap();

    // 验证接收到所有数据且顺序正确
    assert_eq!(received.len(), 1000);
    for (i, &value) in received.iter().enumerate() {
        assert_eq!(value, i as i32, "Data order mismatch at index {}", i);
    }
}
```

**验收标准**:
- ✅ 无数据丢失
- ✅ 数据顺序正确
- ✅ 无死锁或竞态条件

---

### 3. WebSocket 协议消息解析测试

**测试目标**: 验证所有 ElevenLabs 服务端消息类型的正确解析。

**Rust 测试代码**:

```rust
use serde_json;

#[test]
fn test_parse_session_started() {
    let json = r#"{
        "message_type": "session_started",
        "session_id": "550e8400-e29b-41d4-a716-446655440000",
        "config": {
            "model_id": "scribe_v2_realtime",
            "language_code": "zh"
        }
    }"#;

    let msg: ServerMessage = serde_json::from_str(json).unwrap();

    match msg {
        ServerMessage::SessionStarted { session_id, .. } => {
            assert_eq!(session_id, "550e8400-e29b-41d4-a716-446655440000");
        }
        _ => panic!("Expected SessionStarted message"),
    }
}

#[test]
fn test_parse_partial_transcript() {
    let json = r#"{
        "message_type": "partial_transcript",
        "text": "你好世界",
        "created_at_ms": 1706025600000
    }"#;

    let msg: ServerMessage = serde_json::from_str(json).unwrap();

    match msg {
        ServerMessage::PartialTranscript { text, .. } => {
            assert_eq!(text, "你好世界");
        }
        _ => panic!("Expected PartialTranscript message"),
    }
}

#[test]
fn test_parse_committed_transcript() {
    let json = r#"{
        "message_type": "committed_transcript",
        "text": "你好世界",
        "confidence": 0.98,
        "created_at_ms": 1706025601500
    }"#;

    let msg: ServerMessage = serde_json::from_str(json).unwrap();

    match msg {
        ServerMessage::CommittedTranscript { text, confidence, .. } => {
            assert_eq!(text, "你好世界");
            assert!((confidence - 0.98).abs() < 0.001);
        }
        _ => panic!("Expected CommittedTranscript message"),
    }
}
```

**验收标准**:
- ✅ 所有消息类型解析成功
- ✅ 字段类型和值正确
- ✅ 错误消息也能正确解析

---

### 4. 状态机转换验证测试

**测试目标**: 验证 `TranscriptionSession` 状态转换遵循规则。

**Rust 测试代码**:

```rust
#[test]
fn test_valid_state_transitions() {
    let mut session = TranscriptionSession::new();

    // Idle → Connecting
    assert!(session.transition_to(SessionState::Connecting).is_ok());

    // Connecting → Listening
    assert!(session.transition_to(SessionState::Listening {
        session_id: "test-id".to_string()
    }).is_ok());

    // Listening → Recording
    assert!(session.transition_to(SessionState::Recording {
        start_time: Instant::now()
    }).is_ok());

    // Recording → Processing
    assert!(session.transition_to(SessionState::Processing).is_ok());

    // Processing → Committing
    assert!(session.transition_to(SessionState::Committing).is_ok());

    // Committing → Listening
    assert!(session.transition_to(SessionState::Listening {
        session_id: "test-id".to_string()
    }).is_ok());
}

#[test]
fn test_invalid_state_transitions() {
    let mut session = TranscriptionSession::new();

    // Idle → Recording (非法)
    assert!(session.transition_to(SessionState::Recording {
        start_time: Instant::now()
    }).is_err());

    // Idle → Connecting (合法)
    session.transition_to(SessionState::Connecting).unwrap();

    // Connecting → Committing (非法)
    assert!(session.transition_to(SessionState::Committing).is_err());
}
```

**验收标准**:
- ✅ 合法转换成功
- ✅ 非法转换返回错误
- ✅ 错误消息清晰

---

## 集成测试场景

### 5. 完整 WebSocket 会话流程测试

**测试目标**: 使用 Mock WebSocket 服务器测试完整会话流程。

**测试流程**:

1. 启动 Mock WebSocket server
2. 客户端连接
3. 服务端发送 `session_started`
4. 客户端发送 `input_audio_chunk`
5. 服务端返回 `partial_transcript` × 3
6. 服务端返回 `committed_transcript`
7. 客户端断开连接

**Rust 测试代码**:

```rust
use tokio;
use tokio_tungstenite::tungstenite::Message;

#[tokio::test]
async fn test_websocket_session_flow() {
    // 1. 启动 Mock 服务器
    let mock_server = MockWebSocketServer::start("127.0.0.1:9001").await.unwrap();

    // 2. 创建客户端
    let mut client = ScribeClient::connect_to("ws://127.0.0.1:9001", "test-key").await.unwrap();

    // 3. 接收 session_started
    let msg = client.receive().await.unwrap().unwrap();
    assert!(matches!(msg, ServerMessage::SessionStarted { .. }));

    // 4. 发送音频数据
    let audio_data: Vec<i16> = vec![0; 800];
    client.send_audio(&audio_data).await.unwrap();

    // 5. 接收 partial_transcript × 3
    for i in 1..=3 {
        let msg = client.receive().await.unwrap().unwrap();
        match msg {
            ServerMessage::PartialTranscript { text, .. } => {
                assert_eq!(text, format!("partial_{}", i));
            }
            _ => panic!("Expected PartialTranscript"),
        }
    }

    // 6. 接收 committed_transcript
    let msg = client.receive().await.unwrap().unwrap();
    match msg {
        ServerMessage::CommittedTranscript { text, confidence, .. } => {
            assert_eq!(text, "你好世界");
            assert!(confidence > 0.9);
        }
        _ => panic!("Expected CommittedTranscript"),
    }

    // 7. 断开连接
    client.close().await.unwrap();
    mock_server.stop().await.unwrap();
}
```

**验收标准**:
- ✅ 所有消息顺序正确
- ✅ 连接和断开正常
- ✅ 无内存泄漏

---

### 6. 文本注入兼容性测试

**测试目标**: 验证文本注入在主流应用中的兼容性。

**测试应用列表**:

| 应用 | 注入方法 | 特殊字符 | 预期结果 |
|------|---------|---------|---------|
| TextEdit | 键盘模拟 | ✅ 中文/emoji | ✅ 成功 |
| VS Code | 键盘模拟 | ✅ 代码片段 | ✅ 成功 |
| Chrome | 剪贴板粘贴 | ✅ URL | ✅ 成功 |
| Slack | 剪贴板粘贴 | ✅ Markdown | ✅ 成功 |
| Terminal | 键盘模拟 | ⚠️ 命令 | ✅ 成功 |

**测试脚本** (半自动):

```rust
#[test]
#[ignore] // 需要手动运行
fn test_text_injection_compatibility() {
    let test_cases = vec![
        ("TextEdit", "你好世界 👋", InjectionMethod::Keyboard),
        ("VS Code", "fn main() {}", InjectionMethod::Keyboard),
        ("Chrome", "https://example.com", InjectionMethod::Clipboard),
    ];

    for (app_name, text, method) in test_cases {
        println!("Testing {} with {} method...", app_name, method);
        println!("1. Open {} and focus on text field", app_name);
        println!("2. Press Enter to continue");

        let mut input = String::new();
        std::io::stdin().read_line(&mut input).unwrap();

        // 执行注入
        let injector = TextInjector::new();
        injector.inject(text, method).unwrap();

        println!("3. Verify text appeared in {}", app_name);
        println!("4. Press Enter if success, or type 'fail' if failed");

        input.clear();
        std::io::stdin().read_line(&mut input).unwrap();

        assert!(!input.trim().eq_ignore_ascii_case("fail"), "{} test failed", app_name);
    }
}
```

**验收标准**:
- ✅ TextEdit: 100% 成功率
- ✅ VS Code: 100% 成功率
- ✅ Chrome: 100% 成功率
- ✅ Slack: 100% 成功率
- ✅ Terminal: >95% 成功率

---

### 7. 剪贴板恢复测试

**测试目标**: 验证使用剪贴板注入后,原剪贴板内容正确恢复。

**Rust 测试代码**:

```rust
use tauri_plugin_clipboard_manager::ClipboardExt;

#[tokio::test]
async fn test_clipboard_restoration() {
    let app = create_test_app().await;

    // 1. 设置初始剪贴板内容
    let original_content = "原始内容 Original Content 🎉";
    app.clipboard().write_text(original_content).unwrap();

    // 2. 执行文本注入 (会暂时修改剪贴板)
    let injector = ClipboardInjector::new(&app);
    let text_to_inject = "你好世界";
    injector.inject(text_to_inject).await.unwrap();

    // 3. 等待注入完成 (包括剪贴板恢复)
    tokio::time::sleep(Duration::from_millis(200)).await;

    // 4. 验证剪贴板已恢复
    let restored_content = app.clipboard().read_text().unwrap().unwrap();
    assert_eq!(
        restored_content,
        original_content,
        "Clipboard not restored correctly"
    );
}

#[tokio::test]
async fn test_clipboard_restoration_stress() {
    // 压力测试: 连续 100 次注入
    for i in 0..100 {
        let original = format!("原始内容_{}", i);
        // 执行测试...
        // 验证恢复...
    }
}
```

**验收标准**:
- ✅ 单次恢复成功率: 100%
- ✅ 压力测试 (100 次): 100% 成功率
- ✅ 恢复延迟: <200ms

---

## 端到端测试场景

### 8. Happy Path - 完整语音输入流程

**场景描述**: 用户从按下热键到文本插入完成的完整流程。

**测试步骤**:

1. 启动 ScribeFlow 应用
2. 打开 TextEdit 并聚焦到文本区域
3. 按下全局热键 `Cmd+Shift+\`
4. 说出 "你好世界"
5. 等待转写完成和文本插入
6. 验证 TextEdit 中出现 "你好世界"

**自动化测试代码** (伪代码):

```rust
#[tokio::test]
#[ignore] // E2E test
async fn test_e2e_happy_path() {
    // 1. 启动应用
    let app = launch_scribeflow().await;

    // 2. 模拟打开 TextEdit
    open_textedit_and_focus();

    // 3. 模拟按下热键
    simulate_hotkey("Cmd+Shift+\\");

    // 4. 等待悬浮窗出现
    wait_for_overlay_visible(Duration::from_millis(500));

    // 5. 模拟音频输入 (播放预录制的 "你好世界" 音频)
    play_audio_file("test_audio_hello_world.wav");

    // 6. 等待转写完成
    wait_for_transcript_committed(Duration::from_secs(3));

    // 7. 验证 TextEdit 内容
    let textedit_content = get_textedit_content();
    assert!(
        textedit_content.contains("你好世界"),
        "Expected '你好世界' in TextEdit, got: {}",
        textedit_content
    );

    // 8. 清理
    app.quit().await;
}
```

**验收标准**:
- ✅ 端到端延迟: <200ms
- ✅ 转写准确率: 100% (测试音频)
- ✅ 文本插入成功率: 100%

---

### 9. 网络中断恢复测试

**场景描述**: WebSocket 连接在转写过程中断开,系统自动重连。

**测试步骤**:

1. 开始语音输入
2. 已转写 "你好世" (partial)
3. 模拟网络中断 (断开 WebSocket)
4. 验证剪贴板包含 "你好世"
5. 验证显示通知 "网络中断,已转写内容已复制到剪贴板"
6. 恢复网络
7. 再次语音输入
8. 验证自动重连成功

**Rust 测试代码**:

```rust
#[tokio::test]
async fn test_network_interruption_recovery() {
    let mut app = create_test_app().await;

    // 1. 开始转写
    app.start_transcription().await.unwrap();

    // 2. 模拟收到 partial transcript
    app.simulate_server_message(ServerMessage::PartialTranscript {
        text: "你好世".to_string(),
        created_at_ms: 0,
    }).await;

    // 3. 模拟网络中断
    app.simulate_websocket_disconnect().await;

    // 4. 等待处理
    tokio::time::sleep(Duration::from_millis(500)).await;

    // 5. 验证剪贴板
    let clipboard_content = app.clipboard().read_text().unwrap().unwrap();
    assert_eq!(clipboard_content, "你好世");

    // 6. 验证通知
    let notification = app.get_last_notification();
    assert!(notification.contains("网络中断"));

    // 7. 模拟恢复网络
    app.simulate_network_restored().await;

    // 8. 等待重连
    tokio::time::sleep(Duration::from_secs(2)).await;

    // 9. 验证连接状态
    assert_eq!(app.connection_state(), ConnectionState::Connected);
}
```

**验收标准**:
- ✅ 剪贴板回退成功率: 100%
- ✅ 自动重连成功率: >90%
- ✅ 通知显示正确

---

### 10. 密码框检测测试

**场景描述**: 在密码输入框激活语音输入时,系统拒绝注入并显示警告。

**测试步骤**:

1. 打开浏览器登录页面
2. 聚焦到密码输入框
3. 按下全局热键
4. 说话 "test123"
5. 验证显示警告 "当前位置不支持语音输入"
6. 验证密码框内容为空 (未注入)

**验收标准**:
- ✅ 密码框检测准确率: >95%
- ✅ 拒绝注入成功率: 100%
- ✅ 警告提示显示正确

---

## 性能测试场景

### 11. 端到端延迟测试

**测试目标**: 验证从语音停止到文本插入完成的延迟 <200ms。

**测试方法**:

```rust
#[tokio::test]
async fn test_end_to_end_latency() {
    let mut app = create_test_app().await;

    let latencies = Vec::new();

    for _ in 0..10 {
        // 1. 记录开始时间
        let start = Instant::now();

        // 2. 模拟语音输入
        app.start_transcription().await.unwrap();

        // 3. 等待 committed_transcript
        let transcript = app.wait_for_committed_transcript(Duration::from_secs(5)).await.unwrap();

        // 4. 等待文本注入完成
        app.wait_for_text_injected().await;

        // 5. 记录延迟
        let latency = start.elapsed();
        latencies.push(latency);

        println!("Latency: {:?}", latency);
    }

    // 计算平均延迟
    let avg_latency = latencies.iter().sum::<Duration>() / latencies.len() as u32;
    let max_latency = latencies.iter().max().unwrap();

    println!("Average latency: {:?}", avg_latency);
    println!("Max latency: {:?}", max_latency);

    // 验证
    assert!(
        avg_latency < Duration::from_millis(200),
        "Average latency {:?} exceeds 200ms",
        avg_latency
    );

    assert!(
        *max_latency < Duration::from_millis(300),
        "Max latency {:?} exceeds 300ms",
        max_latency
    );
}
```

**验收标准**:
- ✅ 平均延迟: <200ms
- ✅ 最大延迟: <300ms
- ✅ 99th percentile: <250ms

---

### 12. 内存泄漏压力测试

**测试目标**: 连续运行 1 小时,验证无内存泄漏。

**测试方法**:

```rust
#[tokio::test]
#[ignore] // 长时间测试
async fn test_memory_leak_stress() {
    let app = create_test_app().await;

    let initial_memory = get_process_memory();

    // 连续运行 1 小时
    let duration = Duration::from_secs(3600);
    let start = Instant::now();

    let mut iteration = 0;

    while start.elapsed() < duration {
        // 模拟语音输入周期
        app.start_transcription().await.unwrap();
        tokio::time::sleep(Duration::from_secs(5)).await;
        app.stop_transcription().await.unwrap();
        tokio::time::sleep(Duration::from_secs(2)).await;

        iteration += 1;

        // 每 100 次检查内存
        if iteration % 100 == 0 {
            let current_memory = get_process_memory();
            let memory_growth = current_memory - initial_memory;

            println!(
                "Iteration {}: Memory {} MB (growth: {} MB)",
                iteration,
                current_memory / 1024 / 1024,
                memory_growth / 1024 / 1024
            );

            // 验证内存增长 <20MB
            assert!(
                memory_growth < 20 * 1024 * 1024,
                "Memory growth {} MB exceeds limit",
                memory_growth / 1024 / 1024
            );
        }
    }

    let final_memory = get_process_memory();
    let total_growth = final_memory - initial_memory;

    println!("Total memory growth: {} MB", total_growth / 1024 / 1024);

    // 验证总内存增长 <50MB
    assert!(
        total_growth < 50 * 1024 * 1024,
        "Total memory growth {} MB exceeds limit",
        total_growth / 1024 / 1024
    );
}

fn get_process_memory() -> usize {
    // 获取当前进程内存占用 (使用 sysinfo crate)
    // 实现省略...
    0
}
```

**验收标准**:
- ✅ 内存增长 <50MB (1 小时)
- ✅ 无崩溃
- ✅ 无资源泄漏 (文件句柄、线程等)

---

## 边界条件测试

### 13. 极长文本处理测试

**测试目标**: 验证系统能正确处理超长转写文本。

**测试用例**:

| 场景 | 文本长度 | 预期行为 |
|------|---------|---------|
| 短文本 | 10 字符 | 键盘模拟注入 |
| 中等文本 | 100 字符 | 剪贴板注入 |
| 长文本 | 1000 字符 | 剪贴板注入 + 分段 |
| 超长文本 | 10000 字符 | 剪贴板注入 + 分段 + 进度提示 |

**Rust 测试代码**:

```rust
#[tokio::test]
async fn test_long_text_injection() {
    let app = create_test_app().await;

    // 生成 10000 字符文本
    let long_text: String = (0..10000).map(|i| ((i % 26) as u8 + b'a') as char).collect();

    // 执行注入
    let start = Instant::now();
    app.inject_text(&long_text).await.unwrap();
    let duration = start.elapsed();

    println!("Injected 10000 characters in {:?}", duration);

    // 验证
    assert!(duration < Duration::from_secs(5), "Injection took too long");

    // 验证目标应用内容
    let content = get_target_app_content();
    assert_eq!(content, long_text);
}
```

**验收标准**:
- ✅ 10 字符: <50ms
- ✅ 100 字符: <200ms
- ✅ 1000 字符: <1s
- ✅ 10000 字符: <5s

---

### 14. 特殊字符处理测试

**测试目标**: 验证系统正确处理各种特殊字符。

**测试用例**:

```rust
#[tokio::test]
async fn test_special_characters() {
    let test_cases = vec![
        ("中文", "你好世界"),
        ("emoji", "👋 😊 🎉"),
        ("symbols", "!@#$%^&*()"),
        ("newlines", "第一行\n第二行\n第三行"),
        ("mixed", "Hello 你好 👋 !@#"),
    ];

    for (name, text) in test_cases {
        println!("Testing {}: {}", name, text);

        let app = create_test_app().await;
        app.inject_text(text).await.unwrap();

        let content = get_target_app_content();
        assert_eq!(content, text, "Failed for case: {}", name);
    }
}
```

**验收标准**:
- ✅ 中文: 100% 正确
- ✅ Emoji: 100% 正确
- ✅ 符号: 100% 正确
- ✅ 换行符: 正确处理
- ✅ 混合字符: 100% 正确

---

## 总结

### 测试统计

| 测试类型 | 场景数 | 预估时间 |
|---------|-------|---------|
| **单元测试** | 50+ | ~5 分钟 |
| **集成测试** | 15 | ~10 分钟 |
| **E2E 测试** | 8 | ~20 分钟 |
| **性能测试** | 2 | ~1.5 小时 |
| **边界测试** | 2 | ~5 分钟 |
| **总计** | **77+** | **~2 小时** |

### CI/CD 集成

**GitHub Actions 配置**:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: macos-latest

    steps:
      - uses: actions/checkout@v3

      - name: Setup Rust
        uses: actions-rs/toolchain@v1
        with:
          toolchain: stable

      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: 18

      - name: Install dependencies
        run: |
          cd src-tauri && cargo build
          npm install

      - name: Run unit tests
        run: cd src-tauri && cargo test --lib

      - name: Run integration tests
        run: cd src-tauri && cargo test --test '*'

      - name: Run frontend tests
        run: npm run test

      - name: Check code coverage
        run: |
          cargo tarpaulin --out Xml
          bash <(curl -s https://codecov.io/bash)
```

### 测试优先级

| 优先级 | 测试场景 | 执行频率 |
|-------|---------|---------|
| **P0** | 单元测试 (全部) | 每次 commit |
| **P0** | E2E Happy Path | 每次 commit |
| **P1** | 集成测试 (全部) | 每次 PR |
| **P1** | E2E 错误场景 | 每次 PR |
| **P2** | 性能测试 | 每日 nightly |
| **P3** | 压力测试 (1 小时) | 每周 |

---

**测试规范版本**: 1.0.0
**最后更新**: 2026-01-24
**状态**: Complete
