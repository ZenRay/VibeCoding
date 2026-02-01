# 问题修复和改进记录

**项目**: AI Slide Generator  
**日期**: 2026-02-01

---

## 🎯 重要修复

### 1. 候选图片自动确认问题

**日期**: 2026-02-01  
**严重性**: 中

#### 问题描述
生成候选图片后，自动显示绿色边框 + ✓（已确认标记），但用户并没有双击确认。

#### 根本原因
`store` 的 `addImageCandidate` 方法中，新候选图片被设置为 `isSelected: true`。

#### 解决方案
```typescript
// 之前：isSelected: true  ❌ 自动选择
// 现在：isSelected: false ✅ 等待用户确认
{ id: candidateId, slideId, imagePath, isSelected: false }
```

#### 修复后的行为
- ✅ 生成候选图片 → 紫色边框（预览），无 ✓
- ✅ 单击候选图片 → 紫色边框（切换预览），无 ✓
- ✅ 双击候选图片 → 绿色边框 + ✓（确认保存）

---

### 2. 缩略图更新延迟问题

**日期**: 2026-02-01  
**严重性**: 中

#### 问题描述
双击右侧候选图片确认选择后，左侧 Sidebar 的缩略图没有立即更新。

#### 根本原因
`ImageCandidatesPanel` 在双击确认时：
- ✅ 保存到后端
- ✅ 更新预览
- ❌ **未更新前端 store 中的 slide 对象**

#### 解决方案
添加回调链：
```typescript
ImageCandidatesPanel (双击)
  ↓ onSlideUpdated
SlideViewer
  ↓ onSlideUpdated  
App.tsx
  ↓ updateSlideInState
Zustand Store
  ↓ 
Sidebar (重新渲染) ✅
```

#### 关键代码
```typescript
const handleDoubleClickCandidate = async (candidate) => {
  // 保存到后端并获取更新后的 slide
  const updatedSlide = await api.updateSlide(currentVersion, slideId, { 
    image_path: candidate.imagePath 
  });
  
  // ✨ 通知父组件更新（触发 Sidebar 重新渲染）
  onSlideUpdated(updatedSlide);
};
```

---

### 3. CORS 跨域问题

**日期**: 2026-02-01  
**严重性**: 高

#### 问题描述
前端在 5174 端口运行，但后端 CORS 只配置了 5173，导致 API 请求被拒绝。

#### 根本原因
Vite 默认使用 5173，但如果端口被占用会自动切换到 5174，而后端 CORS 没有包含备用端口。

#### 解决方案
```python
# backend/app/core/config.py
CORS_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",  # ✨ 添加备用端口
    "http://127.0.0.1:5174",
]
```

---

### 4. SSL 连接错误

**日期**: 2026-02-01  
**严重性**: 中（间歇性）

#### 问题描述
```
httpx.ConnectError: [SSL: UNEXPECTED_EOF_WHILE_READING] 
EOF occurred in violation of protocol
```

#### 根本原因
代理服务器与 OpenRouter API 的 SSL 握手兼容性问题。

#### 解决方案

**方案 1**: 禁用代理（OpenRouter 不需要）
```bash
unset HTTP_PROXY
unset HTTPS_PROXY
```

**方案 2**: 切换到 Stub 模式
```bash
AI_MODE=stub
```

**方案 3**: 切换到 Google Gemini
```bash
AI_PROVIDER=google
```

**代码层面**：已在 `generator.py` 中为 OpenRouter 自动跳过代理：
```python
if self.provider == "openrouter":
    # OpenRouter 不需要代理，跳过以避免 SSL 错误
    self.client = httpx.Client(
        base_url="https://openrouter.ai/api/v1",
        timeout=60.0,
        # 不使用系统代理
    )
```

---

## 🎨 候选图片交互设计

### 交互规则

| 操作 | 中间预览 | 左侧缩略图 | 保存到 outline.yml | 视觉反馈 |
|------|---------|-----------|-------------------|----------|
| 生成图片 | ✅ 自动显示 | ✅ 自动显示 | ❌ | 紫色边框 |
| 单击 | ✅ 切换显示 | ✅ 切换显示 | ❌ | 紫色边框 + 放大 |
| 双击 | ✅ 保持显示 | ✅ 保持显示 | ✅ | 绿色边框 + ✓ |

### 状态说明

**紫色边框**：临时预览
- 仅前端显示
- 刷新页面会丢失
- 可以随意切换

**绿色边框 + ✓**：已确认保存
- 保存到 outline.yml
- 刷新页面后保留
- 只有一个候选图片可以被确认

### 使用流程

```
1. 生成候选图片（+按钮）
   ↓
2. 单击浏览多个候选（紫色边框切换）
   ↓
3. 找到满意的图片
   ↓
4. 双击确认（绿色 ✓）
   ↓
5. 保存到 outline.yml
```

---

## 🐛 已知限制

### 1. 文本渲染准确性

**问题**：AI 生成的图片中文本可能不完全准确

**原因**：
- AI 模型的文本渲染能力有限
- 复杂字符或特殊符号可能出错

**缓解措施**：
- 使用 Gemini 3 Pro Image Preview (最佳文本能力)
- 简化文本内容（避免特殊符号）
- 生成多个候选图片供选择

### 2. 风格一致性

**问题**：同一风格的不同幻灯片可能略有差异

**原因**：AI 每次生成都有随机性

**缓解措施**：
- 提示词强化风格匹配（v7.2）
- 使用相同的风格参考图片
- 生成候选图片后选择最匹配的

### 3. 生成时间

**问题**：Real 模式生成较慢（30-90秒/图片）

**原因**：
- AI 模型计算复杂
- 高分辨率图片处理时间长

**缓解措施**：
- 降低分辨率：`IMAGE_SIZE=1K`
- 使用 Flash 模型（更快）
- 开发时使用 Stub 模式

---

## 💡 最佳实践

### 1. 多版本工作流

**建议**：
- 不同主题/风格使用不同版本
- 定期清理不需要的版本
- 重要版本导出备份

**示例**：
```
v1: 产品发布会（科技风）
v2: 季度总结（商务风）
v3: 培训材料（教育风）
```

### 2. 候选图片生成策略

**建议**：
- 先生成 2-3 个候选
- 单击浏览对比
- 双击确认最满意的
- 如果都不满意，继续生成

### 3. 风格选择

**建议**：
- 风格描述具体明确
- 参考现有设计风格
- 先用 Stub 模式测试流程
- 确认满意后切换到 Real 模式

---

## 🔄 版本升级记录

### v1.0.0 → v2.0.0 (2026-02-01)

**重大改进**：
- ✅ 多版本项目管理
- ✅ 候选图片交互优化
- ✅ 缩略图实时更新
- ✅ CORS 配置完善
- ✅ SSL 错误处理

**破坏性变更**：
- ❌ 根目录 `outline.yml` 不再使用（需迁移到 `assets/v1/`）

---

## 📚 参考文档

- [多版本项目管理](./VERSIONED_PROJECTS.md)
- [AI 配置指南](./AI_CONFIGURATION.md)
- [测试指南](./TESTING_GUIDE.md)

---

**最后更新**: 2026-02-01
