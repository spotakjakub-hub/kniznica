import { useEffect, useState, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { booksApi, categoriesApi, metaApi, loansApi } from '../api'
import BookFormModal from '../components/BookFormModal'
import toast from 'react-hot-toast'
import { STATUS_LABEL, STATUS_BADGE, ROLE_LABEL, CONDITION_LABEL, langLabel } from '../constants'

function LendingCard({ book, onChanged }) {
  const [borrower, setBorrower] = useState('')
  const [busy, setBusy] = useState(false)
  const loan = book.active_loan
  const history = (book.loans || []).filter(l => l.returned_at)

  const fmt = (iso) => iso ? new Date(iso).toLocaleDateString() : ''

  const lend = async (e) => {
    e.preventDefault()
    if (!borrower.trim()) return
    setBusy(true)
    try {
      await loansApi.lend(book.id, borrower.trim())
      setBorrower('')
      toast.success('Marked as lent')
      onChanged()
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to lend')
    } finally {
      setBusy(false)
    }
  }

  const giveBack = async () => {
    setBusy(true)
    try {
      await loansApi.return(loan.id)
      toast.success('Marked as returned')
      onChanged()
    } catch {
      toast.error('Failed to return')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="card" style={{ padding: 20, marginBottom: 16 }}>
      <h3 style={{ fontFamily: 'var(--font-display)', fontSize: 17, marginBottom: 10 }}>Lending</h3>
      {loan ? (
        <div style={{ display: 'flex', gap: 12, alignItems: 'center', flexWrap: 'wrap' }}>
          <span className="badge badge-missing">On loan</span>
          <span style={{ fontSize: 14 }}>
            Lent to <strong>{loan.borrower}</strong> since {fmt(loan.loaned_at)}
          </span>
          <button className="btn btn-secondary btn-sm" disabled={busy} onClick={giveBack}>
            ↩ Mark as returned
          </button>
        </div>
      ) : (
        <form onSubmit={lend} style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          <input className="form-control" style={{ maxWidth: 260 }}
            placeholder="Who is borrowing it?"
            value={borrower} onChange={e => setBorrower(e.target.value)} />
          <button className="btn btn-secondary" disabled={busy || !borrower.trim()}>📖 Lend</button>
        </form>
      )}
      {history.length > 0 && (
        <div style={{ marginTop: 12, fontSize: 13, color: 'var(--ink-3)' }}>
          {history.map(l => (
            <div key={l.id}>↩ {l.borrower}: {fmt(l.loaned_at)} → {fmt(l.returned_at)}</div>
          ))}
        </div>
      )}
    </div>
  )
}

export default function BookDetailPage() {
  const { id } = useParams()
  const nav = useNavigate()
  const [book, setBook] = useState(null)
  const [categories, setCategories] = useState([])
  const [locations, setLocations] = useState([])
  const [loading, setLoading] = useState(true)
  const [editing, setEditing] = useState(false)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const { data } = await booksApi.get(id)
      setBook(data)
    } catch {
      toast.error('Book not found')
      nav('/books')
    } finally {
      setLoading(false)
    }
  }, [id, nav])

  const loadMeta = useCallback(() => {
    categoriesApi.list().then(({ data }) => setCategories(data)).catch(() => {})
    metaApi.locations().then(({ data }) => setLocations(data)).catch(() => {})
  }, [])

  useEffect(() => { load() }, [load])
  useEffect(() => { loadMeta() }, [loadMeta])

  const remove = async () => {
    if (!window.confirm(`Really delete “${book.title}”?`)) return
    try {
      await booksApi.delete(id)
      toast.success('Book deleted')
      nav('/books')
    } catch {
      toast.error('Delete failed')
    }
  }

  if (loading || !book) {
    return <div className="loading-full"><div className="spinner" style={{ width: 32, height: 32 }} /></div>
  }

  const meta = [
    ['Publisher', book.publisher],
    ['Year published', book.published_year],
    ['Language', book.language && langLabel(book.language)],
    ['Pages', book.pages],
    ['Edition', book.edition],
    ['ISBN', book.isbn],
    ['ISBN-13', book.isbn13],
    ['Category', book.category?.name],
    ['Location', book.location],
    ['Condition', book.condition && (CONDITION_LABEL[book.condition] || book.condition)],
  ].filter(([, v]) => v)

  return (
    <div>
      <div style={{ display: 'flex', gap: 10, marginBottom: 20, flexWrap: 'wrap' }}>
        <button className="btn btn-ghost" onClick={() => nav('/books')}>← Back to catalog</button>
        <div style={{ marginLeft: 'auto', display: 'flex', gap: 8 }}>
          <button className="btn btn-secondary" onClick={() => setEditing(true)}>✏️ Edit</button>
          <button className="btn btn-danger" onClick={remove}>🗑 Delete</button>
        </div>
      </div>

      <div className="book-detail-header">
        <div className="book-detail-cover">
          {book.cover_image_url
            ? <img src={book.cover_image_url} alt={book.title} />
            : <div className="book-card-cover-placeholder">{book.title[0]}</div>}
        </div>
        <div className="book-detail-meta" style={{ flex: 1 }}>
          <h1>{book.title}</h1>
          {book.subtitle && <p style={{ fontSize: 16, color: 'var(--ink-2)', marginBottom: 8 }}>{book.subtitle}</p>}
          {book.authors?.length > 0 && (
            <div className="authors">
              {book.authors.map((a, i) => (
                <span key={`${a.id}-${a.role}`}>
                  {i > 0 && ', '}
                  {a.name}{a.role !== 'author' && ` (${ROLE_LABEL[a.role] || a.role})`}
                </span>
              ))}
            </div>
          )}
          <div style={{ marginBottom: 16 }}>
            <span className={`badge ${STATUS_BADGE[book.status]}`}>{STATUS_LABEL[book.status]}</span>
            {book.tags?.map(t => (
              <span key={t.id} className="badge" style={{ background: 'var(--paper-2)', color: 'var(--ink-3)', marginLeft: 6 }}>
                #{t.name}
              </span>
            ))}
          </div>
          <div className="meta-grid">
            {meta.map(([label, value]) => (
              <div className="meta-item" key={label}>
                <label>{label}</label>
                <span>{value}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <LendingCard book={book} onChanged={load} />

      {book.description && (
        <div className="card" style={{ padding: 20, marginBottom: 16 }}>
          <h3 style={{ fontFamily: 'var(--font-display)', fontSize: 17, marginBottom: 8 }}>Description</h3>
          <p className="book-description">{book.description}</p>
        </div>
      )}
      {book.notes && (
        <div className="card" style={{ padding: 20 }}>
          <h3 style={{ fontFamily: 'var(--font-display)', fontSize: 17, marginBottom: 8 }}>Notes</h3>
          <p className="book-description">{book.notes}</p>
        </div>
      )}

      {editing && (
        <BookFormModal
          book={book}
          categories={categories}
          locations={locations}
          onClose={() => setEditing(false)}
          onSaved={() => { setEditing(false); load(); loadMeta(); toast.success('Changes saved!') }}
        />
      )}
    </div>
  )
}
