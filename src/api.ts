import type { Recipe, RecipeStatus } from './types'

export interface PantryStapleRecord { id: string; name: string }
export interface DeckEntryRecord { id: string; recipe: Recipe; servings: number; cooked: boolean; cookedAt?: string | null }
export interface GroceryItemRecord { id: string; label: string; name: string; quantity: number | null; unit: string | null; category: string; checked: boolean; manual: boolean }
export interface ExcludedStapleRecord { id: string; name: string }
export interface GroceryListRecord { id: string; updatedAt: string; items: GroceryItemRecord[]; excludedStaples: ExcludedStapleRecord[] }
export interface GroceryPreview { additions: string[]; updates: string[]; removals: string[]; excludedStaples: string[]; unchangedCount: number }
export type InboxStatus = 'Pending' | 'Processing' | 'Ready for Review' | 'Failed' | 'Saved'
export interface ClassificationOptions { categories: string[]; cuisines: string[]; proteins?: string[]; tags: string[] }
export interface UnitOptions { options: string[]; aliases: Record<string, string> }
export interface InboxAssetRecord { id: string; url: string; name: string; media_type: string; position: number; role?: 'source' | 'cover' }
export interface InboxRecord { id: string; sourceType: 'web' | 'youtube' | 'instagram' | 'facebook' | 'photo'; sourceUrl: string | null; status: InboxStatus; title: string; draft: RecipeInput; errorMessage: string | null; duplicateRecipeId: string | null; savedRecipeId: string | null; assets: InboxAssetRecord[]; createdAt: string; updatedAt: string }
export interface AIUsage { month: string; spent_usd: number; reserved_usd: number; budget_usd: number; warning_usd: number; warning: boolean; blocked: boolean; model: string; configured: boolean; disclaimer: string }
export interface SavedRecipeMatch { recipe: Recipe; missingIngredients: string[]; matchedCount: number }
export interface AIRecipeResults { savedMatches: SavedRecipeMatch[]; generatedIdeas: RecipeInput[] }
export type RecipeInput = {
  title: string; description: string; status: RecipeStatus; cuisine: string; proteins?: string[]; tags: string[]; categories: string[];
  prep_minutes: number; cook_minutes: number; additional_time_minutes?: number; additional_time_label?: string; base_servings: number | null; yield_unit?: string;
  ingredients: { name: string; quantity: number | null; unit: string | null; note: string | null; optional: boolean; package_detail?: string | null; alternative_measurements?: { quantity: number; unit: string | null }[] }[];
  steps: { instruction: string; tip: string | null }[]; notes: string;
  source: { type: string | null; label: string; url: string | null; page: string | null }
}

type ApiIngredient = { name: string; quantity: number | null; unit?: string | null; note?: string | null; package_detail?: string | null; alternative_measurements?: { quantity: number; unit?: string | null }[] }
type ApiRecipe = {
  id: string; title: string; description: string; status: RecipeStatus; cuisine: string; proteins: string[]; tags: string[]; categories: string[];
  prep_minutes: number; cook_minutes: number; additional_time_minutes: number; additional_time_label: string; base_servings: number; yield_unit: string; image: string | null; image_alt: string;
  ingredients: ApiIngredient[]; steps: { instruction: string; tip?: string | null }[]; notes: string;
  source: { label: string; url?: string | null }; cooking_history: string[]
}
type ApiDeckEntry = { id: string; recipe: ApiRecipe; servings: number; cooked: boolean; cooked_at?: string | null }
type ApiGroceryList = { id: string; updated_at: string; items: GroceryItemRecord[]; excluded_staples: ExcludedStapleRecord[] }
type ApiGroceryPreview = { additions: string[]; updates: string[]; removals: string[]; excluded_staples: string[]; unchanged_count: number }
type ApiInboxRecord = { id: string; source_type: InboxRecord['sourceType']; source_url: string | null; status: InboxStatus; title: string; draft: RecipeInput; error_message: string | null; duplicate_recipe_id: string | null; saved_recipe_id: string | null; assets: InboxAssetRecord[]; created_at: string; updated_at: string }

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(path, { ...options, credentials: 'include', headers: { ...(options.body instanceof FormData ? {} : { 'Content-Type': 'application/json' }), ...options.headers } })
  if (!response.ok) {
    const body = await response.json().catch(() => ({ detail: 'Request failed' }))
    const detail = body.detail
    if (Array.isArray(detail)) {
      const missingYield = detail.some((issue) => issue?.loc?.includes('base_servings'))
      throw new Error(missingYield ? 'Enter a yield amount of at least 1 before saving.' : 'Please review the highlighted recipe details and try again.')
    }
    throw new Error(typeof detail === 'string' ? detail : `Request failed (${response.status})`)
  }
  if (response.status === 204) return undefined as T
  return response.json()
}

const mapRecipe = (recipe: ApiRecipe): Recipe => ({
  id: recipe.id, title: recipe.title, description: recipe.description, status: recipe.status, cuisine: recipe.cuisine, proteins: recipe.proteins, tags: recipe.tags, categories: recipe.categories,
  prepMinutes: recipe.prep_minutes, cookMinutes: recipe.cook_minutes, additionalTimeMinutes: recipe.additional_time_minutes, additionalTimeLabel: recipe.additional_time_label, baseServings: recipe.base_servings, yieldUnit: recipe.yield_unit,
  image: recipe.image, imageAlt: recipe.image_alt,
  ingredients: recipe.ingredients.map((item) => ({ quantity: item.quantity, unit: item.unit ?? undefined, name: item.name, note: item.note ?? undefined, packageDetail: item.package_detail ?? undefined, alternativeMeasurements: item.alternative_measurements?.map((measurement) => ({ quantity: measurement.quantity, unit: measurement.unit ?? undefined })) ?? [] })),
  steps: recipe.steps.map((step) => ({ instruction: step.instruction, tip: step.tip ?? undefined })), notes: recipe.notes,
  source: { label: recipe.source.label, url: recipe.source.url ?? undefined }, cookingHistory: recipe.cooking_history,
})
const mapDeckEntry = (entry: ApiDeckEntry): DeckEntryRecord => ({ id: entry.id, recipe: mapRecipe(entry.recipe), servings: entry.servings, cooked: entry.cooked, cookedAt: entry.cooked_at })
const mapGroceryList = (list: ApiGroceryList): GroceryListRecord => ({ id: list.id, updatedAt: list.updated_at, items: list.items, excludedStaples: list.excluded_staples })
const mapGroceryPreview = (preview: ApiGroceryPreview): GroceryPreview => ({ additions: preview.additions, updates: preview.updates, removals: preview.removals, excludedStaples: preview.excluded_staples, unchangedCount: preview.unchanged_count })
const mapInbox = (item: ApiInboxRecord): InboxRecord => ({ id: item.id, sourceType: item.source_type, sourceUrl: item.source_url, status: item.status, title: item.title, draft: item.draft, errorMessage: item.error_message, duplicateRecipeId: item.duplicate_recipe_id, savedRecipeId: item.saved_recipe_id, assets: item.assets, createdAt: item.created_at, updatedAt: item.updated_at })

export const api = {
  recipes: () => request<ApiRecipe[]>('/api/recipes').then((items) => items.map(mapRecipe)),
  classifications: () => request<ClassificationOptions>('/api/recipes/classifications'),
  units: () => request<UnitOptions>('/api/recipes/units'),
  recipe: (id: string) => request<ApiRecipe>(`/api/recipes/${id}`).then(mapRecipe),
  createRecipe: (payload: RecipeInput) => request<ApiRecipe>('/api/recipes', { method: 'POST', body: JSON.stringify(payload) }).then(mapRecipe),
  updateRecipe: (id: string, payload: RecipeInput) => request<ApiRecipe>(`/api/recipes/${id}`, { method: 'PUT', body: JSON.stringify(payload) }).then(mapRecipe),
  deleteRecipe: (id: string) => request<void>(`/api/recipes/${id}`, { method: 'DELETE' }),
  madeThis: (id: string) => request<ApiRecipe>(`/api/recipes/${id}/made-this`, { method: 'POST' }).then(mapRecipe),
  uploadPhoto: (id: string, file: File, altText: string) => { const body = new FormData(); body.append('file', file); body.append('alt_text', altText); return request(`/api/recipes/${id}/photos`, { method: 'POST', body }) },
  removeRecipePhoto: (id: string) => request<void>(`/api/recipes/${id}/photo`, { method: 'DELETE' }),
  pantry: () => request<PantryStapleRecord[]>('/api/pantry-staples'),
  addStaple: (name: string) => request<PantryStapleRecord>('/api/pantry-staples', { method: 'POST', body: JSON.stringify({ name }) }),
  removeStaple: (id: string) => request<void>(`/api/pantry-staples/${id}`, { method: 'DELETE' }),
  deck: () => request<ApiDeckEntry[]>('/api/deck').then((items) => items.map(mapDeckEntry)),
  addToDeck: (recipeId: string, servings?: number) => request<ApiDeckEntry>('/api/deck', { method: 'POST', body: JSON.stringify({ recipe_id: recipeId, servings }) }).then(mapDeckEntry),
  updateDeckEntry: (id: string, patch: { servings?: number; cooked?: boolean }) => request<ApiDeckEntry>(`/api/deck/${id}`, { method: 'PATCH', body: JSON.stringify(patch) }).then(mapDeckEntry),
  removeDeckEntry: (id: string) => request<void>(`/api/deck/${id}`, { method: 'DELETE' }),
  clearCompletedDeck: () => request<void>('/api/deck/completed', { method: 'DELETE' }),
  groceryList: () => request<ApiGroceryList>('/api/grocery-list').then(mapGroceryList),
  previewGroceryUpdate: () => request<ApiGroceryPreview>('/api/grocery-list/preview', { method: 'POST' }).then(mapGroceryPreview),
  applyGroceryUpdate: () => request<ApiGroceryList>('/api/grocery-list/apply', { method: 'POST' }).then(mapGroceryList),
  addGroceryItem: (input: { label: string; quantity?: number | null; unit?: string | null; category?: string }) => request<GroceryItemRecord>('/api/grocery-list/items', { method: 'POST', body: JSON.stringify(input) }),
  updateGroceryItem: (id: string, patch: Partial<Pick<GroceryItemRecord, 'label' | 'quantity' | 'unit' | 'category' | 'checked'>>) => request<GroceryItemRecord>(`/api/grocery-list/items/${id}`, { method: 'PATCH', body: JSON.stringify(patch) }),
  removeGroceryItem: (id: string) => request<void>(`/api/grocery-list/items/${id}`, { method: 'DELETE' }),
  addBackStaple: (id: string) => request<GroceryItemRecord>(`/api/grocery-list/excluded/${id}/add-back`, { method: 'POST' }),
  inbox: () => request<ApiInboxRecord[]>('/api/inbox').then((items) => items.map(mapInbox)),
  importUrl: (url: string) => request<ApiInboxRecord>('/api/inbox/url', { method: 'POST', body: JSON.stringify({ url }) }).then(mapInbox),
  importPhotos: (files: File[]) => { const body = new FormData(); files.forEach((file) => body.append('files', file)); return request<ApiInboxRecord>('/api/inbox/photos', { method: 'POST', body }).then(mapInbox) },
  retryImport: (id: string) => request<ApiInboxRecord>(`/api/inbox/${id}/retry`, { method: 'POST' }).then(mapInbox),
  saveImport: (id: string, payload: RecipeInput) => request<ApiRecipe>(`/api/inbox/${id}/save`, { method: 'POST', body: JSON.stringify(payload) }).then(mapRecipe),
  deleteImport: (id: string) => request<void>(`/api/inbox/${id}`, { method: 'DELETE' }),
  removeImportImage: (id: string) => request<ApiInboxRecord>(`/api/inbox/${id}/image`, { method: 'DELETE' }).then(mapInbox),
  aiExtractImport: async (id: string) => {
    const controller = new AbortController()
    const timeout = window.setTimeout(() => controller.abort(), 120_000)
    try { return mapInbox(await request<ApiInboxRecord>(`/api/inbox/${id}/ai-extract`, { method: 'POST', signal: controller.signal })) }
    catch (cause) { if (controller.signal.aborted) throw new Error('Recipe extraction timed out. Please try again or enter the recipe manually.'); throw cause }
    finally { window.clearTimeout(timeout) }
  },
  aiUsage: () => request<AIUsage>('/api/ai/usage'),
  whatCanIMake: (ingredients: string[], includePantryStaples: boolean, generateAi: boolean): Promise<AIRecipeResults> => request<{ saved_matches: { recipe: ApiRecipe; missing_ingredients: string[]; matched_count: number }[]; generated_ideas: RecipeInput[] }>('/api/ai/what-can-i-make', { method: 'POST', body: JSON.stringify({ ingredients, include_pantry_staples: includePantryStaples, generate_ai: generateAi }) }).then((result) => ({ savedMatches: result.saved_matches.map((item) => ({ recipe: mapRecipe(item.recipe), missingIngredients: item.missing_ingredients, matchedCount: item.matched_count })), generatedIdeas: result.generated_ideas })),
  helpMePick: (mode: string, generateAi: boolean) => request<{ saved_recipes: ApiRecipe[]; generated_ideas: RecipeInput[] }>('/api/ai/help-me-pick', { method: 'POST', body: JSON.stringify({ mode, generate_ai: generateAi }) }).then((result) => ({ savedRecipes: result.saved_recipes.map(mapRecipe), generatedIdeas: result.generated_ideas })),
  cookingAssist: (recipeId: string, question: string, currentStep?: number | null) => request<{ answer: string }>('/api/ai/assist', { method: 'POST', body: JSON.stringify({ recipe_id: recipeId, question, current_step: currentStep ?? null }) }),
}
