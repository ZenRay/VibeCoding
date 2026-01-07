import * as React from 'react'
import { X } from 'lucide-react'
import { cn } from '@/lib/utils'

type ToastType = 'success' | 'error' | 'info' | 'warning'

interface Toast {
  id: string
  type: ToastType
  message: string
  duration?: number
}

interface ToastContextValue {
  toasts: Toast[]
  addToast: (type: ToastType, message: string, duration?: number) => void
  removeToast: (id: string) => void
}

const ToastContext = React.createContext<ToastContextValue>({
  toasts: [],
  addToast: () => {},
  removeToast: () => {},
})

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = React.useState<Toast[]>([])

  const addToast = React.useCallback(
    (type: ToastType, message: string, duration: number = 3000) => {
      const id = Math.random().toString(36).substr(2, 9)
      const toast: Toast = { id, type, message, duration }

      setToasts(prev => [...prev, toast])

      // 自动移除
      if (duration > 0) {
        setTimeout(() => {
          setToasts(prev => prev.filter(t => t.id !== id))
        }, duration)
      }
    },
    []
  )

  const removeToast = React.useCallback((id: string) => {
    setToasts(prev => prev.filter(t => t.id !== id))
  }, [])

  return (
    <ToastContext.Provider value={{ toasts, addToast, removeToast }}>
      {children}
      <ToastContainer toasts={toasts} onRemove={removeToast} />
    </ToastContext.Provider>
  )
}

function ToastContainer({
  toasts,
  onRemove,
}: {
  toasts: Toast[]
  onRemove: (id: string) => void
}) {
  return (
    <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2 w-80">
      {toasts.map(toast => (
        <ToastItem key={toast.id} toast={toast} onRemove={onRemove} />
      ))}
    </div>
  )
}

function ToastItem({ toast, onRemove }: { toast: Toast; onRemove: (id: string) => void }) {
  const typeStyles = {
    success: 'bg-green-50 border-green-500 text-green-900',
    error: 'bg-red-50 border-red-500 text-red-900',
    warning: 'bg-yellow-50 border-yellow-500 text-yellow-900',
    info: 'bg-blue-50 border-blue-500 text-blue-900',
  }

  return (
    <div
      className={cn(
        'flex items-start gap-3 p-4 rounded-lg border-l-4 shadow-lg animate-in slide-in-from-right',
        typeStyles[toast.type]
      )}
    >
      <div className="flex-1">
        <p className="text-sm font-medium">{toast.message}</p>
      </div>
      <button
        onClick={() => onRemove(toast.id)}
        className="text-current opacity-70 hover:opacity-100 transition-opacity"
      >
        <X className="h-4 w-4" />
      </button>
    </div>
  )
}

export function useToast() {
  const context = React.useContext(ToastContext)
  if (!context) {
    throw new Error('useToast must be used within ToastProvider')
  }
  return context
}

// 便捷方法
export const toast = {
  success: (message: string) => {
    // 通过全局事件触发
    window.dispatchEvent(
      new CustomEvent('toast', { detail: { type: 'success', message } })
    )
  },
  error: (message: string) => {
    window.dispatchEvent(new CustomEvent('toast', { detail: { type: 'error', message } }))
  },
  info: (message: string) => {
    window.dispatchEvent(new CustomEvent('toast', { detail: { type: 'info', message } }))
  },
  warning: (message: string) => {
    window.dispatchEvent(new CustomEvent('toast', { detail: { type: 'warning', message } }))
  },
}
