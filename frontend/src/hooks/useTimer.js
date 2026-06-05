import { useEffect, useRef, useState } from 'react'

// A second-resolution stopwatch. `resetKey` restarts the count from zero
// whenever it changes (e.g. when a new question is loaded), and `running`
// pauses it (e.g. after an answer is submitted).
export function useTimer(resetKey, running = true) {
  const [seconds, setSeconds] = useState(0)
  const startRef = useRef(0)

  useEffect(() => {
    setSeconds(0)
    startRef.current = performance.now()
  }, [resetKey])

  useEffect(() => {
    if (!running) return undefined
    const id = setInterval(() => {
      setSeconds(Math.floor((performance.now() - startRef.current) / 1000))
    }, 250)
    return () => clearInterval(id)
  }, [running, resetKey])

  return seconds
}

export function formatTime(totalSeconds) {
  const minutes = Math.floor(totalSeconds / 60)
  const seconds = totalSeconds % 60
  return `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`
}
