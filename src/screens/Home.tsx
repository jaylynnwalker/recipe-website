import { useEffect, useMemo, useState } from 'react'
import type { Recipe } from '../types'
import { selectRecipeSuggestions } from '../inspiration'
import { Icon } from '../components/Icons'
import { InspirationCard } from '../components/InspirationCard'
import { RecipeCard } from '../components/RecipeCard'
import { SearchField } from '../components/SearchField'

export function Home({ recipes, deckRecipes, search, onSearch, onOpenRecipe, onOpenDeck, onBrowse, onHelpPick, onWhatCanIMake, onSettings, onAddToDeck, deckRecipeIds, deckCount }: { recipes: Recipe[]; deckRecipes: Recipe[]; search: string; onSearch: (value: string) => void; onOpenRecipe: (recipe: Recipe) => void; onOpenDeck: () => void; onBrowse: () => void; onHelpPick: () => void; onWhatCanIMake: () => void; onSettings: () => void; onAddToDeck: (recipe: Recipe) => void; deckRecipeIds: string[]; deckCount: number }) {
  const [suggestionVersion, setSuggestionVersion] = useState(0)
  const suggestions = useMemo(() => {
    let state = suggestionVersion + 1
    const seededRandom = () => ((state = (Math.imul(1664525, state) + 1013904223) >>> 0) / 4294967296)
    const history = recipes.map((recipe) => ({ recipeId: recipe.id, cookCount: recipe.cookingHistory?.length ?? 0, lastCookedAt: recipe.cookingHistory?.[0] ?? null }))
    return selectRecipeSuggestions(recipes, history, seededRandom)
  }, [recipes, suggestionVersion])
  useEffect(() => {
    const timer = window.setInterval(() => setSuggestionVersion((current) => current + 1), 5 * 60 * 1000)
    return () => window.clearInterval(timer)
  }, [])
  return <div className="page home-page">
    <header className="mobile-wordmark"><span>Our Kitchen</span><button aria-label="Open household settings" onClick={onSettings}>J</button></header>
    <section className="welcome">
      <p className="eyebrow">Saturday, November 14</p>
      <h1>Welcome back</h1>
      <p>What sounds good today?</p>
    </section>
    <div className="home-tools">
      <SearchField value={search} onChange={onSearch} />
      <button className="primary pick-button" onClick={onHelpPick}><Icon name="sparkles" /> Help Me Pick</button>
      <button className="secondary make-button" onClick={onWhatCanIMake}>What Can I Make?</button>
    </div>

    <section className="section-block">
      <div className="section-heading"><div><p className="eyebrow">Up next</p><h2>Meals on Deck</h2></div><button className="text-button" onClick={onOpenDeck}>View deck <Icon name="arrow" size={17} /></button></div>
      <button className="deck-summary mobile-only" onClick={onOpenDeck}><span className="deck-icon"><Icon name="deck" /></span><span><strong>{deckCount} meals waiting</strong><small>Flexible plans, no dates attached</small></span><Icon name="arrow" /></button>
      <div className="card-row desktop-deck">
        {deckRecipes.slice(0, 3).map((recipe) => <RecipeCard compact key={recipe.id} recipe={recipe} onOpen={() => onOpenRecipe(recipe)} />)}
        <button className="add-card" onClick={onBrowse}><span><Icon name="plus" /></span>Add a meal</button>
      </div>
    </section>

    <section className="section-block ideas">
      <div className="section-heading"><div><p className="eyebrow">A little inspiration</p><h2>Recipe Ideas</h2></div><button className="text-button" onClick={() => setSuggestionVersion((current) => current + 1)}><Icon name="sparkles" size={16} /> Fresh ideas</button></div>
      <div className="card-row">{suggestions.map((suggestion) => <InspirationCard key={suggestion.recipe.id} suggestion={suggestion} onOpen={() => onOpenRecipe(suggestion.recipe)} onAddToDeck={() => onAddToDeck(suggestion.recipe)} isOnDeck={deckRecipeIds.includes(suggestion.recipe.id)} />)}</div>
    </section>
  </div>
}
