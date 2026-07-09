import { BrowserRouter, Routes, Route, Navigate, NavLink } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import DashboardPage from './pages/DashboardPage'
import BooksPage from './pages/BooksPage'
import BookDetailPage from './pages/BookDetailPage'

const NAV_ITEMS = [
  { to: '/', icon: '🏠', label: 'Overview', end: true },
  { to: '/books', icon: '📚', label: 'Books' },
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
  return (
    <BrowserRouter>
      <Toaster position="top-center" toastOptions={{ style: { fontFamily: 'var(--font-body)', fontSize: 14 } }} />
      <Routes>
        <Route path="/" element={<Layout title="Overview"><DashboardPage /></Layout>} />
        <Route path="/books" element={<Layout title="Books"><BooksPage /></Layout>} />
        <Route path="/books/:id" element={<Layout title="Book detail"><BookDetailPage /></Layout>} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
