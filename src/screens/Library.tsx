import { useMemo, useState } from 'react'
import type { Recipe, RecipeStatus } from '../types'
import { RecipeCard } from '../components/RecipeCard'
import { SearchField } from '../components/SearchField'

type Filter = 'All' | Exclude<RecipeStatus, 'Archived'>

export function Library({ recipes, initialSearch, onOpenRecipe, onAddRecipe, onAddToDeck, deckRecipeIds }: { recipes: Recipe[]; initialSearch: string; onOpenRecipe: (recipe: Recipe) => void; onAddRecipe: () => void; onAddToDeck: (recipe: Recipe) => void; deckRecipeIds: string[] }) {
  const [search, setSearch] = useState(initialSearch)
  const [filter, setFilter] = useState<Filter>('All')
  const [category, setCategory] = useState('All')
  const categoryOptions = useMemo(() => [...new Set(recipes.flatMap((recipe) => recipe.categories ?? []))].sort((left, right) => left.localeCompare(right)), [recipes])
  const filtered = useMemo(() => recipes.filter((recipe) => {
    const haystack = [recipe.title, recipe.cuisine, ...(recipe.categories ?? []), ...recipe.tags, ...recipe.ingredients.map((item) => item.name)].join(' ').toLowerCase()
    return (filter === 'All' || recipe.status === filter) && (category === 'All' || recipe.categories?.includes(category)) && haystack.includes(search.toLowerCase())
  }), [category, filter, recipes, search])

  return <div className="page">
    <header className="page-header"><div><p className="eyebrow">Your collection</p><h1>Recipes</h1><p>{recipes.length} household recipes and counting</p></div><button className="primary small" onClick={onAddRecipe}>+ Add recipe</button></header>
    <SearchField value={search} onChange={setSearch} />
    <div className="filter-row" aria-label="Recipe status filters">
      {(['All', 'Our Rotation', 'Want to Try'] as Filter[]).map((item) => <button key={item} className={filter === item ? 'active' : ''} onClick={() => setFilter(item)}>{item}</button>)}
      <label className="library-category-filter">Category<select aria-label="Filter by category" value={category} onChange={(event) => setCategory(event.target.value)}><option>All</option>{categoryOptions.map((option) => <option key={option}>{option}</option>)}</select></label>
    </div>
    {filtered.length ? <div className="library-grid">{filtered.map((recipe) => <article className="library-recipe" key={recipe.id}><RecipeCard recipe={recipe} onOpen={() => onOpenRecipe(recipe)} /><button className="library-deck-action" disabled={deckRecipeIds.includes(recipe.id)} onClick={() => onAddToDeck(recipe)}>{deckRecipeIds.includes(recipe.id) ? 'On deck' : '+ Add to Deck'}</button></article>)}</div> : <div className="empty-state"><span>⌕</span><h2>No recipes found</h2><p>Try a different ingredient, category, or status.</p><button className="secondary" onClick={() => { setSearch(''); setFilter('All'); setCategory('All') }}>Clear filters</button></div>}
  </div>
}
