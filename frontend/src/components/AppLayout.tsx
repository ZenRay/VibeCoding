import { Routes, Route, useLocation } from 'react-router-dom'
import { useEffect, useState } from 'react'
import HomePage from '@/pages/HomePage'
import TrashPage from '@/pages/TrashPage'

function AppLayout() {
  const location = useLocation()
  const [displayLocation, setDisplayLocation] = useState(location)
  const [transitionStage, setTransitionStage] = useState('fade-in')

  useEffect(() => {
    if (location.pathname !== displayLocation.pathname) {
      setTransitionStage('fade-out')
      setTimeout(() => {
        setDisplayLocation(location)
        setTransitionStage('fade-in')
      }, 150) // 淡出动画时间
    }
  }, [location, displayLocation])

  return (
    <div className="min-h-screen bg-background">
      <div className={`animate-${transitionStage}`}>
        <Routes location={displayLocation}>
          <Route path="/" element={<HomePage />} />
          <Route path="/trash" element={<TrashPage />} />
        </Routes>
      </div>
    </div>
  )
}

export default AppLayout
