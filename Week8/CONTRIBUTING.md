# 贡献指南

感谢你对 Code Agent 的兴趣！本文档说明如何参与项目开发。

## 开发环境

### 前置要求

- Rust 1.93+ (stable)
- Git
- (可选) [rust-analyzer](https://rust-analyzer.github.io/) 用于 IDE 支持

### 克隆与构建

```bash
git clone https://github.com/your-repo/code-agent.git
cd code-agent/Week8

# 构建
cargo build

# 运行测试
cargo test

# 运行 CLI
cargo run -- init
```

## 代码规范

### 通用规则

- 遵循 [CLAUDE.md](CLAUDE.md) 中的项目规范
- 使用 `cargo fmt` 格式化代码
- 使用 `cargo clippy -- -D warnings` 检查，无警告方可提交

### 提交前检查

```bash
# 格式化
cargo fmt

# 构建
cargo build

# 测试
cargo test

# Lint
cargo clippy -- -D warnings
```

### 错误处理

- **禁止** 使用 `unwrap()` 或 `expect()`（测试代码除外）
- 使用 `?` 或 `match` 处理 `Result`
- 库代码使用 `thiserror`，应用代码使用 `anyhow`
- 使用 `.context()` 提供错误上下文

### 测试

- 单元测试: 放在同文件的 `#[cfg(test)] mod tests`
- 集成测试: 放在 `tests/` 目录
- 测试命名: `test_should_<描述行为>`
- 运行忽略的测试: `cargo test -- --ignored`

## 项目结构

```
Week8/
├── apps/ca-cli/          # CLI 入口
│   └── src/commands/     # 命令实现
├── crates/
│   ├── ca-core/          # 核心引擎
│   │   ├── agent/        # Agent 适配器
│   │   ├── engine/       # 执行引擎
│   │   ├── state/        # 状态管理
│   │   ├── worktree/     # Git Worktree
│   │   └── ...
│   └── ca-pm/            # Prompt 管理
│       └── templates/     # 模板文件
└── docs/                 # 文档
```

## 提交变更

### 分支策略

- `main` - 稳定版本
- `001-*` - 功能开发分支

### Commit 规范

采用 [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>

[optional body]
```

类型示例:

- `feat`: 新功能
- `fix`: 修复
- `docs`: 文档
- `refactor`: 重构
- `test`: 测试
- `chore`: 构建/工具

示例:

```
feat(run): 添加 --skip-test 选项
fix(worktree): 修复 Windows 软链接创建失败
docs: 完善 README 安装指南
```

## Pull Request

1. Fork 仓库并创建分支
2. 确保所有测试通过
3. 更新相关文档
4. 提交 PR，描述变更动机和影响范围
5. 等待 Code Review

## 添加新命令

1. 在 `apps/ca-cli/src/main.rs` 添加子命令定义
2. 在 `apps/ca-cli/src/commands/` 创建命令模块
3. 在 `commands/mod.rs` 注册并实现 `execute_*`
4. 添加单元测试

## 添加新 Agent

1. 在 `ca-core/src/agent/` 实现 `Agent` trait
2. 在 `AgentFactory` 中注册
3. 在 `Config` 中添加环境变量支持

## 文档

- 代码中公开 API 需有 `///` 文档注释
- 模块级文档使用 `//!`
- 示例会作为 doc test 运行

## 问题与讨论

- Bug 报告: 使用 Issue 模板
- 功能建议: 建议先开 Discussion
- 安全问题: 请不要公开披露，私信维护者

---

再次感谢你的贡献！
