// Small presentational helper for loading / error / empty states.
export default function StateMessage({ kind = 'info', title, children }) {
  return (
    <div className={`state state--${kind}`}>
      <p className="state__title">{title}</p>
      {children && <div className="state__body">{children}</div>}
    </div>
  )
}
