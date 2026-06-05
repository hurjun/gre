import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api'
import { SUBGROUPS } from '../constants'
import LevelMeter from '../components/LevelMeter.jsx'
import StateMessage from '../components/StateMessage.jsx'

export default function Home() {
  const [progress, setProgress] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    api
      .progress()
      .then((data) => setProgress(data.subgroups))
      .catch((err) => setError(err.message))
  }, [])

  if (error) {
    return (
      <StateMessage kind="error" title="Could not load progress">
        {error}. Is the backend running on port 8000?
      </StateMessage>
    )
  }
  if (!progress) {
    return <StateMessage kind="loading" title="Loading your progress…" />
  }

  const byKey = Object.fromEntries(progress.map((p) => [p.subgroup, p]))

  return (
    <section>
      <div className="page-head">
        <h1>Your study dashboard</h1>
        <p className="page-head__sub">
          Each section adapts to you: answer correctly to climb toward level 5,
          miss one to step back down with a Korean explanation.
        </p>
      </div>

      <h2 className="group-title">Adaptive practice</h2>
      <div className="card-grid">
        {SUBGROUPS.map((subgroup) => {
          const stat = byKey[subgroup.key] ?? { current_level: 1, solved: 0, total: 0 }
          const done = stat.total > 0 && stat.solved >= stat.total
          const pct = stat.total ? Math.round((stat.solved / stat.total) * 100) : 0
          return (
            <article key={subgroup.key} className="card">
              <span className="card__tag">{subgroup.group}</span>
              <h3 className="card__title">{subgroup.label}</h3>
              <LevelMeter level={stat.current_level} />
              <div className="progress-bar" aria-hidden="true">
                <span className="progress-bar__fill" style={{ width: `${pct}%` }} />
              </div>
              <p className="card__stat">
                {stat.solved} / {stat.total} solved · {pct}%
              </p>
              <Link
                to={`/quiz/${subgroup.key}`}
                className={`btn${done ? ' btn--ghost' : ''}`}
              >
                {done ? 'Review complete' : stat.solved ? 'Continue' : 'Start'}
              </Link>
            </article>
          )
        })}
      </div>

      <h2 className="group-title">Analytical Writing</h2>
      <div className="card-grid">
        <article className="card">
          <span className="card__tag">Writing</span>
          <h3 className="card__title">Issue & Argument essays</h3>
          <p className="card__desc">
            Timed essay prompts with model answers. Write your response, then
            self-grade it against the model on the 0–6 scale.
          </p>
          <Link to="/writing" className="btn">
            Open writing practice
          </Link>
        </article>
      </div>

      <p className="footnote">
        Solved questions are never shown again; missed ones return later.
      </p>
    </section>
  )
}
