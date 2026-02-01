# Week7 优化记录

本文档记录所有优化、Bug 修复和功能改进。

---

## 📋 目录

1. [Prompt 优化](#prompt-优化)
2. [UI/UX 优化](#uiux-优化)
3. [功能增强](#功能增强)
4. [Bug 修复](#bug-修复)

---

## Prompt 优化

### v7.2 (2026-02-01) - 强化风格应用 🎨

**问题**：
- 生成的 slide 没有应用选中的风格
- ASCII 图表被简单转换为文本，没有风格一致性
- Prompt 中对风格引用太弱："Match colors from reference style image"

**原因**：
- 虽然代码中发送了风格参考图片，但 prompt 没有明确要求 AI 模仿风格
- 优先级不明确：文本准确性 > 风格匹配

**改进**：
1. **新增 `🎨 STYLE REFERENCE` 部分**（最优先）
   - 明确说明：参考图片是风格指南
   - 5 个具体风格匹配要求：
     - 使用相同颜色调色板
     - 使用相同字体风格
     - 使用相同背景风格
     - 使用相同视觉美学
     - 属于相同设计系统
2. **调整优先级**：
   - 风格匹配：HIGHEST PRIORITY
   - 文本准确性：SECOND PRIORITY
3. **禁止事项**：
   - ❌ DO NOT ignore the reference image style

**效果**：
- 🎯 **待测试**: 需要重新生成 slide 验证风格应用效果

---

### v7.1 (2026-02-01) - 简化 Prompt，避免过度创造 🎯

**问题**：
- v7.0 中文准确性 ✅ 完美（Nano Banana Pro 成功）
- 但内容理解错误：简单文本被扩展为复杂架构图

**示例**：
```
输入: 
标题: 你好
这个一个测试文本内容

AI 输出: 
- 技术栈概览 (Tech Stack Overview)
- 演示说明 (Demo Description)
- 复杂的流程图和列表
```

**原因分析**：
- v7.0 prompt 太"技术化"（提到 "technical slide", "grid layout", "cards"）
- AI 误以为所有输入都是技术文档
- 过度发挥，添加了用户没要求的内容

**解决方案（v7.1）**：

```python
prompt = """
Create a professional presentation slide with the following content:

=== EXACT TEXT (RENDER PRECISELY) ===
{text}
=== END TEXT ===

⚠️ CRITICAL RULES:
1. TEXT ACCURACY (TOP PRIORITY):
   - Display EVERY character EXACTLY as provided
   - DO NOT add content that is not in the input
   - DO NOT create additional sections or diagrams

2. STRUCTURE PARSING:
   If text starts with '标题: X':
     → Display 'X' as main title
   
   For remaining text:
     → If simple sentence: Display as body text
     → If ASCII art: Convert to visual cards
     → If bullets: Format as list

3. WHAT NOT TO DO:
   ❌ DO NOT invent additional content
   ❌ DO NOT create complex diagrams if input is simple
   ❌ DO NOT add decorative cards with unrelated text

✅ GOAL: Display ONLY the provided text, beautifully formatted.
"""
```

**关键改进**：
1. ✅ 移除"technical"等暗示性词汇
2. ✅ 明确禁止"添加额外内容"
3. ✅ 简化结构解析规则
4. ✅ 强调"仅显示提供的文本"
5. ✅ 保持中文准确性（Nano Banana Pro）

**预期效果**：
```
输入: 
标题: 你好
这个一个测试文本内容

预期输出:
┌─────────────────────┐
│       你好          │  ← 标题（大字）
│                     │
│  这个一个测试文本内容 │  ← 正文（居中）
│                     │
└─────────────────────┘
```

**测试计划**：
1. 简单文本："标题: 你好\n这是测试"
2. 复杂结构：带 ASCII 框图的技术文档
3. 验证两种情况都能正确处理

---

### v7.0 (2026-02-01) - 升级到 Nano Banana Pro (Gemini 3) 🚀

**状态**: ✅ 中文准确性完美，但需要简化 prompt（→ v7.1）

**问题回顾**：
- v6.0 两步流程虽然解决了中文准确性，但失去了 AI 原生的文字风格
- Gemini 2.5 Flash Image 模型对中文渲染存在缺陷

**解决方案：升级模型**

切换到 **Nano Banana Pro (Gemini 3 Pro Image Preview)**：

#### 模型特性（来自 OpenRouter）
- ✅ **Professional-grade text rendering** ← **核心优势！**
- ✅ High-fidelity visual synthesis
- ✅ Improved multimodal reasoning
- ✅ 2K/4K 输出支持
- ✅ Real-world grounding
- 📅 发布日期：2025年11月20日（Google 最新图像生成模型）

#### 配置变更
```bash
# .env 文件
OPENROUTER_MODEL=google/gemini-3-pro-image-preview  # 从 gemini-2.5-flash-image 升级
```

#### Prompt 优化（v7.0）
专门针对 Gemini 3 的专业文本渲染能力：

```python
prompt = """
🎨 PROFESSIONAL TECHNICAL SLIDE DESIGN

⚠️ CRITICAL - TEXT ACCURACY (TOP PRIORITY):
- Render EVERY Chinese character EXACTLY as provided
- Use professional Unicode fonts (Noto Sans CJK, etc.)
- You have professional-grade text rendering - USE IT!

Example errors to AVOID:
  ❌ '后端技术栈' → '点师技茉'
  ✅ CORRECT: Copy from Unicode codepoint

🎨 VISUAL DESIGN:
- 16:9, 2K resolution
- Card-based layout with shadows
- Professional typography (60-70pt title, 32-36pt headers)
"""
```

#### 关键改进
1. ✅ **强调模型能力**：明确告知 AI 它具备"professional-grade text rendering"
2. ✅ **提供反例**：展示之前的错误（负面学习）
3. ✅ **技术细节**：Unicode 字体、codepoint 渲染
4. ✅ **2K 分辨率**：更高质量输出

#### 预期效果
- 🎯 中文字符 100% 准确（利用模型的专业文本渲染）
- 🎨 保持 AI 原生的艺术风格（比 Pillow 后处理更自然）
- 🚀 更高的视觉质量（2K/4K 支持）
- 💰 成本：$2/M input tokens, $12/M output tokens

#### 测试计划
1. 重新生成"后端技术栈"幻灯片
2. 验证标题："后端技术栈 (Backend Tech Stack)" ✅
3. 验证章节标题的中文准确性
4. 评估整体视觉质量提升

**备注**：如果 Nano Banana Pro 仍有问题，则说明是 Google 图像生成模型的通用限制，需考虑切换到其他提供商（如 DALL-E 3）。

---

### v6.0 (2026-02-01) - 两步流程：布局生成 + 文本叠加 🎯

**状态**: ⚠️ 已回滚（虽然解决了准确性，但失去了 AI 原生风格）

**问题诊断**：
- v5.2 中文乱码依然存在（"后端技术栈" → "誤证: 后顿技林栈"）
- UTF-8 编码传输完全正确（已验证）
- 问题出在 **AI 模型图像生成时的字符渲染**

**根本原因**：
OpenRouter 的 Gemini 2.5 Flash Image 模型在渲染中文时存在字符误识别，这是**模型的底层限制**，无法通过 prompt 优化解决。

**解决方案：两步流程**

#### 步骤 1：AI 生成纯布局（无文本）
```python
prompt = """
CREATE A PROFESSIONAL SLIDE LAYOUT (NO TEXT CONTENT)

TASK: Create clean, professional slide background:
1. TITLE AREA (Top 15%): Blank space for title
2. CONTENT AREA (85%): 6-8 empty card boxes (grid layout)
   - Rounded corners, soft colors, shadows
   - NO TEXT - just blank colored boxes
3. VISUAL STYLE: 16:9, soft pastels, minimalist
"""
```

#### 步骤 2：Pillow 添加带风格的文本
```python
def _add_styled_text_overlay(base_image, title, content):
    # 加载中文字体（支持 Linux/macOS/Windows）
    # 渲染标题：阴影 + 主文字（立体效果）
    # 渲染内容：解析章节标题，添加到卡片上
    # 使用阴影和深色文字创建视觉风格
```

**关键特性**：
1. ✅ **中文准确性**：Pillow 直接从 Unicode 渲染，100% 准确
2. ✅ **视觉风格**：
   - 阴影文字（shadow_offset = 3px）
   - 立体效果（阴影 + 主文字）
   - 深色文字配色（40, 40, 40）
3. ✅ **跨平台字体支持**：
   - Linux: DroidSansFallback, Noto Sans CJK, WenQuanYi
   - macOS: PingFang
   - Windows: Microsoft YaHei
4. ✅ **智能内容解析**：
   - 自动提取标题（"标题:" 或 "N. " 格式）
   - 正则匹配章节标题（║ ... ║）
   - 网格布局渲染（3列，最多9个卡片）

**实现细节**：
- 标题：64pt字体，顶部8%位置，居中对齐
- 章节：24pt字体，卡片内20px偏移
- 阴影：偏移3px，透明度150-180
- 主文字：深色，透明度255（完全不透明）

**优势**：
- 🎯 彻底解决中文乱码问题
- 🎨 保持视觉风格（非纯黑文字）
- 🚀 渲染速度快（Pillow 本地处理）
- 🔧 易于调整（字体、颜色、位置可配置）

**测试**：
1. 生成"后端技术栈"幻灯片
2. 验证标题显示："后端技术栈 (Backend Tech Stack)" ✅
3. 验证章节标题准确显示
4. 验证视觉效果（阴影、立体感）

---

### v5.2 (2026-02-01) - 超强中文约束 + 明确错误示例 🔥

**状态**: ❌ 未能解决中文乱码（模型限制）

**问题**：v5.1 仍然出现中文乱码（"后端技术栈" → "点师技茉"）

**根本原因**：AI 图像生成模型可能在渲染中文时使用了某种"识别"机制，而非直接从 Unicode 渲染

**激进解决方案**：

1. **在 prompt 开头使用强警告标记**：
   ```
   🚨 EXTREME CRITICAL REQUIREMENT - TEXT ACCURACY 🚨
   ```

2. **提供具体的错误示例**（让 AI 学习避免）：
   ```
   ⛔ FORBIDDEN CHARACTER ERRORS:
   ❌ WRONG: '前端技术栈' → '青萌技林栈' (NEVER!)
   ❌ WRONG: '后端技术栈' → '点师技茉' (NEVER!)
   ✅ CORRECT: Copy characters EXACTLY
   ```

3. **强制字体和渲染策略**：
   ```
   - Use professional Chinese font (SimHei, Microsoft YaHei, Noto Sans CJK)
   - Render each character from Unicode codepoint
   - DO NOT attempt to 'recognize' Chinese text
   - Treat Chinese as sacred data - copy byte-by-byte
   ```

4. **详细的布局指导**（参考图片风格）：
   - 标题区域：顶部 15%，60-70pt
   - 内容区域：2-3 列网格布局
   - 卡片样式：圆角、阴影、柔和背景色
   - ASCII → 视觉元素转换规则

**关键改进**：
- ✅ 将错误示例直接放入 prompt（负面学习）
- ✅ 明确字体要求（中文专用字体）
- ✅ 强调"byte-by-byte copy"概念
- ✅ 提供详细的网格布局指南
- ✅ 包含完整的视觉检查清单

**测试建议**：
如果此版本仍出现乱码，说明这是 **AI 模型的底层限制**，需要考虑：
- 备选方案 A：使用文本到图片的两步流程（先生成纯文本，再用图片编辑工具渲染）
- 备选方案 B：切换到对中文支持更好的模型（如 DALL-E 3）
- 备选方案 C：后处理验证（OCR 检查，如果错误则重新生成）

---

### v5.0 (2026-02-01) - 结构化图表风格生成 🎨

**问题**：需要生成类似技术架构图的结构化幻灯片，而非简单的文本叠加

**参考效果**：
- 用户提供的参考图片：`GenSlides Data Flow` 技术架构图
- 清晰的标题 + 矩形框 + 分层模块 + 箭头连接
- 专业的技术演示风格

**解决方案**：重写 prompt 为"图表转换引擎"

#### 关键改进

1. **明确目标**：Transform into VISUAL STRUCTURED DIAGRAM
2. **内容类型检测**：
   - Type A: ASCII 框图 (┌─┐│└╔═╗║) → 圆角矩形 + 层次结构
   - Type B: 列表内容 → 卡片式布局
   - Type C: 纯文本 → 居中强调

3. **ASCII 转换规则**：
   ```
   ┌────┐  →  圆角矩形（单线边框）
   ╔════╗  →  双线边框（重要内容）
   嵌套结构 →  保持视觉层次
   ```

4. **视觉设计指南**：
   - 16:9 布局
   - 配色方案：米色、浅蓝等柔和色
   - 阴影效果：增加深度
   - 排版规范：标题 50-70pt, 内容 20-28pt

5. **质量清单**：
   - ☑ 所有文本准确显示
   - ☑ 结构清晰易懂
   - ☑ 视觉层次明确
   - ☑ 专业技术图表外观

**测试内容**：`instructions/Week7/instructions.md:418-582`（前端技术栈 165 行 ASCII 框图）

**预期效果**：生成类似参考图片的专业技术架构图，而非等宽字体的 ASCII 文本

---

### v4.0 (2026-02-01) - 智能内容类型识别 ⭐

**问题**：AI 无法正确理解三种不同的输入类型

**解决方案**：重写 prompt，支持三种输入类型的智能识别

#### 三种输入类型

##### 1️⃣ 自然语言描述
```
用户输入: "用一个生动的页面来展示 Q&A"
AI 理解: 设计要求="生动" + 核心内容="Q&A"
输出: 创意 Q&A 页面（大字体 + 装饰元素）
```

##### 2️⃣ 结构化内容
```
用户输入: "标题: AI 的未来\n- 机器学习"
AI 理解: 标题 + 列表结构
输出: 大标题 "AI 的未来" + 项目符号列表（移除标记）
```

##### 3️⃣ 代码/图表
```
用户输入: ```mermaid graph LR A[开始] --> B[结束] ```
AI 理解: Mermaid 流程图
输出: 可视化流程图
```

#### 最终 Prompt (v4.0)
```python
prompt_text = (
    f"You are a professional slide designer. Create a visually stunning slide image.\n\n"
    f"User's slide request: {text}\n\n"
    f"Instructions:\n"
    f"1. Understand the user's intent:\n"
    f"   - Natural language: Extract core content and apply design requirements\n"
    f"   - Structured: Parse as slide structure (title, lists) and format\n"
    f"   - Code blocks: Convert to visual representations\n\n"
    f"2. Design principles:\n"
    f"   - Title: Large, bold, eye-catching\n"
    f"   - Lists: Clear hierarchy with bullet points\n"
    f"   - Special pages (Q&A, Thank You): Creative, visually striking\n"
    f"   - Code/diagrams: Convert to graphics\n\n"
    f"3. Style inheritance:\n"
    f"   - Match artistic style, color palette, mood of reference image"
)
```

**详细说明**：参考 `SLIDE_CONTENT_UNDERSTANDING_V4.md`

**修改文件**：`backend/app/core/generator.py`

---

## UI/UX 优化

### 2026-02-01 - Sidebar 缩略图优化

#### 问题 1: 缩略图显示不符合 Keynote 风格
- ❌ 显示文字预览（"新幻灯片 点击编辑内容..."）
- ❌ 缩略图太小（w-20 h-14）
- ❌ 控件占用过多空间

#### 解决方案
- ✅ 移除文字预览，只显示纯图片
- ✅ 使用 16:9 比例（`aspect-[16/9]`）
- ✅ 拖拽手柄和删除按钮浮动在图片上方
- ✅ 状态指示器（"内容已更新"）浮动在底部

**视觉效果**：
```
┌──────────────────────────┐
│  🎯 ≡              ✕     │  ← 浮动控件（悬停显示）
│                          │
│   [缩略图 16:9]          │  ← 纯图片
│                          │
│      内容已更新          │  ← 底部状态（如需要）
└──────────────────────────┘
```

**修改文件**：`frontend/src/components/Sidebar.tsx`

**关键代码**：
```tsx
<div className="relative" onClick={onSelect}>
  {/* 浮动控件 */}
  <div className="absolute top-2 left-2 z-10 bg-white/90 opacity-0 group-hover:opacity-100">
    <GripVertical />
  </div>
  <button className="absolute top-2 right-2 z-10 bg-white/90 opacity-0 group-hover:opacity-100">
    <Trash2 />
  </button>
  
  {/* 纯图片缩略图 */}
  <div className="w-full aspect-[16/9] bg-gray-100">
    <img src={...} className="w-full h-full object-cover" />
  </div>
  
  {/* 底部状态 */}
  {needsUpdate && (
    <div className="absolute bottom-2 left-2 right-2">
      <span className="bg-orange-50/95 backdrop-blur-sm">内容已更新</span>
    </div>
  )}
</div>
```

#### 问题 2: 删除按钮有确认提示
- ❌ `confirm('确定要删除这张幻灯片吗?')`
- ❌ 增加操作步骤，影响体验

#### 解决方案
- ✅ 直接删除，无需确认
- ✅ Toast 提示已删除（可撤销）

**修改**：
```tsx
// 之前
const handleDelete = async (e, slideId) => {
  e.stopPropagation();
  if (confirm('确定要删除这张幻灯片吗?')) {
    await onDeleteSlide(slideId);
  }
};

// 优化后
const handleDelete = async (e, slideId) => {
  e.stopPropagation();
  await onDeleteSlide(slideId);  // 直接删除
};
```

---

## 功能增强

### 2026-02-01 - 风格管理功能（StyleManager）

#### 功能说明
替换"添加幻灯片"按钮为"新风格生成"，提供完整的新风格生成功能：
- **显示当前风格**：仅作参考，展示当前使用的风格和原始描述
- **输入新风格描述**：用户输入全新的风格描述（输入框默认为空）
- **调用初始化接口**：点击生成时调用 `/api/style/init` 生成全新的 2 个候选
- **选择新风格**：从候选中选择一个，替换当前风格

**重要**：此功能生成的是**全新的风格**，不是基于当前风格修改，而是完全重新生成。

#### 视觉效果
**按钮**：使用 `Palette` 图标 + "新风格生成"文字

**弹窗布局**：
```
┌────────────────────────────────────┐
│ 🎨 生成新风格                  [X] │
│ 描述新的视觉风格，AI 将生成 2 个  │
│ 全新候选方案                       │
├────────────────────────────────────┤
│ 📌 当前风格（参考）                │
│ [小缩略图]  原始描述: "xxx"        │
│                                    │
│ 新风格描述: *                      │
│ [空白文本框 - 输入新描述]          │
│                                    │
│ [生成全新风格候选]                 │
│                                    │
│ [候选1]  [候选2]                   │
└────────────────────────────────────┘
```

#### 实现要点

**核心逻辑**：
```typescript
// StyleManager 组件
const handleOpen = () => {
  setPrompt('');  // 清空输入框 - 强调是生成新风格
  setIsOpen(true);
};

const handleGenerate = async () => {
  // 调用 /api/style/init 生成全新候选
  const result = await api.generateStyle({ description: prompt });
  setCandidates(result);
};

const handleSelect = async (imagePath: string) => {
  // 保存新风格和新的 prompt
  await api.selectStyle({ 
    image_path: imagePath,
    style_prompt: prompt  // 保存新的描述
  });
  onStyleUpdated();  // 触发重新加载
};
```

**UI 优化**：
- 标题从"更新幻灯片风格"改为"生成新风格"
- 副标题强调"全新候选方案"
- 当前风格区域标注为"（参考）"，弱化视觉权重
- 输入框标签改为"新风格描述"，placeholder 更具体
- 按钮文字"生成全新风格候选"而非"生成新风格候选"
- "再次生成"按钮替代"重新生成"

**后端数据模型更新**：
```python
# yaml_store.py
def set_style_reference(self, image_path: str, style_prompt: str = None):
    data = self._read_data()
    data["style_reference"] = image_path
    if style_prompt is not None:
        data["style_prompt"] = style_prompt
    self._write_data(data)

# schemas.py
class ProjectState(BaseModel):
    style_reference: Optional[str] = None
    style_prompt: Optional[str] = None  # 新增
    slides: list[Slide] = []

class SelectedStyle(BaseModel):
    image_path: str
    style_prompt: Optional[str] = None  # 新增
```

**前端类型更新**：
```typescript
// types/index.ts
export interface ProjectState {
  style_reference: string | null;
  style_prompt: string | null;  // 新增
  slides: Slide[];
}

export interface SelectedStyle {
  image_path: string;
  style_prompt?: string;  // 新增
}
```

**修改文件**：
- `backend/app/data/yaml_store.py`
- `backend/app/models/schemas.py`
- `backend/app/api/endpoints.py`
- `frontend/src/types/index.ts`
- `frontend/src/api/client.ts` ⚠️ 添加 `generateStyle` 别名
- `frontend/src/components/StyleManager.tsx` （新建）
- `frontend/src/components/StyleInitializer.tsx`
- `frontend/src/components/Sidebar.tsx`
- `frontend/src/store/appStore.ts`
- `frontend/src/App.tsx`

**Bug 修复**：
1. **问题**：`api.generateStyle is not a function`
   - **原因**：`api/client.ts` 只有 `initStyle`，没有 `generateStyle`
   - **解决**：添加 `generateStyle` 作为 `initStyle` 的别名

2. **问题**：OpenRouter API 随机不返回图片（`No image found in OpenRouter response`）
   - **原因**：OpenRouter 的 Gemini 图像模型有时会只返回文本，不返回图片（API 不稳定或速率限制）
   - **现象**：日志显示第1/2次调用成功（有 `images` 字段），第2/2次失败（只有文本 `content`）
   - **解决**：在 `_generate_image_openrouter` 方法中添加**重试机制**（最多3次，间隔2秒）
     ```python
     def _generate_image_openrouter(self, prompt: str):
         max_retries = 3
         retry_delay = 2  # 秒
         
         for attempt in range(max_retries):
             try:
                 # ... API 调用 ...
                 if 'images' in message and message['images']:
                     # 成功找到图片
                     return process_image(...)
                 
                 # 没有找到图片
                 if attempt < max_retries - 1:
                     logger.warning(f"Retrying in {retry_delay}s...")
                     time.sleep(retry_delay)
                     continue
                 else:
                     raise RuntimeError("No image after retries")
             except Exception as e:
                 if attempt < max_retries - 1:
                     time.sleep(retry_delay)
                     continue
                 else:
                     raise
     ```

---

### 2026-02-01 - Slide 插入分隔线

#### 功能说明
在两个 Slide 之间显示**插入分隔线**，支持：
- 点击插入
- 按回车插入（Tab 导航 + Enter）

#### 视觉效果
```
[Slide 1]
────────  ← 默认：半透明灰线
────⊕───  ← 悬停：紫色粗线 + Plus 图标
[Slide 2]
```

#### 实现要点

**新组件 `InsertDivider`**：
```tsx
const InsertDivider = ({ onClick, position }) => {
  const [isHovered, setIsHovered] = useState(false);
  const [isFocused, setIsFocused] = useState(false);

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      onClick();
    }
  };

  return (
    <div
      className="relative h-3 cursor-pointer"
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      onClick={onClick}
      onKeyDown={handleKeyDown}
      tabIndex={0}
      role="button"
    >
      {/* 横实线 */}
      <div className={`absolute inset-x-0 h-0.5 transition-all ${
        isHovered || isFocused ? 'bg-purple-500 h-1' : 'bg-gray-300 opacity-0'
      }`} />
      
      {/* Plus 图标 */}
      {(isHovered || isFocused) && (
        <div className="absolute left-1/2 -translate-x-1/2 -top-3">
          <div className="bg-purple-500 text-white rounded-full p-1 shadow-lg animate-in">
            <Plus className="w-3 h-3" />
          </div>
        </div>
      )}
    </div>
  );
};
```

**插入逻辑**：
```typescript
// appStore.ts
createSlide: async (text = '新幻灯片', afterSlideId = null) => {
  const newSlide = await api.createSlide({ text });
  const currentSlides = get().slides;
  
  let slides: Slide[];
  if (afterSlideId === null) {
    slides = [newSlide, ...currentSlides]; // 插入到开头
  } else {
    const insertIndex = currentSlides.findIndex(s => s.id === afterSlideId);
    slides = [
      ...currentSlides.slice(0, insertIndex + 1),
      newSlide,
      ...currentSlides.slice(insertIndex + 1)
    ];
  }
  
  await api.reorderSlides(slides.map(s => s.id));
  set({ slides, currentSlideId: newSlide.id });
}
```

**修改文件**：
- `frontend/src/components/Sidebar.tsx`
- `frontend/src/App.tsx`
- `frontend/src/store/appStore.ts`

---

## Bug 修复

### Bug #8: 中文字符乱码 (2026-02-01) 🔧

**现象**: 
- 标题输入: `标题: 前端技术栈 (Frontend Tech Stack)`
- 生成图片显示: "青萌技林栈 (Tech Stack)"
- 中文字符被错误识别/渲染

**原因分析**:
1. AI 图像生成模型可能使用了 OCR 或字符重新解释
2. 缺少明确的 Unicode/中文字符处理指示
3. Prompt 中没有强调"不要替换相似字符"

**解决方案** (`backend/app/core/generator.py`):

```python
# v5.1 - 添加中文字符准确性约束

⚠️ CRITICAL - CHARACTER ACCURACY:
- The input contains CHINESE CHARACTERS (中文) and ENGLISH text
- You MUST render EVERY character EXACTLY as provided
- DO NOT use OCR or re-interpret the text
- DO NOT substitute similar-looking characters
- Example: '前端技术栈' must appear EXACTLY as '前端技术栈', 
           NOT '青萌技林栈' or any variation
- Use a high-quality Unicode font that supports Chinese characters properly
```

**调试日志**:
```python
logger.info(f"[SlideGen] Input text preview: {text[:100]}")
logger.info(f"[SlideGen] Text encoding: {text.encode('utf-8')[:200]}")
logger.info(f"[SlideGen] Text length: {len(text)} characters")
```

**测试计划**:
1. 重新生成"前端技术栈"幻灯片
2. 检查后端日志中的 UTF-8 编码是否正确
3. 验证生成图片中的中文字符是否准确

**备注**: 如果问题持续，可能需要：
- 在 prompt 中提供具体的错误示例（如当前的"青萌技林栈"）
- 考虑预处理文本，添加字符校验
- 或切换到不同的 AI 模型（某些模型对中文支持更好）

---

## Bug 修复

### Bug #9: 播放模式显示文本内容 (2026-02-01) 🎬

**现象**: 
- 点击"播放"按钮后，全屏展示不仅显示幻灯片图片，还在图片下方显示原始文本内容
- 这与 Keynote/PowerPoint 的演示模式不符

**预期行为**:
- 播放模式应该**只显示幻灯片图片**
- 所有文本内容都已经渲染在图片中，不需要额外显示

**解决方案** (`frontend/src/components/Carousel.tsx`):

```typescript
// 移除 154-161 行的文本内容显示
// Before:
{/* Text Content */}
{currentSlide.text && (
  <div className="mt-8 max-w-4xl text-center">
    <p className="text-white text-2xl leading-relaxed whitespace-pre-wrap">
      {currentSlide.text}
    </p>
  </div>
)}

// After:
// ✅ 只显示图片，不显示文本
```

**改进**:
1. ✅ 移除文本显示区域
2. ✅ 增大图片显示区域 (`max-w-7xl`)
3. ✅ 优化无图片时的提示信息

**测试**:
- 点击"播放"按钮
- 验证只显示图片，没有额外的文本内容
- 检查图片是否完整显示所有内容

---

## Bug 修复

### v1.0 → v4.0 演进

#### Bug 1: 文本被 AI 修改
**问题**：
```
输入: "用一个生动的页面来展示 Q&A"
输出: "用一个生造的两座来展示" ❌
```

**原因**：Prompt 中 "Make best guess" 让 AI 随意修改

**修复**：v1.0 → v2.0，强调 "EXACTLY this text"

---

#### Bug 2: 结构标记显示错误
**问题**：
```
输入: "标题: AI 的未来"
输出: 显示完整的 "标题: AI 的未来" ⚠️
期望: 只显示 "AI 的未来" 作为大标题
```

**原因**：把幻灯片当成纯文本展示

**修复**：v2.0 → v3.0，识别结构标记

---

#### Bug 3: 自然语言描述理解错误
**问题**：
```
输入: "用一个生动的页面来展示 Q&A"
v3.0 理解: 逐字显示整句话 ❌
正确理解: "生动的页面" = 设计要求，"Q&A" = 核心内容 ✅
```

**原因**：没有区分"描述"和"内容"

**修复**：v3.0 → v4.0，智能识别三种类型

---

## 相关文档

- `SLIDE_CONTENT_UNDERSTANDING_V4.md` - Prompt 设计详细说明（探讨性）
- `OPENROUTER_GUIDE.md` - OpenRouter 集成指南
- `MULTI_PROVIDER_SUMMARY.md` - 多 Provider 支持总结
- `PROMPT_BUG_FIX.md` - 详细 Bug 修复过程（已归档到本文档）
