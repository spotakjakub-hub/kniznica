import { useEffect, useState, useCallback, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { booksApi, categoriesApi, metaApi, exportApi } from '../api'
import BookFormModal from '../components/BookFormModal'
import ScanModal from '../components/ScanModal'
import toast from 'react-hot-toast'
import { STATUS_LABEL, STATUS_BADGE, LANGUAGES, langLabel, authorNames } from '../constants'

const PAGE_SIZE = 60

export default function BooksPage() {
  const [books, setBooks] = useState([])
  const [total, setTotal] = useState(0)
  const [categories, setCategories] = useState([])
  const [locations, setLocations] = useState([])
  const [languages, setLanguages] = useState([])
  const [loading, setLoading] = useState(true)
  const [q, setQ] = useState('')
  const [catFilter, setCatFilter] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [langFilter, setLangFilter] = useState('')
  const [locFilter, setLocFilter] = useState('')
  const [page, setPage] = useState(0)
  const [showForm, setShowForm] = useState(false)
  const [showScan, setShowScan] = useState(false)
  const [prefill, setPrefill] = useState(null)
  const nav = useNavigate()
  const debounceRef = useRef(null)
  const [debouncedQ, setDebouncedQ] = useState('')

  useEffect(() => {
    clearTimeout(debounceRef.current)
    debounceRef.current = setTimeout(() => { setDebouncedQ(q); setPage(0) }, 300)
    return () => clearTimeout(debounceRef.current)
  }, [q])

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const params = { skip: page * PAGE_SIZE, limit: PAGE_SIZE }
      if (debouncedQ) params.q = debouncedQ
      if (catFilter) params.category_id = catFilter
      if (statusFilter) params.status = statusFilter
      if (langFilter) params.language = langFilter
      if (locFilter) params.location = locFilter
      const { data } = await booksApi.list(params)
      setBooks(data.items)
      setTotal(data.total)
    } catch {
      toast.error('Failed to load books')
    } finally {
      setLoading(false)
    }
  }, [debouncedQ, catFilter, statusFilter, langFilter, locFilter, page])

  const loadMeta = useCallback(() => {
    categoriesApi.list().then(({ data }) => setCategories(data)).catch(() => {})
    metaApi.locations().then(({ data }) => setLocations(data)).catch(() => {})
    metaApi.languages().then(({ data }) => setLanguages(data)).catch(() => {})
  }, [])

  useEffect(() => { load() }, [load])
  useEffect(() => { loadMeta() }, [loadMeta])

  const hasFilters = debouncedQ || catFilter || statusFilter || langFilter || locFilter
  const pages = Math.ceil(total / PAGE_SIZE)

  return (
    <div>
      <div style={{ display: 'flex', gap: 10, marginBottom: 16, flexWrap: 'wrap' }}>
        <div className="search-wrap" style={{ flex: 1, minWidth: 200 }}>
          <span className="search-icon">🔍</span>
          <input
            placeholder="Search by title, author, publisher, ISBN…"
            value={q}
            onChange={e => setQ(e.target.value)}
          />
        </div>
        <button className="btn btn-ghost" title="Export catalog to CSV"
          onClick={() => exportApi.downloadCsv().catch(() => toast.error('Export failed'))}>
          ⬇ CSV
        </button>
        <button className="btn btn-secondary" onClick={() => setShowScan(true)}>
          📷 Scan
        </button>
        <button className="btn btn-primary" onClick={() => { setPrefill(null); setShowForm(true) }}>
          + Add book
        </button>
      </div>

      <div className="filters-bar">
        <select value={catFilter} onChange={e => { setCatFilter(e.target.value); setPage(0) }}>
          <option value="">All categories</option>
          {categories.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
        </select>
        <select value={langFilter} onChange={e => { setLangFilter(e.target.value); setPage(0) }}>
          <option value="">All languages</option>
          {(languages.length ? languages : LANGUAGES.map(l => l.code)).map(code => (
            <option key={code} value={code}>{langLabel(code)}</option>
          ))}
        </select>
        <select value={locFilter} onChange={e => { setLocFilter(e.target.value); setPage(0) }}>
          <option value="">All locations</option>
          {locations.map(l => <option key={l} value={l}>{l}</option>)}
        </select>
        <select value={statusFilter} onChange={e => { setStatusFilter(e.target.value); setPage(0) }}>
          <option value="">All statuses</option>
          {Object.entries(STATUS_LABEL).map(([v, l]) => <option key={v} value={v}>{l}</option>)}
        </select>
        <span style={{ fontSize: 13, color: 'var(--ink-4)', marginLeft: 'auto' }}>
          {total} books
        </span>
      </div>

      {loading ? (
        <div className="loading-full"><div className="spinner" style={{ width: 32, height: 32 }} /></div>
      ) : books.length === 0 ? (
        <div className="empty-state">
          <div className="empty-icon">📚</div>
          <p>{hasFilters ? 'No results for these filters' : 'The library is empty. Add your first book!'}</p>
        </div>
      ) : (
        <>
          <div className="book-grid">
            {books.map(book => (
              <div key={book.id} className="book-card" onClick={() => nav(`/books/${book.id}`)}>
                <div className="book-card-cover">
                  {book.cover_image_url
                    ? <img src={book.cover_image_url} alt={book.title} loading="lazy" />
                    : <div className="book-card-cover-placeholder">{book.title[0]}</div>}
                  {book.status !== 'available' && (
                    <span className={`badge ${STATUS_BADGE[book.status]}`}
                      style={{ position: 'absolute', top: 6, right: 6, fontSize: 10 }}>
                      {STATUS_LABEL[book.status]}
                    </span>
                  )}
                </div>
                <div className="book-card-info">
                  <div className="book-card-title">{book.title}</div>
                  {book.authors?.length > 0 && <div className="book-card-author">{authorNames(book.authors)}</div>}
                  {book.location && <div className="book-card-location">📍 {book.location}</div>}
                </div>
              </div>
            ))}
          </div>
          {pages > 1 && (
            <div style={{ display: 'flex', gap: 8, justifyContent: 'center', marginTop: 24, alignItems: 'center' }}>
              <button className="btn btn-secondary btn-sm" disabled={page === 0}
                style={page === 0 ? { opacity: .4, cursor: 'default' } : {}}
                onClick={() => setPage(p => p - 1)}>← Previous</button>
              <span style={{ fontSize: 13, color: 'var(--ink-3)' }}>{page + 1} / {pages}</span>
              <button className="btn btn-secondary btn-sm" disabled={page >= pages - 1}
                style={page >= pages - 1 ? { opacity: .4, cursor: 'default' } : {}}
                onClick={() => setPage(p => p + 1)}>Next →</button>
            </div>
          )}
        </>
      )}

      {showScan && (
        <ScanModal
          onClose={() => setShowScan(false)}
          onDone={(p) => { setShowScan(false); setPrefill(p); setShowForm(true) }}
        />
      )}
      {showForm && (
        <BookFormModal
          prefill={prefill}
          categories={categories}
          locations={locations}
          onClose={() => setShowForm(false)}
          onSaved={() => { setShowForm(false); load(); loadMeta(); toast.success('Book saved!') }}
        />
      )}
    </div>
  )
}
