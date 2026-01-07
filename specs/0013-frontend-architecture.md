# 前端架构设计

**文档版本**: v1.0  
**创建时间**: 2026-01-08  
**最后更新**: 2026-01-08

## 📋 目录

1. [技术栈](#技术栈)
2. [项目结构](#项目结构)
3. [组件设计](#组件设计)
4. [状态管理](#状态管理)
5. [API 集成](#api-集成)
6. [样式系统](#样式系统)

---

## 技术栈

### 核心技术

| 技术 | 版本 | 用途 |
|------|------|------|
| React | 18.2+ | UI 框架 |
| TypeScript | 5.3+ | 类型系统 |
| Vite | 5.0+ | 构建工具 |
| Tailwind CSS | 3.4+ | 样式框架 |
| Shadcn UI | - | UI 组件库 |
| Zustand | 4.5+ | 状态管理 |
| Axios | 1.6+ | HTTP 客户端 |
| React Router | 6.21+ | 路由管理 |

### 开发工具

- **Prettier** - 代码格式化
- **ESLint** - 代码检查
- **TypeScript** - 类型检查

---

## 项目结构

```
frontend/src/
├── components/          # 组件
│   ├── ui/             # UI 基础组件（Shadcn）
│   │   ├── button.tsx
│   │   ├── dialog.tsx
│   │   ├── input.tsx
│   │   └── ...
│   ├── AppLayout.tsx   # 应用布局
│   ├── Sidebar.tsx     # 侧边栏（过滤）
│   ├── SearchAndFilter.tsx  # 搜索和过滤（已废弃）
│   ├── TicketListItem.tsx   # Ticket 列表项
│   ├── TicketCard.tsx       # Ticket 卡片（已废弃）
│   ├── TicketDialog.tsx     # Ticket 编辑对话框
│   └── TagDialog.tsx        # Tag 编辑对话框
│
├── pages/              # 页面
│   └── HomePage.tsx    # 主页（列表布局）
│
├── hooks/              # 自定义 Hooks
│   ├── useTickets.ts   # Ticket 数据管理
│   ├── useTags.ts      # Tag 数据管理
│   └── useDebounce.ts  # 防抖 Hook
│
├── services/           # API 服务
│   ├── api.ts          # Axios 实例配置
│   ├── ticketService.ts
│   └── tagService.ts
│
├── store/              # 全局状态
│   └── useStore.ts     # Zustand store
│
├── types/              # 类型定义
│   ├── ticket.ts
│   ├── tag.ts
│   └── api.ts
│
├── lib/                # 工具函数
│   └── utils.ts        # cn() 等工具
│
├── styles/             # 全局样式
│   └── globals.css     # Tailwind 配置
│
└── main.tsx            # 应用入口
```

---

## 组件设计

### UI 层次结构

```
App
└── BrowserRouter
    └── AppLayout
        └── HomePage
            ├── Sidebar（过滤）
            │   ├── 状态过滤（RadioGroup）
            │   ├── 标签过滤（按钮列表）
            │   └── 显示选项（复选框）
            │
            └── 主内容区
                ├── 顶部栏
                │   ├── 标题
                │   ├── 搜索框
                │   └── 操作按钮
                │
                ├── 列表工具栏
                │   ├── 批量操作
                │   └── 排序控制
                │
                └── Ticket 列表
                    └── TicketListItem（循环）
                        ├── 复选框
                        ├── 内容
                        └── 操作按钮

# 对话框（Portal）
├── TicketDialog（创建/编辑 Ticket）
└── TagDialog（创建/编辑 Tag）
```

### 关键组件

#### HomePage（主页面）

**职责**：
- 管理所有状态（搜索、过滤、排序、选择）
- 协调子组件交互
- 处理 CRUD 操作

**状态管理**：
```typescript
const [searchQuery, setSearchQuery] = useState('')
const [statusFilter, setStatusFilter] = useState<'all' | 'pending' | 'completed'>('all')
const [selectedTagIds, setSelectedTagIds] = useState<number[]>([])
const [sortBy, setSortBy] = useState<'created_at' | 'updated_at' | 'title'>('created_at')
const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc')
const [selectedTicketIds, setSelectedTicketIds] = useState<Set<number>>(new Set())
const [includeDeleted, setIncludeDeleted] = useState(false)
```

#### Sidebar（侧边栏）

**职责**：
- 状态过滤（全部/未完成/已完成）
- 标签过滤（多选）
- 显示已删除选项

**特点**：
- 使用 RadioGroup 实现单选
- 标签显示使用次数
- 颜色视觉化

#### TicketListItem（列表项）

**职责**：
- 显示 Ticket 信息
- 复选框选择
- 快速操作（编辑、删除）
- 软删除状态显示（删除线）

**布局**：
```tsx
<div className="flex items-start gap-4 p-4 border-b hover:bg-muted/50">
  <input type="checkbox" />  {/* 复选框 */}
  <div className="flex-1">
    <h3>{ticket.title}</h3>  {/* 标题 */}
    <div>{/* 标签列表 */}</div>
    <div>{/* 元信息 */}</div>
  </div>
  <div>{/* 操作按钮 */}</div>
</div>
```

#### Dialogs（对话框）

**TicketDialog**：
- 创建/编辑 Ticket
- 表单验证
- 标签多选

**TagDialog**：
- 创建/编辑 Tag
- 颜色选择器
- 预设颜色

---

## 状态管理

### Zustand Store

```typescript
// store/useStore.ts
interface AppState {
  tickets: Ticket[]
  tags: Tag[]
  filters: FilterState
  
  setTickets: (tickets: Ticket[]) => void
  setTags: (tags: Tag[]) => void
  addTicket: (ticket: Ticket) => void
  updateTicket: (id: number, updates: Partial<Ticket>) => void
  removeTicket: (id: number) => void
  // ... Tag 操作
}

export const useStore = create<AppState>(set => ({
  tickets: [],
  tags: [],
  filters: {},
  
  setTickets: tickets => set({ tickets }),
  addTicket: ticket => set(state => ({
    tickets: [ticket, ...state.tickets]
  })),
  // ...
}))
```

### 使用方式

```typescript
// 在组件中使用
const { tickets, setTickets } = useStore()

// 选择特定状态
const tickets = useStore(state => state.tickets)
```

---

## API 集成

### Axios 配置

```typescript
// services/api.ts
const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000,
})

// 请求拦截器
api.interceptors.request.use(config => {
  // 添加认证 token 等
  return config
})

// 响应拦截器
api.interceptors.response.use(
  response => response,
  error => {
    // 统一错误处理
    return Promise.reject(apiError)
  }
)
```

### Service 层

```typescript
// services/ticketService.ts
export const ticketService = {
  async getTickets(params?: TicketQueryParams): Promise<TicketListResponse> {
    const response = await api.get<TicketListResponse>('/tickets', { params })
    return response.data
  },
  
  async createTicket(data: CreateTicketRequest): Promise<Ticket> {
    const response = await api.post<Ticket>('/tickets', data)
    return response.data
  },
  
  // ...
}
```

### Custom Hooks

```typescript
// hooks/useTickets.ts
export function useTickets(params?: TicketQueryParams) {
  const [tickets, setTickets] = useState<Ticket[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<Error | null>(null)
  
  const fetchTickets = async () => {
    setLoading(true)
    try {
      const response = await ticketService.getTickets(params)
      setTickets(response.data)
    } catch (err) {
      setError(err as Error)
    } finally {
      setLoading(false)
    }
  }
  
  useEffect(() => {
    fetchTickets()
  }, [/* 依赖 */])
  
  return { tickets, loading, error, refetch: fetchTickets }
}
```

---

## 样式系统

### Tailwind CSS

**配置**：`tailwind.config.js`

```javascript
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        border: 'hsl(var(--border))',
        background: 'hsl(var(--background))',
        // ...
      },
    },
  },
  plugins: [require('tailwindcss-animate')],
}
```

### CSS 变量

**位置**：`src/styles/globals.css`

```css
@layer base {
  :root {
    --background: 0 0% 100%;
    --foreground: 222.2 84% 4.9%;
    --primary: 221.2 83.2% 53.3%;
    /* ... */
  }
  
  .dark {
    --background: 222.2 84% 4.9%;
    --foreground: 210 40% 98%;
    /* ... */
  }
}
```

### Shadcn UI 组件

**安装组件**：
```bash
npx shadcn-ui@latest add button
npx shadcn-ui@latest add dialog
npx shadcn-ui@latest add input
```

**自定义**：
- 组件位于 `src/components/ui/`
- 可以直接修改组件代码
- 使用 `cn()` 工具合并样式

---

## 代码规范

### TypeScript 规范

```typescript
// ✅ 使用接口定义 props
interface TicketCardProps {
  ticket: Ticket
  onUpdate: () => void
  onEdit: (ticket: Ticket) => void
}

// ✅ 使用类型注解
const [tickets, setTickets] = useState<Ticket[]>([])

// ✅ 箭头函数简化
tickets.map(t => t.id)  // 而不是 tickets.map((t) => t.id)

// ✅ 可选链
ticket.tags?.length ?? 0
```

### React 规范

```tsx
// ✅ 使用函数组件
export function TicketCard({ ticket }: TicketCardProps) {
  // ...
}

// ✅ 自定义 Hooks
const { tickets, loading } = useTickets(params)

// ✅ useCallback 优化
const handleDelete = useCallback(async () => {
  await ticketService.deleteTicket(id)
}, [id])

// ✅ React.memo 优化（选择性使用）
export const TicketListItem = React.memo(({ ticket }) => {
  // ...
})
```

### 样式规范

```tsx
// ✅ 使用 Tailwind 类名
<div className="flex items-center gap-2 p-4">

// ✅ 使用 cn() 合并条件类名
<div className={cn(
  "base-classes",
  isActive && "active-classes",
  className
)}>

// ✅ 内联样式用于动态值
<span style={{ backgroundColor: tag.color }}>
```

---

## 性能优化

### 1. 代码分割

```typescript
// 路由懒加载
const HomePage = lazy(() => import('./pages/HomePage'))

// 组件懒加载
const HeavyComponent = lazy(() => import('./components/HeavyComponent'))
```

### 2. 列表优化

```typescript
// 使用 key
{tickets.map(ticket => (
  <TicketListItem key={ticket.id} ticket={ticket} />
))}

// 虚拟滚动（如果列表很长）
// 使用 react-window 或 react-virtual
```

### 3. 防抖和节流

```typescript
// 搜索防抖
const [localSearchQuery, setLocalSearchQuery] = useState('')

useEffect(() => {
  const timer = setTimeout(() => {
    onSearchChange(localSearchQuery)
  }, 300)
  return () => clearTimeout(timer)
}, [localSearchQuery])
```

---

## 相关文档

- [功能说明](./0003-features.md) - 功能详细说明
- [代码质量](./0011-code-quality.md) - 前端代码规范
- [问题排查](./0009-troubleshooting.md) - 前端相关问题

---

## 总结

**前端架构核心**：

1. **组件化** - UI 组件可复用
2. **类型安全** - TypeScript 类型检查
3. **状态管理** - Zustand 轻量级管理
4. **样式系统** - Tailwind + Shadcn UI
5. **代码质量** - Prettier + ESLint 自动保证

**记住**：提交前运行 Docker 检查，确保格式和类型正确！
