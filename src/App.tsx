import { useState } from 'react'
import { Layout, type Page } from './components/Layout'
import { recipes } from './data'
import type { Recipe } from './types'
import { Home } from './screens/Home'
import { Library } from './screens/Library'
import { RecipeDetail } from './screens/RecipeDetail'
import { Deck, type DeckEntry } from './screens/Deck'
import { Groceries } from './screens/Groceries'
import { Inbox } from './screens/Inbox'
import { Settings } from './screens/Settings'
import { WhatCanIMake } from './screens/WhatCanIMake'

export function App() {
  const [page, setPage] = useState<Page>('home')
  const [selectedRecipe, setSelectedRecipe] = useState<Recipe | null>(null)
  const [search, setSearch] = useState('')
  const [pantryStaples, setPantryStaples] = useState(['Olive oil', 'Garlic', 'Salt', 'Black pepper', 'Dried oregano', 'Rice', 'Flour'])
  const [deck, setDeck] = useState<DeckEntry[]>([
    { recipe: recipes[0], servings: 4, cooked: false },
    { recipe: recipes[1], servings: 4, cooked: false },
    { recipe: recipes[2], servings: 2, cooked: false },
  ])
  const navigate = (next: Page) => { setPage(next); setSelectedRecipe(null); window.scrollTo({ top: 0, behavior: 'smooth' }) }
  const openRecipe = (recipe: Recipe) => { setSelectedRecipe(recipe); setPage('recipes'); window.scrollTo(0, 0) }
  const addToDeck = (recipe: Recipe) => { if (!deck.some((entry) => entry.recipe.id === recipe.id)) setDeck([...deck, { recipe, servings: recipe.baseServings, cooked: false }]) }

  let content
  if (selectedRecipe) content = <RecipeDetail recipe={selectedRecipe} onBack={() => setSelectedRecipe(null)} onAddToDeck={addToDeck} />
  else if (page === 'home') content = <Home recipes={recipes} search={search} onSearch={setSearch} onOpenRecipe={openRecipe} onOpenDeck={() => navigate('deck')} onBrowse={() => navigate('recipes')} onWhatCanIMake={() => navigate('make')} onSettings={() => navigate('settings')} onAddToDeck={addToDeck} deckRecipeIds={deck.map((entry) => entry.recipe.id)} deckCount={deck.length} />
  else if (page === 'recipes') content = <Library recipes={recipes} initialSearch={search} onOpenRecipe={openRecipe} />
  else if (page === 'deck') content = <Deck entries={deck} onUpdate={setDeck} onBrowse={() => navigate('recipes')} />
  else if (page === 'groceries') content = <Groceries staples={pantryStaples} />
  else if (page === 'settings') content = <Settings staples={pantryStaples} onChange={setPantryStaples} onBack={() => navigate('home')} />
  else if (page === 'make') content = <WhatCanIMake staples={pantryStaples} recipes={recipes} onOpenRecipe={openRecipe} onBack={() => navigate('home')} />
  else content = <Inbox />

  return <Layout page={page} onNavigate={navigate}>{content}</Layout>
}
