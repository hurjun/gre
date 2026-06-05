import { formatTime } from '../hooks/useTimer'

// Displays a time value (mm:ss). Set `warn` to render it in the warning color —
// used when a countdown is running low or a target pace is exceeded.
export default function Timer({ seconds, warn = false, label }) {
  return (
    <span className={`timer${warn ? ' timer--warn' : ''}`} role="timer" aria-live="off">
      <svg width="14" height="14" viewBox="0 0 24 24" aria-hidden="true">
        <circle cx="12" cy="13" r="8" fill="none" stroke="currentColor" strokeWidth="2" />
        <path d="M12 13V8" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
        <path d="M9 2h6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
      </svg>
      {label && <span className="timer__label">{label}</span>}
      {formatTime(seconds)}
    </span>
  )
}
