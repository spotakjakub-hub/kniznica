import { useState } from 'react'

// Select that ends with a "＋ Custom…" option; choosing it swaps the select
// for a free-text input. If the current value isn't among the options
// (a custom value saved earlier), it starts in input mode.
export default function SelectWithCustom({
  value, onChange, options,
  emptyLabel = null,        // when set, an empty "—" option is offered
  resetValue = '',          // value restored when custom input is cancelled
  placeholder = 'Custom value',
  compact = false,
}) {
  const known = options.some(o => o.value === value)
  const [custom, setCustom] = useState(() => (value && !known ? true : false))

  if (!custom) {
    return (
      <select
        className="form-control"
        style={compact ? { width: 140, flexShrink: 0 } : undefined}
        value={value}
        onChange={e => {
          if (e.target.value === '__custom__') { setCustom(true); onChange('') }
          else onChange(e.target.value)
        }}
      >
        {emptyLabel !== null && <option value="">{emptyLabel}</option>}
        {options.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
        <option value="__custom__">＋ Custom…</option>
      </select>
    )
  }

  return (
    <div className="author-row" style={{ marginBottom: 0, ...(compact ? { width: 140, flexShrink: 0 } : {}) }}>
      <input className="form-control" placeholder={placeholder} autoFocus
        value={value} onChange={e => onChange(e.target.value)} />
      <button type="button" className="remove-btn" title="Back to list"
        onClick={() => { setCustom(false); onChange(resetValue) }}>✕</button>
    </div>
  )
}
