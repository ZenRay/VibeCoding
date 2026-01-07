import { Routes, Route } from 'react-router-dom'
import HomePage from '@/pages/HomePage'
import TrashPage from '@/pages/TrashPage'

function AppLayout() {
  return (
    <div className="min-h-screen bg-background">
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/trash" element={<TrashPage />} />
      </Routes>
    </div>
  )
}

export default AppLayout
