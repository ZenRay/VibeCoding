import { useEffect, useState } from 'react'
import { useLocation } from 'react-router-dom'

export function PageTransition({ children }: { children: React.ReactNode }) {
  const location = useLocation()
  const [displayLocation, setDisplayLocation] = useState(location)
  const [transitionStage, setTransitionStage] = useState('fade-in')

  useEffect(() => {
    if (location !== displayLocation) {
      setTransitionStage('fade-out')
    }
  }, [location, displayLocation])

  return (
    <div
      className={`animate-${transitionStage}`}
      onAnimationEnd={() => {
        if (transitionStage === 'fade-out') {
          setTransitionStage('fade-in')
          setDisplayLocation(location)
        }
      }}
    >
      {children}
    </div>
  )
}
