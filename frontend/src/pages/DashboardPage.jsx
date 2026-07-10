import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { metaApi } from '../api'
import { STATUS_LABEL, langLabel } from '../constants'

export default function DashboardPage() {
  const [stats, setStats] = useState(null)
  const nav = useNavigate()

  useEffect(() => {
    metaApi.stats().then(({ data }) => setStats(data)).catch(() => {})
  }, [])

  if (!stats) {
    return <div className="loading-full"><div className="spinner" style={{ width: 32, height: 32 }} /></div>
  }

  const cards = [
    { icon: '📚', value: stats.total_books, label: 'books in catalog' },
    { icon: '✍️', value: stats.total_authors, label: 'authors' },
    { icon: '✅', value: stats.by_status?.available || 0, label: 'available' },
    { icon: '📖', value: stats.loans_active || 0, label: 'on loan' },
  ]

  const locations = Object.entries(stats.by_location || {}).sort((a, b) => b[1] - a[1])
  const languages = Object.entries(stats.by_language || {}).sort((a, b) => b[1] - a[1])
  const categories = Object.entries(stats.by_category || {}).sort((a, b) => b[1] - a[1])
  const decades = Object.entries(stats.by_decade || {})

  return (
    <div>
      <div className="stats-grid">
        {cards.map(c => (
          <div className="stat-card" key={c.label}>
            <div className="stat-icon">{c.icon}</div>
            <div className="stat-value">{c.value}</div>
            <div className="stat-label">{c.label}</div>
          </div>
        ))}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: 16 }}>
        <div className="card" style={{ padding: 20 }}>
          <h3 style={{ fontFamily: 'var(--font-display)', fontSize: 17, marginBottom: 12 }}>By location</h3>
          {locations.length === 0 && <p style={{ fontSize: 14, color: 'var(--ink-3)' }}>No locations yet.</p>}
          {locations.map(([loc, count]) => (
            <div key={loc} style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0', borderBottom: '1px solid var(--paper-2)', fontSize: 14 }}>
              <span>📍 {loc}</span>
              <strong>{count}</strong>
            </div>
          ))}
        </div>
        <div className="card" style={{ padding: 20 }}>
          <h3 style={{ fontFamily: 'var(--font-display)', fontSize: 17, marginBottom: 12 }}>By language</h3>
          {languages.length === 0 && <p style={{ fontSize: 14, color: 'var(--ink-3)' }}>No books yet.</p>}
          {languages.map(([lang, count]) => (
            <div key={lang} style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0', borderBottom: '1px solid var(--paper-2)', fontSize: 14 }}>
              <span>{langLabel(lang)}</span>
              <strong>{count}</strong>
            </div>
          ))}
        </div>
        <div className="card" style={{ padding: 20 }}>
          <h3 style={{ fontFamily: 'var(--font-display)', fontSize: 17, marginBottom: 12 }}>By category</h3>
          {categories.length === 0 && <p style={{ fontSize: 14, color: 'var(--ink-3)' }}>No categorized books yet.</p>}
          {categories.map(([cat, count]) => (
            <div key={cat} style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0', borderBottom: '1px solid var(--paper-2)', fontSize: 14 }}>
              <span>{cat}</span>
              <strong>{count}</strong>
            </div>
          ))}
        </div>
        <div className="card" style={{ padding: 20 }}>
          <h3 style={{ fontFamily: 'var(--font-display)', fontSize: 17, marginBottom: 12 }}>Top authors</h3>
          {(stats.top_authors || []).length === 0 && <p style={{ fontSize: 14, color: 'var(--ink-3)' }}>No authors yet.</p>}
          {(stats.top_authors || []).map(a => (
            <div key={a.name} style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0', borderBottom: '1px solid var(--paper-2)', fontSize: 14 }}>
              <span>{a.name}</span>
              <strong>{a.count}</strong>
            </div>
          ))}
        </div>
        <div className="card" style={{ padding: 20 }}>
          <h3 style={{ fontFamily: 'var(--font-display)', fontSize: 17, marginBottom: 12 }}>By decade</h3>
          {decades.length === 0 && <p style={{ fontSize: 14, color: 'var(--ink-3)' }}>No publication years yet.</p>}
          {decades.map(([dec, count]) => (
            <div key={dec} style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0', borderBottom: '1px solid var(--paper-2)', fontSize: 14 }}>
              <span>{dec}</span>
              <strong>{count}</strong>
            </div>
          ))}
        </div>
        <div className="card" style={{ padding: 20 }}>
          <h3 style={{ fontFamily: 'var(--font-display)', fontSize: 17, marginBottom: 12 }}>By status</h3>
          {Object.entries(stats.by_status || {}).map(([status, count]) => (
            <div key={status} style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0', borderBottom: '1px solid var(--paper-2)', fontSize: 14 }}>
              <span>{STATUS_LABEL[status] || status}</span>
              <strong>{count}</strong>
            </div>
          ))}
        </div>
      </div>

      <div style={{ marginTop: 24 }}>
        <button className="btn btn-primary btn-lg" onClick={() => nav('/books')}>
          📚 Open catalog
        </button>
      </div>
    </div>
  )
}
