# AI 配置和优化指南

**版本**: v2.0.0  
**日期**: 2026-02-01

---

## 📋 AI 提供商配置

### 支持的提供商

#### 1. OpenRouter (推荐)

**优点**：
- ✅ 无需代理（国内可直接访问）
- ✅ 支持多种模型
- ✅ 统一 API 接口
- ✅ 按需付费

**配置**：
```bash
AI_PROVIDER=openrouter
OPENROUTER_API_KEY=sk-or-v1-...
OPENROUTER_MODEL=google/gemini-3-pro-image-preview
```

**推荐模型**：
- `google/gemini-3-pro-image-preview` (Nano Banana Pro) - 最佳文本渲染
- `google/gemini-2.5-flash-image` - 速度快，成本低

#### 2. Google Gemini

**优点**：
- ✅ 官方 API
- ✅ 免费额度
- ✅ 稳定性高

**配置**：
```bash
AI_PROVIDER=google
GEMINI_API_KEY=AIzaSy...
GEMINI_MODEL=gemini-2.5-flash-image
```

**注意**：国内需要配置代理：
```bash
HTTP_PROXY=http://127.0.0.1:7890
HTTPS_PROXY=http://127.0.0.1:7890
```

---

## 🎨 图片配置

### 分辨率设置

```bash
IMAGE_SIZE=1K    # 选项: 1K, 2K, 4K
```

| 分辨率 | 实际尺寸 | 生成时间 | 文件大小 | 推荐场景 |
|-------|---------|---------|---------|----------|
| 1K | 1024x576 | 30-40秒 | ~2MB | 快速测试、在线演示 |
| 2K | 2048x1152 | 50-70秒 | ~8MB | 高质量演示 |
| 4K | 4096x2304 | 90-120秒 | ~20MB | 印刷、专业展示 |

**推荐**: `1K` - 平衡质量和速度

### 宽高比设置

```bash
IMAGE_ASPECT_RATIO=16:9  # 选项: 16:9, 4:3, 1:1
```

| 宽高比 | 适用场景 |
|-------|----------|
| 16:9 | 现代演示、视频、宽屏 |
| 4:3 | 传统演示、投影仪 |
| 1:1 | 社交媒体、方形展示 |

---

## 🤖 AI 模式

### Stub 模式（测试）

```bash
AI_MODE=stub
```

**特点**：
- ⚡ 瞬间生成（<1秒）
- 💰 零成本（不调用 API）
- 🎯 纯色占位图片 + 文本标签

**使用场景**：
- 开发调试
- UI 测试
- 功能验证
- API 不可用时的降级方案

### Real 模式（生产）

```bash
AI_MODE=real
```

**特点**：
- 🎨 真实 AI 生成
- ⏱️ 需要等待（30-90秒）
- 💸 消耗 API 配额

**使用场景**：
- 生产环境
- 高质量内容生成
- 实际演示使用

---

## 📝 提示词优化

### 风格提示词（Style Prompt）

**版本**: v7.2

**核心原则**：
1. **风格匹配优先**：AI 必须模仿参考图片的视觉风格
2. **文本准确第二**：在保持风格的前提下准确渲染文本
3. **禁止过度创造**：不添加用户未要求的元素

**提示词模板**：
```
🎨 STYLE REFERENCE: The image shown above is your STYLE GUIDE.
You MUST mimic its visual style (colors, fonts, layout, aesthetic) 
while displaying the text below.

=== EXACT TEXT (RENDER PRECISELY) ===
{用户文本}
=== END TEXT ===

⚠️ CRITICAL RULES:
1. STYLE MATCHING (HIGHEST PRIORITY):
   - Use the SAME color palette
   - Use the SAME font style
   - Use the SAME background style
   - Use the SAME visual aesthetic
   
2. TEXT ACCURACY (SECOND PRIORITY):
   - Display EVERY character EXACTLY as provided
   - Match text layout from reference
   - No extra decorations
```

### 幻灯片文本提示词

**优化历史**：
- v1-v4: 基础文本渲染
- v5-v6: 增强准确性，减少过度创造
- v7.0: 添加风格参考
- **v7.2**: 强化风格匹配（当前版本）

**关键改进**：
- 明确 "STYLE MATCHING" 为最高优先级
- 使用 "MUST" 和 "SAME" 等强制性词汇
- 详细列出需要匹配的元素（颜色、字体、布局、美学）

---

## 🔧 性能优化

### 1. 图片大小优化

**问题**：生成的图片过大（>5MB）  
**解决**：降低 `IMAGE_SIZE` 配置

```bash
# 从 2K 降到 1K
IMAGE_SIZE=1K
```

**效果**：
- 生成时间：↓ 40%
- 文件大小：↓ 75%
- 加载速度：↑ 4x

### 2. API 响应时间

**优化策略**：
- 使用 OpenRouter（相比 Gemini 更快）
- 选择 Flash 模型（相比 Pro 更快）
- 禁用代理（OpenRouter 不需要）

**配置**：
```bash
AI_PROVIDER=openrouter
OPENROUTER_MODEL=google/gemini-2.5-flash-image
```

### 3. 资源缓存

后端自动缓存：
- 每个版本的 `YAMLStore` 实例
- 每个版本的 `GeminiGenerator` 实例

**效果**：切换版本时无需重新初始化。

---

## 🐛 常见问题

### SSL 连接错误

**错误信息**：
```
httpx.ConnectError: [SSL: UNEXPECTED_EOF_WHILE_READING] 
EOF occurred in violation of protocol
```

**原因**：代理服务器与 OpenRouter 的 SSL 兼容性问题

**解决方案**：

方案 1：禁用代理（OpenRouter 不需要）
```bash
unset HTTP_PROXY
unset HTTPS_PROXY
# 重启后端
```

方案 2：切换到 Stub 模式
```bash
AI_MODE=stub
```

方案 3：切换到 Google Gemini
```bash
AI_PROVIDER=google
GEMINI_API_KEY=your_key
```

### 图片文本乱码

**原因**：模型选择不当或提示词不够强

**解决方案**：
1. 使用 `gemini-3-pro-image-preview` (文本渲染最佳)
2. 确保使用 v7.2 提示词
3. 增加风格参考图片的权重

### 生成速度慢

**优化**：
1. 降低分辨率：`IMAGE_SIZE=1K`
2. 使用 Flash 模型：`OPENROUTER_MODEL=google/gemini-2.5-flash-image`
3. 使用 Stub 模式测试：`AI_MODE=stub`

---

## 📊 性能基准

### OpenRouter (Gemini 3 Pro Image Preview)

| 操作 | 1K | 2K | 4K |
|------|-----|-----|-----|
| 风格候选 (2张) | 60-90s | 100-150s | 180-240s |
| 幻灯片图片 (1张) | 30-40s | 50-70s | 90-120s |

### Google Gemini (Flash)

| 操作 | 1K | 2K |
|------|-----|-----|
| 风格候选 (2张) | 40-60s | 70-100s |
| 幻灯片图片 (1张) | 20-30s | 35-50s |

---

## 🔗 相关资源

- [OpenRouter 模型列表](https://openrouter.ai/models)
- [Gemini API 文档](https://ai.google.dev/docs)
- [提示词工程最佳实践](https://platform.openai.com/docs/guides/prompt-engineering)

---

**最后更新**: 2026-02-01
