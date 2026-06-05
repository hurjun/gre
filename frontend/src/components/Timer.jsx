import { formatTime } from '../hooks/useTimer'

export default function Timer({ seconds, warnAfter }) {
  const warning = warnAfter != null && seconds >= warnAfter
  return (
    <span className={`timer${warning ? ' timer--warn' : ''}`} role="timer" aria-live="off">
      <svg width="14" height="14" viewBox="0 0 24 24" aria-hidden="true">
        <circle cx="12" cy="13" r="8" fill="none" stroke="currentColor" strokeWidth="2" />
        <path d="M12 13V8" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
        <path d="M9 2h6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
      </svg>
      {formatTime(seconds)}
    </span>
  )
}
