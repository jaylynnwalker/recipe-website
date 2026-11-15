import { useState, type FormEvent } from 'react'
import type { Recipe } from '../types'
import { RecipeCard } from '../components/RecipeCard'

const ideaResults = [
  { title: 'Garlic Butter Chickpea Bowls', detail: 'Uses chickpeas, rice, garlic, and pantry seasonings' },
  { title: 'Lemony Pantry Pasta', detail: 'Uses pasta, lemon, olive oil, and parmesan' },
]

export function WhatCanIMake({ staples, recipes, onOpenRecipe, onBack }: { staples: string[]; recipes: Recipe[]; onOpenRecipe: (recipe: Recipe) => void; onBack: () => void }) {
  const [ingredients, setIngredients] = useState<string[]>(['chickpeas', 'spinach'])
  const [value, setValue] = useState('')
  const [includeStaples, setIncludeStaples] = useState(true)
  const [searched, setSearched] = useState(false)
  const addIngredient = (event: FormEvent) => {
    event.preventDefault()
    const ingredient = value.trim()
    if (ingredient && !ingredients.some((item) => item.toLowerCase() === ingredient.toLowerCase())) setIngredients([...ingredients, ingredient])
    setValue('')
  }

  return <div className="page make-page">
    <button className="back-button" onClick={onBack}>← Back home</button>
    <header className="page-header"><div><p className="eyebrow">Cook with what you have</p><h1>What Can I Make?</h1><p>Choose ingredients on hand and we’ll look for useful matches.</p></div></header>
    <section className="make-panel">
      <form className="add-ingredient-form" onSubmit={addIngredient}><label htmlFor="available-ingredient">Additional ingredients</label><div><input id="available-ingredient" value={value} onChange={(event) => setValue(event.target.value)} placeholder="Add an ingredient" /><button className="secondary" type="submit" disabled={!value.trim()}>Add</button></div></form>
      <div className="ingredient-chips selected-ingredients">{ingredients.map((ingredient) => <span className="ingredient-chip selected" key={ingredient}>{ingredient}<button aria-label={`Remove ${ingredient}`} onClick={() => setIngredients(ingredients.filter((item) => item !== ingredient))}>×</button></span>)}</div>
      <div className="staples-summary"><div><strong>Your pantry staples</strong><p>{staples.slice(0, 6).join(' · ')}{staples.length > 6 ? ` · +${staples.length - 6} more` : ''}</p></div><label className="include-staples"><input type="checkbox" checked={includeStaples} onChange={(event) => setIncludeStaples(event.target.checked)} /> Include my pantry staples</label></div>
      <button className="primary find-recipes" onClick={() => setSearched(true)} disabled={!ingredients.length && !includeStaples}>Find Recipes</button>
    </section>
    {searched && <section className="make-results" aria-live="polite">
      <div className="result-section"><div className="section-heading"><div><p className="eyebrow">From your library</p><h2>Matching Saved Recipes</h2></div><span className="result-label saved">Saved recipes</span></div><div className="make-recipe-grid">{recipes.slice(0, 2).map((recipe) => <RecipeCard key={recipe.id} recipe={recipe} onOpen={() => onOpenRecipe(recipe)} />)}</div></div>
      <div className="result-section idea-results"><div className="section-heading"><div><p className="eyebrow">Optional inspiration</p><h2>Potential Recipe Ideas</h2></div><span className="result-label ai">AI-style preview</span></div><p className="prototype-note">Sample ideas only—no AI request has been made and these are not saved household recipes.</p>{ideaResults.map((idea) => <article key={idea.title}><div><h3>{idea.title}</h3><p>{idea.detail}</p></div><button className="secondary">Preview idea</button></article>)}</div>
    </section>}
  </div>
}
