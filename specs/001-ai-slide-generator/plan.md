# 技术计划: AI Slide Generator (AI 幻灯片生成器)

**状态**: 草稿  
**目标目录**: `Week7/`  
**技术栈**: Python (FastAPI) + TypeScript (React/Vite)

## 1. 目录结构

项目将位于 `Week7/` 目录下，以便与其他周的项目隔离。

```text
Week7/
├── backend/                  # Python FastAPI 后端
│   ├── app/
│   │   ├── api/              # API 路由处理
│   │   │   ├── __init__.py
│   │   │   ├── endpoints.py  # 所有幻灯片/风格端点
│   │   ├── core/             # 核心逻辑
│   │   │   ├── __init__.py
│   │   │   ├── config.py     # 环境变量 (GEMINI_API_KEY)
│   │   │   └── generator.py  # Gemini AI SDK 封装
│   │   ├── data/             # 数据访问层
│   │   │   ├── __init__.py
│   │   │   └── yaml_store.py # outline.yml 读/写
│   │   ├── models/           # Pydantic 模式
│   │   │   ├── __init__.py
│   │   │   └── schemas.py    # 请求/响应模型
│   │   └── main.py           # 应用入口点 (CORS, mounts)
│   ├── requirements.txt
│   ├── .env.example
│   └── run.py                # 开发服务器运行脚本
├── frontend/                 # React Frontend
│   ├── src/
│   │   ├── api/              # Axios/Fetch 封装
│   │   │   └── client.ts
│   │   ├── components/       # UI 组件
│   │   │   ├── Carousel.tsx  # 全屏播放器
│   │   │   ├── Sidebar.tsx   # 拖拽列表 (基于 @dnd-kit)
│   │   │   ├── SlideEditor.tsx # 文本/图片视图
│   │   │   └── StyleInitializer.tsx # 初次运行弹窗
│   │   ├── types/            # TS 接口
│   │   │   └── index.ts
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── package.json
│   ├── tailwind.config.js
│   └── vite.config.ts
├── assets/                   # 生成的图片存储
├── outline.yml               # 单一真实数据源 (Single Source of Truth)
└── README.md
```

## 2. 后端架构 (Python/FastAPI)

### 2.1 API 定义 (Swagger/OpenAPI)

后端将通过 `/docs` 暴露 RESTful 端点文档。

**Base URL**: `http://localhost:8000/api`

#### 端点 (Endpoints)

| 方法 | 路径 | 描述 | 请求体 | 响应 |
|--------|------|-------------|--------------|----------|
| **GET** | `/project` | 加载完整项目状态 | - | `ProjectState` |
| **POST** | `/style/init` | 生成风格候选图 | `StylePrompt` | `List[StyleCandidate]` |
| **POST** | `/style/select` | 保存选定的风格 | `SelectedStyle` | `ProjectState` |
| **POST** | `/slides` | 创建新幻灯片 | `SlideCreate` | `Slide` |
| **PUT** | `/slides/reorder` | 更新幻灯片顺序 | `List[SlideId]` | `ProjectState` |
| **PUT** | `/slides/{id}` | 更新文本内容 | `SlideUpdate` | `Slide` |
| **POST** | `/slides/{id}/generate` | 重新生成图片 | - | `Slide` |
| **DELETE**| `/slides/{id}` | 删除幻灯片 | - | `Success` |

### 2.2 数据模型 (Pydantic)

```python
# models/schemas.py

class Slide(BaseModel):
    id: str
    text: str
    image_path: Optional[str]
    content_hash: str # 当前文本的哈希
    image_hash: Optional[str] # 生成图片时文本的哈希

class ProjectState(BaseModel):
    style_reference: Optional[str]
    slides: List[Slide]

class StylePrompt(BaseModel):
    description: str

class SelectedStyle(BaseModel):
    image_path: str # 临时候选图片的路径
```

### 2.3 业务逻辑 (Service Layer)

1.  **YAML 存储 (`yaml_store.py`)**:
    *   处理 `Week7/outline.yml` 的读/写。
    *   确保原子写入以防止损坏。
    *   如果文件缺失，则初始化空文件。

2.  **生成器 (`generator.py`)**:
    *   封装 `google.genai` SDK (最新版)。
    *   模型: 使用 `gemini-3-pro-image-preview`。
    *   `generate_style_candidates(prompt)`: 返回 2 个图片路径。
    *   `generate_slide_image(text, style_ref_path)`: 返回 1 个图片路径。
    *   代码逻辑参考:
        ```python
        from google import genai
        from google.genai import types
        from PIL import Image

        client = genai.Client()
        response = client.models.generate_content(
            model="gemini-3-pro-image-preview",
            contents=[prompt],
            # config=types.GenerateContentConfig(...) # 如果需要配置参数
        )
        ```
    *   处理 API 错误和重试。

## 3. 前端架构 (React/TS)

### 3.1 组件

1.  **App Container (应用容器)**:
    *   挂载时获取 `ProjectState`。
    *   检查是否缺少 `style_reference` -> 显示 `StyleInitializer`。

2.  **StyleInitializer (模态框)**:
    *   输入: 风格描述文本区域。
    *   显示: 2 张生成的图片 (可选择)。
    *   操作: POST `/style/select`。

3.  **Sidebar (可排序侧边栏)**:
    *   使用 `@dnd-kit` (或 `react-beautiful-dnd`) 实现拖拽。
    *   操作: 拖放时调用 PUT `/slides/reorder`。

4.  **SlideEditor (幻灯片编辑器)**:
    *   左侧: 文本区域 (失去焦点/防抖时自动保存 -> PUT `/slides/{id}`)。
    *   右侧: 图片预览。
    *   逻辑: 比较 `slide.content_hash` vs `slide.image_hash`。如果不同 -> 显示“重新生成”按钮。

5.  **Carousel (全屏轮播)**:
    *   覆盖层: 默认隐藏，由“播放”按钮切换。
    *   自动前进计时器 (例如 5秒)。
    *   "Esc" 键监听退出。

### 3.2 状态管理

*   **全局状态**: `React Context` 或 `Zustand`。
*   **Store**: 保存 `ProjectState`, `isLoading`, `error`。

## 4. 实施步骤

### 第一阶段: 后端核心 (第 1 天)
1.  设置 `Week7` 目录和虚拟环境 (venv, 使用 `uv` 管理)。
2.  实现 `yaml_store.py` (针对 `outline.yml` 的 CRUD)。
3.  实现 `generator.py` (Gemini 集成)。
4.  实现 FastAPI 端点 (先模拟 AI，后接入真实 API)。
5.  通过 Swagger UI 验证。

### 第二阶段: 前端基础 (第 1-2 天)
1.  在 `Week7/frontend` 初始化 Vite 项目。
2.  设置 Tailwind CSS。
3.  实现 `App.tsx` 和 `ProjectState` 获取。
4.  实现 `StyleInitializer` 流程。

### 第三阶段: 编辑器与逻辑 (第 2 天)
1.  实现带拖拽功能的 `Sidebar`。
2.  实现带文本/图片同步逻辑的 `SlideEditor`。
3.  连接“重新生成”按钮到后端。

### 第四阶段: 完善 (第 2-3 天)
1.  实现 `Carousel` (跑马灯模式)。
2.  错误处理 (API 错误的 Toast 通知)。
3.  验证 `outline.yml` 持久化。

## 5. 依赖项与开发环境

**环境管理 (Environment Management)**:
*   后端环境必须使用 `uv` 进行管理 (例如 `uv venv`, `uv pip install`).
*   `.venv` 目录应位于 `Week7/backend/.venv`。

**后端 (Backend)**:
*   `fastapi`, `uvicorn`
*   `pydantic`, `pyyaml`
*   `google-generativeai`
*   `python-dotenv`

**前端**:
*   `react`, `react-dom`
*   `axios` (API 客户端)
*   `@dnd-kit/core`, `@dnd-kit/sortable` (拖拽)
*   `clsx`, `tailwind-merge` (样式工具)
*   `lucide-react` (图标)
