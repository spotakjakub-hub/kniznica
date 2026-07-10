import { useCallback, useEffect, useRef, useState } from 'react'
import toast from 'react-hot-toast'
import { queueApi, categoriesApi, metaApi } from '../api'
import { downscaleImage } from '../imageUtil'
import BookFormModal from '../components/BookFormModal'
import { authorNames } from '../constants'

const STATUS_META = {
  pending: { label: 'Waiting', color: 'var(--ink-3)', bg: 'var(--paper-2)' },
  processing: { label: 'Identifying…', color: '#856404', bg: '#fff3cd' },
  done: { label: 'Ready to review', color: 'var(--green)', bg: 'var(--green-pale)' },
  failed: { label: 'Failed', color: 'var(--red)', bg: 'var(--red-pale)' },
}

export default function ReviewPage() {
  const [jobs, setJobs] = useState([])
  const [counts, setCounts] = useState({})
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(null) // {done, total}
  const [location, setLocation] = useState('')
  const [locations, setLocations] = useState([])
  const [categories, setCategories] = useState([])
  const [reviewJob, setReviewJob] = useState(null)
  const [dragOver, setDragOver] = useState(false)
  const fileRef = useRef(null)
  const pollRef = useRef(null)

  const load = useCallback(async (silent = false) => {
    if (!silent) setLoading(true)
    try {
      const { data } = await queueApi.list()
      setJobs(data.jobs)
      setCounts(data.counts)
    } catch {
      if (!silent) toast.error('Failed to load the queue')
    } finally {
      if (!silent) setLoading(false)
    }
  }, [])

  useEffect(() => { load() }, [load])
  useEffect(() => {
    categoriesApi.list().then(({ data }) => setCategories(data)).catch(() => {})
    metaApi.locations().then(({ data }) => setLocations(data)).catch(() => {})
  }, [])

  // poll while anything is still being processed
  const active = (counts.pending || 0) + (counts.processing || 0)
  useEffect(() => {
    clearInterval(pollRef.current)
    if (active > 0) pollRef.current = setInterval(() => load(true), 4000)
    return () => clearInterval(pollRef.current)
  }, [active, load])

  const uploadFiles = async (fileList) => {
    const files = [...fileList].filter(f => f.type.startsWith('image/') || /\.(heic|heif)$/i.test(f.name))
    if (!files.length) return
    setUploading({ done: 0, total: files.length })
    let failed = 0
    // one photo per request: robust, shows progress, avoids one giant request
    for (let i = 0; i < files.length; i++) {
      try {
        const small = await downscaleImage(files[i])
        await queueApi.upload([small], location.trim())
      } catch {
        failed++
      }
      setUploading({ done: i + 1, total: files.length })
      if (i % 3 === 2) load(true)
    }
    setUploading(null)
    if (failed) toast.error(`${failed} of ${files.length} photos failed to upload`)
    else toast.success(`${files.length} photo${files.length > 1 ? 's' : ''} queued`)
    load(true)
  }

  const reject = async (job) => {
    try {
      await queueApi.delete(job.id)
      setJobs(js => js.filter(j => j.id !== job.id))
      load(true)
    } catch {
      toast.error('Failed to remove')
    }
  }

  const retry = async (job) => {
    try {
      await queueApi.retry(job.id)
      load(true)
    } catch {
      toast.error('Retry failed')
    }
  }

  const onSaved = async () => {
    const job = reviewJob
    setReviewJob(null)
    toast.success('Book saved!')
    if (job) {
      try { await queueApi.delete(job.id) } catch { /* job cleanup is best-effort */ }
    }
    load(true)
  }

  const doneJobs = jobs.filter(j => j.status === 'done')

  return (
    <div>
      <div
        className={`dropzone ${dragOver ? 'active' : ''}`}
        style={{ marginBottom: 16 }}
        onClick={() => fileRef.current?.click()}
        onDragOver={e => { e.preventDefault(); setDragOver(true) }}
        onDragLeave={() => setDragOver(false)}
        onDrop={e => { e.preventDefault(); setDragOver(false); uploadFiles(e.dataTransfer.files) }}
      >
        <input ref={fileRef} type="file" accept="image/*" multiple style={{ display: 'none' }}
          onChange={e => { uploadFiles(e.target.files); e.target.value = '' }} />
        <div className="dropzone-icon">📚📷</div>
        {uploading ? (
          <p><span className="spinner" style={{ marginRight: 8 }} />Uploading {uploading.done} / {uploading.total}…</p>
        ) : (
          <p>Drop dozens of cover photos here, or tap to select from your gallery.<br />
            They are identified in the background — you can keep photographing.</p>
        )}
      </div>

      <div style={{ display: 'flex', gap: 10, marginBottom: 20, alignItems: 'center', flexWrap: 'wrap' }}>
        <input className="form-control" style={{ maxWidth: 320 }} list="review-locations"
          placeholder="Location for this batch (e.g. Study — shelf B2)"
          value={location} onChange={e => setLocation(e.target.value)} />
        <datalist id="review-locations">
          {locations.map(l => <option key={l} value={l} />)}
        </datalist>
        <span style={{ fontSize: 13, color: 'var(--ink-3)', marginLeft: 'auto' }}>
          {active > 0 && <><span className="spinner" style={{ width: 12, height: 12, marginRight: 6 }} />{active} in progress · </>}
          {doneJobs.length} to review
        </span>
      </div>

      {loading ? (
        <div className="loading-full"><div className="spinner" style={{ width: 32, height: 32 }} /></div>
      ) : jobs.length === 0 ? (
        <div className="empty-state">
          <div className="empty-icon">🧺</div>
          <p>The queue is empty. Photograph a shelf and drop the photos above.</p>
        </div>
      ) : (
        <div style={{ display: 'grid', gap: 10 }}>
          {jobs.map(job => {
            const meta = STATUS_META[job.status] || STATUS_META.pending
            const r = job.result || {}
            return (
              <div key={job.id} className="card" style={{ padding: 12, display: 'flex', gap: 14, alignItems: 'center', flexWrap: 'wrap' }}>
                <img src={job.cover_url} alt="" loading="lazy"
                  style={{ width: 48, height: 72, objectFit: 'cover', borderRadius: 4, background: 'var(--paper-2)' }} />
                <div style={{ flex: 1, minWidth: 180 }}>
                  <span className="badge" style={{ color: meta.color, background: meta.bg }}>{meta.label}</span>
                  {job.status === 'done' && (
                    <div style={{ marginTop: 6, fontSize: 14 }}>
                      <strong>{r.title || 'Unknown title'}</strong>
                      {r.authors?.length > 0 && <span style={{ color: 'var(--ink-3)' }}> — {authorNames(r.authors)}</span>}
                      <div style={{ fontSize: 12, color: 'var(--ink-4)' }}>
                        {[r.publisher, r.published_year, r.location].filter(Boolean).join(' · ')}
                        {r.ai_confidence != null && ` · AI ${Math.round(r.ai_confidence * 100)} %`}
                      </div>
                    </div>
                  )}
                  {job.status === 'failed' && (
                    <div style={{ marginTop: 6, fontSize: 12, color: 'var(--red)' }}>{job.error}</div>
                  )}
                </div>
                <div style={{ display: 'flex', gap: 8 }}>
                  {job.status === 'done' && (
                    <button className="btn btn-primary btn-sm" onClick={() => setReviewJob(job)}>✓ Review & save</button>
                  )}
                  {job.status === 'failed' && (
                    <button className="btn btn-secondary btn-sm" onClick={() => retry(job)}>↻ Retry</button>
                  )}
                  <button className="btn btn-danger btn-sm" onClick={() => reject(job)}>✕</button>
                </div>
              </div>
            )
          })}
        </div>
      )}

      {reviewJob && (
        <BookFormModal
          prefill={reviewJob.result}
          categories={categories}
          locations={locations}
          onClose={() => setReviewJob(null)}
          onSaved={onSaved}
        />
      )}
    </div>
  )
}
