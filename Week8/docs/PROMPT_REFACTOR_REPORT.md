# Prompt 模板重构完成报告

**日期**: 2026-02-11  
**任务**: 实现 Code Agent 项目的 Prompt 模板重构,支持 3 文件结构  
**状态**: ✅ **全部完成**

---

## 任务目标

重构 `ca-pm` (Prompt Manager) crate 以支持新的 3 文件模板结构:
- `config.yml` - Phase 配置 (工具/权限/预算)
- `system.jinja` - 系统提示词 (角色定义,可选)
- `user.jinja` - 用户提示词 (具体任务)

---

## 完成的工作

### 1. ✅ 定义新结构 (manager.rs)

添加了以下结构:

```rust
// 权限模式枚举
#[derive(Debug, Clone, Copy, Serialize, Deserialize, Default, PartialEq, Eq)]
pub enum PermissionMode {
    #[default]
    Default,           // 需要审批
    BypassPermissions, // 自动批准
}

// 任务配置 (从 config.yml 加载)
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TaskConfig {
    pub preset: bool,                      // 是否使用 Agent preset
    pub tools: Vec<String>,                // 允许的工具列表
    pub disallowed_tools: Vec<String>,     // 禁止的工具列表
    pub permission_mode: PermissionMode,   // 权限模式
    pub max_turns: usize,                  // 最大轮次 (默认: 20)
    pub max_budget_usd: f64,              // 预算限制 (默认: 5.0)
}

// 任务模板 (3文件结构)
#[derive(Debug, Clone)]
pub struct TaskTemplate {
    pub config: TaskConfig,                // 从 config.yml 加载
    pub system_template: Option<String>,   // 从 system.jinja 加载 (可选)
    pub user_template: String,             // 从 user.jinja 加载 (必需)
}
```

**特性**:
- 所有字段都有合理的默认值
- 使用 `serde` 支持 YAML 反序列化
- 支持向后兼容 (没有 config.yml 时使用默认配置)

### 2. ✅ 实现核心方法

#### `load_task_dir()` - 加载任务模板

```rust
pub fn load_task_dir(&mut self, task_dir: &Path) -> Result<TaskTemplate>
```

**功能**:
1. 读取 `config.yml` (可选,不存在则使用默认配置)
2. 读取 `system.jinja` (可选)
3. 读取 `user.jinja` (必需,不存在则报错)
4. 返回完整的 `TaskTemplate`

**向后兼容**: 如果只有 `user.jinja`,仍然可以正常工作。

#### `render_task()` - 渲染任务提示词

```rust
pub fn render_task(
    &self,
    task: &TaskTemplate,
    context: &TemplateContext,
) -> Result<(Option<String>, String)>
```

**功能**:
- 渲染 `system.jinja` (如果存在)
- 渲染 `user.jinja`
- 返回元组 `(system_prompt, user_prompt)`

### 3. ✅ 创建 12 个 config.yml 文件

成功为以下模板创建了配置文件:

**Run 模板** (8个):
- `run/phase1_observer/config.yml` - 观察阶段 (15 turns, $3.0)
- `run/phase2_planning/config.yml` - 规划阶段 (20 turns, $4.0)
- `run/phase3_execute/config.yml` - 执行阶段 (30 turns, $5.0, 完整访问)
- `run/phase4_execute/config.yml` - 执行阶段 (30 turns, $5.0, 完整访问)
- `run/phase5_review/config.yml` - **审查阶段 (10 turns, $2.0, 只读模式)** ⭐
- `run/phase6_fix/config.yml` - 修复阶段 (20 turns, $4.0)
- `run/phase7_verification/config.yml` - 验证阶段 (10 turns, $2.0, 只读模式)
- `run/resume/config.yml` - 恢复执行 (30 turns, $5.0)

**Plan 模板** (3个):
- `plan/feature_analysis/config.yml` - 功能分析 (20 turns, $4.0)
- `plan/task_breakdown/config.yml` - 任务分解 (25 turns, $4.5)
- `plan/milestone_planning/config.yml` - 里程碑规划 (20 turns, $4.0)

**Init 模板** (1个):
- `init/project_setup/config.yml` - 项目初始化 (15 turns, $3.0)

**关键配置示例 (Phase 5 Review)**:
```yaml
# Review 阶段配置 - 只读模式
preset: true
tools: []
disallowed_tools:  # 禁止文件修改
  - Write
  - StrReplace
  - EditNotebook
  - Delete
permission_mode: default
max_turns: 10
max_budget_usd: 2.0
```

### 4. ✅ 重构模板目录结构

**之前的结构**:
```
templates/run/
├── phase5_review.jinja
├── phase6_fix.jinja
└── ...
```

**重构后的结构**:
```
templates/run/
├── phase5_review/
│   ├── config.yml
│   └── user.jinja
├── phase6_fix/
│   ├── config.yml
│   └── user.jinja
└── ...
```

**统计**:
- 重构了 15 个目录
- 创建了 24 个文件 (12 个 config.yml + 12 个 user.jinja)
- 所有模板内容保持不变,只是组织方式改变

### 5. ✅ 更新导出 (lib.rs)

```rust
pub use manager::{
    PermissionMode,     // 新增
    PromptConfig,
    PromptManager,
    TaskConfig,         // 新增
    TaskTemplate,       // 新增
};
```

### 6. ✅ 创建单元测试

添加了 8 个新测试:

1. `test_task_config_default` - 测试 TaskConfig 默认值
2. `test_task_config_deserialization` - 测试 YAML 反序列化
3. `test_permission_mode_default` - 测试 PermissionMode 默认值
4. `test_load_task_dir_with_all_files` - 测试加载完整的 3 文件结构
5. `test_load_task_dir_minimal` - 测试最小配置 (只有 user.jinja)
6. `test_load_task_dir_missing_user_jinja` - 测试错误处理
7. `test_render_task_with_system` - 测试渲染带 system prompt
8. `test_render_task_without_system` - 测试渲染不带 system prompt

**测试结果**: ✅ **14/14 测试全部通过**

### 7. ✅ 添加依赖

**Cargo.toml 更新**:
- 添加 `serde_yaml` (已在 workspace 中)
- 添加 `tempfile` (dev-dependency, 用于测试)

### 8. ✅ 代码质量检查

- **Cargo test**: ✅ 14 测试全部通过
- **Cargo clippy**: ✅ 无警告 (`-D warnings`)

---

## 目录结构总览

```
Week8/crates/ca-pm/
├── src/
│   ├── lib.rs          # 导出新类型 ✅
│   ├── manager.rs      # TaskConfig, TaskTemplate, load_task_dir, render_task ✅
│   ├── template.rs     # (无变化)
│   ├── context.rs      # (无变化)
│   └── error.rs        # (无变化)
├── templates/
│   ├── run/
│   │   ├── phase1_observer/     # ✅ 重构
│   │   │   ├── config.yml       # ✅ 新增
│   │   │   └── user.jinja       # ✅ 移动
│   │   ├── phase2_planning/     # ✅ 重构
│   │   ├── phase3_execute/      # ✅ 重构
│   │   ├── phase4_execute/      # ✅ 重构
│   │   ├── phase5_review/       # ✅ 重构 (关键配置)
│   │   ├── phase6_fix/          # ✅ 重构
│   │   ├── phase7_verification/ # ✅ 重构
│   │   └── resume/              # ✅ 重构
│   ├── plan/
│   │   ├── feature_analysis/    # ✅ 重构
│   │   ├── task_breakdown/      # ✅ 重构
│   │   └── milestone_planning/  # ✅ 重构
│   └── init/
│       └── project_setup/       # ✅ 重构
├── examples/
│   └── task_template.rs         # ✅ 新增示例
├── Cargo.toml                   # ✅ 更新依赖
└── tests/                       # (14 单元测试全部通过)
```

---

## 成功标准验证

| 标准 | 状态 | 说明 |
|------|------|------|
| TaskConfig 和相关结构定义完成 | ✅ | 包含 PermissionMode, TaskConfig, TaskTemplate |
| load_task_dir 方法实现 | ✅ | 支持 3 文件结构,向后兼容 |
| render_task 方法实现 | ✅ | 正确渲染 system 和 user prompt |
| 所有模板有 config.yml | ✅ | 12 个 config.yml 文件全部创建 |
| 模板目录结构重构完成 | ✅ | 15 个目录,24 个文件 |
| 单元测试通过 | ✅ | 14/14 测试通过 |
| Clippy 无警告 | ✅ | 通过 `-D warnings` 检查 |
| 向后兼容 | ✅ | 可以读取只有 user.jinja 的旧格式 |

---

## 关键特性

### 1. 灵活的配置系统

- **Phase 5 (Review)**: 禁止 Write, StrReplace, EditNotebook, Delete
- **Phase 7 (Verification)**: 同样禁止修改工具
- **Phase 3/4 (Execute)**: 完整工具访问
- **预算控制**: Review/Verification ($2.0) < Planning ($4.0) < Execute ($5.0)

### 2. 向后兼容性

如果只有 `user.jinja`:
```rust
let task = manager.load_task_dir("old_template/")?;
// task.config 使用默认值
// task.system_template = None
// task.user_template = "..." (正常加载)
```

### 3. 类型安全

- 使用 Rust 枚举 `PermissionMode`
- YAML 反序列化自动验证
- 编译时类型检查

---

## 下一步建议

1. **集成到 ExecutionEngine** (Phase 1 任务):
   - 在运行时从 TaskConfig 读取配置
   - 传递 `disallowed_tools` 到 Agent
   - 实现 `permission_mode` 逻辑

2. **文档更新**:
   - 更新 `ca-pm/README.md`
   - 添加模板创建指南

3. **可选增强**:
   - 支持 `system.jinja` 覆盖 Agent preset
   - 添加模板验证 CLI 命令
   - 支持模板变量文档 (在 config.yml 中)

---

## 总结

✅ **所有任务目标全部达成**:

- 定义了 TaskConfig, TaskTemplate, PermissionMode 结构
- 实现了 load_task_dir 和 render_task 方法
- 为 12 个模板创建了 config.yml 文件
- 重构了模板目录结构 (phase*.jinja → phase*/user.jinja)
- 更新了 lib.rs 导出
- 创建了 8 个新单元测试 (14 个测试全部通过)
- 通过了 Cargo test 和 Clippy 验证
- 保持了向后兼容性

**代码质量**: 
- 14 测试全部通过
- Clippy 无警告
- 完整的文档注释
- 合理的错误处理

**设计原则**:
- 向后兼容 ✅
- 类型安全 ✅
- 灵活配置 ✅
- 清晰的默认值 ✅

🎉 **Prompt 模板重构圆满完成!**
