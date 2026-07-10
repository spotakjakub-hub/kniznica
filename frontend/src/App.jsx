import { BrowserRouter, Routes, Route, Navigate, NavLink } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import { useEffect, useState } from 'react'
import { authApi } from './api'
import DashboardPage from './pages/DashboardPage'
import BooksPage from './pages/BooksPage'
import BookDetailPage from './pages/BookDetailPage'
import ReviewPage from './pages/ReviewPage'

function LoginGate({ onUnlocked }) {
  const [password, setPassword] = useState('')
  const [error, setError] = useState(false)
  const [busy, setBusy] = useState(false)

  const submit = async (e) => {
    e.preventDefault()
    setBusy(true)
    setError(false)
    try {
      const { data } = await authApi.check(password)
      if (data.ok) {
        localStorage.setItem('library_key', password)
        onUnlocked()
      } else {
        setError(true)
      }
    } catch {
      setError(true)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="login-page">
      <div className="login-box">
        <div className="login-logo">
          <h1>Lib<span>rary</span></h1>
          <p>Enter the shared family password</p>
        </div>
        <form onSubmit={submit}>
          <div className="form-group">
            <input className="form-control" type="password" autoFocus
              placeholder="Password" value={password}
              onChange={e => setPassword(e.target.value)} />
          </div>
          {error && <p style={{ color: 'var(--red)', fontSize: 13, marginBottom: 12 }}>Wrong password, try again.</p>}
          <button className="btn btn-primary btn-lg" style={{ width: '100%' }} disabled={busy}>
            {busy ? 'Checking…' : 'Unlock'}
          </button>
        </form>
      </div>
    </div>
  )
}

const NAV_ITEMS = [
  { to: '/', icon: '🏠', label: 'Overview', end: true },
  { to: '/books', icon: '📚', label: 'Books' },
  { to: '/review', icon: '🧺', label: 'Review' },
]

function Layout({ children, title }) {
  return (
    <div className="layout">
      <aside className="sidebar">
        <div className="sidebar-logo">
          <h1>Lib<span>rary</span></h1>
        </div>
        <nav>
          {NAV_ITEMS.map(({ to, icon, label, end }) => (
            <NavLink key={to} to={to} end={end}
              className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
              <span className="nav-icon">{icon}</span>
              {label}
            </NavLink>
          ))}
        </nav>
      </aside>
      <div className="main-area">
        <header className="topbar">
          <h2>{title}</h2>
        </header>
        <main className="page-content">
          {children}
        </main>
      </div>
      <nav className="mobile-nav">
        {NAV_ITEMS.map(({ to, icon, label, end }) => (
          <NavLink key={to} to={to} end={end}
            className={({ isActive }) => (isActive ? 'active' : '')}>
            <span className="nav-icon">{icon}</span>
            {label}
          </NavLink>
        ))}
      </nav>
    </div>
  )
}

export default function App() {
  const [locked, setLocked] = useState(false)

  useEffect(() => {
    const onUnauthorized = () => setLocked(true)
    window.addEventListener('library-unauthorized', onUnauthorized)
    return () => window.removeEventListener('library-unauthorized', onUnauthorized)
  }, [])

  if (locked) {
    return <LoginGate onUnlocked={() => { setLocked(false); window.location.reload() }} />
  }

  return (
    <BrowserRouter>
      <Toaster position="top-center" toastOptions={{ style: { fontFamily: 'var(--font-body)', fontSize: 14 } }} />
      <Routes>
        <Route path="/" element={<Layout title="Overview"><DashboardPage /></Layout>} />
        <Route path="/books" element={<Layout title="Books"><BooksPage /></Layout>} />
        <Route path="/books/:id" element={<Layout title="Book detail"><BookDetailPage /></Layout>} />
        <Route path="/review" element={<Layout title="Batch review"><ReviewPage /></Layout>} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
