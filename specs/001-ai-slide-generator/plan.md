# 技术计划: AI Slide Generator (AI 幻灯片生成器)

**状态**: ✅ **v2.0.0 完成 - 生产就绪**  
**版本**: v2.0.0 (多版本项目管理)  
**最后更新**: 2026-02-01  
**目标目录**: `Week7/`  
**技术栈**: Python (FastAPI) + TypeScript (React/Vite)

---

## 📊 实施进度

| 阶段 | 状态 | 完成度 |
|-----|------|--------|
| Phase 1: 基础架构 | ✅ 完成 | 100% |
| Phase 2: 风格初始化 | ✅ 完成 | 100% |
| Phase 3: 幻灯片管理 | ✅ 完成 | 100% |
| Phase 4: 全屏播放 | ✅ 完成 | 100% |
| Phase 5: 优化完善 | ✅ 完成 | 100% |
| **Phase 6: 多版本管理** | ✅ 完成 | 100% |
| **总计** | **✅ 完成** | **100%** |

**已完成交付物**:
- ✅ 完整的后端 API (11 个端点，含版本管理)
- ✅ 5 个核心前端组件 (VersionSelector, StyleInitializer, Sidebar, SlideEditor, Carousel)
- ✅ Zustand 状态管理
- ✅ Tailwind CSS 设计系统
- ✅ Toast 通知和错误处理
- ✅ 自动保存和 Hash 检测
- ✅ 拖拽排序功能
- ✅ 全屏播放功能
- ✅ 多版本项目管理 (v2.0.0)
- ✅ 候选图片交互优化
- ✅ 端到端测试 (19 个自动化测试)

---

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

---

## 6. Phase 6: Multi-Version Project Management (v2.0.0)

### 6.1 架构目标

**问题**: v1.0.0 只支持单个项目，所有数据存在一个 `outline.yml` 中。

**解决方案**: 引入多版本项目管理，每个版本独立存储 `outline.yml` 和资源文件。

### 6.2 目录结构更新

```text
Week7/
├── assets/
│   ├── v1/
│   │   ├── outline.yml            # 版本 1 的项目数据
│   │   ├── style_reference.png
│   │   ├── style_candidate_*.png
│   │   └── slide_*.png
│   ├── v2/
│   │   ├── outline.yml            # 版本 2 的项目数据
│   │   └── ...
│   └── v13/
│       ├── outline.yml            # 版本 13 的项目数据
│       └── ...
```

**特点**:
- 每个版本完全隔离
- 版本号自动递增
- 支持并行编辑多个项目

### 6.3 后端架构变更

#### YAMLStore 版本化

```python
# app/data/yaml_store.py

class YAMLStore:
    def __init__(self, version: Optional[int] = None):
        """
        初始化 YAMLStore，支持版本化
        
        Args:
            version: 版本号（如 1, 2, 3）
                    如果为 None，使用根目录的 outline.yml（向后兼容）
        """
        if version is not None:
            self.yaml_path = Path(f"assets/v{version}/outline.yml")
            self.assets_dir = Path(f"assets/v{version}")
        else:
            self.yaml_path = Path("outline.yml")
            self.assets_dir = Path("assets")
        
        self.assets_dir.mkdir(parents=True, exist_ok=True)
    
    def list_versions(self) -> List[int]:
        """列出所有可用版本"""
        assets_dir = Path("assets")
        return sorted([
            int(d.name[1:]) for d in assets_dir.iterdir() 
            if d.is_dir() and d.name.startswith("v") and d.name[1:].isdigit()
        ])
    
    def get_version_info(self, version: int) -> Dict:
        """获取版本摘要信息"""
        store = YAMLStore(version)
        data = store.load()
        return {
            "version": version,
            "created_at": data.get("created_at"),
            "project_name": data.get("project_name"),
            "style_reference": data.get("style_reference"),
            "style_prompt": data.get("style_prompt"),
            "slide_count": len(data.get("slides", []))
        }
    
    def create_new_version(self, style_prompt: str = None, 
                          project_name: str = None) -> int:
        """创建新版本，返回版本号"""
        versions = self.list_versions()
        new_version = max(versions) + 1 if versions else 1
        
        store = YAMLStore(new_version)
        initial_data = {
            "version": new_version,
            "created_at": datetime.utcnow().isoformat(),
            "project_name": project_name or f"Project v{new_version}",
            "style_reference": None,
            "style_prompt": style_prompt,
            "slides": []
        }
        store.save(initial_data)
        return new_version
```

#### API 端点扩展

**新增版本管理端点**:

```python
# app/api/endpoints.py

@router.get("/versions", response_model=List[VersionInfo])
async def list_versions():
    """列出所有项目版本"""
    store = YAMLStore()
    versions = store.list_versions()
    return [store.get_version_info(v) for v in versions]

@router.get("/versions/{version}", response_model=VersionInfo)
async def get_version_info(version: int):
    """获取指定版本的信息"""
    store = YAMLStore()
    return store.get_version_info(version)

@router.post("/versions/create", response_model=VersionCreated)
async def create_version(prompt: Optional[StylePrompt] = None):
    """创建新版本"""
    store = YAMLStore()
    new_version = store.create_new_version(
        style_prompt=prompt.description if prompt else None
    )
    return {"version": new_version}
```

**修改现有端点，添加版本参数**:

```python
@router.get("/project", response_model=ProjectState)
async def get_project(version: int = Query(...)):
    """获取指定版本的项目数据"""
    store = YAMLStore(version)
    return store.load()

@router.post("/style/init", response_model=List[StyleCandidate])
async def init_style(
    version: int = Query(...),
    prompt: StylePrompt = Body(...)
):
    """为指定版本生成风格候选"""
    generator = GeminiGenerator(version=version)
    candidates = await generator.generate_style_candidates(prompt.description)
    return candidates
```

#### GeminiGenerator 版本绑定

```python
# app/core/generator.py

class GeminiGenerator:
    def __init__(self, version: int):
        """绑定到特定版本"""
        self.version = version
        self.assets_dir = Path(f"assets/v{version}")
        self.assets_dir.mkdir(parents=True, exist_ok=True)
    
    async def generate_style_candidates(self, prompt: str) -> List[str]:
        """生成并保存到版本化目录"""
        images = []
        for i in range(1, 3):
            image_path = self.assets_dir / f"style_candidate_{i}_{timestamp}.png"
            # ... AI 生成逻辑 ...
            images.append(str(image_path))
        return images
```

#### 资源缓存机制

为了避免频繁创建 `YAMLStore` 和 `GeminiGenerator` 实例，使用字典缓存：

```python
# app/api/endpoints.py

_version_resources: Dict[int, Tuple[YAMLStore, GeminiGenerator]] = {}

def get_version_resources(version: int) -> Tuple[YAMLStore, GeminiGenerator]:
    """获取或创建版本资源"""
    if version not in _version_resources:
        store = YAMLStore(version)
        generator = GeminiGenerator(version)
        _version_resources[version] = (store, generator)
    return _version_resources[version]
```

### 6.4 前端架构变更

#### 类型定义更新

```typescript
// frontend/src/types/index.ts

export interface ProjectState {
  version: number | null;
  created_at: string | null;
  project_name: string | null;
  style_reference: string | null;
  style_prompt: string | null;
  slides: Slide[];
}

export interface VersionInfo {
  version: number;
  created_at: string | null;
  project_name: string | null;
  style_reference: string | null;
  style_prompt: string | null;
  slide_count: number;
}
```

#### API 客户端更新

```typescript
// frontend/src/api/client.ts

export const api = {
  // 版本管理
  listVersions: async (): Promise<VersionInfo[]> => {
    const { data } = await client.get('/versions');
    return data;
  },
  
  createNewVersion: async (prompt?: StylePrompt): Promise<{ version: number }> => {
    const { data } = await client.post('/versions/create', prompt);
    return data;
  },
  
  // 所有方法添加 version 参数
  getProject: async (version: number): Promise<ProjectState> => {
    const { data } = await client.get('/project', {
      params: { version }
    });
    return data;
  },
  
  initStyle: async (version: number, prompt: StylePrompt) => {
    const { data } = await client.post('/style/init', prompt, {
      params: { version }
    });
    return data;
  },
  
  // ... 其他方法类似更新 ...
};
```

#### Zustand Store 更新

```typescript
// frontend/src/store/appStore.ts

interface AppState {
  currentVersion: number | null;
  
  setVersion: (version: number) => void;
  loadProject: (version: number) => Promise<void>;
  
  // 其他 action 自动使用 currentVersion
  createSlide: () => Promise<void>;
  // ...
}

export const useAppStore = create<AppState>((set, get) => ({
  currentVersion: null,
  
  setVersion: (version) => set({ currentVersion: version }),
  
  loadProject: async (version) => {
    try {
      const project = await api.getProject(version);
      set({ 
        currentVersion: version,
        slides: project.slides,
        styleReference: project.style_reference
      });
    } catch (err) {
      // ...
    }
  },
  
  createSlide: async () => {
    const { currentVersion } = get();
    if (!currentVersion) return;
    
    const newSlide = await api.createSlide(currentVersion, {...});
    // ...
  }
}));
```

#### 版本选择器组件

```tsx
// frontend/src/components/VersionSelector.tsx

export function VersionSelector({ 
  onSelectVersion 
}: { 
  onSelectVersion: (version: number) => void 
}) {
  const [versions, setVersions] = useState<VersionInfo[]>([]);
  const [isCreating, setIsCreating] = useState(false);
  
  useEffect(() => {
    api.listVersions().then(setVersions);
  }, []);
  
  const handleCreateNew = async () => {
    setIsCreating(true);
    // 显示 StyleInitializer 模态框
  };
  
  return (
    <div className="version-selector">
      <h1>选择项目</h1>
      
      <div className="versions-grid">
        {versions.map(v => (
          <div 
            key={v.version} 
            onClick={() => onSelectVersion(v.version)}
            className="version-card"
          >
            <h3>项目 v{v.version}</h3>
            <p>{v.slide_count} 张幻灯片</p>
            <p>{v.created_at}</p>
            {v.style_reference && (
              <img src={v.style_reference} alt="Style" />
            )}
          </div>
        ))}
        
        <button onClick={handleCreateNew}>
          + 创建新项目
        </button>
      </div>
      
      {isCreating && (
        <StyleInitializer 
          onCreateVersion={...}
          onCancel={...}
        />
      )}
    </div>
  );
}
```

#### App.tsx 重构

```tsx
// frontend/src/App.tsx

export function App() {
  const { currentVersion, setVersion, loadProject } = useAppStore();
  
  const handleSelectVersion = (version: number) => {
    setVersion(version);
    loadProject(version);
  };
  
  if (!currentVersion) {
    return <VersionSelector onSelectVersion={handleSelectVersion} />;
  }
  
  return (
    <div className="app">
      {/* 主编辑界面 */}
      <Sidebar />
      <SlideViewer />
    </div>
  );
}
```

### 6.5 候选图片交互优化

#### 单击预览 vs 双击确认

```tsx
// frontend/src/components/ImageCandidatesPanel.tsx

const handleClickCandidate = (candidate: ImageCandidate) => {
  // 单击：预览（紫色边框）
  setSelectedCandidateId(candidate.id);
  onImagePreview(candidate.imagePath);
  
  // 临时更新左侧缩略图（不保存到 outline.yml）
  const tempSlide = {
    ...currentSlide,
    image_path: candidate.imagePath
  };
  onSlideUpdated(tempSlide);
};

const handleDoubleClickCandidate = async (candidate: ImageCandidate) => {
  // 双击：确认并保存（绿色边框 + ✓）
  const updatedSlide = await api.updateSlide(
    currentVersion, 
    slideId, 
    { image_path: candidate.imagePath }
  );
  
  selectImageCandidate(slideId, candidate.id); // 标记为已选择
  onSlideUpdated(updatedSlide); // 更新 store
  onImagePreview(candidate.imagePath);
};
```

#### 修复自动确认问题

```typescript
// frontend/src/store/appStore.ts

addImageCandidate: (slideId, imagePath) => {
  const candidateId = `${slideId}-${Date.now()}`;
  const candidates = get().imageCandidates[slideId] || [];
  
  set({
    imageCandidates: {
      ...get().imageCandidates,
      [slideId]: [
        ...candidates.map(c => ({ ...c, isSelected: false })),
        { 
          id: candidateId, 
          slideId, 
          imagePath, 
          isSelected: false  // 不自动确认
        }
      ]
    }
  });
  
  return candidateId;
}
```

### 6.6 修复和改进

#### CORS 配置更新

```python
# backend/app/core/config.py

CORS_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",  # Vite 备用端口
    "http://127.0.0.1:5174",
]
```

#### 缩略图实时更新

添加回调链 `ImageCandidatesPanel` → `SlideViewer` → `App.tsx` → `appStore.updateSlideInState`：

```tsx
// 组件层级传递 onSlideUpdated 回调
<SlideViewer 
  onSlideUpdated={(slide) => updateSlideInState(slide)} 
/>
```

### 6.7 测试策略

#### 后端测试

```bash
# 测试版本管理 API
curl http://localhost:8000/api/versions
curl -X POST http://localhost:8000/api/versions/create \
  -H "Content-Type: application/json" \
  -d '{"description": "测试风格"}'

# 测试版本隔离
curl "http://localhost:8000/api/project?version=1"
curl "http://localhost:8000/api/project?version=2"
```

#### 前端测试

1. **版本选择器**: 显示所有版本卡片
2. **创建新版本**: 输入提示词生成风格
3. **版本切换**: 切换版本后数据正确加载
4. **候选图片交互**:
   - 生成：不自动标记为已选择 ✓
   - 单击：预览 + 左侧缩略图更新 ✓
   - 双击：确认 + 绿色边框 ✓

### 6.8 技术债务

#### 必需（v2.1）
- 数据迁移脚本（将根目录 outline.yml 迁移到 assets/v1/）
- 版本删除功能（带确认对话框）

#### 可选（v2.2+）
- 版本导出/导入
- 项目重命名
- 版本对比
- 批量操作

---

## 7. 总结

v2.0.0 通过引入**多版本项目管理**，实现了：
- ✅ 完全隔离的项目版本
- ✅ 直观的版本选择器 UI
- ✅ 优化的候选图片交互体验
- ✅ 实时的缩略图更新
- ✅ 完善的错误处理

**项目状态**: 生产就绪

---

**最后更新**: 2026-02-01
