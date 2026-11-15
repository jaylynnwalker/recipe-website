import type { DeckEntryRecord } from '../api'
import { Icon } from '../components/Icons'
import { RecipeImage } from '../components/RecipeCard'

export type DeckEntry = DeckEntryRecord

export function Deck({ entries, onChange, onRemove, onClearCompleted, onBrowse, onGroceries }: {
  entries: DeckEntry[]
  onChange: (entry: DeckEntry, patch: { servings?: number; cooked?: boolean }) => Promise<void>
  onRemove: (entry: DeckEntry) => Promise<void>
  onClearCompleted: () => Promise<void>
  onBrowse: () => void
  onGroceries: () => void
}) {
  const completed = entries.filter((entry) => entry.cooked).length
  return <div className="page"><header className="page-header"><div><p className="eyebrow">Flexible meal planning</p><h1>Meals on Deck</h1><p>Keep a few dinners ready—no dates or weekly schedule required.</p></div><div className="deck-header-actions">{completed > 0 && <button className="secondary" onClick={() => void onClearCompleted()}>Clear completed</button>}<button className="primary" onClick={onBrowse}><Icon name="sparkles" /> Help Me Pick</button></div></header>
    {entries.length ? <div className="deck-list">{entries.map((entry) => <article className={`deck-item ${entry.cooked ? 'cooked' : ''}`} key={entry.id}><RecipeImage recipe={entry.recipe} /><div className="deck-item-copy"><div><span className="status-dot">{entry.cooked ? '✓ Cooked' : entry.recipe.status}</span><h2>{entry.recipe.title}</h2><p>{entry.recipe.cuisine} · {entry.recipe.prepMinutes + entry.recipe.cookMinutes} min</p></div><div className="deck-controls"><div className="mini-stepper"><button aria-label={`Decrease servings for ${entry.recipe.title}`} disabled={entry.servings === 1 || entry.cooked} onClick={() => void onChange(entry, { servings: entry.servings - 1 })}>−</button><span>{entry.servings} servings</span><button aria-label={`Increase servings for ${entry.recipe.title}`} disabled={entry.cooked} onClick={() => void onChange(entry, { servings: entry.servings + 1 })}>+</button></div><button className="secondary" onClick={() => void onChange(entry, { cooked: !entry.cooked })}>{entry.cooked ? 'Mark uncooked' : 'Mark cooked'}</button><button className="remove" aria-label={`Remove ${entry.recipe.title}`} onClick={() => void onRemove(entry)}>Remove</button></div></div></article>)}</div> : <div className="empty-state"><span>✦</span><h2>Your deck is open</h2><p>Add saved recipes when you’re deciding what to cook next.</p><button className="primary" onClick={onBrowse}>Browse recipes</button></div>}
    <button className="add-meal-row" onClick={onBrowse}><Icon name="plus" /><span><strong>Add another meal</strong><small>Browse recipes or let us help you pick</small></span></button>
    <aside className="deck-grocery"><div><span>Shopping list</span><h2>Ready to plan groceries?</h2><p>Review a new snapshot from unfinished meals. It won’t change unless you apply it.</p></div><button className="secondary" onClick={onGroceries}>Update Grocery List</button></aside>
  </div>
}
