import { useEffect, useRef, useState } from 'react'

// A second-resolution stopwatch. `resetKey` restarts the count from zero
// whenever it changes (e.g. when a new question is loaded), and `running`
// pauses it (e.g. after an answer is submitted).
//
// Returns both the elapsed time (counting up, used for recording how long an
// answer took) and — when `durationSeconds` is given — the remaining time
// counting down from that duration (used to display a countdown timer).
export function useTimer(resetKey, running = true, durationSeconds = null) {
  const [elapsed, setElapsed] = useState(0)
  const startRef = useRef(0)

  useEffect(() => {
    setElapsed(0)
    startRef.current = performance.now()
  }, [resetKey])

  useEffect(() => {
    if (!running) return undefined
    const id = setInterval(() => {
      setElapsed(Math.floor((performance.now() - startRef.current) / 1000))
    }, 250)
    return () => clearInterval(id)
  }, [running, resetKey])

  const remaining =
    durationSeconds == null ? null : Math.max(0, durationSeconds - elapsed)

  return { elapsed, remaining, expired: remaining === 0 }
}

export function formatTime(totalSeconds) {
  const minutes = Math.floor(totalSeconds / 60)
  const seconds = totalSeconds % 60
  return `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`
}
