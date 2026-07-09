import { useEffect, useState, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { booksApi, categoriesApi, metaApi } from '../api'
import BookFormModal from '../components/BookFormModal'
import toast from 'react-hot-toast'
import { STATUS_LABEL, STATUS_BADGE, ROLE_LABEL, langLabel } from '../constants'

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
      toast.error('Kniha nenájdená')
      nav('/books')
    } finally {
      setLoading(false)
    }
  }, [id, nav])

  useEffect(() => { load() }, [load])
  useEffect(() => {
    categoriesApi.list().then(({ data }) => setCategories(data)).catch(() => {})
    metaApi.locations().then(({ data }) => setLocations(data)).catch(() => {})
  }, [])

  const remove = async () => {
    if (!window.confirm(`Naozaj vymazať knihu „${book.title}“?`)) return
    try {
      await booksApi.delete(id)
      toast.success('Kniha vymazaná')
      nav('/books')
    } catch {
      toast.error('Vymazanie zlyhalo')
    }
  }

  if (loading || !book) {
    return <div className="loading-full"><div className="spinner" style={{ width: 32, height: 32 }} /></div>
  }

  const meta = [
    ['Vydavateľ', book.publisher],
    ['Rok vydania', book.published_year],
    ['Jazyk', book.language && langLabel(book.language)],
    ['Počet strán', book.pages],
    ['Edícia', book.edition],
    ['ISBN', book.isbn],
    ['ISBN-13', book.isbn13],
    ['Kategória', book.category?.name],
    ['Umiestnenie', book.location],
    ['Fyzický stav', book.condition],
  ].filter(([, v]) => v)

  return (
    <div>
      <div style={{ display: 'flex', gap: 10, marginBottom: 20, flexWrap: 'wrap' }}>
        <button className="btn btn-ghost" onClick={() => nav('/books')}>← Späť na katalóg</button>
        <div style={{ marginLeft: 'auto', display: 'flex', gap: 8 }}>
          <button className="btn btn-secondary" onClick={() => setEditing(true)}>✏️ Upraviť</button>
          <button className="btn btn-danger" onClick={remove}>🗑 Vymazať</button>
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

      {book.description && (
        <div className="card" style={{ padding: 20, marginBottom: 16 }}>
          <h3 style={{ fontFamily: 'var(--font-display)', fontSize: 17, marginBottom: 8 }}>Popis</h3>
          <p className="book-description">{book.description}</p>
        </div>
      )}
      {book.notes && (
        <div className="card" style={{ padding: 20 }}>
          <h3 style={{ fontFamily: 'var(--font-display)', fontSize: 17, marginBottom: 8 }}>Poznámky</h3>
          <p className="book-description">{book.notes}</p>
        </div>
      )}

      {editing && (
        <BookFormModal
          book={book}
          categories={categories}
          locations={locations}
          onClose={() => setEditing(false)}
          onSaved={() => { setEditing(false); load(); toast.success('Zmeny uložené!') }}
        />
      )}
    </div>
  )
}
