# Code Agent 使用示例

## 安装和配置

```bash
# 1. 编译项目
cd ~/Documents/VibeCoding/Week8
cargo build --release

# 2. 设置 API Key
export ANTHROPIC_API_KEY="your-api-key-here"

# 3. (可选) 添加到 PATH
export PATH="$PWD/target/release:$PATH"
```

## 基础使用

### 1. 初始化项目

```bash
code-agent init /path/to/your/project
```

这会:
- ✅ 验证环境变量 (ANTHROPIC_API_KEY)
- ✅ 测试 Agent 连接
- ✅ 生成 CLAUDE.md 配置文件

### 2. 规划功能

```bash
code-agent plan user-authentication \
  --description "Add user login and registration"
```

这会:
- ✅ 分析功能需求
- ✅ 生成 spec.md 和 design.md
- ✅ 创建任务分解

### 3. 执行功能开发 (完整流程)

```bash
code-agent run user-authentication
```

**执行流程**:
```
Phase 1: Observer    → 分析项目结构和代码库
Phase 2: Planning    → 制定详细实施计划
Phase 3: Execute     → 实现核心功能 (Part 1)
Phase 4: Execute     → 完善功能实现 (Part 2)
Phase 5: Review      → 代码审查 + 自动修复 (最多 3 次)
Phase 6: Fix         → 应用审查建议
Phase 7: Verification → 运行测试验证
          ↓
      自动生成 PR
```

### 4. 跳过某些阶段

```bash
# 跳过代码审查
code-agent run user-authentication --skip-review

# 跳过测试验证
code-agent run user-authentication --skip-test

# 两者都跳过
code-agent run user-authentication --skip-review --skip-test
```

### 5. 断点恢复

```bash
# 如果执行中断,可以恢复
code-agent run user-authentication --resume
```

### 6. Dry Run (模拟执行)

```bash
# 不实际执行,只显示会做什么
code-agent run user-authentication --dry-run
```

### 7. 执行特定 Phase

```bash
# 只执行 Phase 5 (Review)
code-agent run user-authentication --phase 5
```

## Review/Fix 自动循环示例

当 Phase 5 (Review) 检测到问题时,会自动进入修复循环:

```
Phase 5: Code Review
  迭代 1/3
  ⚙️  执行审查中...
  ⚠️  需要修复问题 (NEEDS_CHANGES)
    → 执行自动修复...
    ✅ 修复完成
  
  迭代 2/3
  ⚙️  执行审查中...
  ✅ 代码审查通过! (APPROVED)
```

**最多 3 次迭代**。如果 3 次后仍未通过,会报错退出。

## 高级用法

### 1. 查看功能状态

```bash
code-agent status user-authentication
```

输出:
```yaml
feature:
  slug: user-authentication
  status: InProgress
  current_phase: 3
  completion_percentage: 43%

cost_summary:
  total_cost_usd: 1.25
  total_tokens_input: 50000
  total_tokens_output: 25000
```

### 2. 列出所有功能

```bash
code-agent list
```

### 3. 清理 Worktree

```bash
code-agent clean user-authentication
```

## 配置文件

### app.yaml

```yaml
agent:
  agent_type: claude
  model: claude-3-5-sonnet-20241022
  api_key: ${ANTHROPIC_API_KEY}
  api_url: null  # 可选: 使用自定义 endpoint

default_repo: /path/to/your/project

prompt:
  template_dir: crates/ca-pm/templates
```

### Phase 配置 (例如: phase5_review/config.yml)

```yaml
preset: true
disallowed_tools:
  - Write        # Review 阶段禁止写文件
  - StrReplace   # Review 阶段禁止编辑
  - Delete       # Review 阶段禁止删除
permission_mode: default
max_turns: 10
max_budget_usd: 2.0
```

## 故障排除

### 问题: Agent 连接失败

```bash
# 检查 API Key
echo $ANTHROPIC_API_KEY

# 测试连接
code-agent init --verify-only
```

### 问题: Review 一直失败

```bash
# 跳过 Review 继续
code-agent run user-authentication --skip-review

# 或手动查看 Review 输出
cat specs/user-authentication/.ca-state/phase5_output.md
```

### 问题: 断点恢复失败

```bash
# 从特定 Phase 重新开始
code-agent run user-authentication --phase 3
```

## 最佳实践

1. **Always Review the Spec First**: 在运行前检查 `specs/feature-slug/spec.md`
2. **Use Dry Run**: 第一次使用时,先用 `--dry-run` 看看会做什么
3. **Monitor Costs**: 定期检查 `status.md` 中的成本统计
4. **Save Often**: 项目会自动保存状态,但建议定期 commit
5. **Read Review Output**: Review 失败时,查看 `.ca-state/phase5_output.md` 了解问题

---

**更多信息**: 查看 `docs/` 目录中的详细文档。
