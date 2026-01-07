import React from 'react'
import { Button } from './ui/button'

interface Props {
  children: React.ReactNode
}

interface State {
  hasError: boolean
  error: Error | null
}

export class ErrorBoundary extends React.Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('ErrorBoundary caught error:', error, errorInfo)
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex flex-col items-center justify-center min-h-screen p-4">
          <div className="max-w-md text-center space-y-4">
            <h1 className="text-2xl font-bold text-destructive">出错了</h1>
            <p className="text-muted-foreground">
              {this.state.error?.message || '应用遇到了一个错误'}
            </p>
            <div className="flex gap-2 justify-center">
              <Button
                onClick={() => {
                  this.setState({ hasError: false, error: null })
                  window.location.reload()
                }}
              >
                重新加载
              </Button>
              <Button
                variant="outline"
                onClick={() => {
                  this.setState({ hasError: false, error: null })
                }}
              >
                返回
              </Button>
            </div>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}
