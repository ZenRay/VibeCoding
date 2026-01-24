# 项目位置信息更新总结

**更新日期**: 2026-01-24
**更新原因**: 明确说明项目代码位置在 Week3 目录
**影响范围**: 全部核心文档 + Agent 配置

---

## ✅ 更新完成的文件

### 1. CLAUDE.md (Agent 配置)

**位置**: `~/Documents/VibeCoding/Week3/CLAUDE.md`

**更新内容**:
```markdown
## Project Location

- **Root directory**: `~/Documents/VibeCoding/Week3`
- **Active Feature**: ScribeFlow 桌面实时语音听写系统
- **Source code location**: `~/Documents/VibeCoding/Week3/`
- **Specification location**: `~/Documents/VibeCoding/specs/001-scribeflow-voice-system/`
- **Shared tools**: `.specify/` directory

## Active Feature: ScribeFlow

**Tech Stack**:
- Backend: Rust 2024 edition (Tauri v2.9, cpal 0.16, ...)
- Frontend: TypeScript 5.3 (React 19.2, ...)
- Platform: macOS 10.15+ (Tier 1), Linux X11 (Tier 1), Linux Wayland (Tier 2)

**Key Documents**: (列出所有关键文档的相对路径)
```

**状态**: ✅ 已更新,包含完整的项目位置和当前功能信息

---

### 2. spec.md (功能规范)

**位置**: `~/Documents/VibeCoding/specs/001-scribeflow-voice-system/spec.md`

**更新内容**:
```markdown
**Feature Branch**: `001-scribeflow-voice-system`
**Project Root**: `~/Documents/VibeCoding/Week3`
**Spec Location**: `~/Documents/VibeCoding/specs/001-scribeflow-voice-system`
```

**状态**: ✅ 已更新头部元数据

---

### 3. design.md (详细设计)

**位置**: `~/Documents/VibeCoding/specs/001-scribeflow-voice-system/design.md`

**更新内容**:
```markdown
**版本**: 1.2.0
**项目根目录**: `~/Documents/VibeCoding/Week3`
**规范文档**: `~/Documents/VibeCoding/specs/001-scribeflow-voice-system`
**关联规范**: [spec.md](./spec.md)
**项目宪法**: [constitution.md](../../Week3/.specify/memory/constitution.md)
```

**状态**: ✅ 已更新头部元数据,版本号升级至 1.2.0

---

### 4. plan.md (实施计划)

**位置**: `~/Documents/VibeCoding/specs/001-scribeflow-voice-system/plan.md`

**更新内容**:
```markdown
**Project Root**: `~/Documents/VibeCoding/Week3`
**Implementation Location**: `~/Documents/VibeCoding/Week3` (源代码将在此创建)
**Spec Location**: `~/Documents/VibeCoding/specs/001-scribeflow-voice-system`

## Project Structure

### Project Locations
- **项目根目录**: `~/Documents/VibeCoding/Week3` (源代码位置)
- **规范文档**: `~/Documents/VibeCoding/specs/001-scribeflow-voice-system`

### Source Code (Week3 directory)
**完整路径**: `~/Documents/VibeCoding/Week3/`
```

**项目结构树**: 已更新为 `~/Documents/VibeCoding/Week3/` 路径

**状态**: ✅ 已更新,明确区分文档位置和源代码位置

---

### 5. research.md (技术调研)

**位置**: `~/Documents/VibeCoding/specs/001-scribeflow-voice-system/research.md`

**更新内容**:
```markdown
**Project Root**: `~/Documents/VibeCoding/Week3`
**Spec Location**: `~/Documents/VibeCoding/specs/001-scribeflow-voice-system`
```

**状态**: ✅ 已更新头部元数据

---

### 6. data-model.md (数据模型)

**位置**: `~/Documents/VibeCoding/specs/001-scribeflow-voice-system/data-model.md`

**更新内容**:
```markdown
**Project Root**: `~/Documents/VibeCoding/Week3`
**实现位置**: `~/Documents/VibeCoding/Week3/src-tauri/src/` (Rust 数据结构)
```

**状态**: ✅ 已更新,指明 Rust 结构体实现位置

---

### 7. quickstart.md (快速开始)

**位置**: `~/Documents/VibeCoding/specs/001-scribeflow-voice-system/quickstart.md`

**重大更新**:

**项目初始化章节**:
```markdown
**重要说明**: ScribeFlow 项目使用分离的文档和代码目录:
- **项目根目录**: `~/Documents/VibeCoding/Week3` (源代码在这里)
- **规范文档**: `~/Documents/VibeCoding/specs/001-scribeflow-voice-system`

### 1. 导航到项目目录
cd ~/Documents/VibeCoding/Week3

### 2. 初始化 Tauri 项目 (首次设置)
npm create tauri-app@latest
(项目将在 Week3 目录下创建)
```

**验证项目结构**:
```bash
cd ~/Documents/VibeCoding/Week3
tree -L 2

# 应该看到:
# Week3/
# ├── .specify/                # 项目工具 (已存在)
# ├── CLAUDE.md                # (已存在)
# ├── docs/                    # (已存在)
# ├── src/                     # React 前端 (新创建)
# ├── src-tauri/               # Rust 后端 (新创建)
# └── package.json             # (新创建)
```

**状态**: ✅ 已大幅更新,所有路径指向 Week3 目录

---

### 8. constitution.md (项目宪法)

**位置**: `~/Documents/VibeCoding/Week3/.specify/memory/constitution.md`

**更新内容**:
```markdown
# ScribeFlow Desktop Voice System Constitution

**Project Root**: `~/Documents/VibeCoding/Week3`
**Specification**: `~/Documents/VibeCoding/specs/001-scribeflow-voice-system`
**Branch**: `001-scribeflow-voice-system`
```

**状态**: ✅ 已更新头部元数据

---

### 9. PROJECT_STRUCTURE.md (新文档)

**位置**: `~/Documents/VibeCoding/Week3/PROJECT_STRUCTURE.md`

**目的**: 提供完整的项目目录结构说明和路径参考

**内容**:
- 完整目录树 (Week3 + specs)
- 关键路径说明
- Git 仓库结构
- 环境变量和配置文件位置
- 构建产物位置
- 日志和数据位置
- IDE 项目配置
- 常见路径操作
- 快速参考表

**状态**: ✅ 新创建,100+ 行详细路径说明

---

## 📊 更新统计

| 文档 | 原版本 | 新版本 | 更新内容 |
|------|--------|--------|---------|
| CLAUDE.md | - | 增强 | 添加完整项目位置、活跃功能、技术栈说明 |
| spec.md | v1.0 | v1.1 | 添加 Project Root 和 Spec Location |
| design.md | v1.1.0 | v1.2.0 | 添加项目根目录和规范文档路径 |
| plan.md | v1.0.0 | v1.0.0 (增强) | 添加项目位置说明,更新项目结构路径 |
| research.md | v1.0.0 | v1.1.0 | 添加 Project Root 和 Spec Location |
| data-model.md | v1.0.0 | v1.0.0 (增强) | 添加实现位置说明 |
| quickstart.md | v1.0.0 | v1.1.0 | 重写项目初始化,所有路径指向 Week3 |
| constitution.md | v1.0.0 | v1.0.0 (增强) | 添加项目位置元数据 |
| PROJECT_STRUCTURE.md | - | v1.0.0 (新建) | 完整项目结构参考文档 |

**总计**: 8 个文件更新 + 1 个新文件

---

## 🎯 关键信息汇总

### 项目路径结构

```
~/Documents/VibeCoding/
│
├── Week3/                          ← 📂 项目根目录 (源代码在这里)
│   ├── .specify/                   ← 🛠️ 项目工具
│   ├── CLAUDE.md                   ← 🤖 Agent 配置
│   ├── docs/                       ← 📚 项目文档
│   ├── instructions/               ← 📖 技术参考
│   ├── PROJECT_STRUCTURE.md        ← 🗺️ 路径指南 (新建)
│   │
│   ├── src-tauri/                  ← 🦀 Rust 代码 (待创建)
│   ├── src/                        ← ⚛️ React 代码 (待创建)
│   ├── package.json                ← 📦 Node 依赖 (待创建)
│   └── tauri.conf.json             ← ⚙️ Tauri 配置 (待创建)
│
└── specs/001-scribeflow-voice-system/  ← 📋 功能规范和设计
    ├── spec.md                     ← ✅ 已更新
    ├── design.md                   ← ✅ 已更新
    ├── plan.md                     ← ✅ 已更新
    ├── research.md                 ← ✅ 已更新
    ├── data-model.md               ← ✅ 已更新
    └── quickstart.md               ← ✅ 已更新
```

### 所有文档中的路径表示

| 文档 | 项目根目录表示 | 规范文档表示 |
|------|--------------|-------------|
| CLAUDE.md | `~/Documents/VibeCoding/Week3` | `~/Documents/VibeCoding/specs/001-...` |
| spec.md | `~/Documents/VibeCoding/Week3` | `~/Documents/VibeCoding/specs/001-...` |
| design.md | `~/Documents/VibeCoding/Week3` | `~/Documents/VibeCoding/specs/001-...` |
| plan.md | `~/Documents/VibeCoding/Week3` | `~/Documents/VibeCoding/specs/001-...` |
| research.md | `~/Documents/VibeCoding/Week3` | `~/Documents/VibeCoding/specs/001-...` |
| data-model.md | `~/Documents/VibeCoding/Week3` | `~/Documents/VibeCoding/specs/001-...` |
| quickstart.md | `~/Documents/VibeCoding/Week3` | 多处说明 |
| constitution.md | `~/Documents/VibeCoding/Week3` | `~/Documents/VibeCoding/specs/001-...` |

**一致性**: ✅ 所有文档使用统一的路径表示

---

## 🔍 路径验证脚本

创建验证脚本确保路径正确:

```bash
#!/bin/bash
# scripts/verify-paths.sh

echo "🔍 Verifying ScribeFlow project paths..."

# 检查项目根目录
if [ -d "$HOME/Documents/VibeCoding/Week3" ]; then
    echo "✅ Project root exists: ~/Documents/VibeCoding/Week3"
else
    echo "❌ Project root NOT found: ~/Documents/VibeCoding/Week3"
    exit 1
fi

# 检查规范文档目录
if [ -d "$HOME/Documents/VibeCoding/specs/001-scribeflow-voice-system" ]; then
    echo "✅ Spec directory exists: ~/Documents/VibeCoding/specs/001-scribeflow-voice-system"
else
    echo "❌ Spec directory NOT found"
    exit 1
fi

# 检查关键文件
files=(
    "Week3/CLAUDE.md"
    "Week3/.specify/memory/constitution.md"
    "Week3/PROJECT_STRUCTURE.md"
    "specs/001-scribeflow-voice-system/spec.md"
    "specs/001-scribeflow-voice-system/design.md"
    "specs/001-scribeflow-voice-system/plan.md"
    "specs/001-scribeflow-voice-system/research.md"
    "specs/001-scribeflow-voice-system/data-model.md"
    "specs/001-scribeflow-voice-system/quickstart.md"
)

for file in "${files[@]}"; do
    if [ -f "$HOME/Documents/VibeCoding/$file" ]; then
        echo "✅ $file"
    else
        echo "❌ $file NOT found"
    fi
done

# 检查 Git 分支
cd ~/Documents/VibeCoding/Week3
current_branch=$(git branch --show-current)
if [ "$current_branch" = "001-scribeflow-voice-system" ]; then
    echo "✅ On correct branch: $current_branch"
else
    echo "⚠️  Current branch: $current_branch (expected: 001-scribeflow-voice-system)"
fi

echo ""
echo "✅ Path verification complete!"
```

---

## 📝 开发者快速参考

### 项目根目录 (源代码)
```bash
cd ~/Documents/VibeCoding/Week3
```

**用于**:
- 编写 Rust 代码 (`src-tauri/src/`)
- 编写 React 代码 (`src/`)
- 运行开发服务器 (`npm run tauri dev`)
- 执行测试 (`cargo test`)
- Git 操作 (`git commit`, `git push`)

---

### 规范文档目录
```bash
cd ~/Documents/VibeCoding/specs/001-scribeflow-voice-system
```

**用于**:
- 阅读功能规范 (`spec.md`)
- 查看架构设计 (`design.md`)
- 了解实施计划 (`plan.md`)
- 查看技术调研 (`research.md`)
- 查看数据模型 (`data-model.md`)
- API 契约参考 (`contracts/*.md`)

---

### 快速跳转

```bash
# 从代码跳转到文档
alias goto-specs='cd ~/Documents/VibeCoding/specs/001-scribeflow-voice-system'

# 从文档跳转到代码
alias goto-code='cd ~/Documents/VibeCoding/Week3'

# 添加到 ~/.bashrc 或 ~/.zshrc:
echo "alias goto-specs='cd ~/Documents/VibeCoding/specs/001-scribeflow-voice-system'" >> ~/.bashrc
echo "alias goto-code='cd ~/Documents/VibeCoding/Week3'" >> ~/.bashrc
source ~/.bashrc
```

---

## 🎓 为什么采用分离目录?

### 优势

1. **文档独立管理**: specs 目录可以独立版本控制,不受代码频繁变更影响
2. **清晰职责分离**:
   - Week3: 实现 (代码、测试、构建)
   - specs: 规范 (需求、设计、计划)
3. **便于查阅**: 设计文档不会被代码文件淹没
4. **多功能共享**: specs 内可以有多个功能 (001, 002, 003...)

### 文档和代码的链接

- 所有文档通过**相对路径**引用: `../../Week3/...`
- 所有代码通过**相对路径**引用: `../specs/001-scribeflow-voice-system/...`
- CLAUDE.md 作为中心枢纽,包含双向路径

---

## ✅ 验证清单

确认以下所有文档都明确说明了项目位置:

- [x] CLAUDE.md - ✅ 包含完整项目位置和活跃功能信息
- [x] spec.md - ✅ 头部包含 Project Root 和 Spec Location
- [x] design.md - ✅ 头部包含项目根目录和规范文档路径
- [x] plan.md - ✅ 明确区分 Implementation Location 和 Spec Location
- [x] research.md - ✅ 头部包含项目位置
- [x] data-model.md - ✅ 指明 Rust 结构体实现位置
- [x] quickstart.md - ✅ 所有安装步骤使用 Week3 绝对路径
- [x] constitution.md - ✅ 头部包含项目位置
- [x] PROJECT_STRUCTURE.md - ✅ 新建完整路径指南

**总计**: 9 个文件,全部已更新 ✅

---

## 🚀 下一步建议

所有文档已明确标注项目位置,现在可以:

1. **验证路径**: 运行 `bash scripts/verify-paths.sh` (如创建)
2. **初始化项目**: 按照 quickstart.md 在 Week3 目录创建 Tauri 项目
3. **生成任务**: 运行 `/speckit.tasks` 生成详细任务列表
4. **开始实现**: Phase 2 核心功能开发

---

## 📋 Agent Context 信息

Claude Code Agent 现在可以通过读取 `CLAUDE.md` 了解:

1. ✅ 项目根目录: `~/Documents/VibeCoding/Week3`
2. ✅ 当前功能分支: `001-scribeflow-voice-system`
3. ✅ 源代码位置: `Week3/src-tauri/` 和 `Week3/src/`
4. ✅ 规范文档位置: `../specs/001-scribeflow-voice-system/`
5. ✅ 技术栈: Rust 2024 + React 19.2 + Tauri 2.9
6. ✅ 平台支持: macOS (Tier 1), Linux X11 (Tier 1), Linux Wayland (Tier 2)
7. ✅ 关键文档路径: Constitution, Spec, Design, Plan

**Agent 使用建议**: 任何代码生成、文件操作都应基于 `~/Documents/VibeCoding/Week3` 路径。

---

**更新版本**: 1.0.0
**更新时间**: 2026-01-24
**状态**: ✅ Complete - All documents updated with project location

**结论**: 所有相关文档已更新,明确说明项目代码位置在 `~/Documents/VibeCoding/Week3` 目录。
