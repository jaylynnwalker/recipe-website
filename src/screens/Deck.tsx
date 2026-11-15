import type { Recipe } from '../types'
import { Icon } from '../components/Icons'
import { RecipeImage } from '../components/RecipeCard'

export interface DeckEntry { recipe: Recipe; servings: number; cooked: boolean }

export function Deck({ entries, onUpdate, onBrowse }: { entries: DeckEntry[]; onUpdate: (entries: DeckEntry[]) => void; onBrowse: () => void }) {
  const change = (index: number, patch: Partial<DeckEntry>) => onUpdate(entries.map((entry, itemIndex) => itemIndex === index ? { ...entry, ...patch } : entry))
  return <div className="page"><header className="page-header"><div><p className="eyebrow">Flexible meal planning</p><h1>Meals on Deck</h1><p>Keep a few dinners ready—no dates or weekly schedule required.</p></div><button className="primary" onClick={onBrowse}><Icon name="sparkles" /> Help Me Pick</button></header>
    <div className="deck-list">{entries.map((entry, index) => <article className={`deck-item ${entry.cooked ? 'cooked' : ''}`} key={entry.recipe.id}><RecipeImage recipe={entry.recipe} /><div className="deck-item-copy"><div><span className="status-dot">{entry.cooked ? '✓ Cooked' : entry.recipe.status}</span><h2>{entry.recipe.title}</h2><p>{entry.recipe.cuisine} · {entry.recipe.prepMinutes + entry.recipe.cookMinutes} min</p></div><div className="deck-controls"><div className="mini-stepper"><button aria-label="Decrease servings" disabled={entry.servings === 1} onClick={() => change(index, { servings: entry.servings - 1 })}>−</button><span>{entry.servings} servings</span><button aria-label="Increase servings" onClick={() => change(index, { servings: entry.servings + 1 })}>+</button></div><button className="secondary" onClick={() => change(index, { cooked: !entry.cooked })}>{entry.cooked ? 'Mark uncooked' : 'Mark cooked'}</button><button className="remove" aria-label={`Remove ${entry.recipe.title}`} onClick={() => onUpdate(entries.filter((_, itemIndex) => itemIndex !== index))}>Remove</button></div></div></article>)}</div>
    <button className="add-meal-row" onClick={onBrowse}><Icon name="plus" /><span><strong>Add another meal</strong><small>Browse recipes or let us help you pick</small></span></button>
    <aside className="deck-grocery"><div><span>Shopping list</span><h2>Ready to plan groceries?</h2><p>Generate a snapshot from the meals above. It won’t change unless you ask it to.</p></div><button className="secondary">Update Grocery List</button></aside>
  </div>
}
