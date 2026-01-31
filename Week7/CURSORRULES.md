# Cursor AI 开发规则说明

## 概述

为前后端分别创建了 Cursor AI 规则文件 (`.cursorrules`)，用于指导 AI 助手在开发时遵循项目的最佳实践和架构原则。

## 文件位置

- **后端规则**: `Week7/backend/.cursorrules` (283 行)
- **前端规则**: `Week7/frontend/.cursorrules` (490 行)

## 规则内容

### 后端规则 (`backend/.cursorrules`)

**覆盖内容**:
1. **架构原则**: SOLID/YAGNI/KISS/DRY
2. **代码组织**: 清晰的模块职责划分
3. **Python 最佳实践**: 
   - Python 3.12+ 特性
   - 类型提示
   - PEP 8 代码风格
4. **错误处理**: 具体异常处理和日志记录 (structlog)
5. **并发处理**: async/await 模式，线程安全
6. **环境管理**: uv + venv 工作流
7. **FastAPI 特定**: 依赖注入、错误响应、请求验证
8. **测试指南**: 单元测试和集成测试
9. **代码审查清单**: 提交前的检查项

**核心原则**:
- 每个模块单一职责
- 使用依赖注入
- 所有函数都有类型提示
- 原子文件操作
- 结构化日志
- 异步 I/O 操作

### 前端规则 (`frontend/.cursorrules`)

**覆盖内容**:
1. **架构原则**: SOLID (React 上下文) + YAGNI/KISS/DRY
2. **代码组织**: 组件、hooks、工具函数分离
3. **TypeScript 最佳实践**:
   - 严格类型检查
   - 避免类型断言
   - 泛型复用
4. **React 最佳实践**:
   - 函数组件 + Hooks
   - Memoization (useMemo/useCallback)
   - 正确的 Effect 依赖
5. **状态管理**: Zustand 模式
6. **样式规范**: Tailwind CSS 一致性
7. **错误处理**: Toast 通知和错误边界
8. **性能优化**: 代码分割、防抖
9. **无障碍性**: 语义化 HTML、键盘导航
10. **测试指南**: 组件测试

**核心原则**:
- 每个组件单一职责
- 所有类型显式定义
- 函数组件 (不用类)
- 合理使用 memoization
- 完整的依赖数组
- 用户友好的错误提示

## 如何使用

### Subagent 开发

当使用 Cursor 的 Task 工具执行任务时，AI 会自动读取并遵循这些规则：

```bash
# 后端 subagent 会读取 Week7/backend/.cursorrules
# 前端 subagent 会读取 Week7/frontend/.cursorrules
```

### 手动开发

在 Cursor IDE 中，当你在对应目录下工作时：
- 在 `backend/` 目录下开发时，AI 会应用后端规则
- 在 `frontend/` 目录下开发时，AI 会应用前端规则

### 规则生效验证

可以通过以下方式验证规则是否生效：
1. 在对应目录下创建新文件
2. 要求 AI 生成代码
3. 检查生成的代码是否遵循规则中的模式

## 规则特色

### 1. **语言框架最佳实践**
- **后端**: FastAPI 依赖注入、Pydantic 验证、async/await
- **前端**: React Hooks、TypeScript 严格模式、Zustand 状态管理

### 2. **架构设计原则**
- **SOLID**: 单一职责、依赖倒置、接口隔离
- **YAGNI**: 只实现当前需求
- **KISS**: 简单优于复杂
- **DRY**: 避免代码重复

### 3. **代码组织**
- **后端**: API/Core/Data/Models 清晰分层
- **前端**: Components/Hooks/Utils/Types 结构化

### 4. **并发处理**
- **后端**: async/await + 文件锁保证原子操作
- **前端**: 防抖、节流、异步状态管理

### 5. **错误处理**
- **后端**: 具体异常 + structlog 结构化日志
- **前端**: Toast 通知 + 错误边界

### 6. **依赖版本**
- 所有依赖使用最新稳定版本
- 后端使用 `uv` 管理虚拟环境
- 前端使用 npm/pnpm 管理依赖

### 7. **代码风格统一**
- **后端**: PEP 8, snake_case, 类型提示
- **前端**: ESLint, camelCase, TypeScript strict mode

## 示例对比

### 后端代码示例

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

### 前端代码示例

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

## 更新规则

如果需要修改规则：
1. 编辑对应的 `.cursorrules` 文件
2. 规则会立即生效（无需重启 Cursor）
3. 建议与团队讨论后再修改核心原则

## 注意事项

1. **规则不是限制**: 规则是指导原则，特殊情况下可以偏离，但需要注释说明原因
2. **持续演进**: 随着项目发展，规则应该不断完善
3. **团队共识**: 确保团队成员理解并认同这些规则
4. **工具辅助**: 配合 linter (ruff, eslint) 和 formatter 使用

## 相关文件

- 项目结构: `Week7/README.md`
- 技术计划: `specs/001-ai-slide-generator/plan.md`
- 功能规范: `specs/001-ai-slide-generator/spec.md`
- 任务列表: `specs/001-ai-slide-generator/tasks.md`
