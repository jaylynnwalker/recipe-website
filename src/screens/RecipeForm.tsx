import { useState, type FormEvent } from 'react'
import type { Recipe, RecipeStatus } from '../types'
import type { ClassificationOptions, RecipeInput, UnitOptions } from '../api'
import { ClassificationFields } from '../components/ClassificationFields'
import { canonicalUnit, UnitField } from '../components/UnitField'

type MeasurementDraft = { quantity: string; unit: string }
type IngredientDraft = { name: string; quantity: string; unit: string; note: string; packageDetail: string; alternatives: MeasurementDraft[] }
type StepDraft = { instruction: string; tip: string }

const emptyIngredient = (): IngredientDraft => ({ name: '', quantity: '', unit: '', note: '', packageDetail: '', alternatives: [] })
const emptyStep = (): StepDraft => ({ instruction: '', tip: '' })

export function RecipeForm({ recipe, classifications, units, mode = recipe ? 'edit' : 'add', sourceType, onSave, onExtract, extracting = false, extractionMessage = '', extractionError = '', onDelete, onCancel }: {
  recipe?: Recipe | null
  classifications: ClassificationOptions
  units: UnitOptions
  mode?: 'add' | 'edit' | 'review'
  sourceType?: string
  onSave: (payload: RecipeInput, photo?: File) => Promise<void>
  onExtract?: () => Promise<void>
  extracting?: boolean
  extractionMessage?: string
  extractionError?: string
  onDelete?: () => Promise<void>
  onCancel: () => void
}) {
  const [title, setTitle] = useState(recipe?.title ?? '')
  const [description, setDescription] = useState(recipe?.description ?? '')
  const [status, setStatus] = useState<RecipeStatus>(recipe?.status ?? 'Want to Try')
  const [cuisine, setCuisine] = useState(recipe?.cuisine ?? '')
  const [proteins, setProteins] = useState(recipe?.proteins ?? [])
  const [categories, setCategories] = useState(recipe?.categories ?? [])
  const [tags, setTags] = useState(recipe?.tags ?? [])
  const [prepMinutes, setPrepMinutes] = useState(recipe?.prepMinutes ?? 0)
  const [cookMinutes, setCookMinutes] = useState(recipe?.cookMinutes ?? 0)
  const [additionalTimeMinutes, setAdditionalTimeMinutes] = useState(recipe?.additionalTimeMinutes ?? 0)
  const [additionalTimeLabel, setAdditionalTimeLabel] = useState(recipe?.additionalTimeLabel ?? 'Additional')
  const [servings, setServings] = useState(recipe?.baseServings ?? 4)
  const [yieldUnit, setYieldUnit] = useState(recipe?.yieldUnit ?? 'servings')
  const [ingredients, setIngredients] = useState<IngredientDraft[]>(recipe?.ingredients.map((item) => ({ name: item.name, quantity: item.quantity?.toString() ?? '', unit: item.unit ?? '', note: item.note ?? '', packageDetail: item.packageDetail ?? '', alternatives: item.alternativeMeasurements?.map((measurement) => ({ quantity: measurement.quantity.toString(), unit: measurement.unit ?? '' })) ?? [] })) ?? [emptyIngredient()])
  const [steps, setSteps] = useState<StepDraft[]>(recipe?.steps.map((item) => ({ instruction: item.instruction, tip: item.tip ?? '' })) ?? [emptyStep()])
  const [notes, setNotes] = useState(recipe?.notes ?? '')
  const [sourceName, setSourceName] = useState(recipe?.source.label ?? 'Household recipe')
  const [sourceUrl, setSourceUrl] = useState(recipe?.source.url ?? '')
  const [photo, setPhoto] = useState<File>()
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [dirty, setDirty] = useState(false)

  const submit = async (event: FormEvent) => {
    event.preventDefault()
    const cleanIngredients = ingredients.filter((item) => item.name.trim())
    const cleanSteps = steps.filter((item) => item.instruction.trim())
    if (!title.trim() || !cleanIngredients.length || !cleanSteps.length) {
      setError('Add a title, at least one ingredient, and at least one instruction.')
      return
    }
    setBusy(true); setError('')
    try {
      await onSave({
        title: title.trim(), description: description.trim(), status, cuisine: cuisine.trim(), proteins, categories, tags,
        prep_minutes: prepMinutes, cook_minutes: cookMinutes, additional_time_minutes: additionalTimeMinutes, additional_time_label: additionalTimeLabel.trim() || 'Additional', base_servings: servings, yield_unit: yieldUnit.trim() || 'servings',
        ingredients: cleanIngredients.map((item) => ({ name: item.name.trim(), quantity: item.quantity === '' ? null : Number(item.quantity), unit: canonicalUnit(item.unit, units) || null, note: item.note.trim() || null, optional: false, package_detail: item.packageDetail.trim() || null, alternative_measurements: item.alternatives.filter((measurement) => measurement.quantity !== '').map((measurement) => ({ quantity: Number(measurement.quantity), unit: canonicalUnit(measurement.unit, units) || null })) })),
        steps: cleanSteps.map((item) => ({ instruction: item.instruction.trim(), tip: item.tip.trim() || null })), notes: notes.trim(),
        source: { type: sourceType ?? (sourceUrl ? 'web' : 'household'), label: sourceName.trim() || 'Household recipe', url: sourceUrl.trim() || null, page: null },
      }, photo)
    } catch (cause) { setError(cause instanceof Error ? cause.message : 'Unable to save recipe') }
    finally { setBusy(false) }
  }

  const updateIngredient = (index: number, key: keyof IngredientDraft, value: string) => setIngredients((items) => items.map((item, position) => position === index ? { ...item, [key]: value } : item))
  const updateAlternative = (ingredientIndex: number, measurementIndex: number, patch: Partial<MeasurementDraft>) => setIngredients((items) => items.map((item, position) => position === ingredientIndex ? { ...item, alternatives: item.alternatives.map((measurement, index) => index === measurementIndex ? { ...measurement, ...patch } : measurement) } : item))
  const updateStep = (index: number, key: keyof StepDraft, value: string) => setSteps((items) => items.map((item, position) => position === index ? { ...item, [key]: value } : item))

  return <div className="page recipe-form-page">
    <button className="back-button" type="button" onClick={onCancel}>← Back</button>
    <header className="page-header"><div><p className="eyebrow">{mode === 'review' ? 'Recipe Inbox' : 'Your collection'}</p><h1>{mode === 'review' ? 'Review imported recipe' : mode === 'edit' ? 'Edit recipe' : 'Add a recipe'}</h1><p>{mode === 'review' ? 'Correct anything that was unavailable or extracted incorrectly before saving.' : 'Keep the details that make this recipe yours.'}</p></div>{mode === 'review' && onExtract && <button className="secondary" type="button" disabled={extracting} onClick={async () => { if (dirty && !window.confirm('Re-extracting will replace your unsaved edits. Continue?')) return; try { await onExtract() } catch { /* parent feedback preserves this form */ } }}>{extracting ? 'Extracting…' : 'Extract with AI'}</button>}</header>
    <form className="recipe-form" onSubmit={submit} onChangeCapture={() => setDirty(true)}>
      {extractionMessage && <p className="data-success" role="status">{extractionMessage}</p>}
      {extractionError && <p className="data-error" role="alert">{extractionError}</p>}
      {error && <p className="data-error" role="alert">{error}</p>}
      <section><h2>Recipe details</h2><div className="form-grid">
        <label className="wide">Recipe title<input required maxLength={200} value={title} onChange={(event) => setTitle(event.target.value)} /></label>
        <label className="wide">Description<textarea value={description} onChange={(event) => setDescription(event.target.value)} rows={3} /></label>
        <label>Status<select value={status} onChange={(event) => setStatus(event.target.value as RecipeStatus)}><option>Our Rotation</option><option>Want to Try</option><option>Archived</option></select></label>
        <label>Yield amount<input type="number" min="1" max="100" value={servings} onChange={(event) => setServings(Number(event.target.value))} /></label>
        <label>Yield unit<input value={yieldUnit} placeholder="servings, rotis, slices…" onChange={(event) => setYieldUnit(event.target.value)} /></label>
        <label>Prep time (minutes)<input type="number" min="0" value={prepMinutes} onChange={(event) => setPrepMinutes(Number(event.target.value))} /></label>
        <label>Cook time (minutes)<input type="number" min="0" value={cookMinutes} onChange={(event) => setCookMinutes(Number(event.target.value))} /></label>
        <label>Additional time label<input value={additionalTimeLabel} placeholder="Resting, chilling…" onChange={(event) => setAdditionalTimeLabel(event.target.value)} /></label>
        <label>Additional time (minutes)<input type="number" min="0" value={additionalTimeMinutes} onChange={(event) => setAdditionalTimeMinutes(Number(event.target.value))} /></label>
        <ClassificationFields options={classifications} cuisine={cuisine} proteins={proteins} categories={categories} tags={tags} onCuisineChange={setCuisine} onProteinsChange={setProteins} onCategoriesChange={setCategories} onTagsChange={setTags} />
      </div></section>
      <section><div className="form-section-title"><h2>Ingredients</h2><button className="secondary small" type="button" onClick={() => setIngredients([...ingredients, emptyIngredient()])}>+ Add ingredient</button></div>
        <div className="form-repeater">{ingredients.map((item, index) => <div className="ingredient-editor" key={index}><div className="ingredient-fields"><input aria-label={`Ingredient ${index + 1}`} placeholder="Ingredient" value={item.name} onChange={(event) => updateIngredient(index, 'name', event.target.value)} /><input aria-label={`Quantity ${index + 1}`} type="number" min="0" step="any" placeholder="Qty" value={item.quantity} onChange={(event) => updateIngredient(index, 'quantity', event.target.value)} /><UnitField index={index} value={item.unit} units={units} onChange={(value) => updateIngredient(index, 'unit', value)} /><input aria-label={`Ingredient note ${index + 1}`} placeholder="Note (optional)" value={item.note} onChange={(event) => updateIngredient(index, 'note', event.target.value)} /><button className="remove-row" type="button" aria-label={`Remove ingredient ${index + 1}`} onClick={() => setIngredients(ingredients.filter((_, position) => position !== index))}>×</button></div><div className="measurement-extras"><input aria-label={`Package detail ${index + 1}`} placeholder="Package size (e.g. 15 oz each)" value={item.packageDetail} onChange={(event) => updateIngredient(index, 'packageDetail', event.target.value)} />{item.alternatives.map((measurement, measurementIndex) => <div className="alternative-measurement" key={measurementIndex}><span>Alternative</span><input aria-label={`Alternative quantity ${index + 1}.${measurementIndex + 1}`} type="number" min="0" step="any" placeholder="Qty" value={measurement.quantity} onChange={(event) => updateAlternative(index, measurementIndex, { quantity: event.target.value })} /><UnitField index={index} ariaLabel={`Alternative unit ${index + 1}.${measurementIndex + 1}`} value={measurement.unit} units={units} onChange={(unit) => updateAlternative(index, measurementIndex, { unit })} /><button className="remove-row" type="button" aria-label={`Remove alternative measurement ${index + 1}.${measurementIndex + 1}`} onClick={() => setIngredients((items) => items.map((ingredient, position) => position === index ? { ...ingredient, alternatives: ingredient.alternatives.filter((_, alternatePosition) => alternatePosition !== measurementIndex) } : ingredient))}>×</button></div>)}<button className="text-button add-measurement" type="button" onClick={() => setIngredients((items) => items.map((ingredient, position) => position === index ? { ...ingredient, alternatives: [...ingredient.alternatives, { quantity: '', unit: '' }] } : ingredient))}>+ Add alternative measurement</button></div></div>)}</div>
      </section>
      <section><div className="form-section-title"><h2>Instructions</h2><button className="secondary small" type="button" onClick={() => setSteps([...steps, emptyStep()])}>+ Add step</button></div>
        <div className="form-repeater">{steps.map((step, index) => <div className="step-fields" key={index}><span>{index + 1}</span><div><textarea aria-label={`Instruction ${index + 1}`} placeholder="Describe this step" rows={2} value={step.instruction} onChange={(event) => updateStep(index, 'instruction', event.target.value)} /><input aria-label={`Cooking tip ${index + 1}`} placeholder="Inline cooking tip (optional)" value={step.tip} onChange={(event) => updateStep(index, 'tip', event.target.value)} /></div><button className="remove-row" type="button" aria-label={`Remove instruction ${index + 1}`} onClick={() => setSteps(steps.filter((_, position) => position !== index))}>×</button></div>)}</div>
      </section>
      <section><h2>Source & notes</h2><div className="form-grid"><label>Source name<input value={sourceName} onChange={(event) => setSourceName(event.target.value)} /></label><label>Original URL<input type="url" value={sourceUrl} onChange={(event) => setSourceUrl(event.target.value)} /></label><label className="wide">Kitchen notes<textarea rows={3} value={notes} onChange={(event) => setNotes(event.target.value)} /></label><label className="wide">Recipe photo <small>JPEG, PNG, or WebP</small><input type="file" accept="image/jpeg,image/png,image/webp" onChange={(event) => setPhoto(event.target.files?.[0])} /></label></div></section>
      <div className="form-actions">{recipe && onDelete && <button className="danger" type="button" disabled={busy} onClick={async () => { if (window.confirm(`Delete “${recipe.title}”? This cannot be undone.`)) { setBusy(true); try { await onDelete() } catch (cause) { setError(cause instanceof Error ? cause.message : 'Unable to delete recipe'); setBusy(false) } } }}>Delete recipe</button>}<span /><button className="secondary" type="button" onClick={onCancel}>Cancel</button><button className="primary" disabled={busy}>{busy ? 'Saving…' : 'Save recipe'}</button></div>
    </form>
  </div>
}
