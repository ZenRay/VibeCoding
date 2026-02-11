# Code Agent 开发状态分析报告

**日期**: 2026-02-11  
**文档版本**: v1.0  
**设计文档版本**: design.md v1.7

---

## 执行摘要

本报告对比了 `design.md` 设计文档 (v1.7) 与 `Week8/` 目录下的现有代码实现,识别了缺失功能、需要重构的代码,并制定了完整的开发规划。

**整体完成度**: ~35%

- ✅ **已完成** (35%): 基础架构、init 命令、状态管理、部分 Prompt 模板
- 🚧 **部分完成** (20%): plan/run 命令框架、Claude Agent 集成
- ❌ **缺失** (45%): TUI 界面、EventHandler、KeywordMatcher、Review 机制、多 SDK 支持

---

## 一、设计文档核心需求清单

### 1.1 核心架构 (design.md § 核心架构)

| 组件 | 设计要求 | 状态 |
|------|---------|------|
| **EventHandler 流式处理** | trait + TUI/CLI 实现 | ❌ 缺失 |
| **状态持久化** | state.yml + 断点恢复 | ✅ 已实现 (`state/mod.rs`) |
| **并发模型** | TUI + Worker 双 Task (mpsc) | ❌ 缺失 |

### 1.2 Crate 设计

#### ca-core (核心执行引擎)

| 模块 | 设计要求 | 当前状态 | Gap |
|------|---------|---------|-----|
| `agent/` | Agent trait + 3 SDK 适配器 | 🚧 只有 Claude | ❌ 缺少 Copilot, Cursor |
| `engine/` | 执行引擎 + Phase 编排 | ✅ 基础实现 | ⚠️ 需增强配置传递 |
| `state/` | 状态管理 + hooks | ✅ 完整实现 | ✅ 无 |
| `status/` | status.md 生成器 | ✅ 完整实现 | ✅ 无 |
| `repository/` | 文件管理 + .gitignore | ✅ 基础实现 | ✅ 无 |
| `review/` | **KeywordMatcher + Review循环** | ❌ 完全缺失 | ❌ 高优先级 |
| `event/` | **EventHandler trait** | ❌ 完全缺失 | ❌ 高优先级 |

#### ca-pm (Prompt Manager)

| 模块 | 设计要求 | 当前状态 | Gap |
|------|---------|---------|-----|
| `manager.rs` | PromptManager + 模板加载 | ✅ 基础实现 | ⚠️ 需支持 config.yml |
| `template.rs` | Template 渲染 (minijinja) | ✅ 已实现 | ✅ 无 |
| `context.rs` | Context 构建器 | ✅ 已实现 | ✅ 无 |
| `templates/` | **3文件结构** (config.yml + system + user) | ❌ 只有 user.jinja | ❌ 缺少 config.yml, system.jinja |

**模板结构 Gap**:
```
设计要求:                         当前实现:
templates/run/                   templates/run/
├── phase5_review/               ├── phase5_review.jinja  ✅
│   ├── config.yml      ❌       └── (无 config.yml)      ❌
│   ├── system.jinja    ❌
│   └── user.jinja      ✅
```

#### ca-cli (命令行界面)

| 模块 | 设计要求 | 当前状态 | Gap |
|------|---------|---------|-----|
| `commands/init.rs` | 环境验证 + 项目初始化 | ✅ 完整实现 | ✅ 无 |
| `commands/plan.rs` | Plan 命令 + TUI 集成 | 🚧 基础框架 | ❌ 缺少 TUI |
| `commands/run.rs` | Run 命令 + Review 循环 | 🚧 基础框架 | ❌ 缺少 Review |
| `commands/list.rs` | 功能列表 | ✅ 已实现 | ✅ 无 |
| `commands/status.rs` | 状态查询 | ✅ 已实现 | ✅ 无 |
| `commands/clean.rs` | Worktree 清理 | ✅ 已实现 | ✅ 无 |
| `ui/` | **TUI 界面** | ❌ 完全缺失 | ❌ 高优先级 |

### 1.3 核心流程

| 流程 | 设计要求 | 当前状态 | Gap |
|------|---------|---------|-----|
| Init 流程 | 环境验证 + 项目初始化 + CLAUDE.md | ✅ 完整 | ✅ 无 |
| Plan 流程 | 交互式规划 + TUI | 🚧 基础 | ❌ 无 TUI |
| Run 流程 | 7 Phase + Review/Fix 循环 | 🚧 框架 | ❌ 无 Review |

### 1.4 TUI 界面 (design.md § Phase 6)

| 组件 | 设计要求 | 当前状态 |
|------|---------|---------|
| 3区域布局 | Chat + Input + Stats | ❌ 缺失 |
| 非阻塞事件循环 | 100ms poll | ❌ 缺失 |
| 流式响应显示 | EventHandler 集成 | ❌ 缺失 |
| 并发模型 | TUI Task + Worker Task | ❌ 缺失 |

### 1.5 Review/Verification 机制 (design.md § Phase 5)

| 组件 | 设计要求 | 当前状态 |
|------|---------|---------|
| KeywordMatcher | 4种匹配模式 | ❌ 缺失 |
| Review 循环 | MAX_FIX_ITERATIONS=3 | ❌ 缺失 |
| 关键词定义 | APPROVED/NEEDS_CHANGES/VERIFIED/FAILED | ❌ 缺失 |

---

## 二、现有代码实现状态

### 2.1 ✅ 已完成的模块 (35%)

1. **state/ 完整实现** (100%)
   - FeatureState, PhaseState, TaskState
   - StateManager + HookRegistry
   - StatusDocumentHook (自动更新 status.md)
   - 断点恢复支持

2. **status/ 完整实现** (100%)
   - StatusDocument 生成器
   - 中文格式化输出
   - 完整的字段支持

3. **repository/ 基础实现** (80%)
   - 文件读写
   - .gitignore 支持
   - 文件过滤

4. **commands/init.rs 完整实现** (95%)
   - 环境变量验证
   - Agent 连接测试
   - CLAUDE.md 模板生成
   - 幂等性保证

5. **commands/list.rs, status.rs, clean.rs** (100%)
   - 功能列表
   - 状态查询
   - Worktree 清理

6. **agent/claude.rs** (70%)
   - Claude Agent SDK 集成
   - 基础 API 调用
   - 元数据收集

7. **Prompt 模板** (60%)
   - 13 个 user.jinja 模板已创建
   - 缺少 config.yml 和 system.jinja

### 2.2 🚧 部分完成的模块 (20%)

1. **engine/ 基础框架** (40%)
   - ExecutionEngine 基础结构
   - PhaseConfig 定义
   - ⚠️ **Gap**: 无法在运行时配置 Agent (Arc<dyn Agent> 不可变)
   - ⚠️ **Gap**: Phase 配置 (tools, permissions) 未传递到 Agent

2. **commands/plan.rs** (30%)
   - 基础命令框架
   - ⚠️ **Gap**: 无交互式 TUI
   - ⚠️ **Gap**: 未集成 PromptManager

3. **commands/run.rs** (25%)
   - 基础命令框架
   - ⚠️ **Gap**: 无 Review/Fix 循环
   - ⚠️ **Gap**: 无 Phase 编排逻辑

4. **ca-pm/manager.rs** (50%)
   - 基础模板加载
   - ⚠️ **Gap**: 不支持 config.yml
   - ⚠️ **Gap**: 不支持 system.jinja

### 2.3 ❌ 完全缺失的模块 (45%)

1. **ca-core/src/event/** (0%)
   - EventHandler trait
   - TuiEventHandler 实现
   - CliEventHandler 实现

2. **ca-core/src/review/** (0%)
   - KeywordMatcher 实现
   - Review 循环逻辑
   - 4种匹配模式

3. **ca-cli/src/ui/** (0%)
   - PlanApp (TUI)
   - 3区域布局
   - 事件循环
   - 流式响应显示

4. **Agent 多 SDK 支持** (0%)
   - CopilotAgent (设计中提到但未实现)
   - CursorAgent (设计中提到但未实现)

5. **模板 3文件结构** (0%)
   - config.yml (工具/权限/预算)
   - system.jinja (角色定义)
   - 当前只有 user.jinja

---

## 三、需要重构的代码

### 3.1 高优先级重构

#### 1. **ExecutionEngine - Agent 配置传递** ⚠️

**问题**: 
```rust
// crates/ca-core/src/engine/mod.rs:50
// TODO: 目前无法直接修改 Arc<dyn Agent>,需要重构为支持运行时配置
```

**设计要求** (design.md § Agent 配置设计):
- Phase 5 (Review): disallowedTools = [Write, StrReplace, ...]
- Phase 1-4: 完整工具访问

**重构方案**:
```rust
// 方案 A: 在 AgentRequest 中传递配置
pub struct AgentRequest {
    // ... 现有字段
    pub phase_config: Option<PhaseConfig>,  // 新增
}

// 方案 B: 使用 Builder 模式重新创建 Agent
impl ExecutionEngine {
    pub async fn execute_phase_with_config(
        &self,
        phase: Phase,
        prompt: String,
    ) -> Result<ExecutionResult> {
        let config = PhaseConfig::for_phase(phase)?;
        // 根据 config 调整 agent 行为
    }
}
```

#### 2. **PromptManager - 支持 3文件模板结构** ⚠️

**问题**: 当前只加载 `*.jinja` 文件,不支持 `config.yml`

**设计要求** (design.md § Task 模板结构):
```
templates/run/phase5_review/
├── config.yml        # Phase 配置
├── system.jinja      # 系统提示词
└── user.jinja        # 用户提示词
```

**重构方案**:
```rust
pub struct TaskTemplate {
    pub config: TaskConfig,           // 从 config.yml 加载
    pub system_template: Option<String>,  // 从 system.jinja 加载
    pub user_template: String,        // 从 user.jinja 加载
}

impl PromptManager {
    pub fn load_task_dir(&mut self, task_dir: &Path) -> Result<TaskTemplate> {
        // 1. 读取 config.yml
        // 2. 读取 system.jinja (可选)
        // 3. 读取 user.jinja (必需)
    }
}
```

### 3.2 中优先级重构

#### 3. **commands/run.rs - 集成 Phase 编排和 Review 循环**

**当前状态**: 只有空框架

**需要实现**:
```rust
pub async fn execute_run(/* ... */) -> Result<()> {
    // 1. 加载或创建 FeatureState
    // 2. 执行 Phase 1-4 (Observer, Planning, Execute)
    // 3. 执行 Phase 5 (Review + Fix 循环)
    // 4. 执行 Phase 6-7 (Verification)
    // 5. 生成 PR (使用 gh cli)
}
```

#### 4. **commands/plan.rs - 集成交互式流程**

**当前状态**: 只有空框架

**需要实现**:
```rust
pub async fn execute_plan(/* ... */) -> Result<()> {
    if interactive {
        // 启动 TUI
        let app = PlanApp::new(/* ... */);
        app.run().await?;
    } else {
        // 非交互式: 使用 description 生成 specs
    }
}
```

---

## 四、开发规划

### Phase 1: 核心机制实现 (高优先级, 3-4 天)

**目标**: 实现 EventHandler、KeywordMatcher、Review 循环

#### 任务列表:

1. **创建 `ca-core/src/event/mod.rs`** (1 天)
   ```rust
   pub trait EventHandler: Send + Sync {
       fn on_text(&mut self, text: &str);
       fn on_tool_use(&mut self, tool: &str, input: &Value);
       fn on_tool_result(&mut self, result: &str);
       fn on_error(&mut self, error: &str);
       fn on_complete(&mut self);
   }
   
   pub struct CliEventHandler; // 实现
   pub struct TuiEventHandler { /* mpsc::Sender */ } // 实现
   ```

2. **创建 `ca-core/src/review/mod.rs`** (1 天)
   ```rust
   pub struct KeywordMatcher {
       success_keywords: Vec<String>,
       fail_keywords: Vec<String>,
   }
   
   impl KeywordMatcher {
       pub fn for_review() -> Self; // APPROVED, NEEDS_CHANGES
       pub fn for_verification() -> Self; // VERIFIED, FAILED
       pub fn check(&self, output: &str) -> Option<bool>;
       // 4种匹配模式实现
   }
   ```

3. **重构 `ExecutionEngine`** (1 天)
   - 支持 PhaseConfig 传递到 Agent
   - 支持 EventHandler 集成
   ```rust
   impl ExecutionEngine {
       pub fn with_event_handler(mut self, handler: Box<dyn EventHandler>) -> Self;
       pub async fn execute_phase_with_config(
           &self,
           phase: Phase,
           config: &PhaseConfig,
           prompt: String,
       ) -> Result<ExecutionResult>;
   }
   ```

4. **实现 Review/Fix 循环** (0.5 天)
   ```rust
   // apps/ca-cli/src/commands/run.rs
   const MAX_FIX_ITERATIONS: usize = 3;
   
   async fn execute_review_phase(
       engine: &Engine,
       state: &mut FeatureState,
   ) -> Result<()> {
       for iteration in 1..=MAX_FIX_ITERATIONS {
           // Review → KeywordMatcher → Fix (如需要)
       }
   }
   ```

5. **测试和集成** (0.5 天)
   - 单元测试 KeywordMatcher
   - 集成测试 Review 循环
   - 验证 EventHandler 正常工作

**交付物**:
- ✅ `ca-core/src/event/` (EventHandler trait + 实现)
- ✅ `ca-core/src/review/` (KeywordMatcher + Review 循环)
- ✅ 重构后的 ExecutionEngine
- ✅ 完整测试

---

### Phase 2: Prompt 模板重构 (中优先级, 1-2 天)

**目标**: 实现 3文件模板结构 (config.yml + system.jinja + user.jinja)

#### 任务列表:

1. **创建 TaskConfig 结构** (0.5 天)
   ```rust
   // ca-pm/src/manager.rs
   #[derive(Deserialize)]
   pub struct TaskConfig {
       pub preset: bool,
       pub tools: Vec<String>,
       pub disallowed_tools: Vec<String>,
       pub permission_mode: PermissionMode,
       pub max_turns: usize,
       pub max_budget_usd: f64,
   }
   ```

2. **重构 PromptManager.load_task_dir()** (0.5 天)
   - 支持从目录加载 3 个文件
   - 解析 config.yml (使用 serde_yaml)

3. **创建所有模板的 config.yml** (0.5 天)
   - `templates/run/phase5_review/config.yml` (关键: disallowedTools)
   - `templates/run/phase1_observer/config.yml`
   - ... (共 13 个)

4. **重构 PhaseConfig** (0.5 天)
   - 从 TaskConfig 读取配置
   - 传递到 Agent

**交付物**:
- ✅ 支持 3文件结构的 PromptManager
- ✅ 13 个 config.yml 文件
- ✅ 单元测试

---

### Phase 3: Run 命令完整实现 (高优先级, 2-3 天)

**目标**: 实现完整的 7 Phase 执行流程

#### 任务列表:

1. **实现 Phase 编排逻辑** (1 天)
   ```rust
   pub async fn execute_run(/* ... */) -> Result<()> {
       let state = load_or_create_state(slug, resume)?;
       
       for phase_idx in state.current_phase..7 {
           match phase_idx {
               0 => execute_observer_phase(&engine, &mut state).await?,
               1 => execute_planning_phase(&engine, &mut state).await?,
               2..=3 => execute_execute_phase(&engine, &mut state, phase_idx).await?,
               4 => execute_review_phase(&engine, &mut state).await?, // 使用 KeywordMatcher
               5 => execute_fix_phase(&engine, &mut state).await?,
               6 => execute_verification_phase(&engine, &mut state).await?,
               _ => unreachable!(),
           }
           
           state.save(slug)?; // 每个 Phase 后保存
       }
   }
   ```

2. **集成 PromptManager** (0.5 天)
   - 为每个 Phase 加载对应模板
   - 构建上下文 (ContextBuilder)

3. **集成 Review 循环** (0.5 天)
   - 在 Phase 5 中使用 KeywordMatcher
   - MAX_FIX_ITERATIONS 重试逻辑

4. **断点恢复** (0.5 天)
   - 使用 resume.jinja 模板
   - 构建恢复上下文

5. **PR 生成** (0.5 天)
   - Phase 7 完成后调用 `gh pr create`
   - 生成详细的 PR description

**交付物**:
- ✅ 完整的 run 命令实现
- ✅ 7 Phase 编排逻辑
- ✅ Review/Fix 循环集成
- ✅ 断点恢复功能
- ✅ PR 自动生成

---

### Phase 4: TUI 界面实现 (中优先级, 3-4 天)

**目标**: 实现 Plan 和 Run 的 TUI 界面

#### 任务列表:

1. **创建 `ca-cli/src/ui/` 模块** (0.5 天)
   - `mod.rs` (模块导出)
   - `plan_app.rs` (Plan TUI)
   - `run_app.rs` (Run TUI - 可选)

2. **实现 PlanApp** (2 天)
   ```rust
   pub struct PlanApp {
       messages: Vec<ChatMessage>,
       input: String,
       scroll_offset: usize,
       session: Session,
       stats: SessionStats,
       event_rx: mpsc::Receiver<TuiEvent>,
       worker_tx: mpsc::Sender<UserMessage>,
   }
   
   impl PlanApp {
       pub async fn run(&mut self) -> Result<()> {
           // 3区域布局
           // 非阻塞事件循环 (100ms poll)
           // 流式响应显示
       }
   }
   ```

3. **实现并发模型** (1 天)
   ```rust
   pub async fn execute_plan_tui(slug: &str) -> Result<()> {
       let (ui_tx, ui_rx) = mpsc::channel(100);
       let (worker_tx, worker_rx) = mpsc::channel(100);
       
       // TUI Task
       let ui_handle = tokio::spawn(async move {
           let mut app = PlanApp::new(ui_rx, worker_tx);
           app.run().await
       });
       
       // Worker Task
       let worker_handle = tokio::spawn(async move {
           let mut worker = PlanWorker::new(worker_rx, ui_tx);
           worker.run().await
       });
       
       tokio::select! {
           _ = ui_handle => {},
           _ = worker_handle => {},
       }
   }
   ```

4. **集成 EventHandler** (0.5 天)
   - TuiEventHandler 发送到 mpsc channel
   - PlanApp 接收并显示

5. **键盘快捷键** (0.5 天)
   - Enter: 发送消息
   - Ctrl+C: 退出
   - 上下键: 历史记录

**交付物**:
- ✅ `ca-cli/src/ui/plan_app.rs` (完整 TUI)
- ✅ 3区域布局 (Chat, Input, Stats)
- ✅ 并发模型 (TUI + Worker)
- ✅ 流式响应显示
- ✅ 键盘交互

---

### Phase 5: 多 SDK 支持 (低优先级, 可选, 4-5 天)

**目标**: 实现 Copilot 和 Cursor Agent

**注意**: 设计文档中提到,但当前只有 Claude 实现。可以延后到 v0.2.0

#### 任务列表:

1. **CopilotAgent 实现** (2 天)
   - 研究 GitHub Copilot Agent SDK
   - 实现 Agent trait
   - 能力降级 (不支持工具控制)

2. **CursorAgent 实现** (2 天)
   - 研究 Cursor Cloud API
   - 实现 Agent trait
   - 能力降级

3. **AgentFactory 扩展** (0.5 天)
   - 支持创建 3 种 Agent
   - 自动检测环境变量

4. **测试和文档** (0.5 天)

---

## 五、优先级和时间线

### 里程碑 1: 核心功能完整 (1-2 周)

**Phase 1 + Phase 2 + Phase 3** = 6-9 天

完成后可实现:
- ✅ 完整的 run 命令 (7 Phase)
- ✅ Review/Fix 循环
- ✅ 断点恢复
- ✅ PR 自动生成
- ✅ 3文件模板结构

**状态**: **可发布 v0.1.0 (CLI 版本)**

---

### 里程碑 2: TUI 增强 (3-4 天)

**Phase 4** = 3-4 天

完成后可实现:
- ✅ 交互式 Plan 命令 (TUI)
- ✅ 流式响应显示
- ✅ 实时统计

**状态**: **可发布 v0.2.0 (TUI 版本)**

---

### 里程碑 3: 多 SDK 支持 (可选, 4-5 天)

**Phase 5** = 4-5 天

完成后可实现:
- ✅ Copilot Agent
- ✅ Cursor Agent
- ✅ 自动检测和切换

**状态**: **可发布 v0.3.0 (Multi-Agent 版本)**

---

## 六、立即行动项 (建议使用 subagent 执行)

### 6.1 高优先级 (必须完成)

1. **实现 EventHandler** (`ca-core/src/event/mod.rs`)
   - 3-4 小时
   - 依赖: 无
   - 阻塞: TUI 实现

2. **实现 KeywordMatcher** (`ca-core/src/review/mod.rs`)
   - 4-5 小时
   - 依赖: 无
   - 阻塞: Review 循环

3. **重构 ExecutionEngine**
   - 3-4 小时
   - 依赖: PhaseConfig
   - 阻塞: Run 命令集成

4. **重构 PromptManager 支持 3文件结构**
   - 4-5 小时
   - 依赖: TaskConfig 定义
   - 阻塞: 模板加载

5. **实现 Run 命令完整逻辑**
   - 1-2 天
   - 依赖: ExecutionEngine, KeywordMatcher, PromptManager
   - 阻塞: 无 (关键路径)

### 6.2 中优先级

6. **创建所有 config.yml 文件**
   - 2-3 小时
   - 依赖: TaskConfig 结构定义

7. **实现 Plan TUI**
   - 2-3 天
   - 依赖: EventHandler

### 6.3 Subagent 执行策略

**建议并行执行** (2 个 subagent):

- **Subagent 1**: Phase 1 任务 (EventHandler + KeywordMatcher + Engine 重构)
- **Subagent 2**: Phase 2 任务 (Prompt 模板重构 + config.yml 创建)

完成后:
- **Subagent 3**: Phase 3 任务 (Run 命令完整实现)
- **Subagent 4**: Phase 4 任务 (TUI 界面)

---

## 七、总结

### 完成度矩阵

| 模块 | 完成度 | 关键缺失 |
|------|--------|---------|
| **ca-core** | 40% | EventHandler, KeywordMatcher, Review 循环 |
| **ca-pm** | 60% | 3文件模板结构 |
| **ca-cli** | 35% | TUI, Run/Plan 完整逻辑 |
| **整体** | **35%** | **核心机制 + TUI** |

### 关键路径

```
EventHandler + KeywordMatcher
         ↓
ExecutionEngine 重构
         ↓
Run 命令完整实现  ← 关键里程碑
         ↓
TUI 界面 (可选)
```

### 建议

1. **立即启动 Phase 1** (EventHandler + KeywordMatcher) - 最高优先级
2. **并行执行 Phase 2** (模板重构) - 不阻塞 Phase 1
3. **完成 Phase 3 后发布 v0.1.0** - 核心功能完整
4. **Phase 4 (TUI) 可延后到 v0.2.0**
5. **Phase 5 (Multi-SDK) 延后到 v0.3.0 或更晚**

---

**报告结束**
