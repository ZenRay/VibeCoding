# Feature Specification: AI Slide Generator

**Feature Branch**: `001-ai-slide-generator`  
**Created**: 2026-02-01  
**Version**: v2.0.0 (Multi-Version Project Management)  
**Status**: ✅ **100% Complete - Production Ready**  
**Last Updated**: 2026-02-01  
**Input**: User description: "这个 app是一个本地运行的单页app,使用nano banana pro生成图片 slides,可以以走马灯的形式全屏播出。后端使用Python,前端使用Typescript。参考NotebookLM的slide功能，要求图片的视觉风格要统一，用户可以提供一个视觉风格图片或者文字描述。"

**Updates**: 
1. Use Google AI SDK (Gemini) instead of Nano Banana Pro.
2. Sidebar slide reordering via drag-and-drop.
3. Manual regeneration button for content changes.
4. First-run style selection workflow (2 options -> save to outline.yml).
5. Update model to `gemini-3-pro-image-preview`.
6. **v2.0.0**: Multi-version project management (2026-02-01).

---

## 🎯 Implementation Status

### ✅ Completed (100%)
- **Phase 1**: Project foundation (FastAPI + React + Vite + Tailwind CSS)
- **Phase 2**: Style initialization system (StyleInitializer component + 2 API endpoints)
- **Phase 3**: Slide management (CRUD + drag-and-drop + auto-save + hash detection)
- **Phase 4**: Carousel fullscreen presentation (auto-advance + keyboard navigation + controls)
- **Phase 5**: Polish & testing (error handling + E2E tests)
- **Phase 6**: Multi-version project management (v2.0.0)
- **UI/UX**: Modern gradient design, toast notifications, loading states, error handling
- **Infrastructure**: Structured logging, three-layer error handling, atomic YAML writes
- **Testing**: 19 automated API tests (100% pass rate) + comprehensive frontend test checklist

### 🎉 Project Complete
All 38 tasks completed, 5 User Stories fully implemented and tested.

### 📊 Metrics
- **Code**: ~5,000 lines (Backend: 1,500 lines, Frontend: 3,500 lines)
- **Components**: 5 core React components (VersionSelector, StyleInitializer, Sidebar, SlideEditor, Carousel)
- **API Endpoints**: 11 RESTful endpoints (including version management)
- **Tests**: 19 automated backend tests + comprehensive E2E testing
- **Documentation**: 5 consolidated guides (~1,320 lines)

---

## Clarifications

### Session 2026-02-01
- Q: Which tech stack to use for Frontend and Backend? → A: Option A: React + Vite + Tailwind CSS (Frontend) and FastAPI (Backend).
- Q: Should we use Swagger for API documentation? → A: Option A: Yes, use Swagger (Built-in with FastAPI).
- Q: Should we use SQLite or just YAML for data persistence? → A: Option A: YAML-only (`outline.yml`) as the Single Source of Truth.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - 风格初始化与生成 (Priority: P1)

作为一个新用户，我希望为我的演示建立一个视觉风格，以便所有后续的幻灯片都具有一致的外观。

**Why this priority**: 对于“统一视觉风格”的需求至关重要，并且是应用程序的入口点。

**Independent Test**: 清除 `outline.yml`，启动应用程序，验证是否出现弹窗，验证是否生成了 2 张图片，验证选择是否保存到文件。

**Acceptance Scenarios**:

1. **Given** 不存在 `outline.yml` (或未定义风格), **When** 我打开应用程序, **Then** 会出现一个弹窗询问风格描述。
2. **Given** 我输入了风格描述, **When** 我提交, **Then** 系统使用 **Gemini** 生成 2 张候选图片。
3. **Given** 显示了 2 张候选图片, **When** 我选择其中一张, **Then** 该图片作为风格参考被保存到 `outline.yml`，并加载主界面。
4. **Given** 已保存风格, **When** 我生成后续的幻灯片, **Then** 它们会使用保存的图片作为风格参考。

---

### User Story 2 - 幻灯片管理与排序 (Priority: P2)

作为一个创作者，我希望通过在侧边栏中拖动幻灯片来组织它们，以便我可以控制演示的流程。

**Why this priority**: 播放前需要基本的内容组织功能。

**Independent Test**: 生成 3 张幻灯片，将第 3 张拖到第 1 个位置，验证顺序是否持久化。

**Acceptance Scenarios**:

1. **Given** 侧边栏中有一列生成的幻灯片, **When** 我拖动一张幻灯片, **Then** 我可以将它放置在一个新位置。
2. **Given** 我已经重新排序了幻灯片, **When** 我播放轮播, **Then** 图片按新顺序出现。
3. **Given** 我已经重新排序了幻灯片, **When** 我重启应用程序, **Then** 新顺序被保留 (保存在 `outline.yml` 中)。

---

### User Story 3 - 内容变更时手动重新生成 (Priority: P2)

作为一个编辑内容的用户，我希望在更改文本时手动触发图片更新，以便我可以在打字时节省资源，不进行自动生成。

**Why this priority**: 优化资源使用并赋予用户控制权。

**Independent Test**: 更改幻灯片的文本，验证“重新生成”按钮出现，点击它，验证新图片替换旧图片。

**Acceptance Scenarios**:

1. **Given** 一张已有图片的幻灯片, **When** 我编辑文本内容, **Then** 图片保持不变，但在主图片区域下方出现“重新生成图片”按钮。
2. **Given** “重新生成图片”按钮可见, **When** 我点击它, **Then** 基于新文本和保存的风格生成一张新图片。
3. **Given** 新图片已生成, **Then** “重新生成图片”按钮消失。

---

### User Story 4 - 全屏轮播播放 (Priority: P1)

作为一个演示者，我希望全屏自动播放生成的图片。

**Why this priority**: 主要的消费模式。

**Independent Test**: 进入全屏，验证自动播放。

**Acceptance Scenarios**:

1. **Given** 已生成的幻灯片, **When** 我点击“播放”, **Then** 应用程序进入全屏跑马灯模式。
2. **Given** 全屏模式, **Then** 图片自动循环播放。
3. **Given** 全屏模式, **When** 我按 Esc 键, **Then** 应用程序退出全屏。

---

### User Story 5 - 多版本项目管理 (Priority: P2) ✨ **v2.0.0 新增**

作为一个内容创作者，我希望创建和管理多个独立的幻灯片项目，以便我可以为不同场景准备不同的演示。

**Why this priority**: 支持多项目工作流，提升应用实用性。

**Independent Test**: 启动应用，选择现有版本或创建新项目，验证版本之间完全隔离。

**Acceptance Scenarios**:

1. **Given** 启动应用程序且未选择版本, **When** 我查看版本选择器, **Then** 显示所有可用的项目版本卡片。
2. **Given** 版本选择器, **When** 我点击某个版本卡片, **Then** 加载该版本的所有幻灯片和风格数据。
3. **Given** 版本选择器, **When** 我点击"创建新项目", **Then** 显示风格初始化模态框。
4. **Given** 风格初始化模态框, **When** 我输入提示词并选择风格, **Then** 自动创建新版本并进入编辑界面。
5. **Given** 我在版本 A 中编辑, **When** 我切换到版本 B, **Then** 版本 A 的数据被保存，版本 B 的数据被加载。
6. **Given** 多个版本, **Then** 每个版本的 `outline.yml` 和图片资源完全独立存储在 `assets/vX/` 目录中。
7. **Given** 候选图片面板, **When** 我单击候选图片, **Then** 预览图片并更新左侧缩略图（不保存到 outline.yml）。
8. **Given** 候选图片面板, **When** 我双击候选图片, **Then** 确认选择（绿色边框 + ✓）并保存到 outline.yml。
9. **Given** 生成新的候选图片, **Then** 不自动标记为已选择，需要用户双击确认。

---

### Edge Cases

- **Gemini API Error**: 如果 **Google AI SDK** 返回错误 (配额/网络)，显示 Toast 通知。
- **Missing Style File**: 如果 `outline.yml` 损坏或丢失风格，再次触发初始化弹窗。
- **No Text**: 如果文本为空，“重新生成”按钮应被禁用。

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: 系统必须使用 **Google AI SDK (Gemini)** 进行所有图片生成任务。
- **FR-002**: 系统必须将项目状态 (幻灯片顺序、文本、风格参考路径) 存储在 `outline.yml` 中。
- **FR-003**: 在首次启动 (缺少风格) 时，系统必须提示输入风格文本，生成 2 个选项，并强制用户选择。
- **FR-004**: 系统必须允许用户通过侧边栏中的 **drag-and-drop** 重新排序幻灯片。
- **FR-005**: 系统必须检测幻灯片文本内容哈希是否与图片的存储哈希不同。
- **FR-006**: 当哈希不同时，系统必须显示手动的“生成/更新图片”按钮 (不自动生成)。
- **FR-007**: 后端必须是 **Python (FastAPI)**; 前端必须是 **TypeScript (React + Vite + Tailwind)**。
- **FR-008**: 系统必须支持全屏自动播放 (marquee)。
- **FR-009**: 系统必须要求并验证 `GEMINI_API_KEY` 环境变量。
- **FR-010**: 系统必须启用 **Swagger UI** (`/docs`) 以进行 API 文档和测试。
- **FR-011**: 数据持久化必须**仅使用** `outline.yml` 文件 (Single Source of Truth)，不使用额外数据库。
- **FR-012** ✨: 系统必须支持多版本项目管理，每个版本存储在独立的 `assets/vX/outline.yml` 目录中 (v2.0.0)。
- **FR-013** ✨: 启动时必须显示版本选择器，列出所有可用版本 (v2.0.0)。
- **FR-014** ✨: 用户必须能够创建新版本，通过输入风格提示词并选择生成的风格 (v2.0.0)。
- **FR-015** ✨: 候选图片单击必须仅预览（不保存），双击必须确认并保存到 outline.yml (v2.0.0)。
- **FR-016** ✨: 新生成的候选图片不得自动标记为已选择 (v2.0.0)。

### Key Entities

- **outline.yml**: YAML 文件存储:
  - `style_reference`: 选中风格图片的路径。
  - `slides`: 对象列表 { `id`, `text`, `image_path`, `content_hash` }。
- **Style Candidate**: 初始化阶段生成的临时图片。

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 首次运行流程 (提示 -> 2 张图片 -> 选择) 在 1 分钟内完成。
- **SC-002**: 幻灯片重新排序立即反映在 UI 中 (延迟 < 100ms)。
- **SC-003**: `outline.yml` 在应用程序重启后准确持久化状态。
- **SC-004**: 100% 的图片生成请求使用 **Google AI SDK**。
