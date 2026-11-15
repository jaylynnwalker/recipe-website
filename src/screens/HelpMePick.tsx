import { useState } from 'react'
import { api, type RecipeInput } from '../api'
import type { Recipe } from '../types'
import { RecipeCard } from '../components/RecipeCard'

const modes = ['Our Rotation', 'Forgotten Favorites', 'Want to Try', 'Mix'] as const

export function HelpMePick({ onBack, onOpenRecipe, onAddToDeck, onReviewIdea, deckRecipeIds }: { onBack: () => void; onOpenRecipe: (recipe: Recipe) => void; onAddToDeck: (recipe: Recipe) => void; onReviewIdea: (idea: RecipeInput) => void; deckRecipeIds: string[] }) {
  const [mode, setMode] = useState<(typeof modes)[number]>('Mix')
  const [recipes, setRecipes] = useState<Recipe[]>([])
  const [ideas, setIdeas] = useState<RecipeInput[]>([])
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const find = async (generateAi: boolean) => { setBusy(true); setError(''); try { const result = await api.helpMePick(mode, generateAi); setRecipes(result.savedRecipes); if (generateAi) setIdeas(result.generatedIdeas) } catch (cause) { setError(cause instanceof Error ? cause.message : 'Unable to suggest recipes') } finally { setBusy(false) } }
  return <div className="page"><button className="back-button" onClick={onBack}>← Back home</button><header className="page-header"><div><p className="eyebrow">A little inspiration</p><h1>Help Me Pick</h1><p>Start with your saved library. Generate something new only when you want it.</p></div></header><section className="make-panel"><div className="filter-row">{modes.map((item) => <button className={mode === item ? 'active' : ''} key={item} onClick={() => setMode(item)}>{item}</button>)}</div>{error && <p className="data-error">{error}</p>}<div className="make-actions"><button className="primary" disabled={busy} onClick={() => void find(false)}>Suggest from My Library</button><button className="secondary" disabled={busy} onClick={() => void find(true)}>Include a New AI Idea</button></div></section>{recipes.length > 0 && <section className="section-block"><div className="section-heading"><div><p className="eyebrow">Saved recipes</p><h2>{mode}</h2></div></div><div className="library-grid">{recipes.map((recipe) => <article className="library-recipe" key={recipe.id}><RecipeCard recipe={recipe} onOpen={() => onOpenRecipe(recipe)} /><button className="library-deck-action" disabled={deckRecipeIds.includes(recipe.id)} onClick={() => onAddToDeck(recipe)}>{deckRecipeIds.includes(recipe.id) ? 'On deck' : '+ Add to Deck'}</button></article>)}</div></section>}{ideas.map((idea) => <section className="settings-card" key={idea.title}><p className="eyebrow">New AI idea · Not saved</p><h2>{idea.title}</h2><p>{idea.description}</p><button className="secondary" onClick={() => onReviewIdea(idea)}>Review & save to Want to Try</button></section>)}</div>
}
