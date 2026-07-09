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
    { icon: '📚', value: stats.total_books, label: 'kníh v katalógu' },
    { icon: '✍️', value: stats.total_authors, label: 'autorov' },
    { icon: '🏷️', value: stats.total_categories, label: 'kategórií' },
    { icon: '✅', value: stats.by_status?.available || 0, label: 'dostupných' },
  ]

  const locations = Object.entries(stats.by_location || {}).sort((a, b) => b[1] - a[1])
  const languages = Object.entries(stats.by_language || {}).sort((a, b) => b[1] - a[1])

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
          <h3 style={{ fontFamily: 'var(--font-display)', fontSize: 17, marginBottom: 12 }}>Podľa umiestnenia</h3>
          {locations.length === 0 && <p style={{ fontSize: 14, color: 'var(--ink-3)' }}>Zatiaľ žiadne umiestnenia.</p>}
          {locations.map(([loc, count]) => (
            <div key={loc} style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0', borderBottom: '1px solid var(--paper-2)', fontSize: 14 }}>
              <span>📍 {loc}</span>
              <strong>{count}</strong>
            </div>
          ))}
        </div>
        <div className="card" style={{ padding: 20 }}>
          <h3 style={{ fontFamily: 'var(--font-display)', fontSize: 17, marginBottom: 12 }}>Podľa jazyka</h3>
          {languages.length === 0 && <p style={{ fontSize: 14, color: 'var(--ink-3)' }}>Zatiaľ žiadne knihy.</p>}
          {languages.map(([lang, count]) => (
            <div key={lang} style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0', borderBottom: '1px solid var(--paper-2)', fontSize: 14 }}>
              <span>{langLabel(lang)}</span>
              <strong>{count}</strong>
            </div>
          ))}
        </div>
        <div className="card" style={{ padding: 20 }}>
          <h3 style={{ fontFamily: 'var(--font-display)', fontSize: 17, marginBottom: 12 }}>Podľa stavu</h3>
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
          📚 Otvoriť katalóg
        </button>
      </div>
    </div>
  )
}
