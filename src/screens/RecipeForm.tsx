import { useEffect, useRef, useState, type FormEvent, type RefObject, type TextareaHTMLAttributes } from 'react'
import type { Recipe, RecipeStatus } from '../types'
import type { ClassificationOptions, RecipeInput, UnitOptions } from '../api'
import { ClassificationFields } from '../components/ClassificationFields'
import { canonicalUnit, UnitField } from '../components/UnitField'

type MeasurementDraft = { quantity: string; unit: string }
type IngredientDraft = { name: string; quantity: string; unit: string; note: string; packageDetail: string; alternatives: MeasurementDraft[]; sectionIndex: number | null }
type StepDraft = { instruction: string; tip: string; sectionIndex: number | null }
export type ReviewRecipe = Omit<Recipe, 'baseServings'> & { baseServings: number | null }

const emptyIngredient = (): IngredientDraft => ({ name: '', quantity: '', unit: '', note: '', packageDetail: '', alternatives: [], sectionIndex: null })
const emptyStep = (): StepDraft => ({ instruction: '', tip: '', sectionIndex: null })

function AutoTextarea({ value, inputRef, ...props }: TextareaHTMLAttributes<HTMLTextAreaElement> & { value: string; inputRef?: RefObject<HTMLTextAreaElement | null> }) {
  const localRef = useRef<HTMLTextAreaElement>(null)
  const resize = (element: HTMLTextAreaElement | null) => {
    if (!element) return
    element.style.height = 'auto'
    element.style.height = `${element.scrollHeight}px`
  }
  useEffect(() => resize(inputRef?.current ?? localRef.current), [value, inputRef])
  return <textarea {...props} value={value} ref={(element) => { localRef.current = element; if (inputRef) inputRef.current = element; resize(element) }} onInput={(event) => resize(event.currentTarget)} />
}

export function RecipeForm({ recipe, classifications, units, mode = recipe ? 'edit' : 'add', sourceType, onSave, onExtract, onRemoveImage, extracting = false, extractionMessage = '', extractionError = '', onDelete, onCancel }: {
  recipe?: Recipe | ReviewRecipe | null
  classifications: ClassificationOptions
  units: UnitOptions
  mode?: 'add' | 'edit' | 'review'
  sourceType?: string
  onSave: (payload: RecipeInput, photo?: File) => Promise<void>
  onExtract?: (manualTranscript?: string) => Promise<void>
  onRemoveImage?: () => Promise<void>
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
  const [servings, setServings] = useState(recipe ? recipe.baseServings?.toString() ?? '' : '4')
  const [yieldUnit, setYieldUnit] = useState(recipe ? recipe.yieldUnit ?? '' : 'servings')
  const [ingredientSections, setIngredientSections] = useState(recipe?.ingredientSections ?? [])
  const [instructionSections, setInstructionSections] = useState(recipe?.instructionSections ?? [])
  const [ingredients, setIngredients] = useState<IngredientDraft[]>(recipe?.ingredients.map((item) => ({ name: item.name, quantity: item.quantity?.toString() ?? '', unit: item.unit ?? '', note: item.note ?? '', packageDetail: item.packageDetail ?? '', alternatives: item.alternativeMeasurements?.map((measurement) => ({ quantity: measurement.quantity.toString(), unit: measurement.unit ?? '' })) ?? [], sectionIndex: item.sectionIndex ?? null })) ?? [emptyIngredient()])
  const [steps, setSteps] = useState<StepDraft[]>(recipe?.steps.map((item) => ({ instruction: item.instruction, tip: item.tip ?? '', sectionIndex: item.sectionIndex ?? null })) ?? [emptyStep()])
  const [notes, setNotes] = useState(recipe?.notes ?? '')
  const [sourceName, setSourceName] = useState(recipe?.source.label ?? 'Household recipe')
  const [sourceUrl, setSourceUrl] = useState(recipe?.source.url ?? '')
  const [photo, setPhoto] = useState<File>()
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [dirty, setDirty] = useState(false)
  const [manualTranscript, setManualTranscript] = useState('')
  const [collapsedIngredientGroups, setCollapsedIngredientGroups] = useState<Set<string>>(new Set())
  const ingredientFocusRef = useRef<HTMLInputElement>(null)
  const stepFocusRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    const protectUnsavedChanges = (event: BeforeUnloadEvent) => {
      if (!dirty) return
      event.preventDefault()
      event.returnValue = ''
    }
    window.addEventListener('beforeunload', protectUnsavedChanges)
    return () => window.removeEventListener('beforeunload', protectUnsavedChanges)
  }, [dirty])

  const focusNew = (ref: RefObject<HTMLElement | null>) => requestAnimationFrame(() => {
    if (typeof ref.current?.scrollIntoView === 'function') ref.current.scrollIntoView({ behavior: 'smooth', block: 'center' })
    ref.current?.focus()
  })
  const cancel = () => {
    if (!dirty || window.confirm('Discard your unsaved recipe changes?')) onCancel()
  }

  const submit = async (event: FormEvent) => {
    event.preventDefault()
    const cleanIngredients = ingredients.filter((item) => item.name.trim())
    const cleanSteps = steps.filter((item) => item.instruction.trim())
    if (!title.trim() || !cleanIngredients.length || !cleanSteps.length) {
      setError('Add a title, at least one ingredient, and at least one instruction.')
      return
    }
    if ([...ingredientSections, ...instructionSections].some((heading) => !heading.trim())) {
      setError('Give each recipe section a heading or delete the empty section.')
      return
    }
    const servingCount = Number(servings)
    if (!servings || !Number.isInteger(servingCount) || servingCount < 1 || servingCount > 100) {
      setError('Enter a yield amount between 1 and 100 before saving.')
      return
    }
    setBusy(true); setError('')
    try {
      await onSave({
        title: title.trim(), description: description.trim(), status, cuisine: cuisine.trim(), proteins, categories, tags,
        prep_minutes: prepMinutes, cook_minutes: cookMinutes, additional_time_minutes: additionalTimeMinutes, additional_time_label: additionalTimeLabel.trim() || 'Additional', base_servings: servingCount, yield_unit: yieldUnit.trim() || 'servings',
        ingredient_sections: ingredientSections.map((heading) => ({ heading: heading.trim() })), instruction_sections: instructionSections.map((heading) => ({ heading: heading.trim() })),
        ingredients: cleanIngredients.map((item) => ({ name: item.name.trim(), quantity: item.quantity === '' ? null : Number(item.quantity), unit: canonicalUnit(item.unit, units) || null, note: item.note.trim() || null, optional: false, package_detail: item.packageDetail.trim() || null, section_index: item.sectionIndex, alternative_measurements: item.alternatives.filter((measurement) => measurement.quantity !== '').map((measurement) => ({ quantity: Number(measurement.quantity), unit: canonicalUnit(measurement.unit, units) || null })) })),
        steps: cleanSteps.map((item) => ({ instruction: item.instruction.trim(), tip: item.tip.trim() || null, section_index: item.sectionIndex })), notes: notes.trim(),
        source: { type: sourceType ?? (sourceUrl ? 'web' : 'household'), label: sourceName.trim() || 'Household recipe', url: sourceUrl.trim() || null, page: null },
      }, photo)
      setDirty(false)
    } catch (cause) { setError(cause instanceof Error ? cause.message : 'Unable to save recipe') }
    finally { setBusy(false) }
  }

  const updateIngredient = (index: number, key: 'name' | 'quantity' | 'unit' | 'note' | 'packageDetail', value: string) => setIngredients((items) => items.map((item, position) => position === index ? { ...item, [key]: value } : item))
  const updateAlternative = (ingredientIndex: number, measurementIndex: number, patch: Partial<MeasurementDraft>) => setIngredients((items) => items.map((item, position) => position === ingredientIndex ? { ...item, alternatives: item.alternatives.map((measurement, index) => index === measurementIndex ? { ...measurement, ...patch } : measurement) } : item))
  const updateStep = (index: number, key: 'instruction' | 'tip', value: string) => setSteps((items) => items.map((item, position) => position === index ? { ...item, [key]: value } : item))
  const addIngredient = (sectionIndex: number | null = null) => {
    setIngredients((items) => [...items, { ...emptyIngredient(), sectionIndex }])
    setDirty(true)
    focusNew(ingredientFocusRef)
  }
  const addStep = (afterIndex?: number, sectionIndex: number | null = null) => {
    setSteps((items) => {
      const next = [...items]
      next.splice(afterIndex === undefined ? next.length : afterIndex + 1, 0, { ...emptyStep(), sectionIndex })
      return next
    })
    setDirty(true)
    focusNew(stepFocusRef)
  }
  const moveItem = <T,>(items: T[], index: number, direction: -1 | 1, update: (items: T[]) => void) => {
    const target = index + direction
    if (target < 0 || target >= items.length) return
    const next = [...items]; [next[index], next[target]] = [next[target], next[index]]
    update(next); setDirty(true)
  }
  const deleteSection = (kind: 'ingredient' | 'instruction', index: number) => {
    const sectionName = (kind === 'ingredient' ? ingredientSections : instructionSections)[index]
    const affected = (kind === 'ingredient' ? ingredients : steps).filter((item) => item.sectionIndex === index).length
    if (affected > 0 && !window.confirm(`Delete “${sectionName}”? ${affected} ${kind === 'ingredient' ? `ingredient${affected === 1 ? '' : 's'}` : `step${affected === 1 ? '' : 's'}`} will be moved to No section.`)) return
    const updateItems = <T extends { sectionIndex: number | null }>(items: T[]) => items.map((item) => ({ ...item, sectionIndex: item.sectionIndex === index ? null : item.sectionIndex !== null && item.sectionIndex > index ? item.sectionIndex - 1 : item.sectionIndex }))
    if (kind === 'ingredient') { setIngredientSections((items) => items.filter((_, position) => position !== index)); setIngredients(updateItems) }
    else { setInstructionSections((items) => items.filter((_, position) => position !== index)); setSteps(updateItems) }
    setDirty(true)
  }
  const moveSection = (kind: 'ingredient' | 'instruction', index: number, direction: -1 | 1) => {
    const target = index + direction
    const remap = <T extends { sectionIndex: number | null }>(items: T[]) => items.map((item) => ({ ...item, sectionIndex: item.sectionIndex === index ? target : item.sectionIndex === target ? index : item.sectionIndex }))
    const swap = (items: string[]) => items.map((item, position) => position === index ? items[target] : position === target ? items[index] : item)
    if (kind === 'ingredient' && target >= 0 && target < ingredientSections.length) { setIngredientSections(swap); setIngredients(remap) }
    if (kind === 'instruction' && target >= 0 && target < instructionSections.length) { setInstructionSections(swap); setSteps(remap) }
    setDirty(true)
  }

  const renderIngredient = (item: IngredientDraft, index: number, isNewest: boolean) => <div className="ingredient-editor" key={index}>
    <div className="ingredient-fields">
      <input ref={isNewest ? ingredientFocusRef : undefined} className="ingredient-name-field" aria-label={`Ingredient ${index + 1}`} placeholder="Ingredient name" value={item.name} onChange={(event) => updateIngredient(index, 'name', event.target.value)} />
      <input className="ingredient-quantity-field" aria-label={`Quantity ${index + 1}`} type="number" min="0" step="any" placeholder="Qty" value={item.quantity} onChange={(event) => updateIngredient(index, 'quantity', event.target.value)} />
      <UnitField index={index} value={item.unit} units={units} onChange={(value) => updateIngredient(index, 'unit', value)} />
      <div className="row-controls"><button className="text-button" type="button" disabled={index === 0} aria-label={`Move ingredient ${index + 1} up`} onClick={() => moveItem(ingredients, index, -1, setIngredients)}>↑</button><button className="text-button" type="button" disabled={index === ingredients.length - 1} aria-label={`Move ingredient ${index + 1} down`} onClick={() => moveItem(ingredients, index, 1, setIngredients)}>↓</button><button className="remove-row" type="button" aria-label={`Remove ingredient ${index + 1}`} onClick={() => { setIngredients(ingredients.filter((_, position) => position !== index)); setDirty(true) }}>×</button></div>
      {ingredientSections.length > 0 && <select className="ingredient-section-select" aria-label={`Ingredient ${index + 1} section`} value={item.sectionIndex ?? ''} onChange={(event) => setIngredients((items) => items.map((ingredient, position) => position === index ? { ...ingredient, sectionIndex: event.target.value === '' ? null : Number(event.target.value) } : ingredient))}><option value="">No section</option>{ingredientSections.map((heading, sectionIndex) => <option key={sectionIndex} value={sectionIndex}>{heading}</option>)}</select>}
    </div>
    <details className="ingredient-extras" open={Boolean(item.note || item.packageDetail || item.alternatives.length)}><summary>Notes & measurements{item.note ? ' • Note added' : ''}</summary><div className="measurement-extras"><AutoTextarea aria-label={`Ingredient note ${index + 1}`} placeholder="Preparation note (optional)" rows={1} value={item.note} onChange={(event) => updateIngredient(index, 'note', event.target.value)} /><input aria-label={`Package detail ${index + 1}`} placeholder="Package size (e.g. 15 oz each)" value={item.packageDetail} onChange={(event) => updateIngredient(index, 'packageDetail', event.target.value)} />{item.alternatives.map((measurement, measurementIndex) => <div className="alternative-measurement" key={measurementIndex}><span>Alternative</span><input aria-label={`Alternative quantity ${index + 1}.${measurementIndex + 1}`} type="number" min="0" step="any" placeholder="Qty" value={measurement.quantity} onChange={(event) => updateAlternative(index, measurementIndex, { quantity: event.target.value })} /><UnitField index={index} ariaLabel={`Alternative unit ${index + 1}.${measurementIndex + 1}`} value={measurement.unit} units={units} onChange={(unit) => updateAlternative(index, measurementIndex, { unit })} /><button className="remove-row" type="button" aria-label={`Remove alternative measurement ${index + 1}.${measurementIndex + 1}`} onClick={() => setIngredients((items) => items.map((ingredient, position) => position === index ? { ...ingredient, alternatives: ingredient.alternatives.filter((_, alternatePosition) => alternatePosition !== measurementIndex) } : ingredient))}>×</button></div>)}<button className="text-button add-measurement" type="button" onClick={() => setIngredients((items) => items.map((ingredient, position) => position === index ? { ...ingredient, alternatives: [...ingredient.alternatives, { quantity: '', unit: '' }] } : ingredient))}>+ Add alternative measurement</button></div></details>
  </div>

  const ingredientEditorGroups = ingredientSections.length === 0
    ? [{ key: 'all', sectionIndex: null, heading: '', indexes: ingredients.map((_, index) => index) }]
    : [
        { key: 'none', sectionIndex: null, heading: 'No section', indexes: ingredients.map((_, index) => index).filter((index) => ingredients[index].sectionIndex === null) },
        ...ingredientSections.map((heading, sectionIndex) => ({ key: `section-${sectionIndex}`, sectionIndex, heading, indexes: ingredients.map((_, index) => index).filter((index) => ingredients[index].sectionIndex === sectionIndex) })),
      ]

  return <div className="page recipe-form-page">
    <button className="back-button" type="button" onClick={cancel}>← Back</button>
    <header className="page-header"><div><p className="eyebrow">{mode === 'review' ? 'Recipe Inbox' : 'Your collection'}</p><h1>{mode === 'review' ? 'Review imported recipe' : mode === 'edit' ? 'Edit recipe' : 'Add a recipe'}</h1><p>{mode === 'review' ? 'Correct anything that was unavailable or extracted incorrectly before saving.' : 'Keep the details that make this recipe yours.'}</p></div>{mode === 'review' && onExtract && <button className="secondary" type="button" disabled={extracting} onClick={async () => { if (dirty && !window.confirm('Re-extracting will replace your unsaved edits. Continue?')) return; try { await onExtract(manualTranscript) } catch { /* parent feedback preserves this form */ } }}>{extracting ? sourceType === 'youtube' ? 'Retrieving transcript…' : 'Extracting…' : 'Extract with AI'}</button>}</header>
    <form className="recipe-form" onSubmit={submit} onChangeCapture={() => setDirty(true)}>
      {extractionMessage && <p className="data-success" role="status">{extractionMessage}</p>}
      {extractionError && <p className="data-error" role="alert">{extractionError}</p>}
      {error && <p className="data-error" role="alert">{error}</p>}
      {mode === 'review' && sourceType === 'youtube' && <section><h2>YouTube transcript</h2><p>Public captions are retrieved automatically when available. If YouTube blocks them or no captions exist, paste transcript text here and retry extraction.</p><label className="wide">Transcript text<textarea rows={6} value={manualTranscript} placeholder="Paste transcript text (optional)" onChange={(event) => setManualTranscript(event.target.value)} /></label></section>}
      <section className="recipe-basics"><h2>Recipe details</h2><div className="form-grid">
        <label className="wide">Recipe title<input required maxLength={200} value={title} onChange={(event) => setTitle(event.target.value)} /></label>
        <label className="wide">Description<textarea value={description} onChange={(event) => setDescription(event.target.value)} rows={3} /></label>
        <label>Status<select value={status} onChange={(event) => setStatus(event.target.value as RecipeStatus)}><option>Our Rotation</option><option>Want to Try</option><option>Archived</option></select></label>
        <label>Yield amount<input type="number" min="1" max="100" value={servings} placeholder={mode === 'review' ? 'Enter amount' : undefined} onChange={(event) => setServings(event.target.value)} /></label>
        <label>Yield unit<input value={yieldUnit} placeholder="servings, rotis, slices…" onChange={(event) => setYieldUnit(event.target.value)} /></label>
        <label>Prep time (minutes)<input type="number" min="0" value={prepMinutes} onChange={(event) => setPrepMinutes(Number(event.target.value))} /></label>
        <label>Cook time (minutes)<input type="number" min="0" value={cookMinutes} onChange={(event) => setCookMinutes(Number(event.target.value))} /></label>
        <label>Additional time label<input value={additionalTimeLabel} placeholder="Resting, chilling…" onChange={(event) => setAdditionalTimeLabel(event.target.value)} /></label>
        <label>Additional time (minutes)<input type="number" min="0" value={additionalTimeMinutes} onChange={(event) => setAdditionalTimeMinutes(Number(event.target.value))} /></label>
        <ClassificationFields options={classifications} cuisine={cuisine} proteins={proteins} categories={categories} tags={tags} onCuisineChange={setCuisine} onProteinsChange={setProteins} onCategoriesChange={setCategories} onTagsChange={setTags} />
      </div></section>
      <div className="recipe-content-editors">
      <section className="ingredients-editor-section"><div className="form-section-title"><h2>Ingredients</h2></div>
        <p className="section-help">Use sections for recipe components such as Crust, Filling, Sauce, or Topping. Simple recipes can remain unsectioned.</p>
        <div className="ingredient-section-editor">{ingredientEditorGroups.map((group) => {
          if (group.sectionIndex === null && ingredientSections.length > 0 && group.indexes.length === 0) return null
          const sectionIndex = group.sectionIndex
          const collapsed = collapsedIngredientGroups.has(group.key)
          return <div className={`ingredient-section-group${sectionIndex === null ? ' unsectioned' : ''}`} key={group.key}>
            {ingredientSections.length > 0 && (sectionIndex === null
              ? <button type="button" className="group-collapse" aria-expanded={!collapsed} onClick={() => setCollapsedIngredientGroups((current) => toggleSet(current, group.key))}><span><h3>No section</h3><small>{group.indexes.length} ingredient{group.indexes.length === 1 ? '' : 's'}</small></span><span>{collapsed ? '⌄' : '⌃'}</span></button>
              : <div className="ingredient-section-toolbar"><button type="button" className="group-collapse" aria-expanded={!collapsed} onClick={() => setCollapsedIngredientGroups((current) => toggleSet(current, group.key))}><span>{ingredientSections[sectionIndex]} <small>{group.indexes.length} ingredient{group.indexes.length === 1 ? '' : 's'}</small></span><span>{collapsed ? '⌄' : '⌃'}</span></button><div className="section-edit-row"><input aria-label={`Ingredient section ${sectionIndex + 1} heading`} value={ingredientSections[sectionIndex]} onChange={(event) => setIngredientSections((items) => items.map((item, position) => position === sectionIndex ? event.target.value : item))} /><button type="button" className="text-button" disabled={sectionIndex === 0} aria-label={`Move ingredient section ${sectionIndex + 1} up`} onClick={() => moveSection('ingredient', sectionIndex, -1)}>↑</button><button type="button" className="text-button" disabled={sectionIndex === ingredientSections.length - 1} aria-label={`Move ingredient section ${sectionIndex + 1} down`} onClick={() => moveSection('ingredient', sectionIndex, 1)}>↓</button><button type="button" className="remove-row" aria-label={`Delete ingredient section ${sectionIndex + 1}`} onClick={() => deleteSection('ingredient', sectionIndex)}>×</button></div></div>)}
            {!collapsed && <><div className="form-repeater">{group.indexes.map((ingredientIndex) => renderIngredient(ingredients[ingredientIndex], ingredientIndex, ingredientIndex === ingredients.length - 1))}</div><button type="button" className="text-button group-add" onClick={() => addIngredient(sectionIndex)}>+ Add ingredient</button></>}
          </div>
        })}</div>
        <button className="secondary section-add" type="button" aria-label="+ Add section" onClick={() => { setIngredientSections([...ingredientSections, `Ingredient group ${ingredientSections.length + 1}`]); setDirty(true) }}>+ Add Group</button>
      </section>
      <section className="instructions-editor-section"><div className="form-section-title"><h2>Instructions</h2><div><button className="secondary small" type="button" onClick={() => { setInstructionSections([...instructionSections, `Instruction section ${instructionSections.length + 1}`]); setDirty(true) }}>+ Add section</button></div></div>
        {instructionSections.length > 0 && <div className="section-manager">{instructionSections.map((heading, index) => <div key={index}><input aria-label={`Instruction section ${index + 1} heading`} value={heading} onChange={(event) => setInstructionSections((items) => items.map((item, position) => position === index ? event.target.value : item))} /><button type="button" className="text-button" aria-label={`Add instruction to section ${index + 1}`} onClick={() => addStep(undefined, index)}>+</button><button type="button" className="text-button" disabled={index === 0} aria-label={`Move instruction section ${index + 1} up`} onClick={() => moveSection('instruction', index, -1)}>↑</button><button type="button" className="text-button" disabled={index === instructionSections.length - 1} aria-label={`Move instruction section ${index + 1} down`} onClick={() => moveSection('instruction', index, 1)}>↓</button><button type="button" className="remove-row" aria-label={`Delete instruction section ${index + 1}`} onClick={() => deleteSection('instruction', index)}>×</button></div>)}</div>}
        <div className="form-repeater">{steps.map((step, index) => <div className="step-fields" key={index}><span>{index + 1}</span><div>{instructionSections.length > 0 && <select aria-label={`Instruction ${index + 1} section`} value={step.sectionIndex ?? ''} onChange={(event) => setSteps((items) => items.map((item, position) => position === index ? { ...item, sectionIndex: event.target.value === '' ? null : Number(event.target.value) } : item))}><option value="">No section</option>{instructionSections.map((heading, sectionIndex) => <option key={sectionIndex} value={sectionIndex}>{heading}</option>)}</select>}<AutoTextarea inputRef={index === steps.length - 1 ? stepFocusRef : undefined} aria-label={`Instruction ${index + 1}`} placeholder="Describe this step" rows={2} value={step.instruction} onChange={(event) => updateStep(index, 'instruction', event.target.value)} /><details className="step-extras" open={Boolean(step.tip)}><summary>Optional tip & references</summary><AutoTextarea aria-label={`Cooking tip ${index + 1}`} placeholder="Inline cooking tip (optional)" rows={1} value={step.tip} onChange={(event) => updateStep(index, 'tip', event.target.value)} /></details><button className="text-button insert-step" type="button" onClick={() => addStep(index, step.sectionIndex)}>+ Insert step after</button></div><div className="row-controls"><button className="text-button" type="button" disabled={index === 0} aria-label={`Move instruction ${index + 1} up`} onClick={() => moveItem(steps, index, -1, setSteps)}>↑</button><button className="text-button" type="button" disabled={index === steps.length - 1} aria-label={`Move instruction ${index + 1} down`} onClick={() => moveItem(steps, index, 1, setSteps)}>↓</button><button className="remove-row" type="button" aria-label={`Remove instruction ${index + 1}`} onClick={() => { setSteps(steps.filter((_, position) => position !== index)); setDirty(true) }}>×</button></div></div>)}</div>
        <button className="secondary section-add" type="button" onClick={() => addStep()}>+ Add Step</button>
      </section>
      </div>
      <section><h2>Source & notes</h2><div className="form-grid"><label>Source name<input value={sourceName} onChange={(event) => setSourceName(event.target.value)} /></label><label>Original URL<input type="url" value={sourceUrl} onChange={(event) => setSourceUrl(event.target.value)} /></label><label className="wide">Kitchen notes<textarea rows={3} value={notes} onChange={(event) => setNotes(event.target.value)} /></label><label className="wide">Recipe photo <small>JPEG, PNG, or WebP. Choosing a file replaces the extracted image when saved.</small><input type="file" accept="image/jpeg,image/png,image/webp" onChange={(event) => setPhoto(event.target.files?.[0])} /></label>{onRemoveImage && <button className="remove" type="button" onClick={() => void onRemoveImage()}>Remove extracted image</button>}</div></section>
      <div className="form-actions">{recipe && onDelete && <button className="danger" type="button" disabled={busy} onClick={async () => { if (window.confirm(`Delete “${recipe.title}”? This cannot be undone.`)) { setBusy(true); try { await onDelete() } catch (cause) { setError(cause instanceof Error ? cause.message : 'Unable to delete recipe'); setBusy(false) } } }}>Delete recipe</button>}<span /><button className="secondary" type="button" onClick={cancel}>Cancel</button><button className="primary" disabled={busy}>{busy ? 'Saving…' : mode === 'edit' ? 'Save Changes' : 'Save recipe'}</button></div>
    </form>
  </div>
}

function toggleSet(current: Set<string>, key: string) {
  const next = new Set(current)
  if (next.has(key)) next.delete(key)
  else next.add(key)
  return next
}
