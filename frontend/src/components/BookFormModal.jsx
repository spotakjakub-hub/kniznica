import { useState } from 'react'
import { booksApi } from '../api'
import toast from 'react-hot-toast'
import { STATUS_LABEL, ROLE_LABEL, LANGUAGES, CONDITIONS } from '../constants'

const EMPTY = {
  title: '', subtitle: '', isbn: '', isbn13: '', publisher: '',
  published_year: '', language: 'sk', pages: '', edition: '',
  description: '', notes: '', cover_image_url: '', location: '',
  condition: '', status: 'available', category_id: '',
}

function toPayload(form, authors, tagsText) {
  return {
    ...form,
    isbn: form.isbn.trim() || null,
    isbn13: form.isbn13.trim() || null,
    subtitle: form.subtitle.trim() || null,
    publisher: form.publisher.trim() || null,
    edition: form.edition.trim() || null,
    description: form.description.trim() || null,
    notes: form.notes.trim() || null,
    cover_image_url: form.cover_image_url.trim() || null,
    location: form.location.trim() || null,
    condition: form.condition || null,
    published_year: form.published_year ? Number(form.published_year) : null,
    pages: form.pages ? Number(form.pages) : null,
    category_id: form.category_id ? Number(form.category_id) : null,
    authors: authors.filter(a => a.name.trim()),
    tag_names: tagsText.split(',').map(t => t.trim()).filter(Boolean),
  }
}

export default function BookFormModal({ book, categories, locations = [], onClose, onSaved }) {
  const [form, setForm] = useState(() => {
    if (!book) return EMPTY
    const f = { ...EMPTY }
    for (const k of Object.keys(EMPTY)) {
      if (book[k] !== null && book[k] !== undefined) f[k] = String(book[k])
    }
    f.language = book.language || 'sk'
    f.status = book.status || 'available'
    return f
  })
  const [authors, setAuthors] = useState(
    book?.authors?.length ? book.authors.map(a => ({ name: a.name, role: a.role })) : [{ name: '', role: 'author' }]
  )
  const [tagsText, setTagsText] = useState(book?.tags?.map(t => t.name).join(', ') || '')
  const [saving, setSaving] = useState(false)

  const set = (k) => (e) => setForm(f => ({ ...f, [k]: e.target.value }))
  const setAuthor = (i, k) => (e) =>
    setAuthors(list => list.map((a, j) => (j === i ? { ...a, [k]: e.target.value } : a)))

  const submit = async (e) => {
    e.preventDefault()
    if (!form.title.trim()) { toast.error('Názov je povinný'); return }
    setSaving(true)
    try {
      const payload = toPayload({ ...form, title: form.title.trim() }, authors, tagsText)
      if (book) await booksApi.update(book.id, payload)
      else await booksApi.create(payload)
      onSaved()
    } catch {
      toast.error('Uloženie zlyhalo')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="modal-backdrop" onMouseDown={e => e.target === e.currentTarget && onClose()}>
      <div className="modal">
        <form onSubmit={submit}>
          <div className="modal-header">
            <h3>{book ? 'Upraviť knihu' : 'Pridať knihu'}</h3>
            <button type="button" className="btn btn-ghost" onClick={onClose}>✕</button>
          </div>
          <div className="modal-body">
            <div className="form-group">
              <label>Názov *</label>
              <input className="form-control" value={form.title} onChange={set('title')} autoFocus required />
            </div>
            <div className="form-group">
              <label>Podtitul</label>
              <input className="form-control" value={form.subtitle} onChange={set('subtitle')} />
            </div>

            <div className="form-group">
              <label>Autori</label>
              {authors.map((a, i) => (
                <div className="author-row" key={i}>
                  <input className="form-control" placeholder="Meno autora"
                    value={a.name} onChange={setAuthor(i, 'name')} />
                  <select className="form-control" value={a.role} onChange={setAuthor(i, 'role')}>
                    {Object.entries(ROLE_LABEL).map(([v, l]) => <option key={v} value={v}>{l}</option>)}
                  </select>
                  {authors.length > 1 && (
                    <button type="button" className="remove-btn"
                      onClick={() => setAuthors(list => list.filter((_, j) => j !== i))}>✕</button>
                  )}
                </div>
              ))}
              <button type="button" className="btn btn-ghost btn-sm"
                onClick={() => setAuthors(list => [...list, { name: '', role: 'author' }])}>
                + ďalší autor
              </button>
            </div>

            <div className="form-grid-2">
              <div className="form-group">
                <label>Vydavateľ</label>
                <input className="form-control" value={form.publisher} onChange={set('publisher')} />
              </div>
              <div className="form-group">
                <label>Rok vydania</label>
                <input className="form-control" type="number" min="0" max="2100"
                  value={form.published_year} onChange={set('published_year')} />
              </div>
              <div className="form-group">
                <label>ISBN</label>
                <input className="form-control" value={form.isbn} onChange={set('isbn')} />
              </div>
              <div className="form-group">
                <label>ISBN-13</label>
                <input className="form-control" value={form.isbn13} onChange={set('isbn13')} />
              </div>
              <div className="form-group">
                <label>Jazyk</label>
                <select className="form-control" value={form.language} onChange={set('language')}>
                  {LANGUAGES.map(l => <option key={l.code} value={l.code}>{l.label}</option>)}
                </select>
              </div>
              <div className="form-group">
                <label>Počet strán</label>
                <input className="form-control" type="number" min="1" value={form.pages} onChange={set('pages')} />
              </div>
              <div className="form-group">
                <label>Edícia</label>
                <input className="form-control" value={form.edition} onChange={set('edition')} />
              </div>
              <div className="form-group">
                <label>Kategória</label>
                <select className="form-control" value={form.category_id} onChange={set('category_id')}>
                  <option value="">— bez kategórie —</option>
                  {categories.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
                </select>
              </div>
              <div className="form-group">
                <label>Umiestnenie</label>
                <input className="form-control" list="locations-list" placeholder="napr. Obývačka — polica A3"
                  value={form.location} onChange={set('location')} />
                <datalist id="locations-list">
                  {locations.map(l => <option key={l} value={l} />)}
                </datalist>
              </div>
              <div className="form-group">
                <label>Fyzický stav</label>
                <select className="form-control" value={form.condition} onChange={set('condition')}>
                  <option value="">— neuvedený —</option>
                  {CONDITIONS.map(c => <option key={c} value={c}>{c}</option>)}
                </select>
              </div>
              <div className="form-group">
                <label>Status</label>
                <select className="form-control" value={form.status} onChange={set('status')}>
                  {Object.entries(STATUS_LABEL).map(([v, l]) => <option key={v} value={v}>{l}</option>)}
                </select>
              </div>
              <div className="form-group">
                <label>URL obálky</label>
                <input className="form-control" placeholder="https://…"
                  value={form.cover_image_url} onChange={set('cover_image_url')} />
              </div>
            </div>

            <div className="form-group">
              <label>Štítky (oddelené čiarkou)</label>
              <input className="form-control" placeholder="napr. klasika, darček od babky"
                value={tagsText} onChange={e => setTagsText(e.target.value)} />
            </div>
            <div className="form-group">
              <label>Popis</label>
              <textarea className="form-control" value={form.description} onChange={set('description')} />
            </div>
            <div className="form-group">
              <label>Poznámky</label>
              <textarea className="form-control" value={form.notes} onChange={set('notes')} />
            </div>
          </div>
          <div className="modal-footer">
            <button type="button" className="btn btn-secondary" onClick={onClose}>Zrušiť</button>
            <button type="submit" className="btn btn-primary" disabled={saving}>
              {saving ? 'Ukladám…' : 'Uložiť'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
