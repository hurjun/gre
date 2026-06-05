import { useEffect, useMemo, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { api } from '../api'
import { useTimer } from '../hooks/useTimer'
import Timer from '../components/Timer.jsx'
import StateMessage from '../components/StateMessage.jsx'

const TASK_LABEL = { issue: 'Issue Task', argument: 'Argument Task' }

export default function Writing() {
  const { promptId } = useParams()
  return promptId ? <EssayWorkspace promptId={Number(promptId)} /> : <PromptList />
}

function PromptList() {
  const [prompts, setPrompts] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    api.writingPrompts().then(setPrompts).catch((err) => setError(err.message))
  }, [])

  if (error) return <StateMessage kind="error" title="Could not load prompts">{error}</StateMessage>
  if (!prompts) return <StateMessage kind="loading" title="Loading prompts…" />

  return (
    <section>
      <div className="page-head">
        <h1>Analytical Writing</h1>
        <p className="page-head__sub">
          Pick a prompt, write under the timer, then reveal the model answer and
          grade yourself on the 0–6 scale.
        </p>
      </div>
      {prompts.length === 0 ? (
        <StateMessage kind="info" title="No prompts yet">
          Seed the database to add Issue and Argument prompts.
        </StateMessage>
      ) : (
        <div className="card-grid">
          {prompts.map((prompt) => (
            <article key={prompt.id} className="card">
              <span className="card__tag">{TASK_LABEL[prompt.task_type]}</span>
              <p className="card__desc card__desc--clamp">{prompt.prompt_text}</p>
              <p className="card__stat">
                {prompt.suggested_minutes} min · {prompt.essay_count} written
              </p>
              <Link to={`/writing/${prompt.id}`} className="btn">
                Start writing
              </Link>
            </article>
          ))}
        </div>
      )}
    </section>
  )
}

function EssayWorkspace({ promptId }) {
  const navigate = useNavigate()
  const [prompt, setPrompt] = useState(null)
  const [error, setError] = useState(null)
  const [essay, setEssay] = useState('')
  const [revealed, setRevealed] = useState(false)
  const [grade, setGrade] = useState(4)
  const [saved, setSaved] = useState(false)

  const running = !saved
  // Count down from the prompt's suggested time budget.
  const durationSeconds = prompt ? prompt.suggested_minutes * 60 : null
  const { elapsed, remaining } = useTimer(promptId, running, durationSeconds)

  useEffect(() => {
    api.writingPrompt(promptId).then(setPrompt).catch((err) => setError(err.message))
  }, [promptId])

  const words = useMemo(
    () => (essay.trim() ? essay.trim().split(/\s+/).length : 0),
    [essay],
  )

  const save = () => {
    api
      .submitEssay({
        prompt_id: promptId,
        essay_text: essay,
        self_grade: grade,
        elapsed_seconds: elapsed,
      })
      .then(() => setSaved(true))
      .catch((err) => setError(err.message))
  }

  if (error) return <StateMessage kind="error" title="Something went wrong">{error}</StateMessage>
  if (!prompt) return <StateMessage kind="loading" title="Loading prompt…" />

  return (
    <section className="writing">
      <header className="quiz__head">
        <div>
          <Link to="/writing" className="back-link">← All prompts</Link>
          <h1 className="quiz__title">{TASK_LABEL[prompt.task_type]}</h1>
        </div>
        <Timer seconds={remaining ?? durationSeconds} warn={running && remaining != null && remaining <= 60} />
      </header>

      <blockquote className="passage">{prompt.prompt_text}</blockquote>

      <textarea
        className="essay-input"
        placeholder="Write your response here…"
        value={essay}
        onChange={(e) => setEssay(e.target.value)}
        disabled={saved}
        rows={14}
      />
      <p className="essay-meta">
        {words} words · suggested {prompt.suggested_minutes} minutes
      </p>

      {!revealed ? (
        <button
          className="btn"
          disabled={words === 0}
          onClick={() => setRevealed(true)}
        >
          Reveal model answer & self-grade
        </button>
      ) : (
        <>
          <div className="model-answer">
            <h3>Model answer (6.0)</h3>
            <p>{prompt.model_answer}</p>
          </div>

          {!saved ? (
            <div className="grader">
              <label className="grader__label">
                Your self-grade: <strong>{grade.toFixed(1)}</strong> / 6
              </label>
              <input
                type="range"
                min="0"
                max="6"
                step="0.5"
                value={grade}
                onChange={(e) => setGrade(Number(e.target.value))}
                className="grader__slider"
              />
              <button className="btn btn--primary" onClick={save}>
                Save essay & grade
              </button>
            </div>
          ) : (
            <StateMessage kind="success" title={`Saved — you scored yourself ${grade.toFixed(1)} / 6`}>
              <div className="state__actions">
                <button className="btn" onClick={() => navigate('/writing')}>
                  Back to prompts
                </button>
              </div>
            </StateMessage>
          )}
        </>
      )}
    </section>
  )
}
