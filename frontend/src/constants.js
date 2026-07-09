export const STATUS_LABEL = { available: 'Dostupná', missing: 'Chýba', damaged: 'Poškodená' }
export const STATUS_BADGE = { available: 'badge-available', missing: 'badge-missing', damaged: 'badge-damaged' }
export const ROLE_LABEL = { author: 'Autor', editor: 'Editor', translator: 'Prekladateľ' }
export const LANGUAGES = [
  { code: 'sk', label: 'slovenčina' },
  { code: 'cs', label: 'čeština' },
  { code: 'en', label: 'angličtina' },
  { code: 'de', label: 'nemčina' },
  { code: 'hu', label: 'maďarčina' },
  { code: 'ru', label: 'ruština' },
  { code: 'pl', label: 'poľština' },
  { code: 'fr', label: 'francúzština' },
  { code: 'la', label: 'latinčina' },
]
export const LANGUAGE_LABEL = Object.fromEntries(LANGUAGES.map(l => [l.code, l.label]))
export const CONDITIONS = ['výborný', 'dobrý', 'opotrebovaný', 'poškodený']

export function langLabel(code) {
  return LANGUAGE_LABEL[code] || code
}

export function authorNames(authors, role = 'author') {
  const main = (authors || []).filter(a => a.role === role)
  return (main.length ? main : authors || []).map(a => a.name).join(', ')
}
