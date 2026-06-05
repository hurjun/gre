import { NavLink, Navigate, Route, Routes } from 'react-router-dom'
import Home from './pages/Home.jsx'
import Quiz from './pages/Quiz.jsx'
import Writing from './pages/Writing.jsx'

export default function App() {
  return (
    <div className="app">
      <header className="app__header">
        <NavLink to="/" className="brand">
          GRE<span className="brand__accent">Study</span>
        </NavLink>
        <nav className="app__nav">
          <NavLink to="/" end className={navClass}>
            Dashboard
          </NavLink>
          <NavLink to="/writing" className={navClass}>
            Writing
          </NavLink>
        </nav>
      </header>

      <main className="app__main">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/quiz/:subgroup" element={<Quiz />} />
          <Route path="/writing" element={<Writing />} />
          <Route path="/writing/:promptId" element={<Writing />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>

      <footer className="app__footer">
        Adaptive GRE practice · Verbal · Quantitative · Analytical Writing
      </footer>
    </div>
  )
}

function navClass({ isActive }) {
  return isActive ? 'app__nav-link app__nav-link--active' : 'app__nav-link'
}
