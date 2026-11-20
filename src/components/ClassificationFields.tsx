import { useId, useState, type KeyboardEvent } from 'react'
import type { ClassificationOptions } from '../api'

const keyFor = (value: string) => value.trim().toLocaleLowerCase().replace(/[\s_-]+/g, ' ')
const canonical = (value: string, options: string[]) => options.find((option) => keyFor(option) === keyFor(value)) ?? value.trim().replace(/\s+/g, ' ')

export function ClassificationFields({ options, cuisine, category, tags, onCuisineChange, onCategoryChange, onTagsChange }: {
  options: ClassificationOptions
  cuisine: string
  category: string
  tags: string[]
  onCuisineChange: (value: string) => void
  onCategoryChange: (value: string) => void
  onTagsChange: (value: string[]) => void
}) {
  return <>
    <CreatableSingle label="Cuisine" value={cuisine} options={options.cuisines} onChange={onCuisineChange} />
    <CreatableSingle label="Category" value={category} options={options.categories} onChange={onCategoryChange} />
    <TagSelector options={options.tags} values={tags} onChange={onTagsChange} />
  </>
}

function CreatableSingle({ label, value, options, onChange }: { label: string; value: string; options: string[]; onChange: (value: string) => void }) {
  const id = useId()
  return <label>{label}<input list={id} value={value} onChange={(event) => onChange(event.target.value)} onBlur={() => onChange(canonical(value, options))} placeholder={`Choose or add ${label.toLocaleLowerCase()}`} /><datalist id={id}>{options.map((option) => <option key={option} value={option} />)}</datalist></label>
}

function TagSelector({ options, values, onChange }: { options: string[]; values: string[]; onChange: (value: string[]) => void }) {
  const id = useId()
  const [draft, setDraft] = useState('')
  const add = () => {
    const value = canonical(draft, options)
    if (value && !values.some((item) => keyFor(item) === keyFor(value))) onChange([...values, value])
    setDraft('')
  }
  const keyDown = (event: KeyboardEvent<HTMLInputElement>) => { if (event.key === 'Enter') { event.preventDefault(); add() } }
  return <div className="classification-tags wide"><label htmlFor={`${id}-input`}>Tags</label><div className="classification-add"><input id={`${id}-input`} list={id} value={draft} onChange={(event) => setDraft(event.target.value)} onKeyDown={keyDown} placeholder="Search or add a tag" /><datalist id={id}>{options.filter((option) => !values.some((value) => keyFor(value) === keyFor(option))).map((option) => <option key={option} value={option} />)}</datalist><button className="secondary" type="button" onClick={add} disabled={!draft.trim()}>Add tag</button></div><div className="classification-chips">{values.map((tag) => <span key={tag}>{tag}<button type="button" aria-label={`Remove ${tag}`} onClick={() => onChange(values.filter((value) => value !== tag))}>×</button></span>)}</div></div>
}
