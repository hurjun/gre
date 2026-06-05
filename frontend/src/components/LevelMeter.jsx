import { DEFAULT_MAX_LEVEL } from '../constants'

// Pips showing the current adaptive level for a subgroup. The number of pips
// follows the section's own ceiling (5 for verbal/math, 10 for the Word Test).
export default function LevelMeter({ level, max = DEFAULT_MAX_LEVEL }) {
  return (
    <span className="level-meter" title={`Level ${level} of ${max}`}>
      {Array.from({ length: max }, (_, i) => (
        <span key={i} className={`pip${i < level ? ' pip--on' : ''}`} />
      ))}
      <span className="level-meter__label">
        Lv {level}/{max}
      </span>
    </span>
  )
}
