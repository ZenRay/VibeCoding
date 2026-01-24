# QuickStart: ScribeFlow 开发环境搭建指南

**版本**: 1.1.0
**日期**: 2026-01-24
**目标平台**: macOS 10.15+ / Linux (Ubuntu 22.04+, Fedora 38+)

本文档提供 ScribeFlow 实时语音听写系统的开发环境搭建和快速上手指南。

---

## 目录

1. [系统要求](#系统要求)
2. [开发工具安装](#开发工具安装)
   - [macOS 安装](#macos-安装)
   - [Ubuntu/Debian 安装](#ubuntudebian-安装)
   - [Fedora 安装](#fedora-安装)
3. [项目初始化](#项目初始化)
4. [配置 API 密钥](#配置-api-密钥)
5. [平台权限授予](#平台权限授予)
   - [macOS 权限](#macos-权限)
   - [Linux 权限](#linux-权限)
6. [运行开发服务器](#运行开发服务器)
7. [构建生产版本](#构建生产版本)
8. [测试指南](#测试指南)
9. [常见问题](#常见问题)
   - [macOS 问题](#macos-问题)
   - [Linux 问题](#linux-问题)
10. [开发工作流](#开发工作流)

---

## 系统要求

### 硬件要求

| 组件 | 最低要求 | 推荐配置 |
|------|---------|---------|
| **CPU** | Intel Core i5 (2015+) | Apple M1 或更新 |
| **内存** | 8GB RAM | 16GB RAM |
| **存储** | 2GB 可用空间 | 5GB 可用空间 |
| **麦克风** | 内置或外接麦克风 | 高质量外接麦克风 |

### 软件要求

#### macOS

| 软件 | 版本 | 必需 | 备注 |
|------|------|------|------|
| **macOS** | 10.15+ (Catalina) | ✅ | Tier 1 支持 |
| **Xcode Command Line Tools** | 最新 | ✅ | 编译 Rust 代码 |
| **Rust** | 1.77+ | ✅ | 使用 rustup 安装 |
| **Node.js** | 18 LTS | ✅ | 前端构建工具 |
| **Git** | 2.x | ✅ | 版本控制 |

#### Linux (Ubuntu/Fedora/Arch)

| 软件 | 版本 | 必需 | 备注 |
|------|------|------|------|
| **发行版** | Ubuntu 22.04+ / Fedora 38+ | ✅ | Tier 1 支持 (X11) |
| **显示服务器** | X11 (推荐) / Wayland (降级) | - | Wayland 功能受限 |
| **Rust** | 1.77+ | ✅ | 使用 rustup 安装 |
| **Node.js** | 18 LTS | ✅ | 使用 nvm 安装 |
| **Git** | 2.x | ✅ | 版本控制 |
| **PulseAudio** | - | 推荐 | 音频混合 |
| **GNOME Keyring / KWallet** | - | 推荐 | 密钥安全存储 |

### 网络要求

- **稳定的互联网连接** (往返延迟 <100ms)
- **访问 ElevenLabs API** (wss://api.elevenlabs.io)
- **防火墙** 允许 WebSocket 连接 (WSS, 端口 443)

---

## 开发工具安装

### macOS 安装

#### 1. 安装 Xcode Command Line Tools

```bash
# 检查是否已安装
xcode-select -p

# 如果未安装,执行:
xcode-select --install
```

等待安装完成,然后验证:

```bash
clang --version
# 应该显示 Apple clang version 14.x.x 或更高
```

---

### Ubuntu/Debian 安装

#### 1. 安装系统依赖

```bash
# 更新包列表
sudo apt update

# Tauri 核心依赖
sudo apt install -y \
   build-essential \
   curl \
   wget \
   file \
   pkg-config \
   libssl-dev \
   libgtk-3-dev \
   libayatana-appindicator3-dev \
   librsvg2-dev \
   libwebkit2gtk-4.1-dev \
   patchelf

# 音频依赖
sudo apt install -y libasound2-dev

# 密钥存储 (推荐)
sudo apt install -y gnome-keyring libsecret-1-dev

# X11 开发库
sudo apt install -y libx11-dev libxtst-dev

# 音频服务 (运行时)
sudo apt install -y pulseaudio
```

验证安装:

```bash
# 检查编译器
gcc --version

# 检查 PulseAudio
pulseaudio --check && echo "PulseAudio is running" || pulseaudio --start

# 检查 GNOME Keyring
ps aux | grep gnome-keyring
```

**可选**: 如果使用 Wayland,安装实验性支持:
```bash
# GNOME 46+ libei 支持
sudo apt install -y libei-dev
```

---

### Fedora 安装

#### 1. 安装系统依赖

```bash
# 更新系统
sudo dnf update -y

# Tauri 核心依赖
sudo dnf install -y \
    gcc \
    gcc-c++ \
    make \
    openssl-devel \
    gtk3-devel \
    webkit2gtk4.0-devel \
    libappindicator-gtk3-devel \
    librsvg2-devel

# 音频依赖
sudo dnf install -y alsa-lib-devel

# 密钥存储
sudo dnf install -y gnome-keyring libsecret-devel

# X11 开发库
sudo dnf install -y libX11-devel libXtst-devel
```

---

### 通用步骤 (macOS + Linux)

#### 2. 安装 Rust

```bash
# 使用 rustup 安装 Rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# 选择默认安装选项 (1)
# 安装完成后,激活环境:
source $HOME/.cargo/env

# 验证安装
rustc --version
# 应该显示 rustc 1.77.0 或更高

cargo --version
# 应该显示 cargo 1.77.0 或更高
```

#### 3. 安装 Node.js

**方法 1: 使用 nvm (推荐)**

```bash
# 安装 nvm
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash

# 重新加载 shell 配置
source ~/.bashrc  # 或 source ~/.zshrc (macOS)

# 安装 Node.js 18 LTS
nvm install 18
nvm use 18
nvm alias default 18

# 验证
node --version  # v18.x.x
npm --version   # 9.x.x or 10.x.x
```

**方法 2: 系统包管理器**

```bash
# macOS (使用 Homebrew)
brew install node@18

# Ubuntu
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# Fedora
sudo dnf install -y nodejs
```

---

### 2. 安装 Rust

使用 rustup 安装 Rust 工具链:

```bash
# 下载并安装 rustup
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# 选择默认安装选项 (1)
# 安装完成后,重新加载 shell 配置
source $HOME/.cargo/env
```

验证安装:

```bash
rustc --version
# 应该显示 rustc 1.77.0 或更高

cargo --version
# 应该显示 cargo 1.77.0 或更高
```

配置 Rust 2024 edition (项目要求):

```bash
# 更新到最新稳定版
rustup update stable

# 设置默认工具链
rustup default stable
```

---

### 3. 安装 Node.js

使用 nvm (Node Version Manager) 安装 Node.js:

```bash
# 安装 nvm
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.5/install.sh | bash

# 重新加载 shell 配置
source ~/.bashrc  # 或 ~/.zshrc

# 安装 Node.js 18 LTS
nvm install 18
nvm use 18
nvm alias default 18
```

验证安装:

```bash
node --version
# 应该显示 v18.x.x

npm --version
# 应该显示 9.x.x 或更高
```

---

### 4. 安装 Git (如果未安装)

```bash
# macOS 通常预装 Git,检查版本
git --version

# 如果未安装,通过 Xcode Command Line Tools 安装
xcode-select --install
```

---

## 项目初始化

**重要说明**: ScribeFlow 项目使用分离的文档和代码目录:
- **项目根目录**: `~/Documents/VibeCoding/Week3` (源代码在这里)
- **规范文档**: `~/Documents/VibeCoding/specs/001-scribeflow-voice-system` (设计文档)

### 1. 导航到项目目录

```bash
# 进入项目根目录
cd ~/Documents/VibeCoding/Week3

# 确认分支
git branch
# 应该显示: * 001-scribeflow-voice-system

# 查看项目结构
ls -la
# 应该看到: .specify/, CLAUDE.md, docs/, instructions/ 等
```

**注意**: 如果您是从仓库克隆,请使用:

```bash
# 克隆整个 VibeCoding 仓库
git clone https://github.com/your-org/VibeCoding.git

# 进入 Week3 工作目录
cd VibeCoding/Week3

# 切换到功能分支
git checkout 001-scribeflow-voice-system
```

### 2. 初始化 Tauri 项目 (首次设置)

**如果 Week3 目录下尚未创建 Tauri 项目**,需要先初始化:

```bash
# 确认在 Week3 目录
cd ~/Documents/VibeCoding/Week3
pwd  # 应该输出: /home/ray/Documents/VibeCoding/Week3

# 创建 Tauri 项目
npm create tauri-app@latest

# 按提示操作:
# - Project name: scribeflow (或直接回车使用当前目录)
# - Choose template: React
# - Add TypeScript: Yes
# - Package manager: npm

# 项目将在当前目录 (Week3) 下创建标准 Tauri 结构
```

### 3. 安装 Rust 依赖

```bash
# 确认在 Week3 根目录
cd ~/Documents/VibeCoding/Week3

# 进入 Rust 后端目录
cd src-tauri

# 构建项目 (首次会下载所有依赖,耗时较长)
cargo build

# 预期输出:
#   Compiling cpal v0.16.0
#   Compiling rubato v0.16.2
#   Compiling tokio-tungstenite v0.28.0
#   ...
#   Finished dev [unoptimized + debuginfo] target(s) in 2m 30s
```

**首次构建时间**: 约 2-5 分钟 (取决于网络速度和 CPU 性能)

### 4. 安装 Node.js 依赖

```bash
# 返回 Week3 根目录
cd ~/Documents/VibeCoding/Week3

# 安装前端依赖
npm install

# 预期输出:
#   added 1234 packages in 30s
```

### 5. 验证项目结构

```bash
# 在 Week3 目录下
cd ~/Documents/VibeCoding/Week3
tree -L 2 -I 'node_modules|target'

# 应该看到:
# Week3/
# ├── .specify/                # 项目工具和模板 (已存在)
# ├── CLAUDE.md                # Agent 指导 (已存在)
# ├── docs/                    # 项目文档 (已存在)
# ├── instructions/            # 技术参考 (已存在)
# ├── src/                     # React 前端源码 (新创建)
# │   ├── App.tsx
# │   ├── components/
# │   └── ...
# ├── src-tauri/               # Rust 后端源码 (新创建)
# │   ├── src/
# │   ├── Cargo.toml
# │   └── ...
# ├── package.json             # Node.js 依赖 (新创建)
# ├── tsconfig.json            # TypeScript 配置 (新创建)
# └── tauri.conf.json          # Tauri 配置 (新创建)
# ├── package.json
# ├── tsconfig.json
# └── README.md
```

---

## 配置 API 密钥

### 1. 获取 ElevenLabs API 密钥

1. 访问 [ElevenLabs 官网](https://elevenlabs.io/)
2. 注册账户 (提供免费试用额度)
3. 前往 [Profile Settings](https://elevenlabs.io/settings/api-keys)
4. 创建新的 API 密钥,复制保存

**免费额度**: 通常提供 10,000 字符/月的免费额度,足够初期开发测试使用。

### 2. 配置环境变量

在项目根目录创建 `.env` 文件:

```bash
# 创建 .env 文件 (不会提交到 Git)
touch .env

# 编辑文件
nano .env
```

添加以下内容:

```env
# ElevenLabs API 密钥
ELEVENLABS_API_KEY=your_api_key_here

# 开发环境配置
RUST_LOG=debug
TAURI_DEBUG=true
```

保存并退出 (`Ctrl+O`, `Enter`, `Ctrl+X`)。

### 3. 验证 API 密钥

测试 API 密钥是否有效:

```bash
# 使用 curl 测试连接
curl -X GET "https://api.elevenlabs.io/v1/user" \
  -H "xi-api-key: your_api_key_here"

# 应该返回用户信息 JSON,如:
# {
#   "subscription": {
#     "tier": "free",
#     "character_count": 9500,
#     "character_limit": 10000
#   }
# }
```

如果返回 `401 Unauthorized`,说明 API 密钥无效,请重新生成。

---

## macOS 权限授予

ScribeFlow 需要以下 macOS 权限才能正常工作。

### 1. 麦克风权限

**说明**: 用于采集音频数据。

**授予方式**: 首次运行应用时,macOS 会自动弹出权限请求对话框。

**手动授予**:

1. 打开 "系统偏好设置 > 安全性与隐私 > 隐私"
2. 选择 "麦克风"
3. 勾选 "ScribeFlow" 或 "Terminal" (开发模式)

### 2. 辅助功能 (Accessibility) 权限

**说明**: 用于文本注入和焦点检测。

**授予方式**:

1. 打开 "系统偏好设置 > 安全性与隐私 > 隐私"
2. 选择 "辅助功能"
3. 点击左下角锁图标,输入管理员密码
4. 点击 "+" 按钮,添加以下应用:
   - **开发模式**: `/Applications/Utilities/Terminal.app`
   - **生产模式**: `/Applications/ScribeFlow.app`

**验证权限**:

```bash
# 使用 Rust 代码检查权限
cd src-tauri
cargo run --example check_permissions

# 应该输出:
# Microphone: ✅ Granted
# Accessibility: ✅ Granted
```

### 3. 屏幕录制权限 (可选)

**说明**: 用于获取活跃窗口标题 (可选功能)。

**授予方式**: 与辅助功能权限相同,在 "屏幕录制" 选项中添加应用。

**注意**: 如果不授予此权限,窗口标题将显示为空,但不影响核心功能。

---

## 运行开发服务器

### 1. 启动开发模式

```bash
# 在项目根目录执行
npm run tauri dev

# 预期输出:
#   Compiling scribeflow v0.1.0 (/path/to/scribeflow/src-tauri)
#   Finished dev [unoptimized + debuginfo] target(s) in 5.2s
#   Running `target/debug/scribeflow`
#
#   VITE v4.5.0  ready in 1200 ms
#   ➜  Local:   http://localhost:1420/
#   ➜  Network: use --host to expose
```

**首次启动时间**: 约 30 秒 - 1 分钟 (编译 Rust 代码)

**后续启动时间**: 约 5-10 秒 (增量编译)

### 2. 应用窗口

启动后,应该看到:

1. **主窗口**: React 开发界面 (http://localhost:1420)
2. **系统托盘图标**: ScribeFlow 图标出现在菜单栏
3. **开发者工具**: 可按 `Cmd+Option+I` 打开前端 DevTools

### 3. 测试全局热键

1. 打开任意文本编辑器 (如 TextEdit)
2. 将光标放在文本区域
3. 按下 `Cmd+Shift+\` (全局快捷键)
4. 应该看到悬浮窗出现,显示 "正在连接..."

如果没有反应,检查:

- 辅助功能权限是否授予
- 终端是否在 "辅助功能" 列表中
- 热键是否与其他应用冲突

### 4. 热重载

开发模式支持热重载:

- **前端代码** (src/): 修改后自动刷新浏览器
- **Rust 代码** (src-tauri/src/): 修改后需要重新编译 (自动触发,约 5-10 秒)

**观察日志输出**:

```bash
# Rust 后端日志 (在终端)
[2026-01-24T10:30:45Z INFO  scribeflow] Audio capture started
[2026-01-24T10:30:46Z INFO  scribeflow] WebSocket connected
[2026-01-24T10:30:47Z DEBUG scribeflow] Received partial_transcript: "你好"

# 前端日志 (在 DevTools Console)
Audio level: 0.75
Partial transcript: 你好
Committed transcript: 你好世界
```

---

## 构建生产版本

### 1. 构建应用

```bash
# 构建生产版本 (优化编译)
npm run tauri build

# 预期输出:
#   Compiling scribeflow v0.1.0 (/path/to/scribeflow/src-tauri)
#   Finished release [optimized] target(s) in 5m 30s
#
#   Bundling ScribeFlow.app
#   Creating DMG installer
#   Done! Artifacts:
#     - src-tauri/target/release/bundle/macos/ScribeFlow.app
#     - src-tauri/target/release/bundle/dmg/ScribeFlow_0.1.0_aarch64.dmg
```

**构建时间**: 约 5-10 分钟 (首次),2-3 分钟 (增量)

### 2. 输出产物

| 文件 | 路径 | 用途 |
|------|------|------|
| **应用包** | `src-tauri/target/release/bundle/macos/ScribeFlow.app` | 可直接运行的应用 |
| **DMG 安装包** | `src-tauri/target/release/bundle/dmg/ScribeFlow_0.1.0_*.dmg` | 分发安装包 |
| **二进制文件** | `src-tauri/target/release/scribeflow` | 命令行可执行文件 |

### 3. 安装应用

```bash
# 方式 1: 直接运行应用包
open src-tauri/target/release/bundle/macos/ScribeFlow.app

# 方式 2: 安装 DMG
open src-tauri/target/release/bundle/dmg/ScribeFlow_0.1.0_*.dmg
# 拖拽 ScribeFlow.app 到 /Applications/ 文件夹
```

### 4. 验证生产构建

```bash
# 检查二进制大小
du -sh src-tauri/target/release/bundle/macos/ScribeFlow.app
# 预期: 约 8-12 MB (取决于架构)

# 检查启动时间
time open src-tauri/target/release/bundle/macos/ScribeFlow.app
# 预期: <500ms
```

---

## 测试指南

### 1. 运行单元测试 (Rust)

```bash
cd src-tauri

# 运行所有单元测试
cargo test

# 运行特定模块测试
cargo test audio::

# 运行特定测试
cargo test test_resampler_accuracy

# 显示详细输出
cargo test -- --nocapture

# 预期输出:
#   running 50 tests
#   test audio::test_resampler_accuracy ... ok
#   test network::test_websocket_protocol ... ok
#   test input::test_clipboard_restoration ... ok
#   ...
#   test result: ok. 50 passed; 0 failed; 0 ignored; 0 measured
```

### 2. 运行集成测试

```bash
# 运行集成测试 (需要启动 Mock 服务器)
cargo test --test '*'

# 运行特定集成测试
cargo test --test end_to_end_test

# 预期输出:
#   running 15 tests
#   test test_websocket_session_flow ... ok
#   test test_text_injection_compatibility ... ok
#   ...
#   test result: ok. 15 passed; 0 failed; 0 ignored
```

### 3. 运行前端测试

```bash
# 返回项目根目录
cd ..

# 运行前端单元测试
npm run test

# 运行特定测试文件
npm run test OverlayWindow.test.tsx

# 运行测试并生成覆盖率报告
npm run test:coverage

# 预期输出:
#   PASS  src/components/OverlayWindow.test.tsx
#   PASS  src/components/WaveformVisualizer.test.tsx
#   ...
#   Test Suites: 10 passed, 10 total
#   Tests:       50 passed, 50 total
#   Coverage:    85%
```

### 4. 代码质量检查

```bash
# Rust 代码检查 (clippy)
cd src-tauri
cargo clippy -- -D warnings

# Rust 代码格式化
cargo fmt --check

# 前端代码检查 (ESLint)
cd ..
npm run lint

# 前端代码格式化 (Prettier)
npm run format
```

---

## 常见问题

### macOS 问题

#### 问题 1: "Audio device not found" 错误

**症状**: 启动应用时提示未检测到麦克风设备。

**解决方案**:

1. 检查麦克风是否连接 (内置或外接)
2. 前往 "系统偏好设置 > 声音 > 输入",确认麦克风正常工作
3. 检查麦克风权限是否授予
4. 重启应用

#### 问题 2: "Permission denied for Accessibility" 错误

**症状**: 无法注入文本,提示权限不足。

**解决方案**:

1. 前往 "系统偏好设置 > 安全性与隐私 > 隐私 > 辅助功能"
2. 点击左下角锁图标,输入管理员密码
3. 确认 "Terminal.app" (开发模式) 或 "ScribeFlow.app" (生产模式) 在列表中且已勾选
4. 如果已在列表中,尝试移除后重新添加
5. 重启应用

---

### Linux 问题

#### 问题 1: "Failed to initialize audio backend" (Linux)

**症状**: cpal 无法枚举音频设备。

**解决方案**:

```bash
# 检查 ALSA 设备
arecord -l

# 如果无设备,检查 PulseAudio
pulseaudio --check
pulseaudio --start

# 测试麦克风
arecord -d 3 -f cd test.wav
aplay test.wav

# 如果仍然失败,检查是否安装 libasound2-dev
dpkg -l | grep libasound2-dev  # Ubuntu
rpm -qa | grep alsa-lib-devel  # Fedora
```

#### 问题 2: "Secret Service not available" (Linux)

**症状**: 无法保存 API 密钥到密钥管理器。

**解决方案**:

```bash
# 安装 GNOME Keyring
sudo apt install gnome-keyring  # Ubuntu
sudo dnf install gnome-keyring  # Fedora

# 启动 keyring daemon
gnome-keyring-daemon --start --components=secrets

# 验证
ps aux | grep gnome-keyring

# 如果仍然失败,应用会降级为加密文件存储
```

#### 问题 3: "Global hotkey not working" (Wayland)

**症状**: Ctrl+Shift+\ 快捷键无响应。

**解决方案**:

**选项 A (推荐)**: 切换到 X11 会话
```bash
# 登录界面选择 "Ubuntu on Xorg" 或类似选项
# 而非 "Ubuntu" (Wayland)
```

**选项 B**: 配置 GNOME Shell 扩展 (GNOME 44+)
```bash
# 安装扩展管理器
sudo apt install gnome-shell-extensions

# 需要配置自定义快捷键扩展
# 将 Ctrl+Shift+\ 映射到 ScribeFlow 命令
```

**选项 C**: 手动模式
- 不使用全局热键
- 通过托盘菜单手动激活语音输入

#### 问题 4: "Text injection not working" (Wayland)

**症状**: 转写文本无法插入到活跃应用。

**解决方案**:

Wayland 下键盘模拟受限,应用已自动降级为剪贴板注入:
- 转写完成后,文本自动复制到剪贴板
- 手动按 Ctrl+V 粘贴
- 或等待应用自动模拟 Ctrl+V (可能不工作)

**推荐**: 使用 X11 会话以获得最佳体验。

#### 问题 5: Tauri 构建失败 "webkit2gtk not found"

**症状**: 编译时提示缺少 webkit2gtk。

**解决方案**:

```bash
# Ubuntu/Debian
sudo apt install libwebkit2gtk-4.0-dev

# Fedora
sudo dnf install webkit2gtk4.0-devel

# Arch
sudo pacman -S webkit2gtk
```

---

### 通用问题

#### 问题 3: "WebSocket connection failed" 错误

**症状**: 无法连接到 ElevenLabs API。

**解决方案**:

1. 检查网络连接
2. 验证 API 密钥是否正确 (`.env` 文件)
3. 测试 API 连接:
   ```bash
   curl -H "xi-api-key: YOUR_KEY" https://api.elevenlabs.io/v1/user
   ```
4. 检查防火墙是否阻止 WebSocket 连接
5. 查看详细错误日志:
   ```bash
   RUST_LOG=debug npm run tauri dev
   ```

### 问题 4: 热键不响应

**症状**: 按下 `Cmd+Shift+\` 无反应。

**解决方案**:

1. 检查辅助功能权限 (见问题 2)
2. 检查热键是否与其他应用冲突:
   - 前往 "系统偏好设置 > 键盘 > 快捷键"
   - 搜索是否有相同的快捷键
3. 尝试更改热键:
   - 打开应用设置
   - 修改全局快捷键为其他组合 (如 `Cmd+Shift+V`)
4. 重启应用

### 问题 5: 构建失败 "linker `cc` not found"

**症状**: `cargo build` 提示找不到链接器。

**解决方案**:

1. 安装 Xcode Command Line Tools:
   ```bash
   xcode-select --install
   ```
2. 验证安装:
   ```bash
   clang --version
   ```
3. 如果已安装但仍报错,重置工具链:
   ```bash
   sudo xcode-select --reset
   ```

### 问题 6: "EACCES: permission denied" (npm install)

**症状**: npm 安装依赖时权限错误。

**解决方案**:

1. 不要使用 `sudo npm install`
2. 修复 npm 权限:
   ```bash
   mkdir ~/.npm-global
   npm config set prefix '~/.npm-global'
   echo 'export PATH=~/.npm-global/bin:$PATH' >> ~/.zshrc
   source ~/.zshrc
   ```
3. 重新安装:
   ```bash
   npm install
   ```

---

## 开发工作流

### 日常开发流程

```bash
# 1. 拉取最新代码
git pull origin 001-scribeflow-voice-system

# 2. 创建功能分支
git checkout -b feature/your-feature-name

# 3. 启动开发服务器
npm run tauri dev

# 4. 编写代码
# - 修改 Rust 后端: src-tauri/src/
# - 修改 React 前端: src/

# 5. 运行测试
cd src-tauri && cargo test && cd ..
npm run test

# 6. 代码质量检查
cd src-tauri && cargo clippy && cargo fmt && cd ..
npm run lint && npm run format

# 7. 提交代码
git add .
git commit -m "feat(scope): description"

# 8. 推送到远程
git push origin feature/your-feature-name

# 9. 创建 Pull Request
# 前往 GitHub 创建 PR
```

### Git Commit 规范

使用 Conventional Commits 格式:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**类型 (type)**:

| 类型 | 说明 | 示例 |
|------|------|------|
| `feat` | 新功能 | `feat(audio): add resampling support` |
| `fix` | Bug 修复 | `fix(websocket): handle connection timeout` |
| `docs` | 文档更新 | `docs(readme): update installation guide` |
| `style` | 代码格式 | `style(clippy): fix linter warnings` |
| `refactor` | 重构 | `refactor(input): extract clipboard logic` |
| `test` | 测试 | `test(audio): add resampler accuracy test` |
| `chore` | 构建/工具 | `chore(deps): update tauri to 2.9.5` |

**示例**:

```bash
git commit -m "feat(overlay): add waveform visualization

- Implement canvas-based waveform rendering
- Add audio level updates at 50ms intervals
- Smooth animation with 30fps target

Closes #42"
```

### 调试技巧

**Rust 后端调试**:

```bash
# 启用详细日志
RUST_LOG=debug npm run tauri dev

# 使用 lldb 调试器
cd src-tauri
cargo build
lldb target/debug/scribeflow
(lldb) breakpoint set --name main
(lldb) run
```

**前端调试**:

```bash
# 在应用中打开 DevTools
Cmd+Option+I

# 查看网络请求
Network Tab

# 查看 React 组件
安装 React DevTools 扩展
```

**WebSocket 流量调试**:

```bash
# 使用 wscat 工具
npm install -g wscat

# 连接到 ElevenLabs API
wscat -c "wss://api.elevenlabs.io/v1/speech-to-text/realtime?model_id=scribe_v2_realtime" \
  -H "xi-api-key: YOUR_KEY"

# 发送测试消息
> {"message_type": "input_audio_chunk", "audio_base_64": "AAABAAACAAA..."}
```

---

## 资源链接

### 官方文档

- [Tauri v2 Documentation](https://v2.tauri.app/)
- [Rust Book](https://doc.rust-lang.org/book/)
- [React Documentation](https://react.dev/)
- [ElevenLabs API Reference](https://elevenlabs.io/docs/api-reference)

### 依赖库文档

- [cpal (音频采集)](https://docs.rs/cpal/)
- [rubato (重采样)](https://docs.rs/rubato/)
- [tokio-tungstenite (WebSocket)](https://docs.rs/tokio-tungstenite/)
- [enigo (键盘模拟)](https://docs.rs/enigo/)

### 社区资源

- [Tauri Discord](https://discord.gg/tauri)
- [Rust Users Forum](https://users.rust-lang.org/)
- [Stack Overflow](https://stackoverflow.com/questions/tagged/tauri)

### 项目仓库

- **GitHub**: https://github.com/your-org/scribeflow
- **Issue Tracker**: https://github.com/your-org/scribeflow/issues
- **CI/CD**: GitHub Actions

---

## 下一步

完成开发环境搭建后,建议:

1. ✅ 阅读 [spec.md](./spec.md) 了解功能需求
2. ✅ 阅读 [design.md](./design.md) 了解架构设计
3. ✅ 阅读 [data-model.md](./data-model.md) 了解数据模型
4. ✅ 阅读 [contracts/](./contracts/) 了解 API 契约
5. ✅ 运行所有测试,确保环境正常
6. ✅ 尝试修改代码,熟悉开发流程

---

**QuickStart 版本**: 1.0.0
**最后更新**: 2026-01-24
**状态**: Complete
