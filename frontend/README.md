# Project Alpha Frontend

Project Alpha Ticket 管理系统的前端应用。

## 技术栈

- **框架**: React 18.2+
- **语言**: TypeScript 5.3+
- **构建工具**: Vite 5.0+
- **样式**: Tailwind CSS 3.4+
- **组件库**: Shadcn UI
- **状态管理**: Zustand 4.5+
- **路由**: React Router 6.21+
- **HTTP 客户端**: Axios 1.6+

## 快速开始

### 前置要求

- Node.js 20.x LTS 或更高版本
- npm 或 pnpm

### 安装依赖

```bash
cd frontend
npm install
# 或
pnpm install
```

### 配置环境变量

```bash
# 复制环境变量示例
cp .env.example .env.local

# 编辑 .env.local，配置 API 地址
VITE_API_URL=http://localhost:8000/api/v1
```

### 启动开发服务器

```bash
npm run dev
# 或
pnpm dev
```

访问 http://localhost:5173

### 构建生产版本

```bash
npm run build
# 或
pnpm build
```

## 项目结构

```
frontend/
├── src/
│   ├── components/          # 组件
│   │   └── ui/            # Shadcn UI 组件（待安装）
│   ├── pages/              # 页面组件
│   ├── services/           # API 服务
│   ├── hooks/              # 自定义 Hooks
│   ├── store/              # 状态管理
│   ├── types/              # TypeScript 类型
│   ├── lib/                # 工具库
│   └── styles/             # 样式文件
├── public/                 # 静态资源
├── package.json
├── tsconfig.json
├── vite.config.ts
├── tailwind.config.js
└── components.json         # Shadcn UI 配置
```

## 开发命令

```bash
# 开发服务器
npm run dev

# 构建生产版本
npm run build

# 预览生产构建
npm run preview

# 代码检查
npm run lint

# 代码格式化
npm run format

# 类型检查
npm run type-check
```

## 阶段 1 完成内容

- ✅ 项目结构搭建
- ✅ TypeScript 配置
- ✅ Vite 配置
- ✅ Tailwind CSS 配置
- ✅ TypeScript 类型定义（Ticket, Tag, API）
- ✅ API 服务封装（ticketService, tagService）
- ✅ 状态管理配置（Zustand）
- ✅ 自定义 Hooks（useTickets, useTags, useDebounce）
- ✅ 基础页面结构

## 下一步（阶段 4）

- ⏳ 安装 Shadcn UI 组件
- ⏳ 实现主布局和导航
- ⏳ 实现 Ticket 列表和卡片
- ⏳ 实现 Ticket 创建和编辑
- ⏳ 实现标签管理

## 相关文档

- [Vite 文档](https://vitejs.dev/)
- [React 文档](https://react.dev/)
- [Tailwind CSS 文档](https://tailwindcss.com/)
- [Shadcn UI 文档](https://ui.shadcn.com/)
- [Zustand 文档](https://zustand-demo.pmnd.rs/)
