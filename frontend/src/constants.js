export const STATUS_LABEL = { available: 'Available', missing: 'Missing', damaged: 'Damaged' }
export const STATUS_BADGE = { available: 'badge-available', missing: 'badge-missing', damaged: 'badge-damaged' }
export const ROLE_LABEL = { author: 'Author', editor: 'Editor', translator: 'Translator' }
export const LANGUAGES = [
  { code: 'sk', label: 'Slovak' },
  { code: 'cs', label: 'Czech' },
  { code: 'en', label: 'English' },
  { code: 'de', label: 'German' },
  { code: 'hu', label: 'Hungarian' },
  { code: 'ru', label: 'Russian' },
  { code: 'pl', label: 'Polish' },
  { code: 'fr', label: 'French' },
  { code: 'la', label: 'Latin' },
]
export const LANGUAGE_LABEL = Object.fromEntries(LANGUAGES.map(l => [l.code, l.label]))
export const CONDITIONS = ['excellent', 'good', 'worn', 'damaged']
export const CONDITION_LABEL = { excellent: 'Excellent', good: 'Good', worn: 'Worn', damaged: 'Damaged' }

export function langLabel(code) {
  return LANGUAGE_LABEL[code] || code
}

export function authorNames(authors, role = 'author') {
  const main = (authors || []).filter(a => a.role === role)
  return (main.length ? main : authors || []).map(a => a.name).join(', ')
}
