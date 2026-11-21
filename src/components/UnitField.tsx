import { useId } from 'react'
import type { UnitOptions } from '../api'

export function canonicalUnit(value: string, units: UnitOptions): string {
  const cleaned = value.trim().replace(/\s+/g, ' ')
  if (!cleaned) return ''
  return units.aliases[cleaned.toLocaleLowerCase()] ?? units.options.find((unit) => unit.toLocaleLowerCase() === cleaned.toLocaleLowerCase()) ?? cleaned
}

export function UnitField({ index, value, units, onChange, ariaLabel }: { index: number; value: string; units: UnitOptions; onChange: (value: string) => void; ariaLabel?: string }) {
  const id = useId()
  const options = value && !units.options.some((unit) => unit.toLocaleLowerCase() === value.toLocaleLowerCase()) ? [...units.options, value] : units.options
  return <><input aria-label={ariaLabel ?? `Unit ${index + 1}`} list={id} placeholder="Unit (optional)" value={value} onChange={(event) => onChange(event.target.value)} onBlur={() => onChange(canonicalUnit(value, units))} /><datalist id={id}><option value="" />{options.map((unit) => <option key={unit} value={unit} />)}</datalist></>
}
