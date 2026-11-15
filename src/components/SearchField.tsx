import { Icon } from './Icons'

export function SearchField({ value, onChange, placeholder = 'Search recipes or ingredients' }: { value: string; onChange: (value: string) => void; placeholder?: string }) {
  return <label className="search-field">
    <Icon name="search" size={20} />
    <input aria-label="Search recipes" value={value} onChange={(event) => onChange(event.target.value)} placeholder={placeholder} />
    {value && <button aria-label="Clear search" onClick={() => onChange('')}>×</button>}
  </label>
}
