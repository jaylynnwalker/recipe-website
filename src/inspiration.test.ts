import { describe, expect, it } from 'vitest'
import { recipes } from './data'
import { sampleCookingHistory, selectRecipeSuggestions } from './inspiration'

describe('selectRecipeSuggestions', () => {
  it('returns a duplicate-free mix of library recipe reasons', () => {
    const suggestions = selectRecipeSuggestions(recipes, sampleCookingHistory, () => 0, new Date('2026-11-14'))

    expect(suggestions).toHaveLength(3)
    expect(new Set(suggestions.map(({ recipe }) => recipe.id)).size).toBe(3)
    expect(suggestions.map(({ reason }) => reason)).toEqual(['Forgotten Favorite', 'Want to Try', 'Rediscover'])
    expect(suggestions.every(({ recipe }) => recipes.includes(recipe))).toBe(true)
  })

  it('does not include archived recipes', () => {
    const archived = { ...recipes[0], id: 'archived', status: 'Archived' as const }
    const suggestions = selectRecipeSuggestions([archived, ...recipes.slice(1)], sampleCookingHistory, () => 0, new Date('2026-11-14'))

    expect(suggestions.some(({ recipe }) => recipe.id === 'archived')).toBe(false)
  })
})
