# AI Slide Generator - Frontend

React 19 + TypeScript + Vite + Tailwind CSS

## 快速开始

### 1. 安装依赖

```bash
npm install
```

### 2. 启动开发服务器

```bash
npm run dev
```

应用将运行在: http://localhost:5173

## 项目结构

```
src/
├── api/
│   └── client.ts          # API 客户端
├── components/
│   ├── StyleInitializer.tsx  # 风格初始化模态框
│   ├── Sidebar.tsx           # 侧边栏 + 拖拽排序
│   └── SlideEditor.tsx       # 幻灯片编辑器
├── store/
│   └── appStore.ts        # Zustand 状态管理
├── types/
│   └── index.ts           # TypeScript 类型
├── lib/
│   ├── utils.ts           # 工具函数
│   └── dnd-kit.ts         # DnD Kit 导出
├── App.tsx                # 主应用
└── main.tsx               # 入口文件
```

## 功能特性

### Phase 2: 风格初始化 ✅
- 首次使用时弹出风格设置模态框
- 输入风格描述生成 2 个候选图片
- 点击选择应用风格

### Phase 3: 幻灯片管理 ✅
- 创建/编辑/删除幻灯片
- 拖拽排序 (@dnd-kit)
- 自动保存 (防抖 1 秒)
- Hash 检测自动提示重新生成图片
- Toast 通知 (sonner)

### Phase 4: 全屏播放 (待实现)
- 全屏演示模式
- 自动翻页
- 键盘导航

## 技术栈

- **React 19** - UI 框架
- **TypeScript** - 类型安全
- **Vite** - 构建工具
- **Tailwind CSS 4** - 样式
- **Zustand** - 状态管理
- **@dnd-kit** - 拖拽排序
- **lucide-react** - 图标库
- **sonner** - Toast 通知
- **axios** - HTTP 客户端

## 开发命令

```bash
npm run dev      # 启动开发服务器
npm run build    # 构建生产版本
npm run preview  # 预览生产构建
```

## 注意事项

1. 后端必须先启动在 http://localhost:8000
2. Vite 代理配置见 vite.config.ts
3. 图片路径: http://localhost:8000/assets/...
