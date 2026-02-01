# AI Slide Generator - Week7 项目文档

**版本**: v2.0.0 (多版本项目管理)  
**日期**: 2026-02-01  
**状态**: ✅ 生产就绪

---

## 📋 项目概述

AI Slide Generator 是一个基于 AI 的幻灯片生成工具，支持通过自然语言描述自动生成精美的幻灯片内容和图片。

### 核心特性

- 🎨 **AI 风格生成**：根据文字描述生成独特的视觉风格
- 📊 **智能幻灯片生成**：自动将文本内容转换为带图片的幻灯片
- 🔄 **多版本项目管理**：支持创建和管理多个独立项目
- 🖼️ **候选图片系统**：生成多个候选图片供用户选择
- 🎯 **实时预览**：单击预览、双击确认的直观交互
- 💾 **自动保存**：所有修改自动保存到本地文件

---

## 🚀 快速开始

### 环境要求

- **后端**: Python 3.12+
- **前端**: Node.js 18+
- **AI API**: OpenRouter API Key 或 Google Gemini API Key

### 安装和启动

```bash
# 1. 克隆项目
cd ~/Documents/VibeCoding/Week7

# 2. 配置后端
cd backend
cp .env.example .env
# 编辑 .env 填入你的 API keys

# 3. 启动服务（一键启动）
cd ..
./start-dev.sh
```

访问：http://localhost:5174

### 一键脚本

```bash
./start-dev.sh        # 启动前端和后端
./start-backend.sh    # 只启动后端
./stop-backend.sh     # 停止后端
```

---

## 📖 技术栈

### 后端
- **框架**: FastAPI (Python)
- **AI SDK**: OpenAI SDK (兼容 OpenRouter)
- **图片处理**: Pillow
- **数据存储**: YAML (outline.yml)

### 前端
- **框架**: React 19 + TypeScript
- **状态管理**: Zustand
- **样式**: TailwindCSS
- **构建**: Vite
- **交互**: @dnd-kit (拖拽排序)

---

## 🎯 核心概念

### 1. 多版本项目管理

每个项目版本独立存储：
```
assets/
├── v1/
│   ├── outline.yml        # 项目配置和幻灯片数据
│   ├── style_xxx.png      # 风格参考图片
│   └── slide_xxx.png      # 幻灯片图片
├── v2/
│   └── ...
└── v3/
    └── ...
```

### 2. 工作流程

1. **创建项目**：输入风格描述 → 生成候选风格 → 选择喜欢的风格
2. **添加幻灯片**：输入文本内容 → 自动生成匹配风格的图片
3. **精细调整**：生成多个候选图片 → 预览对比 → 双击确认
4. **演示播放**：全屏播放模式

### 3. 候选图片交互

- **单击**：临时预览（更新显示，不保存）
- **双击**：确认选择（保存到 outline.yml）
- **+按钮**：生成新的候选图片

---

## ⚙️ 配置说明

### 环境变量 (.env)

```bash
# AI 模式
AI_MODE=real                 # stub (测试) 或 real (生产)

# AI 提供商
AI_PROVIDER=openrouter       # google 或 openrouter
OPENROUTER_API_KEY=sk-or-v1-...
OPENROUTER_MODEL=google/gemini-3-pro-image-preview

# 图片配置
IMAGE_SIZE=1K                # 1K, 2K, 4K
IMAGE_ASPECT_RATIO=16:9      # 16:9, 4:3, 1:1

# 代理配置（可选）
HTTP_PROXY=http://127.0.0.1:7890
HTTPS_PROXY=http://127.0.0.1:7890
```

### 推荐配置

**开发测试**：
```bash
AI_MODE=stub                 # 快速测试，不消耗API
IMAGE_SIZE=1K
```

**生产使用**：
```bash
AI_MODE=real
AI_PROVIDER=openrouter
IMAGE_SIZE=1K                # 平衡质量和速度
IMAGE_ASPECT_RATIO=16:9
```

---

## 📚 相关文档

### 完整指南

- [多版本项目管理](./VERSIONED_PROJECTS.md) - 版本系统详细说明
- [AI 配置指南](./AI_CONFIGURATION.md) - 提供商、模型、提示词配置
- [问题修复记录](./FIXES_AND_IMPROVEMENTS.md) - 已知问题和解决方案
- [测试指南](./TESTING_GUIDE.md) - 功能测试和验证

### 快速参考

| 需求 | 文档 |
|------|------|
| 如何切换 AI 模型？ | [AI_CONFIGURATION.md](./AI_CONFIGURATION.md#模型配置) |
| 如何创建新项目版本？ | [VERSIONED_PROJECTS.md](./VERSIONED_PROJECTS.md#创建新版本) |
| 候选图片如何工作？ | [FIXES_AND_IMPROVEMENTS.md](./FIXES_AND_IMPROVEMENTS.md#候选图片交互) |
| 遇到 SSL 错误？ | [FIXES_AND_IMPROVEMENTS.md](./FIXES_AND_IMPROVEMENTS.md#ssl-连接错误) |

---

## 🔧 故障排除

### 常见问题

**Q: 图片生成失败（SSL 错误）**
```bash
# 方案 1: 切换到 stub 模式测试
AI_MODE=stub

# 方案 2: 切换到 Google Gemini
AI_PROVIDER=google
```

**Q: 前端无法连接后端**
```bash
# 检查 CORS 配置
# backend/app/core/config.py 应包含 5173 和 5174 端口
```

**Q: 图片分辨率不对**
```bash
# 修改 .env
IMAGE_SIZE=1K          # 推荐：平衡质量和速度
IMAGE_ASPECT_RATIO=16:9
```

---

## 📊 性能指标

### 生成时间（Real 模式）

| 操作 | OpenRouter (Gemini 3 Pro) |
|------|--------------------------|
| 风格候选 (2张) | ~60-90 秒 |
| 幻灯片图片 (1张) | ~30-40 秒 |

### 资源使用

- **Stub 模式**: <1秒/图片，无 API 消耗
- **Real 模式**: API 费用取决于提供商

---

## 🎓 开发指南

### 项目结构

```
Week7/
├── backend/              # FastAPI 后端
│   ├── app/
│   │   ├── api/         # API 端点
│   │   ├── core/        # 核心逻辑（生成器）
│   │   ├── data/        # 数据存储（YAML）
│   │   └── models/      # 数据模型
│   └── .env             # 环境配置
├── frontend/            # React 前端
│   └── src/
│       ├── components/  # UI 组件
│       ├── store/       # Zustand 状态
│       └── api/         # API 客户端
└── assets/              # 生成的资源
    └── vX/              # 版本化存储
```

### 添加新功能

1. 后端 API：`backend/app/api/endpoints.py`
2. 前端组件：`frontend/src/components/`
3. 状态管理：`frontend/src/store/appStore.ts`

---

## 🤝 贡献指南

### 代码规范

- **Python**: PEP 8
- **TypeScript**: ESLint + Prettier
- **提交信息**: Conventional Commits

### 测试

```bash
# 后端测试
cd backend
pytest

# 前端测试
cd frontend
npm run test

# E2E 测试
./e2e-test.sh
```

---

## 📄 许可证

MIT License

---

## 🔗 相关链接

- [OpenRouter API 文档](https://openrouter.ai/docs)
- [Google Gemini API 文档](https://ai.google.dev/docs)
- [项目 GitHub]()

---

**最后更新**: 2026-02-01  
**维护者**: Ray
