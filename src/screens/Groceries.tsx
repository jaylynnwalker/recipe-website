import { useMemo, useState } from 'react'
import type { ExcludedStapleRecord, GroceryItemRecord, GroceryListRecord, GroceryPreview } from '../api'

const categoryOrder = ['Produce', 'Meat & seafood', 'Dairy & eggs', 'Bakery', 'Frozen', 'Pantry', 'Other']

export function Groceries({ list, onPreview, onApply, onToggle, onAdd, onEdit, onDelete, onAddBack }: {
  list: GroceryListRecord
  onPreview: () => Promise<GroceryPreview>
  onApply: () => Promise<void>
  onToggle: (item: GroceryItemRecord) => Promise<void>
  onAdd: (label: string, category: string, quantity: number | null, unit: string | null) => Promise<void>
  onEdit: (item: GroceryItemRecord, patch: { label: string; quantity: number | null; unit: string | null; category: string }) => Promise<void>
  onDelete: (item: GroceryItemRecord) => Promise<void>
  onAddBack: (item: ExcludedStapleRecord) => Promise<void>
}) {
  const [collapsed, setCollapsed] = useState<string[]>([])
  const [showExcluded, setShowExcluded] = useState(false)
  const [preview, setPreview] = useState<GroceryPreview | null>(null)
  const [newItem, setNewItem] = useState('')
  const [newCategory, setNewCategory] = useState('Other')
  const [newQuantity, setNewQuantity] = useState('')
  const [newUnit, setNewUnit] = useState('')
  const [updateError, setUpdateError] = useState('')
  const [updating, setUpdating] = useState(false)
  const groups = useMemo(() => {
    const byCategory = new Map<string, GroceryItemRecord[]>()
    list.items.forEach((item) => byCategory.set(item.category, [...(byCategory.get(item.category) ?? []), item]))
    return [...byCategory].sort(([left], [right]) => (categoryOrder.indexOf(left) < 0 ? 99 : categoryOrder.indexOf(left)) - (categoryOrder.indexOf(right) < 0 ? 99 : categoryOrder.indexOf(right)))
  }, [list.items])
  const remaining = list.items.filter((item) => !item.checked).length
  const review = async () => {
    setUpdating(true); setUpdateError('')
    try { setPreview(await onPreview()) }
    catch (cause) { setUpdateError(cause instanceof Error ? cause.message : 'Unable to review Meals on Deck changes. Your current grocery list is unchanged.') }
    finally { setUpdating(false) }
  }
  const apply = async () => {
    setUpdating(true); setUpdateError('')
    try { await onApply(); setPreview(null) }
    catch (cause) { setUpdateError(cause instanceof Error ? cause.message : 'Unable to update the grocery list. Your current grocery list is unchanged.') }
    finally { setUpdating(false) }
  }
  const toggleSection = (category: string) => setCollapsed((current) => current.includes(category) ? current.filter((value) => value !== category) : [...current, category])

  return <div className="page"><header className="page-header"><div><p className="eyebrow">Shared household list</p><h1>Grocery List</h1><p>Current list · {remaining} items remaining</p></div><button className="secondary" disabled={updating} onClick={() => void review()}>{updating ? 'Checking…' : 'Review deck changes'}</button></header>
    <div className="grocery-banner"><span>✓</span><p><strong>Your list is a saved snapshot.</strong> Meals on Deck can change without changing this list.</p><button disabled={updating} onClick={() => void review()}>{updating ? 'Checking…' : 'Update list'}</button></div>
    {updateError && <p className="data-error" role="alert">{updateError}</p>}
    {preview && <section className="grocery-review" aria-label="Grocery list update review"><div className="form-section-title"><div><p className="eyebrow">Review changes</p><h2>Ready to update?</h2></div><button className="remove" onClick={() => setPreview(null)}>Close</button></div><div className="review-columns"><ReviewGroup title="Add" items={preview.additions} /><ReviewGroup title="Update" items={preview.updates} /><ReviewGroup title="Remove" items={preview.removals} /></div>{preview.excludedStaples.length > 0 && <p><strong>Pantry staples excluded:</strong> {preview.excludedStaples.join(', ')}</p>}<p>{preview.unchangedCount} generated items will remain unchanged. Manual and checked items are preserved.</p><button className="primary" disabled={updating} onClick={() => void apply()}>{updating ? 'Updating…' : 'Apply update'}</button></section>}
    <section className="excluded-staples"><button className="excluded-summary" aria-expanded={showExcluded} onClick={() => setShowExcluded(!showExcluded)}><span><strong>Pantry staples excluded</strong><small>{list.excludedStaples.length} items kept off this list</small></span><span aria-hidden="true">{showExcluded ? '⌃' : '⌄'}</span></button>{showExcluded && <div className="excluded-list"><p>Staples are excluded by default. Add one back when you need to restock it.</p><div className="ingredient-chips">{list.excludedStaples.map((staple) => <span className="excluded-chip" key={staple.id}>{staple.name}<button onClick={() => void onAddBack(staple)}>+ Add</button></span>)}</div></div>}</section>
    {groups.length ? <div className="grocery-groups">{groups.map(([category, items]) => {
      const isCollapsed = collapsed.includes(category)
      const sectionId = `grocery-${category.toLowerCase().replaceAll(/[^a-z]+/g, '-')}`
      return <section key={category}><h2><button className="grocery-section-toggle" aria-expanded={!isCollapsed} aria-controls={sectionId} onClick={() => toggleSection(category)}><span>{category}<small>{items.length}</small></span><span className="collapse-icon" aria-hidden="true">⌄</span></button></h2>{!isCollapsed && <div id={sectionId}>{items.map((item) => <label className={item.checked ? 'checked' : ''} key={item.id}><input type="checkbox" checked={item.checked} onChange={() => void onToggle(item)} /><span>{item.display_label}{item.manual ? <small>Manual</small> : item.sources.length > 0 && <small>From {item.sources.map((source) => source.title).join(', ')}</small>}</span><button type="button" aria-label={`Edit ${item.label}`} onClick={() => { const label = window.prompt('Item name', item.label); if (!label?.trim()) return; const quantity = window.prompt('Quantity (leave blank for none)', item.quantity?.toString() ?? ''); if (quantity === null) return; const unit = window.prompt('Unit (optional)', item.unit ?? ''); if (unit === null) return; const nextCategory = window.prompt('Category', item.category); if (!nextCategory?.trim()) return; void onEdit(item, { label: label.trim(), quantity: quantity.trim() ? Number(quantity) : null, unit: unit.trim() || null, category: nextCategory.trim() }) }}>Edit</button><button type="button" aria-label={`Delete ${item.label}`} onClick={() => void onDelete(item)}>×</button></label>)}</div>}</section>
    })}</div> : <div className="empty-state"><span>☷</span><h2>Your grocery list is empty</h2><p>Review Meals on Deck changes or add an item manually.</p></div>}
    <form className="add-grocery-form" onSubmit={(event) => { event.preventDefault(); if (newItem.trim()) void onAdd(newItem.trim(), newCategory, newQuantity ? Number(newQuantity) : null, newUnit.trim() || null).then(() => { setNewItem(''); setNewQuantity(''); setNewUnit('') }) }}><input aria-label="New grocery item" placeholder="Add an item" value={newItem} onChange={(event) => setNewItem(event.target.value)} /><input aria-label="New item quantity" type="number" min="0" step="any" placeholder="Qty" value={newQuantity} onChange={(event) => setNewQuantity(event.target.value)} /><input aria-label="New item unit" placeholder="Unit" value={newUnit} onChange={(event) => setNewUnit(event.target.value)} /><select aria-label="Grocery category" value={newCategory} onChange={(event) => setNewCategory(event.target.value)}>{categoryOrder.map((category) => <option key={category}>{category}</option>)}</select><button className="primary">Add</button></form>
  </div>
}

function ReviewGroup({ title, items }: { title: string; items: string[] }) {
  return <div><strong>{title} <span>{items.length}</span></strong>{items.length ? <ul>{items.map((item) => <li key={item}>{item}</li>)}</ul> : <p>None</p>}</div>
}
