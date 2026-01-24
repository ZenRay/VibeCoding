# ScribeFlow 项目结构说明

**项目名称**: ScribeFlow 桌面实时语音听写系统
**Git Branch**: `001-scribeflow-voice-system`
**最后更新**: 2026-01-24

---

## 目录结构概览

ScribeFlow 采用**分离的文档和代码**目录结构:

```
~/Documents/VibeCoding/
│
├── Week3/                                  # 📂 项目根目录 (源代码)
│   ├── .specify/                           # 🛠️ 项目工具和模板
│   │   ├── memory/
│   │   │   └── constitution.md             # 项目宪法
│   │   ├── scripts/                        # Bash 脚本
│   │   └── templates/                      # 文档模板
│   │
│   ├── docs/                               # 📚 项目文档
│   │   ├── integration-summary.md          # 整合总结
│   │   ├── phase-completion-summary.md     # 阶段完成总结
│   │   ├── linux-compatibility-analysis.md # Linux 兼容性分析
│   │   └── linux-compatibility-summary.md  # Linux 兼容性总结
│   │
│   ├── instructions/                       # 📖 技术参考资料
│   │   └── project.md                      # 原始技术架构报告
│   │
│   ├── CLAUDE.md                           # 🤖 Claude Code Agent 指导
│   │
│   ├── src-tauri/                          # 🦀 Rust 后端 (待创建)
│   │   ├── src/
│   │   │   ├── main.rs
│   │   │   ├── lib.rs
│   │   │   ├── audio/                      # 音频处理模块
│   │   │   ├── network/                    # 网络通信模块
│   │   │   ├── input/                      # 文本注入模块
│   │   │   ├── system/                     # 系统集成模块
│   │   │   ├── ui/                         # UI 交互模块
│   │   │   ├── config/                     # 配置管理模块
│   │   │   └── utils/                      # 工具函数
│   │   ├── Cargo.toml
│   │   ├── capabilities/
│   │   │   └── default.json                # Tauri 权限声明
│   │   └── icons/
│   │
│   ├── src/                                # ⚛️ React 前端 (待创建)
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   ├── components/
│   │   │   ├── OverlayWindow.tsx
│   │   │   ├── WaveformVisualizer.tsx
│   │   │   ├── TranscriptDisplay.tsx
│   │   │   └── SettingsPanel.tsx
│   │   ├── stores/
│   │   │   └── transcriptStore.ts
│   │   ├── hooks/
│   │   │   └── useTauriEvents.ts
│   │   └── styles/
│   │       └── globals.css
│   │
│   ├── tests/                              # 🧪 测试目录 (待创建)
│   │   ├── unit/
│   │   ├── integration/
│   │   └── frontend/
│   │
│   ├── package.json                        # Node.js 依赖
│   ├── tsconfig.json                       # TypeScript 配置
│   ├── tailwind.config.js                  # TailwindCSS 配置
│   └── tauri.conf.json                     # Tauri 主配置
│
└── specs/001-scribeflow-voice-system/      # 📋 功能规范和设计文档
    ├── spec.md                             # 功能规范
    ├── design.md                           # 详细设计
    ├── plan.md                             # 实施计划
    ├── research.md                         # 技术调研
    ├── data-model.md                       # 数据模型
    ├── quickstart.md                       # 快速开始
    ├── contracts/                          # API 契约
    │   ├── elevenlabs-websocket-protocol.md
    │   ├── tauri-commands.md
    │   └── test-scenarios.md
    └── checklists/                         # 质量检查清单
        └── requirements.md
```

---

## 关键路径说明

### 1. 项目根目录 (源代码)

```bash
~/Documents/VibeCoding/Week3
```

**用途**:
- Tauri 应用源代码 (src/, src-tauri/)
- 项目级配置 (CLAUDE.md, package.json, Cargo.toml)
- 项目文档 (docs/)
- 开发工具 (.specify/)

**Git 操作**: 所有 Git 命令在此目录执行

```bash
cd ~/Documents/VibeCoding/Week3
git status
git commit
git push
```

---

### 2. 规范文档目录

```bash
~/Documents/VibeCoding/specs/001-scribeflow-voice-system
```

**用途**:
- 功能规范 (spec.md)
- 架构设计 (design.md)
- 实施计划 (plan.md)
- 技术调研 (research.md)
- API 契约 (contracts/)

**访问方式** (从 Week3 目录):

```bash
cd ~/Documents/VibeCoding/Week3

# 相对路径访问规范文档
cat ../specs/001-scribeflow-voice-system/spec.md

# 或使用绝对路径
cat ~/Documents/VibeCoding/specs/001-scribeflow-voice-system/spec.md
```

---

### 3. 共享工具目录

```bash
~/Documents/VibeCoding/Week3/.specify
```

**用途**:
- 项目宪法 (memory/constitution.md)
- Bash 脚本工具 (scripts/)
- 文档模板 (templates/)

**重要脚本**:
- `.specify/scripts/bash/check-prerequisites.sh` - 检查项目环境
- `.specify/scripts/bash/setup-plan.sh` - 初始化计划文档
- `.specify/scripts/bash/update-agent-context.sh` - 更新 AI agent 上下文

---

## 开发工作流中的路径

### 启动开发服务器

```bash
# 必须在 Week3 根目录执行
cd ~/Documents/VibeCoding/Week3
npm run tauri dev
```

### 运行测试

```bash
# Rust 测试
cd ~/Documents/VibeCoding/Week3/src-tauri
cargo test

# 前端测试
cd ~/Documents/VibeCoding/Week3
npm run test
```

### 编辑代码

**Rust 后端**:
```bash
# 路径: ~/Documents/VibeCoding/Week3/src-tauri/src/
vim src-tauri/src/audio/capture.rs
```

**React 前端**:
```bash
# 路径: ~/Documents/VibeCoding/Week3/src/
vim src/components/OverlayWindow.tsx
```

### 查看文档

**规范文档**:
```bash
# 从 Week3 目录访问
cd ~/Documents/VibeCoding/Week3
cat ../specs/001-scribeflow-voice-system/spec.md
```

**项目文档**:
```bash
# Week3 本地文档
cd ~/Documents/VibeCoding/Week3
cat docs/linux-compatibility-summary.md
```

---

## Git 仓库结构

```
~/Documents/VibeCoding/  (Git 仓库根目录)
├── .git/
├── .gitignore
│
├── Week3/               # 当前项目工作目录
│   └── (Tauri 项目代码)
│
├── specs/               # 所有功能的规范文档
│   ├── 001-scribeflow-voice-system/
│   ├── 002-mysql-support/
│   └── 003-export-query-results/
│
└── archive/             # 归档文件
```

**Git 分支**:
- `main` - 主分支
- `001-scribeflow-voice-system` - 当前功能分支

---

## 环境变量和配置

### .env 文件位置

```bash
# 在 Week3 根目录创建
~/Documents/VibeCoding/Week3/.env
```

**内容**:
```env
ELEVENLABS_API_KEY=your_api_key_here
RUST_LOG=debug
```

**重要**: `.env` 文件已在 `.gitignore` 中,不会提交到 Git

---

### Tauri 配置文件

```bash
~/Documents/VibeCoding/Week3/tauri.conf.json
```

**关键配置**:
- `productName`: "ScribeFlow"
- `identifier`: "com.scribeflow.app"
- `windows`: 悬浮窗配置
- `macOSPrivateApi`: true (防止 App Nap)

---

### Cargo.toml 位置

```bash
~/Documents/VibeCoding/Week3/src-tauri/Cargo.toml
```

**工作空间配置** (如使用):
```bash
~/Documents/VibeCoding/Week3/Cargo.toml
```

---

## 构建产物位置

### 开发构建

```bash
~/Documents/VibeCoding/Week3/src-tauri/target/debug/
```

### 生产构建

```bash
~/Documents/VibeCoding/Week3/src-tauri/target/release/
```

### 打包产物

**macOS**:
```bash
~/Documents/VibeCoding/Week3/src-tauri/target/release/bundle/macos/ScribeFlow.app
~/Documents/VibeCoding/Week3/src-tauri/target/release/bundle/dmg/ScribeFlow.dmg
```

**Linux**:
```bash
~/Documents/VibeCoding/Week3/src-tauri/target/release/bundle/deb/scribeflow_0.1.0_amd64.deb
~/Documents/VibeCoding/Week3/src-tauri/target/release/bundle/appimage/scribeflow_0.1.0_amd64.AppImage
```

---

## 日志和数据位置

### 开发模式

**日志输出**: stdout (控制台)

```bash
RUST_LOG=debug npm run tauri dev
```

### 生产模式

**日志文件**:
- macOS: `~/Library/Logs/ScribeFlow/app.log`
- Linux: `~/.local/share/scribeflow/logs/app.log`

**配置文件**:
- macOS: `~/Library/Application Support/ScribeFlow/config.json`
- Linux: `~/.config/scribeflow/config.json`

**API 密钥存储**:
- macOS: Keychain (系统级,不在文件系统)
- Linux: Secret Service (GNOME Keyring / KWallet)

---

## IDE 项目配置

### VS Code

**工作区文件**: `~/Documents/VibeCoding/Week3/scribeflow.code-workspace`

```json
{
  "folders": [
    {
      "name": "Week3 (Source Code)",
      "path": "."
    },
    {
      "name": "Specs (Documentation)",
      "path": "../specs/001-scribeflow-voice-system"
    }
  ],
  "settings": {
    "rust-analyzer.cargo.features": "all",
    "files.exclude": {
      "**/node_modules": true,
      "**/target": true
    }
  }
}
```

### Rust Analyzer

配置路径: `~/Documents/VibeCoding/Week3/src-tauri/rust-analyzer.toml`

```toml
# 确保 rust-analyzer 在 src-tauri 目录工作
[cargo]
features = "all"
```

---

## 常见路径操作

### 从规范文档跳转到代码

```bash
# 当前在 specs 目录
cd ~/Documents/VibeCoding/specs/001-scribeflow-voice-system

# 跳转到源代码
cd ../../Week3

# 或使用绝对路径
cd ~/Documents/VibeCoding/Week3
```

### 从代码跳转到规范文档

```bash
# 当前在 Week3 目录
cd ~/Documents/VibeCoding/Week3

# 跳转到规范文档
cd ../specs/001-scribeflow-voice-system

# 查看规范
cat spec.md
```

### 运行 speckit 命令

```bash
# 必须在 VibeCoding 根目录或 Week3 目录
cd ~/Documents/VibeCoding/Week3

# 运行 speckit 命令
/speckit.tasks
/speckit.analyze
```

---

## 部署和分发

### 构建发布版本

```bash
# 在 Week3 目录
cd ~/Documents/VibeCoding/Week3

# 构建生产版本
npm run tauri build

# 产物位置 (macOS)
ls src-tauri/target/release/bundle/macos/ScribeFlow.app
ls src-tauri/target/release/bundle/dmg/ScribeFlow.dmg

# 产物位置 (Linux)
ls src-tauri/target/release/bundle/deb/*.deb
ls src-tauri/target/release/bundle/appimage/*.AppImage
```

### 版本发布流程

1. **Tag 版本**:
```bash
cd ~/Documents/VibeCoding/Week3
git tag -a v0.1.0 -m "ScribeFlow v0.1.0: Initial release"
git push origin v0.1.0
```

2. **创建 Release Notes**: 在 `~/Documents/VibeCoding/Week3/CHANGELOG.md`

3. **上传产物**: GitHub Releases 或其他分发平台

---

## 快速参考

### 重要文件路径

| 文件 | 路径 | 用途 |
|------|------|------|
| **Constitution** | `Week3/.specify/memory/constitution.md` | 项目宪法 |
| **CLAUDE.md** | `Week3/CLAUDE.md` | Agent 指导 |
| **Specification** | `specs/001-scribeflow-voice-system/spec.md` | 功能规范 |
| **Design** | `specs/001-scribeflow-voice-system/design.md` | 详细设计 |
| **Plan** | `specs/001-scribeflow-voice-system/plan.md` | 实施计划 |
| **Main.rs** | `Week3/src-tauri/src/main.rs` | Rust 入口 |
| **App.tsx** | `Week3/src/App.tsx` | React 根组件 |
| **Cargo.toml** | `Week3/src-tauri/Cargo.toml` | Rust 依赖 |
| **package.json** | `Week3/package.json` | Node.js 依赖 |

### 常用命令 (在 Week3 目录执行)

```bash
cd ~/Documents/VibeCoding/Week3

# 开发
npm run tauri dev

# 测试
cargo test --manifest-path src-tauri/Cargo.toml
npm run test

# 构建
npm run tauri build

# Lint
cargo clippy --manifest-path src-tauri/Cargo.toml
npm run lint

# 格式化
cargo fmt --manifest-path src-tauri/Cargo.toml
npm run format
```

---

## 新开发者入门步骤

1. **克隆仓库**:
```bash
git clone https://github.com/your-org/VibeCoding.git
cd VibeCoding/Week3
git checkout 001-scribeflow-voice-system
```

2. **阅读文档**:
```bash
# 先读规范
cat ../specs/001-scribeflow-voice-system/spec.md

# 再读设计
cat ../specs/001-scribeflow-voice-system/design.md

# 最后读快速开始
cat ../specs/001-scribeflow-voice-system/quickstart.md
```

3. **设置环境**:
```bash
# 按照 quickstart.md 安装依赖
# macOS: 安装 Xcode Tools, Rust, Node.js
# Linux: 运行 scripts/setup-ubuntu.sh
```

4. **配置 IDE**:
```bash
# 打开 VS Code 工作区
code scribeflow.code-workspace
```

5. **开始开发**:
```bash
# 查看任务列表
cat ../specs/001-scribeflow-voice-system/tasks.md

# 启动开发服务器
npm run tauri dev
```

---

**文档版本**: 1.0.0
**创建日期**: 2026-01-24
**维护者**: ScribeFlow 开发团队

**提示**: 将此文件添加到书签,快速查找路径!
