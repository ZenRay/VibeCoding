import { BrowserRouter } from 'react-router-dom'
import AppLayout from './components/AppLayout'
import { ToastProvider } from './components/ui/toast'
import { ErrorBoundary } from './components/ErrorBoundary'

function App() {
  return (
    <ErrorBoundary>
      <ToastProvider>
        <BrowserRouter>
          <AppLayout />
        </BrowserRouter>
      </ToastProvider>
    </ErrorBoundary>
  )
}

export default App
