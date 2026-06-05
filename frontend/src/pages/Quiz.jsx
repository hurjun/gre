import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api } from '../api'
import { SUBGROUP_BY_KEY } from '../constants'
import { useTimer } from '../hooks/useTimer'
import Timer from '../components/Timer.jsx'
import LevelMeter from '../components/LevelMeter.jsx'
import StateMessage from '../components/StateMessage.jsx'

export default function Quiz() {
  const { subgroup } = useParams()
  const meta = SUBGROUP_BY_KEY[subgroup]

  const [data, setData] = useState(null) // { question, current_level, exhausted, ... }
  const [error, setError] = useState(null)
  const [selected, setSelected] = useState([])
  const [result, setResult] = useState(null) // grading response, or null while answering
  const [loadKey, setLoadKey] = useState(0)

  const question = data?.question ?? null
  const answering = question != null && result == null
  const elapsed = useTimer(question?.id ?? loadKey, answering)

  const loadNext = useCallback(() => {
    setData(null)
    setError(null)
    setResult(null)
    setSelected([])
    api
      .nextQuestion(subgroup)
      .then((next) => {
        setData(next)
        setLoadKey((k) => k + 1)
      })
      .catch((err) => setError(err.message))
  }, [subgroup])

  useEffect(() => {
    if (meta) loadNext()
  }, [meta, loadNext])

  const needed = question?.select_count ?? 1
  const isMulti = needed > 1

  const toggleChoice = (index) => {
    if (result) return
    setSelected((current) => {
      if (current.includes(index)) return current.filter((i) => i !== index)
      if (isMulti) {
        const next = [...current, index]
        // keep only the most recent `needed` selections
        return next.slice(-needed)
      }
      return [index]
    })
  }

  const submit = () => {
    api
      .submitAnswer({
        question_id: question.id,
        selected,
        elapsed_seconds: elapsed,
      })
      .then(setResult)
      .catch((err) => setError(err.message))
  }

  const correctSet = useMemo(
    () => new Set(result?.correct_answer ?? []),
    [result],
  )

  if (!meta) {
    return (
      <StateMessage kind="error" title="Unknown section">
        <Link to="/">Back to dashboard</Link>
      </StateMessage>
    )
  }
  if (error) {
    return (
      <StateMessage kind="error" title="Something went wrong">
        {error} · <button className="link-btn" onClick={loadNext}>Try again</button>
      </StateMessage>
    )
  }
  if (!data) {
    return <StateMessage kind="loading" title="Loading question…" />
  }

  if (data.exhausted || !question) {
    return (
      <section className="quiz">
        <QuizHeader meta={meta} level={data.current_level} maxLevel={data.max_level} elapsed={elapsed} running={false} />
        <StateMessage kind="success" title="🎉 You've solved every question in this section!">
          Come back after adding more questions, or keep practicing another section.
          <div className="state__actions">
            <Link to="/" className="btn">Back to dashboard</Link>
          </div>
        </StateMessage>
      </section>
    )
  }

  return (
    <section className="quiz">
      <QuizHeader meta={meta} level={data.current_level} maxLevel={data.max_level} elapsed={elapsed} running={answering} />

      <p className="quiz__hint">
        {data.remaining_at_level} unsolved at level {data.current_level} ·{' '}
        {isMulti ? `Select exactly ${needed}` : 'Select one'}
      </p>

      {question.passage && <blockquote className="passage">{question.passage}</blockquote>}

      <h2 className="quiz__question">{question.question_text}</h2>

      <ul className="choices">
        {question.choices.map((choice, index) => {
          const chosen = selected.includes(index)
          const isCorrect = correctSet.has(index)
          let cls = 'choice'
          if (result) {
            if (isCorrect) cls += ' choice--correct'
            else if (chosen) cls += ' choice--wrong'
          } else if (chosen) {
            cls += ' choice--selected'
          }
          return (
            <li key={index}>
              <button className={cls} onClick={() => toggleChoice(index)} disabled={!!result}>
                <span className="choice__mark">{isMulti ? '◻' : '○'}</span>
                <span className="choice__text">{choice}</span>
              </button>
            </li>
          )
        })}
      </ul>

      {!result ? (
        <button
          className="btn btn--primary"
          disabled={selected.length !== needed}
          onClick={submit}
        >
          Submit answer
        </button>
      ) : (
        <Feedback result={result} onNext={loadNext} />
      )}
    </section>
  )
}

function QuizHeader({ meta, level, maxLevel, elapsed, running }) {
  return (
    <header className="quiz__head">
      <div>
        <Link to="/" className="back-link">← Dashboard</Link>
        <h1 className="quiz__title">{meta.label}</h1>
      </div>
      <div className="quiz__meters">
        <LevelMeter level={level} max={maxLevel} />
        <Timer seconds={elapsed} warnAfter={running ? 90 : null} />
      </div>
    </header>
  )
}

function Feedback({ result, onNext }) {
  const leveledUp = result.new_level > result.previous_level
  const leveledDown = result.new_level < result.previous_level
  return (
    <div className={`feedback feedback--${result.correct ? 'correct' : 'wrong'}`}>
      <div className="feedback__head">
        <span className="feedback__badge">
          {result.correct ? '정답입니다! Correct' : '오답입니다 Incorrect'}
        </span>
        <span className="feedback__level">
          {leveledUp && `레벨 업 → Level ${result.new_level}`}
          {leveledDown && `레벨 다운 → Level ${result.new_level}`}
          {!leveledUp && !leveledDown && `Level ${result.new_level}`}
        </span>
      </div>
      <div className="feedback__explanation">
        <h3>해설</h3>
        <p>{result.explanation_ko}</p>
      </div>
      <button className="btn btn--primary" onClick={onNext}>
        Next question →
      </button>
    </div>
  )
}
