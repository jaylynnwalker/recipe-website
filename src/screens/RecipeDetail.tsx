import { useState } from 'react'
import type { Recipe } from '../types'
import { formatQuantity } from '../utils/formatQuantity'
import { Icon } from '../components/Icons'
import { RecipeImage } from '../components/RecipeCard'
import { api } from '../api'

type Tab = 'Ingredients' | 'Instructions' | 'Notes'

export function RecipeDetail({ recipe, onBack, onAddToDeck, onEdit, onMadeThis }: { recipe: Recipe; onBack: () => void; onAddToDeck: (recipe: Recipe) => void; onEdit: () => void; onMadeThis: () => Promise<void> }) {
  const [tab, setTab] = useState<Tab>('Ingredients')
  const [servings, setServings] = useState(recipe.baseServings)
  const [checked, setChecked] = useState<number[]>([])
  const [cookStep, setCookStep] = useState<number | null>(null)
  const scale = servings / recipe.baseServings
  const totalMinutes = recipe.prepMinutes + recipe.cookMinutes + (recipe.additionalTimeMinutes ?? 0)
  const badges = [
    ['status', recipe.status],
    ['cuisine', recipe.cuisine],
    ...(recipe.proteins ?? []).map((protein, index) => [`protein-${index}`, protein]),
  ].filter((badge): badge is [string, string] => Boolean(badge[1]?.trim()))

  if (cookStep !== null) {
    const step = recipe.steps[cookStep]
    return <div className="cook-mode">
      <header><button className="secondary" onClick={() => setCookStep(null)}>× Exit cook mode</button><span>{cookStep + 1} of {recipe.steps.length}</span></header>
      <div className="cook-content"><p className="eyebrow">{recipe.title}</p><h1>Step {cookStep + 1}</h1><p className="cook-instruction">{step.instruction}</p>{step.tip && <aside className="tip"><strong>Kitchen tip</strong>{step.tip}</aside>}<CookingAssistant recipe={recipe} currentStep={cookStep} /></div>
      <footer><button className="secondary" disabled={cookStep === 0} onClick={() => setCookStep((value) => Math.max(0, (value ?? 0) - 1))}>Previous</button><button className="primary" disabled={cookStep === recipe.steps.length - 1} onClick={() => setCookStep((value) => Math.min(recipe.steps.length - 1, (value ?? 0) + 1))}>Next step</button></footer>
    </div>
  }

  return <div className="page detail-page">
    <button className="back-button" onClick={onBack}>← Back to recipes</button>
    <div className="detail-hero"><RecipeImage recipe={recipe} /><div className="detail-title">{badges.length > 0 && <div className="tag-row">{badges.map(([key, value]) => <span key={key}>{value}</span>)}</div>}<h1>{recipe.title}</h1><p>{recipe.description}</p><div className="metadata"><span><Icon name="clock" size={19} /> Prep {recipe.prepMinutes} min</span><span>Cook {recipe.cookMinutes} min</span>{(recipe.additionalTimeMinutes ?? 0) > 0 && <span>{recipe.additionalTimeLabel || 'Additional'} {recipe.additionalTimeMinutes} min</span>}<span>Total {totalMinutes} min</span><span>{recipe.baseServings} {recipe.yieldUnit || 'servings'}</span>{recipe.cookingHistory?.length ? <span>Made {recipe.cookingHistory.length}×</span> : null}</div><div className="detail-actions"><button className="primary" onClick={() => setCookStep(0)}>Cook Mode</button><button className="secondary" onClick={() => onAddToDeck(recipe)}>+ Add to Deck</button><button className="secondary" onClick={() => void onMadeThis()}>✓ Made this</button><button className="icon-button" aria-label="Edit recipe" onClick={onEdit}>✎</button></div></div></div>
    <div className="tabs" role="tablist">{(['Ingredients', 'Instructions', 'Notes'] as Tab[]).map((item) => <button role="tab" aria-selected={tab === item} className={tab === item ? 'active' : ''} onClick={() => setTab(item)} key={item}>{item}</button>)}</div>
    <section className="tab-panel">
      {tab === 'Ingredients' && <><div className="servings"><div><strong>Servings</strong><small>Quantities adjust automatically</small></div><div className="stepper"><button aria-label="Decrease servings" disabled={servings === 1} onClick={() => setServings(servings - 1)}><Icon name="minus" size={17} /></button><output>{servings}</output><button aria-label="Increase servings" onClick={() => setServings(servings + 1)}><Icon name="plus" size={17} /></button></div></div><ul className="ingredient-list">{recipe.ingredients.map((ingredient, index) => <li key={`${ingredient.name}-${index}`}><label><input type="checkbox" checked={checked.includes(index)} onChange={() => setChecked((current) => current.includes(index) ? current.filter((item) => item !== index) : [...current, index])} /><span><strong>{formatMeasurement(ingredient.quantity, ingredient.unit, scale)}{ingredient.packageDetail ? ` (${ingredient.packageDetail})` : ''}{ingredient.alternativeMeasurements?.length ? ` (${ingredient.alternativeMeasurements.map((measurement) => formatMeasurement(measurement.quantity, measurement.unit, scale)).join('; ')})` : ''} </strong>{ingredient.name}{ingredient.note && <small>{ingredient.note}</small>}</span></label></li>)}</ul></>}
      {tab === 'Instructions' && <ol className="instruction-list">{recipe.steps.map((step, index) => <li key={step.instruction}><span className="step-number">{index + 1}</span><div><p>{step.instruction}</p>{step.tip && <aside className="tip"><strong>Kitchen tip</strong>{step.tip}</aside>}</div></li>)}</ol>}
      {tab === 'Notes' && <div className="notes"><h2>From our kitchen</h2><p>{recipe.notes}</p><hr /><p className="eyebrow">Source</p><p>{recipe.source.label}</p></div>}
    </section>
    <CookingAssistant recipe={recipe} />
  </div>
}

function formatMeasurement(quantity: number | null, unit: string | undefined, scale: number) {
  return quantity === null ? '' : `${formatQuantity(quantity * scale)}${unit ? ` ${unit}` : ''}`
}

function CookingAssistant({ recipe, currentStep }: { recipe: Recipe; currentStep?: number }) {
  const [question, setQuestion] = useState('')
  const [answer, setAnswer] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  return <aside className="cooking-assistant"><p className="eyebrow">Optional AI cooking help</p><h2>Ask about this recipe</h2><p>Try a substitution, technique, adaptation, or question. Answers never change the saved recipe.</p><div><input aria-label="Cooking question" value={question} onChange={(event) => setQuestion(event.target.value)} placeholder="What can I use instead of…?" /><button className="secondary" disabled={busy || question.trim().length < 2} onClick={async () => { setBusy(true); setError(''); try { setAnswer((await api.cookingAssist(recipe.id, question.trim(), currentStep)).answer) } catch (cause) { setError(cause instanceof Error ? cause.message : 'Unable to get cooking help') } finally { setBusy(false) } }}>{busy ? 'Asking…' : 'Ask'}</button></div>{answer && <p className="assistant-answer">{answer}</p>}{error && <p className="data-error">{error}</p>}</aside>
}
