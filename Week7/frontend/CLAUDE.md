# Week7 Frontend Development Guidelines

**Project**: AI Slide Generator Frontend
**Technology Stack**: TypeScript, React 19, Vite, TailwindCSS
**Package Manager**: npm/pnpm
**State Management**: Zustand

---

## Architecture Principles

### SOLID Principles

- **Single Responsibility**: Each component has one clear purpose
  - UI components only handle presentation
  - Service modules handle API communication
  - Hooks encapsulate reusable logic
  - Stores manage state

- **Open/Closed**: Extend through composition, not modification
  - Use HOCs and custom hooks for cross-cutting concerns
  - Compose components instead of modifying them

- **Liskov Substitution**: Components should be swappable
  - Define clear prop interfaces
  - Follow consistent patterns across similar components

- **Interface Segregation**: Minimal, focused prop interfaces
  - Don't pass entire objects when only a few properties are needed
  - Split large components into smaller, focused ones

- **Dependency Inversion**: Depend on abstractions
  - Use hooks to abstract data fetching
  - Inject services through context or props

### YAGNI (You Aren't Gonna Need It)
- Build features when needed, not in advance
- No premature abstractions
- Simple solutions first

### KISS (Keep It Simple, Stupid)
- Prefer simple, readable code
- Avoid over-engineering
- Use standard patterns
- Clear naming over comments

### DRY (Don't Repeat Yourself)
- Extract reusable components
- Create custom hooks for repeated logic
- Use utility functions for common operations
- Centralize API calls in service modules

---

## Project Structure

```
frontend/
├── src/
│   ├── App.tsx                 # Main application component
│   ├── main.tsx                # Application entry point
│   ├── components/             # React components
│   │   ├── SlideEditor/        # Main editor component
│   │   │   ├── SlideEditor.tsx
│   │   │   ├── EditorToolbar.tsx
│   │   │   └── EditorCanvas.tsx
│   │   ├── SlideSidebar/       # Sidebar with slide thumbnails
│   │   │   ├── SlideSidebar.tsx
│   │   │   ├── SlideItem.tsx
│   │   │   └── DraggableSlide.tsx
│   │   ├── SlidePreview/       # Main slide preview area
│   │   │   ├── SlidePreview.tsx
│   │   │   ├── GenerateButton.tsx
│   │   │   └── ImageDisplay.tsx
│   │   ├── StyleSelector/      # Style selection popup
│   │   │   ├── StyleSelector.tsx
│   │   │   ├── StyleOption.tsx
│   │   │   └── StylePrompt.tsx
│   │   ├── Fullscreen/         # Fullscreen slideshow mode
│   │   │   ├── FullscreenView.tsx
│   │   │   └── SlideCarousel.tsx
│   │   └── common/             # Reusable UI components
│   │       ├── Button.tsx
│   │       ├── Input.tsx
│   │       ├── Modal.tsx
│   │       ├── Spinner.tsx
│   │       └── Toast.tsx
│   ├── services/               # API service layer
│   │   ├── api.ts              # Base API client
│   │   ├── slideService.ts     # Slide-related API calls
│   │   ├── outlineService.ts   # Outline CRUD operations
│   │   └── styleService.ts     # Style image management
│   ├── hooks/                  # Custom React hooks
│   │   ├── useSlides.ts        # Slide data management
│   │   ├── useOutline.ts       # Outline operations
│   │   ├── useImageGeneration.ts  # Image generation
│   │   ├── useStyleSelection.ts   # Style selection flow
│   │   ├── useDragAndDrop.ts   # Drag and drop logic
│   │   └── useFullscreen.ts    # Fullscreen mode
│   ├── stores/                 # Zustand state stores
│   │   ├── slideStore.ts       # Slide state management
│   │   ├── uiStore.ts          # UI state (modals, toasts)
│   │   └── styleStore.ts       # Style configuration
│   ├── types/                  # TypeScript type definitions
│   │   ├── slide.ts            # Slide types
│   │   ├── outline.ts          # Outline types
│   │   ├── api.ts              # API request/response types
│   │   └── common.ts           # Common types
│   ├── utils/                  # Utility functions
│   │   ├── hash.ts             # Content hashing
│   │   ├── validation.ts       # Input validation
│   │   ├── formatting.ts       # Data formatting
│   │   └── storage.ts          # LocalStorage helpers
│   ├── assets/                 # Static assets
│   │   ├── icons/              # SVG icons
│   │   └── images/             # Static images
│   └── styles/                 # Global styles
│       ├── globals.css         # Global CSS + Tailwind directives
│       └── variables.css       # CSS custom properties
├── public/                     # Public static files
│   └── favicon.ico
├── index.html                  # HTML entry point
├── package.json                # Dependencies
├── tsconfig.json               # TypeScript configuration
├── tailwind.config.js          # TailwindCSS configuration
├── vite.config.ts              # Vite configuration
├── postcss.config.js           # PostCSS configuration
└── CLAUDE.md                   # This file
```

---

## Code Organization

### Component Structure

```tsx
// Good: Co-locate related files
components/
  SlideEditor/
    SlideEditor.tsx       // Main component
    SlideEditor.test.tsx  // Tests
    SlideEditor.module.css // Component-specific styles (if needed)
    types.ts              // Component-specific types
    utils.ts              // Component-specific utilities

// Component template
import { FC } from 'react'
import type { SlideEditorProps } from './types'
import styles from './SlideEditor.module.css'

/**
 * SlideEditor component for editing slide content.
 *
 * @param props - Component props
 * @returns SlideEditor component
 */
export const SlideEditor: FC<SlideEditorProps> = ({
  slideId,
  onSave,
  onCancel,
}) => {
  // Hooks at the top
  const { slide, updateSlide } = useSlides()
  const [isEditing, setIsEditing] = useState(false)

  // Event handlers
  const handleSave = async () => {
    await updateSlide(slideId, { ... })
    onSave?.()
  }

  // Early returns
  if (!slide) {
    return <Spinner />
  }

  // Render
  return (
    <div className="flex flex-col gap-4">
      {/* Component JSX */}
    </div>
  )
}
```

### Service Layer Pattern

```typescript
// services/api.ts - Base API client
import axios, { AxiosInstance, AxiosRequestConfig } from 'axios'

class APIClient {
  private client: AxiosInstance

  constructor(baseURL: string = 'http://localhost:8000') {
    this.client = axios.create({
      baseURL,
      headers: {
        'Content-Type': 'application/json',
      },
    })

    // Add interceptors for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        // Handle errors globally
        console.error('API Error:', error)
        return Promise.reject(error)
      }
    )
  }

  async get<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.get<T>(url, config)
    return response.data
  }

  async post<T>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.post<T>(url, data, config)
    return response.data
  }

  async put<T>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.put<T>(url, data, config)
    return response.data
  }

  async delete<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.delete<T>(url, config)
    return response.data
  }
}

export const apiClient = new APIClient()

// services/slideService.ts - Slide-specific API calls
import type {
  Slide,
  GenerateImageRequest,
  GenerateImageResponse,
  UpdateSlideOrderRequest,
} from '@/types/api'

export const slideService = {
  async generateImage(request: GenerateImageRequest): Promise<GenerateImageResponse> {
    return apiClient.post<GenerateImageResponse>('/api/slides/generate', request)
  },

  async getSlide(slideId: string): Promise<Slide> {
    return apiClient.get<Slide>(`/api/slides/${slideId}`)
  },

  async updateSlideOrder(request: UpdateSlideOrderRequest): Promise<void> {
    return apiClient.put<void>('/api/slides/order', request)
  },
}
```

---

## Best Practices

### TypeScript

```typescript
// Good: Use strict type checking
// tsconfig.json
{
  "compilerOptions": {
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "noImplicitReturns": true,
    "noFallthroughCasesInSwitch": true
  }
}

// Good: Define clear interfaces
interface Slide {
  id: string
  title: string
  content: string
  imageUrl: string | null
  contentHash: string
  order: number
  createdAt: Date
  updatedAt: Date
}

// Good: Use discriminated unions for state
type AsyncState<T> =
  | { status: 'idle' }
  | { status: 'loading' }
  | { status: 'success'; data: T }
  | { status: 'error'; error: Error }

// Good: Use utility types
type SlideFormData = Pick<Slide, 'title' | 'content'>
type SlideUpdate = Partial<Omit<Slide, 'id' | 'createdAt'>>

// Good: Type guard functions
function isSlide(value: unknown): value is Slide {
  return (
    typeof value === 'object' &&
    value !== null &&
    'id' in value &&
    'title' in value &&
    'content' in value
  )
}

// Good: Generic functions
function createAsyncState<T>(data?: T): AsyncState<T> {
  if (data) {
    return { status: 'success', data }
  }
  return { status: 'idle' }
}
```

### React 19 Best Practices

```tsx
// Good: Use function components
export const SlideItem: FC<SlideItemProps> = ({ slide, onClick }) => {
  // Component logic
}

// Good: Destructure props
const { title, content, imageUrl } = slide

// Good: Use custom hooks for logic
const useSlideValidation = (slide: Slide) => {
  const [errors, setErrors] = useState<string[]>([])

  useEffect(() => {
    const newErrors: string[] = []
    if (!slide.title.trim()) {
      newErrors.push('Title is required')
    }
    if (!slide.content.trim()) {
      newErrors.push('Content is required')
    }
    setErrors(newErrors)
  }, [slide.title, slide.content])

  return { errors, isValid: errors.length === 0 }
}

// Good: Memoize expensive computations
const sortedSlides = useMemo(
  () => slides.sort((a, b) => a.order - b.order),
  [slides]
)

// Good: Memoize callbacks passed to children
const handleSlideClick = useCallback(
  (slideId: string) => {
    setSelectedSlide(slideId)
  },
  []
)

// Good: Use React.lazy for code splitting
const FullscreenView = lazy(() => import('@/components/Fullscreen/FullscreenView'))

// Usage
<Suspense fallback={<Spinner />}>
  <FullscreenView slides={slides} />
</Suspense>
```

### Zustand State Management

```typescript
// stores/slideStore.ts
import { create } from 'zustand'
import { devtools, persist } from 'zustand/middleware'
import type { Slide } from '@/types/slide'

interface SlideState {
  slides: Slide[]
  selectedSlideId: string | null
  isLoading: boolean
  error: Error | null

  // Actions
  setSlides: (slides: Slide[]) => void
  addSlide: (slide: Slide) => void
  updateSlide: (id: string, updates: Partial<Slide>) => void
  deleteSlide: (id: string) => void
  reorderSlides: (slideIds: string[]) => void
  selectSlide: (id: string | null) => void
  setLoading: (isLoading: boolean) => void
  setError: (error: Error | null) => void
}

export const useSlideStore = create<SlideState>()(
  devtools(
    persist(
      (set, get) => ({
        slides: [],
        selectedSlideId: null,
        isLoading: false,
        error: null,

        setSlides: (slides) => set({ slides }),

        addSlide: (slide) =>
          set((state) => ({
            slides: [...state.slides, slide],
          })),

        updateSlide: (id, updates) =>
          set((state) => ({
            slides: state.slides.map((slide) =>
              slide.id === id ? { ...slide, ...updates } : slide
            ),
          })),

        deleteSlide: (id) =>
          set((state) => ({
            slides: state.slides.filter((slide) => slide.id !== id),
          })),

        reorderSlides: (slideIds) =>
          set((state) => {
            const slideMap = new Map(state.slides.map((s) => [s.id, s]))
            const reordered = slideIds
              .map((id) => slideMap.get(id))
              .filter((s): s is Slide => s !== undefined)
              .map((slide, index) => ({ ...slide, order: index }))
            return { slides: reordered }
          }),

        selectSlide: (id) => set({ selectedSlideId: id }),

        setLoading: (isLoading) => set({ isLoading }),

        setError: (error) => set({ error }),
      }),
      {
        name: 'slide-storage',
        partialize: (state) => ({ slides: state.slides }), // Only persist slides
      }
    )
  )
)

// Usage in components
const MyComponent: FC = () => {
  const slides = useSlideStore((state) => state.slides)
  const addSlide = useSlideStore((state) => state.addSlide)
  const updateSlide = useSlideStore((state) => state.updateSlide)

  // Use the state and actions
}
```

### Custom Hooks Pattern

```typescript
// hooks/useImageGeneration.ts
import { useState, useCallback } from 'react'
import { slideService } from '@/services/slideService'
import type { GenerateImageRequest, GenerateImageResponse } from '@/types/api'

interface UseImageGenerationResult {
  generateImage: (request: GenerateImageRequest) => Promise<string | null>
  isGenerating: boolean
  error: Error | null
  reset: () => void
}

export const useImageGeneration = (): UseImageGenerationResult => {
  const [isGenerating, setIsGenerating] = useState(false)
  const [error, setError] = useState<Error | null>(null)

  const generateImage = useCallback(async (request: GenerateImageRequest) => {
    setIsGenerating(true)
    setError(null)

    try {
      const response = await slideService.generateImage(request)
      return response.imagePath
    } catch (err) {
      const error = err instanceof Error ? err : new Error('Unknown error')
      setError(error)
      return null
    } finally {
      setIsGenerating(false)
    }
  }, [])

  const reset = useCallback(() => {
    setIsGenerating(false)
    setError(null)
  }, [])

  return { generateImage, isGenerating, error, reset }
}

// Usage
const MyComponent: FC = () => {
  const { generateImage, isGenerating, error } = useImageGeneration()

  const handleGenerate = async () => {
    const imagePath = await generateImage({
      prompt: 'A beautiful sunset',
      styleImagePath: '/styles/default.png',
    })

    if (imagePath) {
      console.log('Image generated:', imagePath)
    }
  }

  return (
    <button onClick={handleGenerate} disabled={isGenerating}>
      {isGenerating ? 'Generating...' : 'Generate Image'}
    </button>
  )
}
```

---

## Styling with TailwindCSS

### Configuration

```javascript
// tailwind.config.js
/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#f0f9ff',
          100: '#e0f2fe',
          500: '#0ea5e9',
          600: '#0284c7',
          700: '#0369a1',
        },
        secondary: {
          50: '#faf5ff',
          500: '#a855f7',
          600: '#9333ea',
        },
      },
      spacing: {
        18: '4.5rem',
        22: '5.5rem',
      },
      animation: {
        'slide-in': 'slideIn 0.3s ease-out',
        'fade-in': 'fadeIn 0.2s ease-in',
      },
      keyframes: {
        slideIn: {
          '0%': { transform: 'translateX(-100%)' },
          '100%': { transform: 'translateX(0)' },
        },
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
      },
    },
  },
  plugins: [],
}
```

### Best Practices

```tsx
// Good: Use Tailwind utility classes
<div className="flex flex-col gap-4 p-6 bg-white rounded-lg shadow-md">
  <h2 className="text-2xl font-bold text-gray-900">Title</h2>
  <p className="text-gray-600">Description</p>
</div>

// Good: Use @apply for repeated patterns
// globals.css
@layer components {
  .btn-primary {
    @apply px-4 py-2 bg-primary-500 text-white rounded-lg
      hover:bg-primary-600 active:bg-primary-700
      disabled:opacity-50 disabled:cursor-not-allowed
      transition-colors duration-200;
  }

  .card {
    @apply bg-white rounded-lg shadow-md p-6;
  }
}

// Good: Responsive design
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
  {/* Cards */}
</div>

// Good: Dark mode support (if needed)
<div className="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">
  {/* Content */}
</div>
```

---

## Error Handling

### Error Boundaries

```tsx
// components/common/ErrorBoundary.tsx
import { Component, ReactNode } from 'react'

interface Props {
  children: ReactNode
  fallback?: ReactNode
}

interface State {
  hasError: boolean
  error: Error | null
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Error caught by boundary:', error, errorInfo)
  }

  render() {
    if (this.state.hasError) {
      return (
        this.props.fallback || (
          <div className="flex items-center justify-center min-h-screen">
            <div className="text-center">
              <h1 className="text-2xl font-bold text-red-600">Something went wrong</h1>
              <p className="text-gray-600 mt-2">{this.state.error?.message}</p>
              <button
                onClick={() => window.location.reload()}
                className="btn-primary mt-4"
              >
                Reload Page
              </button>
            </div>
          </div>
        )
      )
    }

    return this.props.children
  }
}

// Usage
<ErrorBoundary>
  <App />
</ErrorBoundary>
```

### API Error Handling

```typescript
// utils/errors.ts
export class APIError extends Error {
  constructor(
    message: string,
    public statusCode: number,
    public data?: unknown
  ) {
    super(message)
    this.name = 'APIError'
  }
}

export class NetworkError extends Error {
  constructor(message: string = 'Network error') {
    super(message)
    this.name = 'NetworkError'
  }
}

// services/api.ts
this.client.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      // Server responded with error status
      throw new APIError(
        error.response.data.detail || 'Server error',
        error.response.status,
        error.response.data
      )
    } else if (error.request) {
      // Request made but no response
      throw new NetworkError('No response from server')
    } else {
      // Request setup error
      throw new Error(error.message)
    }
  }
)

// Usage in components
try {
  await slideService.generateImage(request)
} catch (error) {
  if (error instanceof APIError) {
    if (error.statusCode === 429) {
      showToast('Rate limit exceeded. Please try again later.')
    } else if (error.statusCode >= 500) {
      showToast('Server error. Please try again.')
    } else {
      showToast(error.message)
    }
  } else if (error instanceof NetworkError) {
    showToast('Network error. Check your connection.')
  } else {
    showToast('An unexpected error occurred.')
  }
}
```

---

## Performance Optimization

### Code Splitting

```tsx
// App.tsx
import { lazy, Suspense } from 'react'

const FullscreenView = lazy(() => import('@/components/Fullscreen/FullscreenView'))
const StyleSelector = lazy(() => import('@/components/StyleSelector/StyleSelector'))

export const App = () => {
  return (
    <Suspense fallback={<Spinner />}>
      <Router>
        <Routes>
          <Route path="/" element={<SlideEditor />} />
          <Route path="/fullscreen" element={<FullscreenView />} />
        </Routes>
      </Router>
    </Suspense>
  )
}
```

### Memoization

```tsx
// Good: Memoize expensive renders
const SlideList = memo(({ slides }: { slides: Slide[] }) => {
  return (
    <div>
      {slides.map((slide) => (
        <SlideItem key={slide.id} slide={slide} />
      ))}
    </div>
  )
})

// Good: Memoize callbacks
const handleSlideUpdate = useCallback(
  (id: string, updates: Partial<Slide>) => {
    updateSlide(id, updates)
  },
  [updateSlide]
)

// Good: Memoize expensive computations
const filteredSlides = useMemo(
  () => slides.filter((slide) => slide.title.includes(searchTerm)),
  [slides, searchTerm]
)
```

### Image Optimization

```tsx
// Good: Lazy load images
const LazyImage: FC<{ src: string; alt: string }> = ({ src, alt }) => {
  return (
    <img
      src={src}
      alt={alt}
      loading="lazy"
      className="w-full h-auto object-cover"
    />
  )
}

// Good: Use thumbnails for sidebar
<img
  src={`/api/images/${slide.id}/thumbnail`}
  alt={slide.title}
  className="w-20 h-20 object-cover rounded"
/>
```

---

## Testing

### Component Testing with Vitest

```typescript
// SlideItem.test.tsx
import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { SlideItem } from './SlideItem'

describe('SlideItem', () => {
  const mockSlide = {
    id: '1',
    title: 'Test Slide',
    content: 'Test content',
    imageUrl: '/images/test.png',
    contentHash: 'abc123',
    order: 0,
    createdAt: new Date(),
    updatedAt: new Date(),
  }

  it('renders slide title and content', () => {
    render(<SlideItem slide={mockSlide} onClick={vi.fn()} />)

    expect(screen.getByText('Test Slide')).toBeInTheDocument()
    expect(screen.getByText('Test content')).toBeInTheDocument()
  })

  it('calls onClick when clicked', () => {
    const handleClick = vi.fn()
    render(<SlideItem slide={mockSlide} onClick={handleClick} />)

    fireEvent.click(screen.getByRole('button'))

    expect(handleClick).toHaveBeenCalledWith('1')
  })
})
```

---

## Common Patterns

### Drag and Drop

```tsx
// hooks/useDragAndDrop.ts
import { useState } from 'react'

export const useDragAndDrop = (onReorder: (ids: string[]) => void) => {
  const [draggedId, setDraggedId] = useState<string | null>(null)

  const handleDragStart = (id: string) => {
    setDraggedId(id)
  }

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
  }

  const handleDrop = (targetId: string, allIds: string[]) => {
    if (!draggedId || draggedId === targetId) return

    const draggedIndex = allIds.indexOf(draggedId)
    const targetIndex = allIds.indexOf(targetId)

    const newIds = [...allIds]
    newIds.splice(draggedIndex, 1)
    newIds.splice(targetIndex, 0, draggedId)

    onReorder(newIds)
    setDraggedId(null)
  }

  return { handleDragStart, handleDragOver, handleDrop, draggedId }
}
```

### Toast Notifications

```tsx
// stores/uiStore.ts
interface Toast {
  id: string
  message: string
  type: 'success' | 'error' | 'info'
  duration?: number
}

interface UIState {
  toasts: Toast[]
  addToast: (toast: Omit<Toast, 'id'>) => void
  removeToast: (id: string) => void
}

export const useUIStore = create<UIState>((set) => ({
  toasts: [],

  addToast: (toast) =>
    set((state) => ({
      toasts: [...state.toasts, { ...toast, id: Date.now().toString() }],
    })),

  removeToast: (id) =>
    set((state) => ({
      toasts: state.toasts.filter((t) => t.id !== id),
    })),
}))

// components/common/Toast.tsx
export const ToastContainer: FC = () => {
  const toasts = useUIStore((state) => state.toasts)
  const removeToast = useUIStore((state) => state.removeToast)

  return (
    <div className="fixed bottom-4 right-4 space-y-2 z-50">
      {toasts.map((toast) => (
        <Toast key={toast.id} toast={toast} onClose={() => removeToast(toast.id)} />
      ))}
    </div>
  )
}
```

---

## Dependencies

### Core Dependencies (Latest Versions)

```json
{
  "dependencies": {
    "react": "^19.0.0",
    "react-dom": "^19.0.0",
    "zustand": "^5.0.2",
    "axios": "^1.7.9",
    "@dnd-kit/core": "^6.3.1",
    "@dnd-kit/sortable": "^9.0.0",
    "react-router-dom": "^7.1.3",
    "clsx": "^2.1.1",
    "js-sha256": "^0.11.0"
  },
  "devDependencies": {
    "@types/react": "^19.0.6",
    "@types/react-dom": "^19.0.2",
    "@vitejs/plugin-react": "^4.3.4",
    "typescript": "^5.7.2",
    "vite": "^6.0.7",
    "tailwindcss": "^4.1.0",
    "postcss": "^8.4.49",
    "autoprefixer": "^10.4.21",
    "vitest": "^2.1.8",
    "@testing-library/react": "^16.1.0",
    "@testing-library/jest-dom": "^6.6.3",
    "eslint": "^9.18.0",
    "eslint-plugin-react-hooks": "^5.1.0",
    "prettier": "^3.4.2"
  }
}
```

### Installation

```bash
npm install
# or
pnpm install
```

---

## Quick Reference

### Development Commands

```bash
# Start dev server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Run tests
npm run test

# Lint
npm run lint

# Format code
npm run format
```

### Vite Configuration

```typescript
// vite.config.ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
```

---

## Common Pitfalls to Avoid

❌ **Don't** mutate state directly
❌ **Don't** use `any` type
❌ **Don't** create functions inside render
❌ **Don't** use index as key in lists
❌ **Don't** fetch data in render
❌ **Don't** ignore TypeScript errors
❌ **Don't** use inline styles (use Tailwind)
❌ **Don't** create large monolithic components

✅ **Do** use immutable updates
✅ **Do** define proper types
✅ **Do** use `useCallback` for handlers
✅ **Do** use unique IDs as keys
✅ **Do** use hooks for data fetching
✅ **Do** fix TypeScript errors immediately
✅ **Do** use Tailwind utility classes
✅ **Do** break down components into smaller pieces

---

**Last Updated**: 2026-02-01
**React Version**: 19.0+
**TypeScript Version**: 5.7+
**Build Tool**: Vite 6.0+
