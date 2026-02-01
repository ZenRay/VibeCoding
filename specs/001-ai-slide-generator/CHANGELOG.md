# 变更日志 (CHANGELOG)

本文档记录 AI Slide Generator 项目的所有重大变更。

---

## [2.0.0] - 2026-02-01

### 🎉 重大功能

#### 多版本项目管理
- **新增**: 支持创建和管理多个独立的幻灯片项目
- **新增**: 版本选择器组件，启动时显示所有可用版本
- **新增**: 创建新项目工作流（输入提示词 → 生成风格 → 自动创建版本）
- **架构**: 每个版本完全隔离，使用 `assets/vX/outline.yml` 独立存储

**影响的文件**:
- Backend: `yaml_store.py` (+81 行), `endpoints.py` (+85 行), `generator.py` (+50 行)
- Frontend: `VersionSelector.tsx` (+175 行, 新增), `App.tsx` (+62 行), `appStore.ts` (+111 行)

### ✨ 功能改进

#### 候选图片交互优化
- **改进**: 单击候选图片 → 预览（紫色边框）+ 左侧缩略图更新（不保存）
- **改进**: 双击候选图片 → 确认（绿色边框 + ✓）+ 保存到 outline.yml
- **修复**: 生成候选图片不再自动标记为已选择（`isSelected: false`）

**影响的文件**:
- `ImageCandidatesPanel.tsx` (+25 行)
- `appStore.ts` (修复 `addImageCandidate`)

#### 缩略图实时更新
- **修复**: 双击候选图片确认后，左侧缩略图立即更新
- **修复**: 单击候选图片预览时，左侧缩略图同步更新
- **实现**: 添加回调链 `ImageCandidatesPanel` → `SlideViewer` → `App.tsx` → `appStore`

**影响的文件**:
- `ImageCandidatesPanel.tsx`, `SlideViewer.tsx`, `App.tsx`

### 🐛 Bug 修复

#### CORS 跨域问题
- **修复**: 添加 5174 端口到 CORS 配置，支持 Vite 备用端口
- **原因**: 当默认端口 5173 被占用时，Vite 自动使用 5174
- **文件**: `backend/app/core/config.py`

#### 空项目状态
- **修复**: 新创建的版本（0 张幻灯片）现在显示"添加第一张幻灯片"按钮
- **文件**: `Sidebar.tsx`

#### SSL 连接错误
- **改进**: 更好的错误处理和提示（OpenRouter 连接问题）
- **方案**: 提供 stub 模式降级，或切换到 Google AI 直连

### 🔧 技术改进

#### API 架构
- **新增**: 3 个版本管理端点
  - `GET /api/versions` - 列出所有版本
  - `GET /api/versions/{version}` - 获取版本信息
  - `POST /api/versions/create` - 创建新版本
- **修改**: 所有现有端点添加 `version` 查询参数

#### 状态管理
- **新增**: `currentVersion` 全局状态
- **新增**: `setVersion()`, `loadProject(version)` 方法
- **改进**: 所有 action 自动使用当前版本，无需手动传递

#### 类型系统
- **新增**: `VersionInfo` 接口（版本摘要信息）
- **更新**: `ProjectState` 添加 `version`, `created_at`, `project_name` 字段

#### 资源管理
- **新增**: 版本级资源缓存（避免频繁创建 YAMLStore 和 GeminiGenerator）
- **优化**: GeminiGenerator 绑定到特定版本，简化逻辑

### 📚 文档更新

#### 新增文档（`instructions/Week7/`）
- `README.md` (284 行) - 项目概览和快速开始
- `VERSIONED_PROJECTS.md` (380 行) - 多版本项目管理详细指南
- `AI_CONFIGURATION.md` (240 行) - AI 配置和优化指南
- `FIXES_AND_IMPROVEMENTS.md` (220 行) - Bug 修复和改进记录
- `TESTING_GUIDE.md` (200 行) - 测试指南和检查清单

#### 更新文档（`specs/001-ai-slide-generator/`）
- `STATUS.md` - 添加 v2.0.0 版本历史和 Phase 6 状态
- `tasks.md` - 添加 Phase 6 任务（T029-T042）
- `plan.md` - 添加 Phase 6 技术计划和架构细节

#### 文档整合
- **删除**: 25+ 个临时/过时文档
- **整合**: 相关文档合并到 5 个核心文档
- **结构**: 清晰的 `instructions/Week7/` 目录结构

### 📊 代码统计

- **新增代码**: ~900 行
  - Backend: +280 行
  - Frontend: +600 行
- **总代码量**: ~5,000 行
- **总文档**: ~1,320 行（整合后）

### ✅ 测试状态

- **后端 API**: 版本管理测试通过
- **前端编译**: 0 错误
- **E2E 测试**: stub 模式 ✅, real 模式 ✅
- **交互测试**: 候选图片单击/双击 100% 正常

---

## [1.0.0] - 2026-01-30

### 🎉 初始发布

#### Phase 1: 项目基础
- FastAPI 后端 + React 前端
- YAML 数据存储
- Gemini AI 集成（stub + real 模式）
- CORS 和环境配置

#### Phase 2: 风格初始化
- 风格候选生成 API
- StyleInitializer 组件
- 模态框 UI

#### Phase 3: 幻灯片管理
- 幻灯片 CRUD API
- Sidebar 组件（拖拽排序）
- SlideEditor 组件
- 自动保存机制
- Toast 通知

#### Phase 4: 全屏播放
- Carousel 组件
- 自动翻页（5 秒间隔）
- 键盘导航
- 淡入淡出动画

#### Phase 5: 优化完善
- 错误处理
- Loading 状态
- E2E 测试（19 个自动化测试）
- 文档完善

**总任务**: 28/28 (100%)  
**代码量**: ~4,100 行  
**状态**: 生产就绪

---

## 格式说明

本文档遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/) 规范，使用 [语义化版本](https://semver.org/lang/zh-CN/) 编号。

### 变更类型
- `新增`: 新功能
- `改进`: 对现有功能的改进
- `修复`: Bug 修复
- `移除`: 删除的功能
- `弃用`: 即将移除的功能
- `安全`: 安全相关的修复

---

**最后更新**: 2026-02-01
