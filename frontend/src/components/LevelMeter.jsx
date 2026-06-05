import { MAX_LEVEL } from '../constants'

// Five pips showing the current adaptive level for a subgroup.
export default function LevelMeter({ level }) {
  return (
    <span className="level-meter" title={`Level ${level} of ${MAX_LEVEL}`}>
      {Array.from({ length: MAX_LEVEL }, (_, i) => (
        <span key={i} className={`pip${i < level ? ' pip--on' : ''}`} />
      ))}
      <span className="level-meter__label">Lv {level}</span>
    </span>
  )
}
