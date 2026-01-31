# Cursor Rules 创建与使用完整指南

**创建日期**: 2026-02-01  
**项目**: AI Slide Generator (Week7)

---

## 目录

1. [创建 Cursor Rules](#1-创建-cursor-rules)
2. [规则文件内容](#2-规则文件内容)
3. [规则触发机制](#3-规则触发机制)
4. [规则作用域和查找规则](#4-规则作用域和查找规则)
5. [实用技巧和最佳实践](#5-实用技巧和最佳实践)

---

## 1. 创建 Cursor Rules

### 1.1 用户需求

**原始请求**:
> 根据 specs 的相关内容在 backend/和frontend/目录下分别生成 cursor 的前后端不同需求的rule，这样方便前后端的subagent 调用 :
> * 内容考虑所使用语言框架的best practices
> * 架构设计遵循的原则:SOLID/YAGNI/KISS/DRY
> * 代码的组织结构
> * 并发处理
> * 错误处理和日志处理
> * 其中所有所有版本使用最新依赖
> * 后端开发需要使用 uv 管理且有一个独立的 venv 文件
> * 前端需要注意使用统一的风格
> 注意是 cursor 的，不是 claude 的 配置

### 1.2 创建的文件

基于项目规范 (`specs/001-ai-slide-generator/spec.md` 和 `plan.md`)，创建了以下文件：

| 文件 | 位置 | 行数 | 用途 |
|------|------|------|------|
| **后端规则** | `Week7/backend/.cursorrules` | 283 行 | Python/FastAPI 开发规范 |
| **前端规则** | `Week7/frontend/.cursorrules` | 490 行 | TypeScript/React 开发规范 |
| **说明文档** | `Week7/CURSORRULES.md` | 226 行 | 规则使用指南 |
| **快速总结** | `Week7/.cursorrules-summary.md` | 摘要 | 创建说明和验证 |

---

## 2. 规则文件内容

### 2.1 后端规则 (`backend/.cursorrules`)

#### 核心内容

**项目上下文**:
- **技术栈**: Python 3.12+, FastAPI, Pydantic 2.10+, Google Gemini AI SDK
- **环境管理**: uv + venv (`.venv` in `backend/`)
- **数据层**: YAML-only (`outline.yml`)

**架构原则**:
- **SOLID**: 单一职责、开闭原则、里氏替换、接口隔离、依赖倒置
- **YAGNI**: 只实现当前需求，不做推测性开发
- **KISS**: 简单优于复杂
- **DRY**: 避免代码重复

**代码组织**:
```
backend/
├── app/
│   ├── api/           # HTTP 层
│   ├── core/          # 业务逻辑
│   ├── data/          # 数据访问
│   ├── models/        # Pydantic 模型
│   └── main.py
├── .venv/             # uv 管理的虚拟环境
└── requirements.txt
```

**Python 最佳实践**:
- Python 3.12+ 特性 (type hints, match/case, f-strings)
- PEP 8 规范 (4 spaces, snake_case, max 100 chars)
- 类型提示: `def foo(x: int) -> str:`
- 优先组合而非继承

**错误处理示例**:
```python
# Good: 具体异常处理
try:
    data = yaml_store.read()
except FileNotFoundError:
    raise HTTPException(status_code=404, detail="Project file not found")
except yaml.YAMLError as e:
    logger.error(f"YAML parse error: {e}")
    raise HTTPException(status_code=500, detail="Corrupted project file")

# Bad: 泛型异常
try:
    data = yaml_store.read()
except Exception:  # 太宽泛
    raise HTTPException(status_code=500)
```

**日志处理**:
```python
import structlog
logger = structlog.get_logger()

logger.info("slide_created", slide_id=slide.id, text_length=len(slide.text))
logger.error("gemini_api_error", error=str(e), prompt=prompt[:50])
```

**并发处理**:
- async/await 用于 I/O 操作
- 文件锁保证原子写入
- FastAPI 通过 asyncio 处理并发

**环境管理**:
```bash
cd backend
uv venv .venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

#### 代码审查清单

提交前验证：
- [ ] 所有函数都有类型提示
- [ ] 公共函数有 docstring
- [ ] 外部调用都有错误处理
- [ ] 关键事件和错误都有日志
- [ ] 文件操作是原子的
- [ ] 用户输入都经过验证
- [ ] 没有硬编码凭据
- [ ] 测试通过: `pytest tests/`
- [ ] Linting 通过: `ruff check .`
- [ ] 格式化应用: `ruff format .`

### 2.2 前端规则 (`frontend/.cursorrules`)

#### 核心内容

**项目上下文**:
- **技术栈**: TypeScript 5.6+, React 19, Vite 6, Tailwind CSS 4, Zustand, @dnd-kit
- **API**: FastAPI backend at `http://localhost:8000/api`
- **状态**: 单一数据源来自后端 (`outline.yml`)

**架构原则**:
- **SOLID** (React 上下文): 组件单一职责、通过 composition 扩展
- **YAGNI/KISS/DRY**: 简单实用，避免过度工程

**代码组织**:
```
frontend/
├── src/
│   ├── api/              # Backend 通信
│   ├── components/       # UI 组件
│   ├── hooks/            # 自定义 Hooks
│   ├── types/            # TypeScript 接口
│   ├── utils/            # 工具函数
│   ├── App.tsx
│   └── main.tsx
```

**TypeScript 最佳实践**:
```typescript
// Good: 明确类型
interface SlideEditorProps {
  slide: Slide;
  onUpdate: (text: string) => Promise<void>;
  onRegenerate: () => Promise<void>;
}

function SlideEditor({ slide, onUpdate, onRegenerate }: SlideEditorProps) {
  // ...
}

// Bad: any 类型
function SlideEditor({ slide, onUpdate, onRegenerate }: any) {
  // ...
}
```

**React 最佳实践**:
```typescript
// Good: 函数组件 + Hooks
function SlideEditor({ slide }: SlideEditorProps) {
  const [text, setText] = useState(slide.text);
  
  // Memoize callbacks
  const handleUpdate = useCallback((text: string) => {
    return api.updateSlide(slide.id, { text });
  }, [slide.id]);
  
  // Complete dependency array
  useEffect(() => {
    setText(slide.text);
  }, [slide.text]);
  
  return <textarea value={text} onChange={e => setText(e.target.value)} />;
}
```

**状态管理 (Zustand)**:
```typescript
interface ProjectStore {
  project: ProjectState | null;
  loading: boolean;
  error: string | null;
  
  fetchProject: () => Promise<void>;
  updateSlide: (id: string, text: string) => Promise<void>;
}

const useProjectStore = create<ProjectStore>((set) => ({
  project: null,
  loading: false,
  error: null,
  
  fetchProject: async () => {
    set({ loading: true, error: null });
    try {
      const project = await api.getProject();
      set({ project, loading: false });
    } catch (error) {
      set({ error: error.message, loading: false });
    }
  },
}));
```

**错误处理**:
```typescript
// Good: Toast 通知
async function handleRegenerate() {
  try {
    const slide = await api.regenerateImage(slideId);
    toast.success("Image regenerated successfully");
    updateSlide(slide);
  } catch (error) {
    if (error.response?.status === 429) {
      toast.error("API quota exceeded. Please try again later.");
    } else {
      toast.error("Failed to regenerate image. Please try again.");
    }
    console.error("Regenerate error:", error);
  }
}
```

**性能优化**:
```typescript
// Memoize 昂贵计算
const slidesByOrder = useMemo(() => {
  return slides.sort((a, b) => a.order - b.order);
}, [slides]);

// 防抖用户输入
const debouncedSave = useDebouncedCallback(
  (newText: string) => {
    api.updateSlide(slide.id, { text: newText });
  },
  1000
);
```

**无障碍性**:
```typescript
// Good: 语义化 HTML + 键盘导航
<nav aria-label="Slide navigation">
  <ul>
    {slides.map(slide => (
      <li key={slide.id}>
        <button onClick={() => selectSlide(slide.id)}>
          {slide.text}
        </button>
      </li>
    ))}
  </ul>
</nav>

// Keyboard events
useEffect(() => {
  const handleKeyDown = (e: KeyboardEvent) => {
    if (e.key === 'Escape') onClose();
    else if (e.key === 'ArrowLeft') previousSlide();
    else if (e.key === 'ArrowRight') nextSlide();
  };
  
  window.addEventListener('keydown', handleKeyDown);
  return () => window.removeEventListener('keydown', handleKeyDown);
}, [onClose, previousSlide, nextSlide]);
```

#### 代码审查清单

提交前验证：
- [ ] 所有类型显式定义 (无 `any`)
- [ ] 组件是函数式 + Hooks (无类)
- [ ] Memoization 用于昂贵操作
- [ ] Effects 有完整依赖数组
- [ ] 所有 API 调用有错误处理
- [ ] 异步操作有 loading 状态
- [ ] 无障碍: 语义化 HTML、键盘支持、ARIA 标签
- [ ] 响应式设计 (移动端友好)
- [ ] 测试通过: `npm test`
- [ ] Linting 通过: `npm run lint`
- [ ] 构建成功: `npm run build`

---

## 3. 规则触发机制

### 3.1 问题与回答

#### Q1: 是否只要在 cursor 中进行开发就会触发相关 rules，而且不一定使用 `/task` 命令也能触发吗？

**回答**: ✅ **是的，完全正确！**

`.cursorrules` 文件会在以下**所有情况**下自动生效：

| 触发方式 | 是否需要 `/task` | 是否自动应用规则 | 说明 |
|---------|-----------------|----------------|------|
| **普通对话** | ❌ 否 | ✅ 是 | 在 Cursor 中与 AI 对话 |
| **Cmd+K 编辑** | ❌ 否 | ✅ 是 | 使用快捷键内联编辑 |
| **Chat 窗口** | ❌ 否 | ✅ 是 | 右侧聊天面板提问 |
| **代码补全** | ❌ 否 | ✅ 部分 | Tab 自动补全 |
| **`/task` 命令** | ✅ 是 | ✅ 是 | 长任务执行 |

### 3.2 实际使用示例

#### 示例 1: 普通对话
```
你: "帮我写一个处理 YAML 文件的函数"
AI: (自动读取 backend/.cursorrules，按照规则生成代码)
    - 添加类型提示
    - 使用文件锁
    - 添加错误处理
    - 添加日志
```

#### 示例 2: Inline 编辑 (Cmd+K)
```
选中代码 → Cmd+K → "优化这个函数"
→ AI 会根据 .cursorrules 的规范重构代码
  - 添加 memoization
  - 修复依赖数组
  - 添加类型定义
```

#### 示例 3: Chat 窗口
```
在 backend/ 目录下的文件打开 Chat
你: "创建一个新的 API 端点"
AI: (应用 backend/.cursorrules)
    - 使用 async def
    - 添加依赖注入
    - 添加 Pydantic 验证
    - 添加错误处理
```

#### 示例 4: `/task` 命令
```bash
/task "实现 Phase 2 后端功能" --cwd Week7/backend
→ Subagent 自动应用 backend/.cursorrules
```

### 3.3 验证方法

**简单测试**:
```
1. 在 backend/ 目录下打开聊天窗口
2. 输入: "写一个函数读取 YAML 文件"
3. 观察 AI 输出是否包含:
   - 类型提示 (def read_yaml(path: str) -> dict:)
   - docstring
   - 错误处理
   - structlog 日志
```

**对比测试**:
```
在 backend/ 下: "创建一个类"
→ 应该生成 Python 风格的类 (snake_case)

在 frontend/ 下: "创建一个组件"
→ 应该生成 React 函数组件 (PascalCase + TypeScript)
```

---

## 4. 规则作用域和查找规则

### 4.1 问题与回答

#### Q1: 如果是全局生效，那么我没有在这两个目录下，而是在其他目录，例如 Week2 下进行开发有影响吗？

**回答**: ❌ **不会有影响！**

`.cursorrules` 文件**不是全局的**，它是**基于目录的局部生效**。

#### Q2: rules 的判断规则是什么呢？

**回答**: Cursor 使用**向上递归查找**的方式：

### 4.2 查找机制详解

#### 核心规则

| 规则 | 说明 |
|------|------|
| **向上查找** | 从当前文件所在目录开始，逐级向上 |
| **优先最近** | 离文件最近的规则优先 |
| **找到即停** | 找到第一个 `.cursorrules` 就停止，不继续向上 |
| **完全覆盖** | 不会合并多个规则文件 |

#### 查找流程示例

```
/home/ray/Documents/VibeCoding/
├── .cursorrules                           ← Level 4: 仓库根
├── Week2/
│   └── src/
│       └── index.ts                       ← 编辑时: 向上找到 Level 4 或无规则
├── Week7/
│   ├── .cursorrules                       ← Level 3: Week7 项目级
│   ├── backend/
│   │   ├── .cursorrules                   ← Level 2: backend 目录
│   │   └── app/
│   │       ├── .cursorrules               ← Level 1: app 目录 (最近)
│   │       └── api/
│   │           └── endpoints.py           ← 编辑时: 查找 1→2→3→4
│   └── frontend/
│       ├── .cursorrules                   ← Level 2: frontend 目录
│       └── src/
│           └── App.tsx                    ← 编辑时: 查找 2→3→4
```

#### 实际场景分析

**场景 1: 在 Week2 开发**
```
当前目录: Week2/src/index.ts

规则查找顺序:
1. Week2/src/.cursorrules         (不存在)
2. Week2/.cursorrules             (不存在)
3. VibeCoding/.cursorrules        (不存在)

结果: ❌ 无规则应用 (使用 Cursor 全局默认规则)
✅ Week7 的规则完全不会影响 Week2
```

**场景 2: 在 Week7/backend 开发**
```
当前目录: Week7/backend/app/api/endpoints.py

规则查找顺序:
1. Week7/backend/app/api/.cursorrules    (不存在)
2. Week7/backend/app/.cursorrules        (不存在)
3. Week7/backend/.cursorrules            ✅ 找到! 停止查找

结果: ✅ 应用 Week7/backend/.cursorrules
      ❌ Week7/frontend/.cursorrules 不会被应用
```

**场景 3: 在 Week7 根目录**
```
当前目录: Week7/README.md

规则查找顺序:
1. Week7/.cursorrules                (不存在)
2. VibeCoding/.cursorrules           (不存在)

结果: ❌ 无规则应用
注意: 即使 Week7/backend/ 和 Week7/frontend/ 都有规则文件，
      但编辑 Week7/ 根目录的文件时它们都不会生效
```

### 4.3 作用域总结表

| 当前工作目录 | 应用的规则文件 | Week7 的规则是否生效 |
|-------------|--------------|---------------------|
| `Week2/src/` | `Week2/.cursorrules` (如果存在) | ❌ **否** |
| `Week7/backend/app/` | `Week7/backend/.cursorrules` | ✅ 是 (backend 规则) |
| `Week7/frontend/src/` | `Week7/frontend/.cursorrules` | ✅ 是 (frontend 规则) |
| `Week7/` (根目录) | 无 `.cursorrules` | ❌ 否 |
| `VibeCoding/` (仓库根) | `VibeCoding/.cursorrules` (如果存在) | ❌ 否 |

---

## 5. 实用技巧和最佳实践

### 5.1 推荐的项目结构

#### 方案 1: 每个 Week 独立 ✅ **当前方案，推荐**

```
VibeCoding/
├── Week1/
│   └── (无 .cursorrules，使用默认规则)
├── Week2/
│   └── (无 .cursorrules，使用默认规则)
└── Week7/
    ├── backend/.cursorrules      ← Python/FastAPI 专用
    └── frontend/.cursorrules     ← React/TS 专用

优点: 
✅ 各项目互不干扰
✅ Week7 的规则不会影响其他 Week
✅ 每个项目可以有不同的技术栈规则
```

#### 方案 2: 全局规则 + 项目专用

```
VibeCoding/
├── .cursorrules                  ← 通用规则 (简体中文输出等)
├── Week1/
├── Week2/
└── Week7/
    ├── backend/.cursorrules      ← 覆盖全局，应用 Python 规则
    └── frontend/.cursorrules     ← 覆盖全局，应用 React 规则

注意: 
⚠️ 子目录规则会完全覆盖全局规则 (不继承)
⚠️ 需要在每个子规则中重复全局规则的内容
```

#### 方案 3: 每个 Week 单独配置

```
VibeCoding/
├── Week1/.cursorrules            ← Week1 特定规则
├── Week2/.cursorrules            ← Week2 特定规则
└── Week7/
    ├── .cursorrules              ← Week7 通用规则
    ├── backend/.cursorrules      ← 覆盖 Week7，应用后端规则
    └── frontend/.cursorrules     ← 覆盖 Week7，应用前端规则
```

### 5.2 不需要手动提醒

AI 会自动读取规则，无需在提示词中提及：

```
❌ 不好: "根据 .cursorrules 文件帮我写代码"
✅ 好:   "帮我写一个 API 端点" (AI 自动应用规则)
```

### 5.3 规则即时生效

修改 `.cursorrules` 后无需重启 Cursor：

```
编辑 .cursorrules → 保存 → ✅ 立即生效
```

### 5.4 如果需要更细粒度的控制

```
Week7/
├── backend/
│   ├── .cursorrules              ← 通用 Python 规则
│   └── app/
│       ├── api/
│       │   └── .cursorrules      ← API 专用规则（覆盖通用）
│       └── core/
│           └── .cursorrules      ← 核心逻辑专用（覆盖通用）
```

### 5.5 Cursor 规则优先级

Cursor 会按以下优先级应用规则：

1. **最近的 `.cursorrules`** - 当前目录或最近的父目录 (最高优先级)
2. **项目根目录的 `.cursorrules`** - 如果存在
3. **全局规则** - Cursor 设置中的全局规则 (最低优先级)

### 5.6 代码示例对比

#### 后端代码

**❌ 不符合规则**:
```python
def update_slide(slide_id, text):
    data = read_file()
    for slide in data["slides"]:
        if slide["id"] == slide_id:
            slide["text"] = text
    write_file(data)
```

**✅ 符合规则**:
```python
def update_slide(slide_id: str, text: str) -> Optional[Slide]:
    """更新幻灯片文本 (原子操作)"""
    with file_lock(self.file_path):
        data = self._read_data()
        
        for slide in data["slides"]:
            if slide["id"] == slide_id:
                slide["text"] = text
                slide["content_hash"] = hashlib.md5(text.encode()).hexdigest()
                self._write_data(data)
                logger.info("slide_updated", slide_id=slide_id)
                return Slide(**slide)
        
        logger.warning("slide_not_found", slide_id=slide_id)
        return None
```

#### 前端代码

**❌ 不符合规则**:
```typescript
function SlideEditor(props: any) {
  return <div onClick={() => api.update(props.slide.id, text)}>
    <textarea />
  </div>
}
```

**✅ 符合规则**:
```typescript
interface SlideEditorProps {
  slide: Slide;
  onUpdate: (text: string) => Promise<void>;
}

function SlideEditor({ slide, onUpdate }: SlideEditorProps) {
  const [text, setText] = useState(slide.text);
  
  const handleSave = useDebouncedCallback(
    async (newText: string) => {
      try {
        await onUpdate(newText);
        toast.success("Slide updated");
      } catch (error) {
        toast.error("Failed to update slide");
        console.error("Update error:", error);
      }
    },
    1000
  );
  
  return (
    <div className="p-4 rounded-lg border">
      <textarea
        value={text}
        onChange={(e) => {
          setText(e.target.value);
          handleSave(e.target.value);
        }}
        className="w-full p-2 border rounded"
        aria-label="Slide text"
      />
    </div>
  );
}
```

### 5.7 常见问题排查

#### 问题 1: 规则似乎没有生效

**解决方法**:
1. 检查文件路径是否正确 (必须是 `.cursorrules` 不是 `.cursor-rules`)
2. 确认当前编辑的文件在规则文件的目录下或子目录中
3. 尝试重新打开文件或重启 Cursor
4. 检查规则文件语法是否正确 (Markdown 格式)

#### 问题 2: 多个规则冲突

**解决方法**:
- 记住：只有**最近的一个**规则生效
- 如果需要合并规则，需要手动在子目录规则中包含父目录规则的内容

#### 问题 3: 想要某些文件不应用规则

**解决方法**:
- 将这些文件移到没有 `.cursorrules` 的目录
- 或在该目录创建一个空的或最小化的 `.cursorrules` 文件

---

## 附录

### A. 相关文件位置

- **后端规则**: `Week7/backend/.cursorrules` (283 行)
- **前端规则**: `Week7/frontend/.cursorrules` (490 行)
- **使用说明**: `Week7/CURSORRULES.md` (226 行)
- **快速总结**: `Week7/.cursorrules-summary.md`
- **项目 README**: `Week7/README.md`
- **技术计划**: `specs/001-ai-slide-generator/plan.md`
- **功能规范**: `specs/001-ai-slide-generator/spec.md`
- **任务列表**: `specs/001-ai-slide-generator/tasks.md`

### B. 快速参考

#### 后端核心要求
```python
# 1. 类型提示
def update_slide(slide_id: str, text: str) -> Optional[Slide]:

# 2. 原子操作
with file_lock(self.file_path):
    data = self._read_data()
    self._write_data(data)

# 3. 结构化日志
logger.info("event_name", key=value)

# 4. 依赖注入
@router.get("/endpoint")
async def handler(store: Store = Depends(get_store)):
    pass
```

#### 前端核心要求
```typescript
// 1. 明确类型
interface Props {
  data: Data;
  onAction: () => void;
}

// 2. Memoization
const value = useMemo(() => compute(data), [data]);
const handler = useCallback(() => action(), []);

// 3. 完整依赖
useEffect(() => {
  doSomething();
}, [dependency]);

// 4. 错误处理
try {
  await api.call();
  toast.success("Success");
} catch (error) {
  toast.error("Failed");
}
```

### C. 验证清单

#### 验证规则是否生效

- [ ] 在对应目录下创建新文件
- [ ] 要求 AI 生成代码
- [ ] 检查是否包含规则要求的模式
- [ ] 后端: 类型提示、依赖注入、日志
- [ ] 前端: TypeScript 接口、Hooks、Memoization

#### 提交前检查

**后端**:
- [ ] 类型提示完整
- [ ] 错误处理完善
- [ ] 日志记录关键事件
- [ ] 文件操作是原子的
- [ ] 测试通过
- [ ] Linting 通过

**前端**:
- [ ] 无 `any` 类型
- [ ] 使用函数组件 + Hooks
- [ ] Memoization 合理使用
- [ ] 依赖数组完整
- [ ] 错误处理友好
- [ ] 测试通过
- [ ] 构建成功

---

**文档版本**: v1.0  
**最后更新**: 2026-02-01  
**维护者**: AI Slide Generator Team
