import { useMemo, useState } from 'react'
import type { Recipe, RecipeStatus } from '../types'
import { RecipeCard } from '../components/RecipeCard'
import { SearchField } from '../components/SearchField'

type Filter = 'All' | Exclude<RecipeStatus, 'Archived'>

export function Library({ recipes, initialSearch, onOpenRecipe }: { recipes: Recipe[]; initialSearch: string; onOpenRecipe: (recipe: Recipe) => void }) {
  const [search, setSearch] = useState(initialSearch)
  const [filter, setFilter] = useState<Filter>('All')
  const filtered = useMemo(() => recipes.filter((recipe) => {
    const haystack = [recipe.title, recipe.cuisine, ...recipe.tags, ...recipe.ingredients.map((item) => item.name)].join(' ').toLowerCase()
    return (filter === 'All' || recipe.status === filter) && haystack.includes(search.toLowerCase())
  }), [filter, recipes, search])

  return <div className="page">
    <header className="page-header"><div><p className="eyebrow">Your collection</p><h1>Recipes</h1><p>{recipes.length} household recipes and counting</p></div><button className="primary small">+ Add recipe</button></header>
    <SearchField value={search} onChange={setSearch} />
    <div className="filter-row" aria-label="Recipe status filters">
      {(['All', 'Our Rotation', 'Want to Try'] as Filter[]).map((item) => <button key={item} className={filter === item ? 'active' : ''} onClick={() => setFilter(item)}>{item}</button>)}
      <button>More filters</button>
    </div>
    {filtered.length ? <div className="library-grid">{filtered.map((recipe) => <RecipeCard key={recipe.id} recipe={recipe} onOpen={() => onOpenRecipe(recipe)} />)}</div> : <div className="empty-state"><span>⌕</span><h2>No recipes found</h2><p>Try a different ingredient or status.</p><button className="secondary" onClick={() => { setSearch(''); setFilter('All') }}>Clear filters</button></div>}
  </div>
}
