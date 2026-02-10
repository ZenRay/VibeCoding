# EventHandler 和 KeywordMatcher 使用指南

## 概览

本文档介绍了 `ca-core` 中新增的两个核心模块:

1. **EventHandler** (`ca-core/src/event/mod.rs`) - 流式事件处理机制
2. **KeywordMatcher** (`ca-core/src/review/mod.rs`) - 关键词匹配器

## EventHandler - 事件处理器

### 设计目标

`EventHandler` trait 提供了统一的事件处理接口,用于:
- 实时流式输出 Agent 响应
- TUI 界面更新
- 工具调用可视化
- 错误通知

### 架构

```
┌─────────────────┐
│ ExecutionEngine │
└────────┬────────┘
         │ 调用
         v
┌─────────────────┐       ┌──────────────────┐
│     Agent       │──────>│  EventHandler    │
└─────────────────┘       └────────┬─────────┘
                                   │
                    ┌──────────────┴──────────────┐
                    │                             │
          ┌─────────v─────────┐       ┌──────────v──────────┐
          │  CliEventHandler  │       │  TuiEventHandler    │
          │  (直接输出)        │       │  (通过 channel)      │
          └───────────────────┘       └─────────────────────┘
```

### API 文档

#### EventHandler Trait

```rust
pub trait EventHandler: Send + Sync {
    fn on_text(&mut self, text: &str);
    fn on_tool_use(&mut self, tool: &str, input: &serde_json::Value);
    fn on_tool_result(&mut self, result: &str);
    fn on_error(&mut self, error: &str);
    fn on_complete(&mut self);
}
```

#### CliEventHandler

**用途**: 命令行界面,直接输出到 stdout/stderr

```rust
use ca_core::{CliEventHandler, EventHandler};

let mut handler = CliEventHandler::new();
handler.on_text("正在执行...\n");
handler.on_tool_use("Read", &serde_json::json!({"path": "file.rs"}));
handler.on_complete();
```

**特性**:
- 零开销 (Zero-Sized Type)
- 实时刷新输出
- 工具调用自动格式化
- 结果自动截断 (>200 字符)

#### TuiEventHandler

**用途**: TUI 应用,通过 mpsc channel 发送事件

```rust
use ca_core::{TuiEventHandler, TuiEvent};
use tokio::sync::mpsc;

let (tx, mut rx) = mpsc::channel(100);
let mut handler = TuiEventHandler::new(tx);

// 发送事件
handler.on_text("Hello");

// TUI 应用接收
while let Some(event) = rx.recv().await {
    match event {
        TuiEvent::StreamText(text) => { /* 更新界面 */ },
        TuiEvent::ToolUse { tool, input } => { /* 显示工具调用 */ },
        TuiEvent::Complete => { /* 完成 */ },
        _ => {}
    }
}
```

**TuiEvent 枚举**:
```rust
pub enum TuiEvent {
    StreamText(String),              // 流式文本
    ToolUse { tool: String, input: Value }, // 工具调用
    ToolResult(String),              // 工具结果
    Error(String),                   // 错误
    Complete,                        // 完成
}
```

### 集成到 ExecutionEngine

**方案 1: 在 AgentRequest 中传递 EventHandler**

```rust
pub struct AgentRequest {
    pub id: String,
    pub prompt: String,
    pub event_handler: Option<Box<dyn EventHandler>>,  // 新增
    // ... 其他字段
}
```

**方案 2: 在 ExecutionEngine 中配置**

```rust
impl ExecutionEngine {
    pub fn with_event_handler(mut self, handler: Box<dyn EventHandler>) -> Self {
        self.event_handler = Some(handler);
        self
    }
}
```

### 使用示例

#### 在 plan 命令中使用 (TUI)

```rust
// apps/ca-cli/src/commands/plan.rs
pub async fn execute_plan_tui(slug: &str) -> Result<()> {
    let (ui_tx, ui_rx) = mpsc::channel(100);
    
    // 创建 TUI EventHandler
    let handler = TuiEventHandler::new(ui_tx.clone());
    
    // 配置 Engine
    let engine = ExecutionEngine::new(agent, repo)
        .with_event_handler(Box::new(handler));
    
    // TUI Task (显示)
    let ui_handle = tokio::spawn(async move {
        let mut app = PlanApp::new(ui_rx);
        app.run().await
    });
    
    // Worker Task (执行)
    let worker_handle = tokio::spawn(async move {
        engine.execute_phase(Phase::Plan, prompt).await
    });
    
    tokio::select! {
        _ = ui_handle => {},
        _ = worker_handle => {},
    }
    
    Ok(())
}
```

#### 在 run 命令中使用 (CLI)

```rust
// apps/ca-cli/src/commands/run.rs
pub async fn execute_run(slug: &str) -> Result<()> {
    let handler = CliEventHandler::new();
    
    let engine = ExecutionEngine::new(agent, repo)
        .with_event_handler(Box::new(handler));
    
    for phase in phases {
        engine.execute_phase(phase, prompt).await?;
    }
    
    Ok(())
}
```

---

## KeywordMatcher - 关键词匹配器

### 设计目标

`KeywordMatcher` 提供了 4 种关键词匹配模式,用于检测 Agent 输出中的审查和验证结果。

### 4 种匹配模式

#### 1. 单独一行 (完整匹配)

```rust
// 匹配示例:
"APPROVED"
"  APPROVED  "  // 忽略空格
"approved"      // 不区分大小写
```

#### 2. 带前缀格式

```rust
// 支持的前缀: verdict, result, status, outcome
"Verdict: APPROVED"
"Result: VERIFIED"
"Status: NEEDS_CHANGES"
"Outcome: FAILED"
```

#### 3. 特殊格式

```rust
"[APPROVED]"        // 方括号
"**VERIFIED**"      // Markdown 粗体
"`FAILED`"          // Markdown 代码
```

#### 4. 末尾匹配

检查输出最后 100 字符内是否包含关键词 (不区分大小写)。

### API 文档

```rust
pub struct KeywordMatcher {
    success_keywords: Vec<String>,
    fail_keywords: Vec<String>,
}

impl KeywordMatcher {
    // 预定义匹配器
    pub fn for_review() -> Self;           // APPROVED / NEEDS_CHANGES
    pub fn for_verification() -> Self;     // VERIFIED / FAILED
    
    // 自定义匹配器
    pub fn new(success_keywords: Vec<String>, fail_keywords: Vec<String>) -> Self;
    
    // 检查方法
    pub fn check(&self, output: &str) -> Option<bool>;
    // Some(true)  = 匹配到成功关键词
    // Some(false) = 匹配到失败关键词
    // None        = 未匹配到任何关键词
}
```

### 使用示例

#### Review 循环 (Phase 5)

```rust
// apps/ca-cli/src/commands/run.rs
const MAX_FIX_ITERATIONS: usize = 3;

async fn execute_review_phase(
    engine: &ExecutionEngine,
    state: &mut FeatureState,
) -> Result<()> {
    let matcher = KeywordMatcher::for_review();
    
    for iteration in 1..=MAX_FIX_ITERATIONS {
        println!("🔍 执行代码审查 (迭代 {}/{})", iteration, MAX_FIX_ITERATIONS);
        
        // 1. 执行 Review
        let review_result = engine
            .execute_phase(Phase::Review, build_review_prompt(state)?)
            .await?;
        
        // 2. 检查关键词
        match matcher.check(&review_result.message) {
            Some(true) => {
                println!("✅ 代码审查通过!");
                state.phases[4].status = PhaseStatus::Completed;
                return Ok(());
            }
            Some(false) => {
                println!("⚠️  需要修复问题 (迭代 {})", iteration);
                
                // 3. 执行 Fix Phase
                let fix_result = engine
                    .execute_phase(Phase::Fix, build_fix_prompt(state, &review_result.message)?)
                    .await?;
                
                // 继续下一次迭代
                continue;
            }
            None => {
                return Err(anyhow::anyhow!("无法确定审查结果,需要人工介入"));
            }
        }
    }
    
    Err(anyhow::anyhow!("超过最大修复迭代次数 ({})", MAX_FIX_ITERATIONS))
}
```

#### Verification 循环 (Phase 7)

```rust
async fn execute_verification_phase(
    engine: &ExecutionEngine,
    state: &mut FeatureState,
) -> Result<()> {
    let matcher = KeywordMatcher::for_verification();
    
    println!("🧪 执行最终验证...");
    
    let verification_result = engine
        .execute_phase(Phase::Verification, build_verification_prompt(state)?)
        .await?;
    
    match matcher.check(&verification_result.message) {
        Some(true) => {
            println!("✅ 验证通过,可以创建 PR!");
            state.phases[6].status = PhaseStatus::Completed;
            Ok(())
        }
        Some(false) => {
            println!("❌ 验证失败,需要返回修复");
            Err(anyhow::anyhow!("验证失败,请查看详细输出"))
        }
        None => {
            Err(anyhow::anyhow!("无法确定验证结果"))
        }
    }
}
```

#### 自定义匹配器

```rust
// 创建自定义关键词
let matcher = KeywordMatcher::new(
    vec!["SUCCESS".to_string(), "PASS".to_string()],
    vec!["FAILURE".to_string(), "FAIL".to_string()],
);

let output = "测试结果: SUCCESS";
match matcher.check(output) {
    Some(true) => println!("成功"),
    Some(false) => println!("失败"),
    None => println!("未知"),
}
```

### 真实输出示例

#### Review 输出 - 通过

```markdown
# Code Review Results

## Summary
All changes look good. The implementation follows best practices.

## Checks
- ✅ Code style
- ✅ Tests coverage
- ✅ Documentation

## Verdict
**APPROVED**
```

匹配结果: `Some(true)` (模式 3: `**APPROVED**`)

#### Review 输出 - 需要修复

```markdown
# Code Review Results

## Issues Found
1. Missing error handling in parse_config()
2. Incomplete test coverage for edge cases

## Verdict: NEEDS_CHANGES

Please address the issues above and re-submit.
```

匹配结果: `Some(false)` (模式 2: `Verdict: NEEDS_CHANGES`)

---

## 测试

### 运行测试

```bash
# 测试 EventHandler
cargo test --package ca-core --lib event

# 测试 KeywordMatcher
cargo test --package ca-core --lib review

# 运行所有测试
cargo test --package ca-core

# 运行示例
cargo run --package ca-core --example event_and_review
```

### 测试覆盖

- **EventHandler**: 3 个单元测试
  - CLI handler 创建
  - TUI handler 事件发送
  - Trait object 使用

- **KeywordMatcher**: 14 个单元测试
  - 4 种匹配模式
  - 边界情况
  - 优先级 (成功关键词优先)
  - 大小写不敏感
  - 真实场景模拟

---

## 代码质量

### Clippy 检查

```bash
cargo clippy --package ca-core -- -D warnings
```

✅ 无警告

### 代码统计

```
ca-core/src/event/mod.rs   : 240 行 (含测试和文档)
ca-core/src/review/mod.rs  : 430 行 (含测试和文档)
```

---

## 下一步

### Phase 1 剩余任务

1. ✅ 实现 EventHandler (已完成)
2. ✅ 实现 KeywordMatcher (已完成)
3. ⏳ 重构 ExecutionEngine (支持 EventHandler 和 PhaseConfig)
4. ⏳ 实现 Review/Fix 循环 (在 `run` 命令中)
5. ⏳ 集成测试

### 集成清单

- [ ] 更新 `ExecutionEngine` 支持 `EventHandler`
- [ ] 更新 `Agent` trait 支持流式回调
- [ ] 在 `plan` 命令中集成 TUI EventHandler
- [ ] 在 `run` 命令中集成 Review 循环
- [ ] 创建完整的集成测试

---

## 参考资料

- 设计文档: `instructions/Week8/design.md`
- Gap 分析: `instructions/Week8/GAP_ANALYSIS.md`
- 示例代码: `crates/ca-core/examples/event_and_review.rs`
