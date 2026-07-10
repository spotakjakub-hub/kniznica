import axios from 'axios'

// V produkcii nastav VITE_API_URL (napr. https://kniznica-api.onrender.com/api),
// lokálne padá na Vite proxy /api -> localhost:8000
const api = axios.create({ baseURL: import.meta.env.VITE_API_URL || '/api' })

// Zdieľané heslo (ak je na backende zapnuté LIBRARY_PASSWORD)
api.interceptors.request.use(cfg => {
  const key = localStorage.getItem('library_key')
  if (key) cfg.headers['X-Library-Key'] = key
  return cfg
})
api.interceptors.response.use(
  r => r,
  err => {
    if (err.response?.status === 401) {
      window.dispatchEvent(new Event('library-unauthorized'))
    }
    return Promise.reject(err)
  }
)

export const authApi = {
  check: (key) => api.get('/auth/check', { params: { key } }),
}

// Kolekcie voláme s lomkou na konci, inak FastAPI vracia 307 redirect
export const booksApi = {
  list: (params) => api.get('/books/', { params }),
  get: (id) => api.get(`/books/${id}`),
  create: (data) => api.post('/books/', data),
  update: (id, data) => api.put(`/books/${id}`, data),
  delete: (id) => api.delete(`/books/${id}`),
}

export const categoriesApi = {
  list: () => api.get('/categories/'),
  create: (data) => api.post('/categories/', data),
}

export const scanApi = {
  identify: (coverFile, extraFile) => {
    const fd = new FormData()
    fd.append('cover', coverFile)
    if (extraFile) fd.append('extra', extraFile)
    return api.post('/scan/identify', fd, { timeout: 120000 })
  },
  isbn: (isbn) => api.get(`/scan/isbn/${encodeURIComponent(isbn)}`),
  search: (title, author) => api.get('/scan/search', { params: { title, author: author || undefined } }),
}

export const queueApi = {
  upload: (files, location) => {
    const fd = new FormData()
    for (const f of files) fd.append('files', f)
    if (location) fd.append('location', location)
    return api.post('/queue/upload', fd, { timeout: 120000 })
  },
  list: () => api.get('/queue/'),
  retry: (id) => api.post(`/queue/${id}/retry`),
  delete: (id) => api.delete(`/queue/${id}`),
}

export const metaApi = {
  locations: () => api.get('/meta/locations'),
  languages: () => api.get('/meta/languages'),
  stats: () => api.get('/meta/stats'),
}

export const loansApi = {
  lend: (bookId, borrower, note) => api.post(`/books/${bookId}/lend`, { borrower, note }),
  return: (loanId) => api.post(`/loans/${loanId}/return`),
  active: () => api.get('/loans/active'),
}

export const exportApi = {
  downloadCsv: async () => {
    const { data } = await api.get('/export/csv', { responseType: 'blob' })
    const url = URL.createObjectURL(data)
    const a = document.createElement('a')
    a.href = url
    a.download = `library-export-${new Date().toISOString().slice(0, 10)}.csv`
    a.click()
    URL.revokeObjectURL(url)
  },
}

export default api
