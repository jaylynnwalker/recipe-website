import { useId, useState, type KeyboardEvent } from 'react'
import type { ClassificationOptions } from '../api'

const keyFor = (value: string) => value.trim().toLocaleLowerCase().replace(/[\s_-]+/g, ' ')
const canonical = (value: string, options: string[]) => options.find((option) => keyFor(option) === keyFor(value)) ?? value.trim().replace(/\s+/g, ' ')

export function ClassificationFields({ options, cuisine, proteins, categories, tags, onCuisineChange, onProteinsChange, onCategoriesChange, onTagsChange }: {
  options: ClassificationOptions
  cuisine: string
  proteins: string[]
  categories: string[]
  tags: string[]
  onCuisineChange: (value: string) => void
  onProteinsChange: (value: string[]) => void
  onCategoriesChange: (value: string[]) => void
  onTagsChange: (value: string[]) => void
}) {
  return <>
    <CreatableSingle label="Cuisine" value={cuisine} options={options.cuisines} onChange={onCuisineChange} />
    <CreatableMulti label="Proteins" singular="protein" options={options.proteins ?? []} values={proteins} onChange={onProteinsChange} />
    <CreatableMulti label="Categories" singular="category" options={options.categories} values={categories} onChange={onCategoriesChange} />
    <CreatableMulti label="Tags" singular="tag" options={options.tags} values={tags} onChange={onTagsChange} />
  </>
}

function CreatableSingle({ label, value, options, onChange }: { label: string; value: string; options: string[]; onChange: (value: string) => void }) {
  const id = useId()
  return <label>{label}<input list={id} value={value} onChange={(event) => onChange(event.target.value)} onBlur={() => onChange(canonical(value, options))} placeholder={`Choose or add ${label.toLocaleLowerCase()}`} /><datalist id={id}>{options.map((option) => <option key={option} value={option} />)}</datalist></label>
}

function CreatableMulti({ label, singular, options, values, onChange }: { label: string; singular: string; options: string[]; values: string[]; onChange: (value: string[]) => void }) {
  const id = useId()
  const [draft, setDraft] = useState('')
  const add = () => {
    const value = canonical(draft, options)
    if (value && !values.some((item) => keyFor(item) === keyFor(value))) onChange([...values, value])
    setDraft('')
  }
  const keyDown = (event: KeyboardEvent<HTMLInputElement>) => { if (event.key === 'Enter') { event.preventDefault(); add() } }
  return <div className="classification-tags wide"><label htmlFor={`${id}-input`}>{label}</label><div className="classification-add"><input id={`${id}-input`} list={id} value={draft} onChange={(event) => setDraft(event.target.value)} onKeyDown={keyDown} placeholder={`Search or add a ${singular}`} /><datalist id={id}>{options.filter((option) => !values.some((value) => keyFor(value) === keyFor(option))).map((option) => <option key={option} value={option} />)}</datalist><button className="secondary" type="button" onClick={add} disabled={!draft.trim()}>Add {singular}</button></div><div className="classification-chips">{values.map((value) => <span key={value}>{value}<button type="button" aria-label={`Remove ${value}`} onClick={() => onChange(values.filter((item) => item !== value))}>×</button></span>)}</div></div>
}
