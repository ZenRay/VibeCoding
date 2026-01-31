# 🚀 Week7 AI Slide Generator - 快速参考

## 📍 关键文件位置

### 前端组件 (3个)
```
frontend/src/components/
├── StyleInitializer.tsx   # 风格初始化模态框
├── Sidebar.tsx            # 侧边栏 + 拖拽排序
└── SlideEditor.tsx        # 幻灯片编辑器
```

### 状态管理
```
frontend/src/store/
└── appStore.ts            # Zustand 全局状态
```

### API 客户端
```
frontend/src/api/
└── client.ts              # Axios HTTP 客户端
```

---

## ⚡ 快速启动

### 方式 1: 一键启动
```bash
cd /home/ray/Documents/VibeCoding/Week7
./start-dev.sh
```

### 方式 2: 手动启动
```bash
# 终端 1 - 后端
cd backend && source .venv/bin/activate && python run.py

# 终端 2 - 前端
cd frontend && npm install && npm run dev
```

### 访问
- 前端: http://localhost:5173
- 后端 API: http://localhost:8000/docs

---

## 🎯 核心功能

### 1. 风格初始化
- 位置: `StyleInitializer.tsx`
- 触发: `style_reference` 为空时
- API: `POST /api/style/init`, `POST /api/style/select`

### 2. 幻灯片 CRUD
- 创建: `Sidebar.tsx` → "添加幻灯片" 按钮
- 编辑: `SlideEditor.tsx` → 左侧文本区域
- 删除: `Sidebar.tsx` → 垃圾桶图标
- 排序: `Sidebar.tsx` → 拖拽排序

### 3. 自动保存
- 位置: `SlideEditor.tsx`
- 机制: 防抖 1 秒 + 失焦立即保存
- 状态: "保存中..." / "✓ 已保存"

### 4. Hash 检测
- 位置: `SlideEditor.tsx`
- 逻辑: `content_hash !== image_hash`
- 显示: 橙色 "需要更新" 标签 + "重新生成" 按钮

---

## 🛠️ 常用命令

```bash
# 安装依赖
cd frontend && npm install

# 开发模式
cd frontend && npm run dev

# 构建生产版本
cd frontend && npm run build

# 启动后端
cd backend && source .venv/bin/activate && python run.py

# 查看 API 文档
open http://localhost:8000/docs
```

---

## 📦 依赖列表

### 核心依赖
- React 19 - UI 框架
- TypeScript 5.6 - 类型系统
- Vite 6.0 - 构建工具
- Tailwind CSS 4 - 样式

### 功能依赖
- Zustand 5.0 - 状态管理
- @dnd-kit/* - 拖拽排序
- lucide-react - 图标
- sonner - Toast 通知
- axios - HTTP 客户端

---

## 🐛 常见问题

### Q: npm install 失败?
A: 检查网络连接,或使用国内镜像:
```bash
npm config set registry https://registry.npmmirror.com
```

### Q: 图片加载失败?
A: 检查后端是否运行在 `localhost:8000`,图片路径是否正确。

### Q: 拖拽不生效?
A: 确保 `@dnd-kit/utilities` 已安装:
```bash
cd frontend && npm install @dnd-kit/utilities
```

### Q: TypeScript 报错?
A: 运行类型检查:
```bash
cd frontend && npx tsc --noEmit
```

---

## 📚 文档索引

- **实施总结**: `IMPLEMENTATION_SUMMARY.md`
- **项目结构**: `PROJECT_STRUCTURE.md`
- **任务进度**: `TASKS_STATUS.md`
- **交付清单**: `DELIVERY_CHECKLIST.md`
- **前端指南**: `frontend/README.md`

---

## 🎨 UI 组件树

```
App.tsx
├── Toaster (sonner)
├── StyleInitializer (modal)
│   ├── 文本输入框
│   ├── "生成" 按钮
│   └── 2 张候选图片
├── Sidebar
│   ├── "添加幻灯片" 按钮
│   ├── "播放演示" 按钮
│   └── 幻灯片列表 (拖拽排序)
│       ├── 缩略图
│       ├── 文本预览
│       └── "删除" 按钮
└── SlideEditor
    ├── 左侧: 文本编辑器
    ├── 右侧: 图片预览
    └── 底部: "重新生成图片" 按钮
```

---

## 🔑 关键 API 端点

```
GET    /api/project              # 获取项目状态
POST   /api/style/init           # 生成风格候选
POST   /api/style/select         # 选择风格
POST   /api/slides               # 创建幻灯片
PUT    /api/slides/reorder       # 重排序
PUT    /api/slides/{id}          # 更新文本
POST   /api/slides/{id}/generate # 重新生成图片
DELETE /api/slides/{id}          # 删除幻灯片
```

---

## 💡 开发技巧

### 修改组件样式
所有组件使用 Tailwind CSS,查找 `className` 属性修改。

### 添加新的 API
1. 后端: `backend/app/api/endpoints.py`
2. 前端: `frontend/src/api/client.ts`
3. Store: `frontend/src/store/appStore.ts`

### 调试状态
使用 Zustand DevTools:
```typescript
import { devtools } from 'zustand/middleware';
// 在 appStore.ts 中添加
```

### 调试 API
1. 浏览器 DevTools → Network 标签
2. 或访问 http://localhost:8000/docs (Swagger UI)

---

**更新时间**: 2026-02-01  
**版本**: Phase 2 & 3 完成
