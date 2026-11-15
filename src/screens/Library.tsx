import { useMemo, useState } from 'react'
import type { Recipe, RecipeStatus } from '../types'
import { RecipeCard } from '../components/RecipeCard'
import { SearchField } from '../components/SearchField'

type Filter = 'All' | Exclude<RecipeStatus, 'Archived'>

export function Library({ recipes, initialSearch, onOpenRecipe, onAddRecipe, onAddToDeck, deckRecipeIds }: { recipes: Recipe[]; initialSearch: string; onOpenRecipe: (recipe: Recipe) => void; onAddRecipe: () => void; onAddToDeck: (recipe: Recipe) => void; deckRecipeIds: string[] }) {
  const [search, setSearch] = useState(initialSearch)
  const [filter, setFilter] = useState<Filter>('All')
  const filtered = useMemo(() => recipes.filter((recipe) => {
    const haystack = [recipe.title, recipe.cuisine, ...recipe.tags, ...recipe.ingredients.map((item) => item.name)].join(' ').toLowerCase()
    return (filter === 'All' || recipe.status === filter) && haystack.includes(search.toLowerCase())
  }), [filter, recipes, search])

  return <div className="page">
    <header className="page-header"><div><p className="eyebrow">Your collection</p><h1>Recipes</h1><p>{recipes.length} household recipes and counting</p></div><button className="primary small" onClick={onAddRecipe}>+ Add recipe</button></header>
    <SearchField value={search} onChange={setSearch} />
    <div className="filter-row" aria-label="Recipe status filters">
      {(['All', 'Our Rotation', 'Want to Try'] as Filter[]).map((item) => <button key={item} className={filter === item ? 'active' : ''} onClick={() => setFilter(item)}>{item}</button>)}
      <button>More filters</button>
    </div>
    {filtered.length ? <div className="library-grid">{filtered.map((recipe) => <article className="library-recipe" key={recipe.id}><RecipeCard recipe={recipe} onOpen={() => onOpenRecipe(recipe)} /><button className="library-deck-action" disabled={deckRecipeIds.includes(recipe.id)} onClick={() => onAddToDeck(recipe)}>{deckRecipeIds.includes(recipe.id) ? 'On deck' : '+ Add to Deck'}</button></article>)}</div> : <div className="empty-state"><span>⌕</span><h2>No recipes found</h2><p>Try a different ingredient or status.</p><button className="secondary" onClick={() => { setSearch(''); setFilter('All') }}>Clear filters</button></div>}
  </div>
}
