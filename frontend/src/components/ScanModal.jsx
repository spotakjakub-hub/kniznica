import { useRef, useState } from 'react'
import toast from 'react-hot-toast'
import { scanApi } from '../api'

const TABS = [
  { id: 'photo', label: '📷 Photo' },
  { id: 'isbn', label: 'ISBN' },
  { id: 'search', label: 'Search' },
]

function FilePick({ label, file, onFile }) {
  const ref = useRef(null)
  return (
    <div className="form-group">
      <label>{label}</label>
      <input ref={ref} type="file" accept="image/*" capture="environment"
        style={{ display: 'none' }}
        onChange={e => onFile(e.target.files?.[0] || null)} />
      <div className="dropzone" onClick={() => ref.current?.click()}
        style={file ? { padding: '14px 20px' } : undefined}>
        {file ? (
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, justifyContent: 'center' }}>
            <img src={URL.createObjectURL(file)} alt=""
              style={{ height: 72, borderRadius: 4, objectFit: 'cover' }} />
            <span style={{ fontSize: 13 }}>{file.name}<br /><u>tap to replace</u></span>
          </div>
        ) : (
          <>
            <div className="dropzone-icon">📷</div>
            <p>Take a photo or choose an image</p>
          </>
        )}
      </div>
    </div>
  )
}

function CandidateList({ candidates, onPick }) {
  if (!candidates.length) return null
  return (
    <div style={{ marginTop: 14 }}>
      {candidates.map((c, i) => (
        <div key={i} className="card"
          style={{ padding: 12, marginBottom: 8, cursor: 'pointer', display: 'flex', gap: 12 }}
          onClick={() => onPick(c)}>
          {c.cover_image_url
            ? <img src={c.cover_image_url} alt="" style={{ width: 42, height: 63, objectFit: 'cover', borderRadius: 3 }} />
            : <div style={{ width: 42, height: 63, background: 'var(--paper-2)', borderRadius: 3 }} />}
          <div style={{ fontSize: 13, lineHeight: 1.45 }}>
            <strong>{c.title}</strong>{c.subtitle ? ` — ${c.subtitle}` : ''}<br />
            {c.authors?.join(', ')}<br />
            <span style={{ color: 'var(--ink-3)' }}>
              {[c.publisher, c.published_year, c.isbn13 || c.isbn].filter(Boolean).join(' · ')}
              {' · '}{c.source === 'openlibrary' ? 'Open Library' : 'Google Books'}
            </span>
          </div>
        </div>
      ))}
    </div>
  )
}

// Turns a lookup candidate into form prefill shape
function candidateToPrefill(c) {
  return {
    ...c,
    authors: (c.authors || []).map(n => ({ name: n, role: 'author' })),
  }
}

export default function ScanModal({ onClose, onDone }) {
  const [tab, setTab] = useState('photo')
  const [coverFile, setCoverFile] = useState(null)
  const [extraFile, setExtraFile] = useState(null)
  const [isbn, setIsbn] = useState('')
  const [title, setTitle] = useState('')
  const [author, setAuthor] = useState('')
  const [candidates, setCandidates] = useState([])
  const [busy, setBusy] = useState(false)

  const identify = async () => {
    if (!coverFile) { toast.error('Add a cover photo first'); return }
    setBusy(true)
    try {
      const { data } = await scanApi.identify(coverFile, extraFile)
      const conf = data.prefill?.ai_confidence
      if (conf != null && conf < 0.5) toast('Low AI confidence — please check the details', { icon: '⚠️' })
      onDone(data.prefill)
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Identification failed')
    } finally {
      setBusy(false)
    }
  }

  const lookupIsbn = async () => {
    if (!isbn.trim()) return
    setBusy(true)
    try {
      const { data } = await scanApi.isbn(isbn.trim())
      onDone(data.prefill)
    } catch (e) {
      toast.error(e.response?.status === 404 ? 'No book found for this ISBN' : 'Lookup failed')
    } finally {
      setBusy(false)
    }
  }

  const search = async () => {
    if (!title.trim()) return
    setBusy(true)
    setCandidates([])
    try {
      const { data } = await scanApi.search(title.trim(), author.trim())
      if (!data.candidates.length) toast('Nothing found — try a shorter title', { icon: '🤷' })
      setCandidates(data.candidates)
    } catch {
      toast.error('Search failed')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="modal-backdrop" onMouseDown={e => e.target === e.currentTarget && onClose()}>
      <div className="modal">
        <div className="modal-header">
          <h3>Add a book automatically</h3>
          <button type="button" className="btn btn-ghost" onClick={onClose}>✕</button>
        </div>
        <div className="modal-body">
          <div className="tabs">
            {TABS.map(t => (
              <div key={t.id} className={`tab ${tab === t.id ? 'active' : ''}`}
                onClick={() => setTab(t.id)}>{t.label}</div>
            ))}
          </div>

          {tab === 'photo' && (
            <>
              <FilePick label="Cover photo *" file={coverFile} onFile={setCoverFile} />
              <FilePick label="Title / imprint page (optional, improves accuracy)"
                file={extraFile} onFile={setExtraFile} />
              <button className="btn btn-primary btn-lg" style={{ width: '100%' }}
                disabled={busy} onClick={identify}>
                {busy ? <><span className="spinner" style={{ marginRight: 8 }} />Identifying… (10–60 s)</> : '✨ Identify book'}
              </button>
            </>
          )}

          {tab === 'isbn' && (
            <>
              <div className="form-group">
                <label>ISBN (10 or 13 digits)</label>
                <input className="form-control" value={isbn} inputMode="numeric"
                  placeholder="e.g. 9780500287804"
                  onChange={e => setIsbn(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && lookupIsbn()} />
              </div>
              <button className="btn btn-primary" disabled={busy} onClick={lookupIsbn}>
                {busy ? 'Looking up…' : 'Look up'}
              </button>
            </>
          )}

          {tab === 'search' && (
            <>
              <div className="form-group">
                <label>Title *</label>
                <input className="form-control" value={title}
                  onChange={e => setTitle(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && search()} />
              </div>
              <div className="form-group">
                <label>Author</label>
                <input className="form-control" value={author}
                  onChange={e => setAuthor(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && search()} />
              </div>
              <button className="btn btn-primary" disabled={busy} onClick={search}>
                {busy ? 'Searching…' : 'Search'}
              </button>
              <CandidateList candidates={candidates}
                onPick={c => onDone(candidateToPrefill(c))} />
            </>
          )}
        </div>
      </div>
    </div>
  )
}
