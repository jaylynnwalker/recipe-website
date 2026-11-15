import type { Recipe } from './types'

export type SuggestionReason = 'Forgotten Favorite' | 'Want to Try' | 'Rediscover'

export interface CookingHistory {
  recipeId: string
  cookCount: number
  lastCookedAt: string | null
}

export interface RecipeSuggestion {
  recipe: Recipe
  reason: SuggestionReason
}

export const sampleCookingHistory: CookingHistory[] = [
  { recipeId: 'lemon-chicken', cookCount: 8, lastCookedAt: '2025-12-18' },
  { recipeId: 'tomato-pasta', cookCount: 5, lastCookedAt: '2026-10-22' },
  { recipeId: 'salmon-bowls', cookCount: 0, lastCookedAt: null },
  { recipeId: 'beef-stew', cookCount: 3, lastCookedAt: '2026-02-08' },
]

const pick = <T,>(items: T[], random: () => number) => items[Math.floor(random() * items.length)]

export function selectRecipeSuggestions(
  recipes: Recipe[],
  history: CookingHistory[],
  random: () => number = Math.random,
  asOf = new Date(),
): RecipeSuggestion[] {
  const historyByRecipe = new Map(history.map((entry) => [entry.recipeId, entry]))
  const available = recipes.filter((recipe) => recipe.status !== 'Archived')
  const used = new Set<string>()
  const suggestions: RecipeSuggestion[] = []
  const add = (candidates: Recipe[], reason: SuggestionReason) => {
    const eligible = candidates.filter((recipe) => !used.has(recipe.id))
    if (!eligible.length) return
    const recipe = pick(eligible, random)
    used.add(recipe.id)
    suggestions.push({ recipe, reason })
  }
  const forgottenBefore = new Date(asOf)
  forgottenBefore.setDate(forgottenBefore.getDate() - 90)

  add(available.filter((recipe) => {
    const entry = historyByRecipe.get(recipe.id)
    return recipe.status === 'Our Rotation' && !!entry?.lastCookedAt && new Date(entry.lastCookedAt) < forgottenBefore
  }), 'Forgotten Favorite')
  add(available.filter((recipe) => recipe.status === 'Want to Try' && !historyByRecipe.get(recipe.id)?.lastCookedAt), 'Want to Try')
  add(available, 'Rediscover')

  while (suggestions.length < Math.min(3, available.length)) add(available, 'Rediscover')
  return suggestions
}
