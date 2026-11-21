import { useEffect, useState } from 'react'
import { Layout, type Page } from './components/Layout'
import type { Recipe } from './types'
import { api, type AIUsage, type ClassificationOptions, type DeckEntryRecord, type GroceryListRecord, type InboxRecord, type PantryStapleRecord, type RecipeInput, type UnitOptions } from './api'
import { Home } from './screens/Home'
import { Library } from './screens/Library'
import { RecipeDetail } from './screens/RecipeDetail'
import { Deck } from './screens/Deck'
import { Groceries } from './screens/Groceries'
import { Inbox } from './screens/Inbox'
import { Settings } from './screens/Settings'
import { WhatCanIMake } from './screens/WhatCanIMake'
import { RecipeForm } from './screens/RecipeForm'
import { HelpMePick } from './screens/HelpMePick'
import { RecipeCreation } from './screens/RecipeCreation'

export function App() {
  const [page, setPage] = useState<Page>('home')
  const [loading, setLoading] = useState(true)
  const [recipes, setRecipes] = useState<Recipe[]>([])
  const [pantryRecords, setPantryRecords] = useState<PantryStapleRecord[]>([])
  const [selectedRecipe, setSelectedRecipe] = useState<Recipe | null>(null)
  const [editingRecipe, setEditingRecipe] = useState<Recipe | null | undefined>(undefined)
  const [search, setSearch] = useState('')
  const [dataError, setDataError] = useState('')
  const [dataNotice, setDataNotice] = useState('')
  const [deck, setDeck] = useState<DeckEntryRecord[]>([])
  const [groceryList, setGroceryList] = useState<GroceryListRecord>({ id: '', updatedAt: '', items: [], excludedStaples: [] })
  const [inbox, setInbox] = useState<InboxRecord[]>([])
  const [reviewingImport, setReviewingImport] = useState<InboxRecord | null>(null)
  const [extractingImportId, setExtractingImportId] = useState<string | null>(null)
  const [importExtractionMessage, setImportExtractionMessage] = useState('')
  const [importExtractionError, setImportExtractionError] = useState('')
  const [reviewingIdea, setReviewingIdea] = useState<RecipeInput | null>(null)
  const [aiUsage, setAiUsage] = useState<AIUsage | null>(null)
  const [classifications, setClassifications] = useState<ClassificationOptions>({ categories: [], cuisines: [], proteins: [], tags: [] })
  const [units, setUnits] = useState<UnitOptions>({ options: [], aliases: {} })
  const [creatingRecipe, setCreatingRecipe] = useState(false)

  const loadHouseholdData = async () => {
    const [storedRecipes, staples, storedDeck, groceries, inboxItems, usage, storedClassifications, storedUnits] = await Promise.all([api.recipes(), api.pantry(), api.deck(), api.groceryList(), api.inbox(), api.aiUsage(), api.classifications(), api.units()])
    setRecipes(storedRecipes); setPantryRecords(staples); setDeck(storedDeck); setGroceryList(groceries); setInbox(inboxItems); setAiUsage(usage); setClassifications(storedClassifications); setUnits(storedUnits); setDataError('')
  }
  useEffect(() => { loadHouseholdData().catch((cause) => setDataError(cause instanceof Error ? cause.message : 'Unable to open Our Kitchen')).finally(() => setLoading(false)) }, [])

  const navigate = (next: Page) => {
    setPage(next)
    setSelectedRecipe(null)
    setEditingRecipe(undefined)
    setCreatingRecipe(false)
    setReviewingImport(null)
    setReviewingIdea(null)
    setDataNotice('')
    if (next === 'settings') void api.aiUsage().then(setAiUsage).catch(() => undefined)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }
  const openRecipe = async (recipe: Recipe) => {
    try { setSelectedRecipe(await api.recipe(recipe.id)); setPage('recipes'); window.scrollTo(0, 0) }
    catch (cause) { setDataError(cause instanceof Error ? cause.message : 'Unable to open recipe') }
  }
  const addToDeck = async (recipe: Recipe) => {
    if (deck.some((entry) => entry.recipe.id === recipe.id)) return
    try { const entry = await api.addToDeck(recipe.id, recipe.baseServings); setDeck((items) => [...items, entry]); setDataError('') }
    catch (cause) { setDataError(cause instanceof Error ? cause.message : 'Unable to add meal') }
  }
  const updateDeckEntry = async (entry: DeckEntryRecord, patch: { servings?: number; cooked?: boolean }) => {
    try {
      const updated = await api.updateDeckEntry(entry.id, patch)
      setDeck((items) => items.map((item) => item.id === updated.id ? updated : item))
      setRecipes((items) => items.map((recipe) => recipe.id === updated.recipe.id ? updated.recipe : recipe))
      setSelectedRecipe((recipe) => recipe?.id === updated.recipe.id ? updated.recipe : recipe)
      setDataError('')
    } catch (cause) { setDataError(cause instanceof Error ? cause.message : 'Unable to update meal') }
  }
  const removeDeckEntry = async (entry: DeckEntryRecord) => { try { await api.removeDeckEntry(entry.id); setDeck((items) => items.filter((item) => item.id !== entry.id)) } catch (cause) { setDataError(cause instanceof Error ? cause.message : 'Unable to remove meal') } }
  const clearCompleted = async () => { try { await api.clearCompletedDeck(); setDeck((items) => items.filter((item) => !item.cooked)) } catch (cause) { setDataError(cause instanceof Error ? cause.message : 'Unable to clear completed meals') } }
  const updateStaples = async (names: string[]) => {
    const removed = pantryRecords.filter((record) => !names.includes(record.name))
    const added = names.filter((name) => !pantryRecords.some((record) => record.name === name))
    setPantryRecords(names.map((name) => pantryRecords.find((record) => record.name === name) ?? { id: `pending-${name}`, name }))
    try {
      await Promise.all([...removed.map((record) => api.removeStaple(record.id)), ...added.map((name) => api.addStaple(name))])
      setPantryRecords(await api.pantry()); setDataError('')
    } catch (cause) {
      setDataError(cause instanceof Error ? cause.message : 'Unable to update pantry staples')
      setPantryRecords(await api.pantry())
    }
  }

  const saveRecipe = async (payload: RecipeInput, photo?: File) => {
    let saved = editingRecipe ? await api.updateRecipe(editingRecipe.id, payload) : await api.createRecipe(payload)
    if (photo) { await api.uploadPhoto(saved.id, photo, `${saved.title} recipe`); saved = await api.recipe(saved.id) }
    const storedRecipes = await api.recipes()
    setRecipes(storedRecipes); setClassifications(await api.classifications()); setUnits(await api.units()); setSelectedRecipe(saved); setEditingRecipe(undefined); setPage('recipes'); setDataError('')
  }
  const deleteRecipe = async () => {
    if (!editingRecipe) return
    await api.deleteRecipe(editingRecipe.id)
    setRecipes(await api.recipes()); setSelectedRecipe(null); setEditingRecipe(undefined); setPage('recipes'); setDataError('')
  }
  const recordMadeThis = async () => {
    if (!selectedRecipe) return
    try {
      const updated = await api.madeThis(selectedRecipe.id)
      setSelectedRecipe(updated); setRecipes((items) => items.map((item) => item.id === updated.id ? updated : item)); setDataError('')
    } catch (cause) { setDataError(cause instanceof Error ? cause.message : 'Unable to update cooking history') }
  }
  const importedRecipe = reviewingImport ? inboxDraftToRecipe(reviewingImport) : null
  const saveImportedRecipe = async (payload: RecipeInput, photo?: File) => {
    if (!reviewingImport) return
    const inboxId = reviewingImport.id
    let saved = await api.saveImport(inboxId, payload)
    setInbox((items) => items.filter((item) => item.id !== inboxId))
    setReviewingImport(null)
    setRecipes((items) => [saved, ...items.filter((recipe) => recipe.id !== saved.id)])
    if (photo) {
      try { await api.uploadPhoto(saved.id, photo, `${saved.title} recipe`); saved = await api.recipe(saved.id) }
      catch (cause) { setDataError(cause instanceof Error ? `Recipe saved, but its optional photo could not be uploaded: ${cause.message}` : 'Recipe saved, but its optional photo could not be uploaded.') }
    }
    const [storedRecipes, inboxItems, storedClassifications] = await Promise.all([api.recipes(), api.inbox(), api.classifications()])
    setRecipes(storedRecipes); setInbox(inboxItems); setClassifications(storedClassifications); setUnits(await api.units()); setSelectedRecipe(saved); setPage('recipes')
  }
  const saveGeneratedRecipe = async (payload: RecipeInput, photo?: File) => {
    let saved = await api.createRecipe({ ...payload, status: 'Want to Try', source: { ...payload.source, type: 'ai', label: payload.source.label || 'AI-assisted idea' } })
    if (photo) { await api.uploadPhoto(saved.id, photo, `${saved.title} recipe`); saved = await api.recipe(saved.id) }
    setRecipes(await api.recipes()); setClassifications(await api.classifications()); setUnits(await api.units()); setReviewingIdea(null); setSelectedRecipe(saved); setPage('recipes')
  }
  const addInboxItem = (item: InboxRecord) => setInbox((items) => [item, ...items.filter((current) => current.id !== item.id)])
  const extractInboxItem = async (item: InboxRecord) => {
    if (extractingImportId) return
    setExtractingImportId(item.id); setImportExtractionMessage(item.sourceType === 'photo' ? 'Extracting recipe from photo…' : 'Extracting recipe from source…'); setImportExtractionError('')
    try {
      const updated = await api.aiExtractImport(item.id)
      addInboxItem(updated); setReviewingImport(updated); setAiUsage(await api.aiUsage()); setImportExtractionMessage('Extraction complete. Review and correct the recipe before saving.')
    } catch (cause) {
      const message = cause instanceof Error ? cause.message : 'AI extraction failed. Please try again.'
      setImportExtractionMessage(''); setImportExtractionError(`${message} Your original source and current recipe details are unchanged.`)
      throw cause
    } finally { setExtractingImportId(null) }
  }
  const importFromRecipesUrl = async (url: string) => { const item = await api.importUrl(url); addInboxItem(item); setCreatingRecipe(false); setReviewingImport(item) }
  const importFromRecipesPhotos = async (files: File[]) => {
    const item = await api.importPhotos(files); addInboxItem(item); setCreatingRecipe(false); setReviewingImport(item)
    try { await extractInboxItem(item) } catch { /* feedback remains in review */ }
  }

  if (loading) return <div className="app-loading"><p>Opening Our Kitchen…</p></div>

  let content
  if (reviewingImport && importedRecipe) content = <RecipeForm key={`${reviewingImport.id}-${reviewingImport.updatedAt}`} recipe={importedRecipe} classifications={classifications} units={units} mode="review" sourceType={reviewingImport.sourceType} onSave={saveImportedRecipe} onExtract={async () => extractInboxItem(reviewingImport)} onRemoveImage={reviewingImport.assets.some((asset) => asset.role === 'cover') ? async () => { const updated = await api.removeImportImage(reviewingImport.id); addInboxItem(updated); setReviewingImport(updated) } : undefined} extracting={extractingImportId === reviewingImport.id} extractionMessage={importExtractionMessage} extractionError={importExtractionError} onCancel={() => setReviewingImport(null)} />
  else if (reviewingIdea) content = <RecipeForm recipe={draftToRecipe(reviewingIdea, 'generated-idea')} classifications={classifications} units={units} mode="review" sourceType="ai" onSave={saveGeneratedRecipe} onCancel={() => setReviewingIdea(null)} />
  else if (editingRecipe !== undefined) content = <RecipeForm recipe={editingRecipe} classifications={classifications} units={units} onSave={saveRecipe} onDelete={editingRecipe ? deleteRecipe : undefined} onRemoveImage={editingRecipe?.image ? async () => { await api.removeRecipePhoto(editingRecipe.id); const updated = await api.recipe(editingRecipe.id); setEditingRecipe(updated); setRecipes((items) => items.map((item) => item.id === updated.id ? updated : item)) } : undefined} onCancel={() => setEditingRecipe(undefined)} />
  else if (creatingRecipe) content = <RecipeCreation onBack={() => setCreatingRecipe(false)} onManual={() => { setCreatingRecipe(false); setEditingRecipe(null) }} onImportUrl={importFromRecipesUrl} onImportPhotos={importFromRecipesPhotos} />
  else if (selectedRecipe) content = <RecipeDetail recipe={selectedRecipe} onBack={() => setSelectedRecipe(null)} onAddToDeck={addToDeck} onEdit={() => setEditingRecipe(selectedRecipe)} onMadeThis={recordMadeThis} />
  else if (page === 'home') content = <Home recipes={recipes} deckRecipes={deck.map((entry) => entry.recipe)} search={search} onSearch={setSearch} onOpenRecipe={(recipe) => void openRecipe(recipe)} onOpenDeck={() => navigate('deck')} onBrowse={() => navigate('recipes')} onHelpPick={() => navigate('pick')} onWhatCanIMake={() => navigate('make')} onSettings={() => navigate('settings')} onAddToDeck={(recipe) => void addToDeck(recipe)} deckRecipeIds={deck.map((entry) => entry.recipe.id)} deckCount={deck.length} />
  else if (page === 'recipes') content = <Library recipes={recipes} initialSearch={search} onOpenRecipe={(recipe) => void openRecipe(recipe)} onAddRecipe={() => setCreatingRecipe(true)} onAddToDeck={(recipe) => void addToDeck(recipe)} deckRecipeIds={deck.map((entry) => entry.recipe.id)} />
  else if (page === 'deck') content = <Deck entries={deck} onChange={updateDeckEntry} onRemove={removeDeckEntry} onClearCompleted={clearCompleted} onBrowse={() => navigate('recipes')} onGroceries={() => navigate('groceries')} />
  else if (page === 'groceries') content = <Groceries list={groceryList} onPreview={api.previewGroceryUpdate} onApply={async () => { const updated = await api.applyGroceryUpdate(); setGroceryList(updated) }} onToggle={async (item) => { const updated = await api.updateGroceryItem(item.id, { checked: !item.checked }); setGroceryList((list) => ({ ...list, items: list.items.map((current) => current.id === updated.id ? updated : current) })) }} onAdd={async (label, category, quantity, unit) => { const item = await api.addGroceryItem({ label, category, quantity, unit }); setGroceryList((list) => ({ ...list, items: [...list.items, item] })) }} onEdit={async (item, patch) => { const updated = await api.updateGroceryItem(item.id, patch); setGroceryList((list) => ({ ...list, items: list.items.map((current) => current.id === updated.id ? updated : current) })) }} onDelete={async (item) => { await api.removeGroceryItem(item.id); setGroceryList((list) => ({ ...list, items: list.items.filter((current) => current.id !== item.id) })) }} onAddBack={async (staple) => { const item = await api.addBackStaple(staple.id); setGroceryList((list) => ({ ...list, items: [...list.items, item], excludedStaples: list.excludedStaples.filter((current) => current.id !== staple.id) })) }} />
  else if (page === 'settings') content = <Settings staples={pantryRecords.map((record) => record.name)} aiUsage={aiUsage} onChange={(names) => void updateStaples(names)} onBack={() => navigate('home')} />
  else if (page === 'make') content = <WhatCanIMake staples={pantryRecords.map((record) => record.name)} onOpenRecipe={(recipe) => void openRecipe(recipe)} onReviewIdea={setReviewingIdea} onBack={() => navigate('home')} />
  else if (page === 'pick') content = <HelpMePick onBack={() => navigate('home')} onOpenRecipe={(recipe) => void openRecipe(recipe)} onAddToDeck={(recipe) => void addToDeck(recipe)} onReviewIdea={setReviewingIdea} deckRecipeIds={deck.map((entry) => entry.recipe.id)} />
  else content = <Inbox items={inbox} onManual={() => setEditingRecipe(null)} onImportUrl={async (url) => { const item = await api.importUrl(url); addInboxItem(item) }} onImportPhotos={importFromRecipesPhotos} onReview={(item) => { setImportExtractionMessage(''); setImportExtractionError(''); setReviewingImport(item) }} onAiExtract={extractInboxItem} onRetry={async (item) => { const updated = await api.retryImport(item.id); setInbox((items) => items.map((current) => current.id === updated.id ? updated : current)) }} onDelete={async (item) => { if (!window.confirm(`Delete “${item.title}” from the Inbox?`)) return; await api.deleteImport(item.id); setInbox((items) => items.filter((current) => current.id !== item.id)) }} />

  return <Layout page={page} onNavigate={navigate}>{dataError && <p className="data-error" role="alert">{dataError}</p>}{dataNotice && <p className="data-success" role="status">{dataNotice}</p>}{content}</Layout>
}

function draftToRecipe(draft: RecipeInput, id: string): Recipe {
  return { id, title: draft.title, description: draft.description, status: draft.status, cuisine: draft.cuisine, proteins: draft.proteins ?? [], tags: draft.tags, categories: draft.categories, prepMinutes: draft.prep_minutes, cookMinutes: draft.cook_minutes, additionalTimeMinutes: draft.additional_time_minutes, additionalTimeLabel: draft.additional_time_label, baseServings: draft.base_servings, yieldUnit: draft.yield_unit, image: null, imageAlt: 'Generated recipe placeholder', ingredients: draft.ingredients.map(({ name, quantity, unit, note, package_detail, alternative_measurements }) => ({ name, quantity, unit: unit ?? undefined, note: note ?? undefined, packageDetail: package_detail ?? undefined, alternativeMeasurements: alternative_measurements?.map((measurement) => ({ quantity: measurement.quantity, unit: measurement.unit ?? undefined })) })), steps: draft.steps.map(({ instruction, tip }) => ({ instruction, tip: tip ?? undefined })), notes: draft.notes, source: { label: draft.source.label, url: draft.source.url ?? undefined }, cookingHistory: [] }
}

function inboxDraftToRecipe(item: InboxRecord): Recipe {
  const draft = item.draft
  const reviewImage = item.assets.find((asset) => asset.role === 'cover') ?? item.assets[0]
  return {
    id: item.id, title: draft.title, description: draft.description, status: draft.status, cuisine: draft.cuisine, proteins: draft.proteins ?? [],
    tags: draft.tags, categories: draft.categories, prepMinutes: draft.prep_minutes, cookMinutes: draft.cook_minutes, additionalTimeMinutes: draft.additional_time_minutes, additionalTimeLabel: draft.additional_time_label, baseServings: draft.base_servings, yieldUnit: draft.yield_unit,
    image: reviewImage?.url ?? null, imageAlt: reviewImage?.role === 'cover' ? 'Extracted recipe image' : item.assets.length ? 'Original uploaded recipe page' : 'Imported recipe placeholder',
    ingredients: draft.ingredients.map((ingredient) => ({ name: ingredient.name, quantity: ingredient.quantity, unit: ingredient.unit ?? undefined, note: ingredient.note ?? undefined, packageDetail: ingredient.package_detail ?? undefined, alternativeMeasurements: ingredient.alternative_measurements?.map((measurement) => ({ quantity: measurement.quantity, unit: measurement.unit ?? undefined })) })),
    steps: draft.steps.map((step) => ({ instruction: step.instruction, tip: step.tip ?? undefined })), notes: draft.notes,
    source: { label: draft.source.label, url: draft.source.url ?? undefined }, cookingHistory: [],
  }
}
