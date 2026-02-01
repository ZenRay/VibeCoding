# AI Slide Generator

**版本**: v2.0.0 (多版本项目管理)  
**日期**: 2026-02-01  
**状态**: ✅ 生产就绪

基于 **Google Gemini AI** 的智能幻灯片生成应用，支持多版本项目管理。

---

## ✨ 核心特性

- 🎨 **AI 风格生成**：根据文字描述生成独特的视觉风格
- 📊 **智能幻灯片生成**：自动将文本内容转换为带图片的幻灯片
- 🗂️ **多版本项目管理**：支持创建和管理多个独立项目
- 🖼️ **候选图片系统**：生成多个候选图片供用户选择
- 🎯 **实时预览**：单击预览、双击确认的直观交互
- 💾 **自动保存**：所有修改自动保存到本地文件

---

## 🚀 快速开始

### 一键启动

```bash
cd Week7
./start-dev.sh
```

访问：http://localhost:5174

### 手动启动

```bash
# 后端
cd backend
source .venv/bin/activate
python run.py

# 前端（新终端）
cd frontend
npm run dev
```

---

## 📖 技术栈

### 后端
- Python 3.12+
- FastAPI
- Google Gemini AI / OpenRouter
- Pillow (图片处理)
- YAML (数据存储)

### 前端
- React 19 + TypeScript
- Zustand (状态管理)
- TailwindCSS
- Vite
- @dnd-kit (拖拽排序)

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
IMAGE_SIZE=1K                # 1K (快速), 2K (标准), 4K (高清)
IMAGE_ASPECT_RATIO=16:9      # 16:9, 4:3, 1:1
```

### 推荐配置

**开发测试**：
```bash
AI_MODE=stub                 # 瞬间生成，零成本
IMAGE_SIZE=1K
```

**生产使用**：
```bash
AI_MODE=real
AI_PROVIDER=openrouter       # 国内可直接访问
OPENROUTER_MODEL=google/gemini-3-pro-image-preview  # 最佳文本渲染
IMAGE_SIZE=1K                # 平衡质量和速度
```

---

## 📁 项目结构

```
Week7/
├── backend/              # FastAPI 后端
│   ├── app/
│   │   ├── api/         # API 端点
│   │   ├── core/        # 核心逻辑
│   │   ├── data/        # 数据存储
│   │   └── models/      # 数据模型
│   └── .env             # 环境配置
├── frontend/            # React 前端
│   └── src/
│       ├── components/  # UI 组件
│       ├── store/       # Zustand 状态
│       └── api/         # API 客户端
├── assets/              # 生成的资源
│   ├── v1/              # 版本1
│   │   ├── outline.yml  # 项目数据
│   │   └── *.png        # 图片资源
│   └── v2/              # 版本2
└── instructions/        # 📚 详细文档
    └── Week7/
        ├── README.md                      # 项目概览
        ├── VERSIONED_PROJECTS.md          # 多版本管理指南
        ├── AI_CONFIGURATION.md            # AI 配置和优化
        ├── FIXES_AND_IMPROVEMENTS.md      # 问题修复记录
        └── TESTING_GUIDE.md               # 测试指南
```

---

## 📚 文档导航

### 📖 完整指南

| 文档 | 说明 |
|------|------|
| [instructions/Week7/README.md](../instructions/Week7/README.md) | 项目概览和快速开始 |
| [instructions/Week7/VERSIONED_PROJECTS.md](../instructions/Week7/VERSIONED_PROJECTS.md) | 多版本项目管理完整指南 |
| [instructions/Week7/AI_CONFIGURATION.md](../instructions/Week7/AI_CONFIGURATION.md) | AI 提供商、模型、提示词配置 |
| [instructions/Week7/FIXES_AND_IMPROVEMENTS.md](../instructions/Week7/FIXES_AND_IMPROVEMENTS.md) | 已知问题和解决方案 |
| [instructions/Week7/TESTING_GUIDE.md](../instructions/Week7/TESTING_GUIDE.md) | 功能测试和验证指南 |

### 🔧 开发参考

- [CURSORRULES.md](./CURSORRULES.md) - AI 开发规则
- [OPTIMIZATION_LOG.md](./OPTIMIZATION_LOG.md) - 优化历史记录

---

## 🎯 API 端点

### 版本管理
- `GET /api/versions` - 列出所有版本
- `GET /api/versions/{version}` - 获取版本信息
- `POST /api/versions/create` - 创建新版本

### 项目操作（需要 version 参数）
- `GET /api/project?version=X` - 获取项目状态
- `POST /api/style/init?version=X` - 生成风格候选
- `POST /api/style/select?version=X` - 保存选定风格
- `POST /api/slides?version=X` - 创建新幻灯片
- `PUT /api/slides/reorder?version=X` - 更新幻灯片顺序
- `PUT /api/slides/{id}?version=X` - 更新幻灯片
- `POST /api/slides/{id}/generate?version=X` - 重新生成图片
- `DELETE /api/slides/{id}?version=X` - 删除幻灯片

---

## 🔧 开发工具

### 脚本

```bash
./start-dev.sh        # 一键启动前后端
./start-backend.sh    # 只启动后端
./stop-backend.sh     # 停止后端
./check-config.sh     # 检查配置
./e2e-test.sh         # E2E 测试
./test-openrouter.sh  # 测试 OpenRouter API
./test-proxy.sh       # 测试代理配置
```

---

## 🎉 版本历史

### v2.0.0 (2026-02-01)
- ✨ 多版本项目管理
- ✨ 候选图片交互优化（单击预览、双击确认）
- ✨ 缩略图实时更新
- 🐛 修复自动确认问题
- 🐛 修复 CORS 配置
- 🐛 修复 SSL 连接错误

### v1.0.0 (2026-01-30)
- 🎉 初始发布
- 风格生成和选择
- 幻灯片创建和编辑
- 拖拽排序
- 演示播放

---

## 📝 许可证

MIT License

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

**最后更新**: 2026-02-01  
**维护者**: Ray
