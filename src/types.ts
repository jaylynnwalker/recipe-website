export type RecipeStatus = 'Our Rotation' | 'Want to Try' | 'Archived'

export interface Ingredient {
  quantity: number | null
  unit?: string
  name: string
  note?: string
  packageDetail?: string
  alternativeMeasurements?: IngredientMeasurement[]
}

export interface IngredientMeasurement { quantity: number; unit?: string }

export interface RecipeStep {
  instruction: string
  tip?: string
}

export interface Recipe {
  id: string
  title: string
  description: string
  status: RecipeStatus
  cuisine: string
  proteins?: string[]
  tags: string[]
  categories?: string[]
  prepMinutes: number
  cookMinutes: number
  additionalTimeMinutes?: number
  additionalTimeLabel?: string
  baseServings: number
  yieldUnit?: string
  image: string | null
  imageAlt: string
  ingredients: Ingredient[]
  steps: RecipeStep[]
  notes: string
  source: { label: string; url?: string }
  cookingHistory?: string[]
}

export type Page = 'home' | 'recipes' | 'deck' | 'groceries' | 'inbox' | 'recipe'

export interface DeckEntry {
  recipeId: string
  servings: number
  cooked: boolean
}
