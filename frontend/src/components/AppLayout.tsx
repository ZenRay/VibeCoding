import { Routes, Route } from 'react-router-dom'
import HomePage from '@/pages/HomePage'

function AppLayout() {
  return (
    <div className='min-h-screen bg-background'>
      <Routes>
        <Route path='/' element={<HomePage />} />
      </Routes>
    </div>
  )
}

export default AppLayout
