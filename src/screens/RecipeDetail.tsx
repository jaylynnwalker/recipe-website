import { useState } from 'react'
import type { Recipe } from '../types'
import { formatQuantity } from '../utils/formatQuantity'
import { Icon } from '../components/Icons'
import { RecipeImage } from '../components/RecipeCard'

type Tab = 'Ingredients' | 'Instructions' | 'Notes'

export function RecipeDetail({ recipe, onBack, onAddToDeck }: { recipe: Recipe; onBack: () => void; onAddToDeck: (recipe: Recipe) => void }) {
  const [tab, setTab] = useState<Tab>('Ingredients')
  const [servings, setServings] = useState(recipe.baseServings)
  const [checked, setChecked] = useState<number[]>([])
  const [cookStep, setCookStep] = useState<number | null>(null)
  const scale = servings / recipe.baseServings

  if (cookStep !== null) {
    const step = recipe.steps[cookStep]
    return <div className="cook-mode">
      <header><button className="secondary" onClick={() => setCookStep(null)}>× Exit cook mode</button><span>{cookStep + 1} of {recipe.steps.length}</span></header>
      <div className="cook-content"><p className="eyebrow">{recipe.title}</p><h1>Step {cookStep + 1}</h1><p className="cook-instruction">{step.instruction}</p>{step.tip && <aside className="tip"><strong>Kitchen tip</strong>{step.tip}</aside>}</div>
      <footer><button className="secondary" disabled={cookStep === 0} onClick={() => setCookStep((value) => Math.max(0, (value ?? 0) - 1))}>Previous</button><button className="primary" disabled={cookStep === recipe.steps.length - 1} onClick={() => setCookStep((value) => Math.min(recipe.steps.length - 1, (value ?? 0) + 1))}>Next step</button></footer>
    </div>
  }

  return <div className="page detail-page">
    <button className="back-button" onClick={onBack}>← Back to recipes</button>
    <div className="detail-hero"><RecipeImage recipe={recipe} /><div className="detail-title"><div className="tag-row"><span>{recipe.status}</span><span>{recipe.cuisine}</span></div><h1>{recipe.title}</h1><p>{recipe.description}</p><div className="metadata"><span><Icon name="clock" size={19} /> Prep {recipe.prepMinutes} min</span><span>Cook {recipe.cookMinutes} min</span></div><div className="detail-actions"><button className="primary" onClick={() => setCookStep(0)}>Cook Mode</button><button className="secondary" onClick={() => onAddToDeck(recipe)}>+ Add to Deck</button><button className="icon-button" aria-label="Edit recipe">✎</button></div></div></div>
    <div className="tabs" role="tablist">{(['Ingredients', 'Instructions', 'Notes'] as Tab[]).map((item) => <button role="tab" aria-selected={tab === item} className={tab === item ? 'active' : ''} onClick={() => setTab(item)} key={item}>{item}</button>)}</div>
    <section className="tab-panel">
      {tab === 'Ingredients' && <><div className="servings"><div><strong>Servings</strong><small>Quantities adjust automatically</small></div><div className="stepper"><button aria-label="Decrease servings" disabled={servings === 1} onClick={() => setServings(servings - 1)}><Icon name="minus" size={17} /></button><output>{servings}</output><button aria-label="Increase servings" onClick={() => setServings(servings + 1)}><Icon name="plus" size={17} /></button></div></div><ul className="ingredient-list">{recipe.ingredients.map((ingredient, index) => <li key={ingredient.name}><label><input type="checkbox" checked={checked.includes(index)} onChange={() => setChecked((current) => current.includes(index) ? current.filter((item) => item !== index) : [...current, index])} /><span><strong>{ingredient.quantity === null ? '' : `${formatQuantity(ingredient.quantity * scale)} ${ingredient.unit ?? ''}`} </strong>{ingredient.name}{ingredient.note && <small>{ingredient.note}</small>}</span></label></li>)}</ul></>}
      {tab === 'Instructions' && <ol className="instruction-list">{recipe.steps.map((step, index) => <li key={step.instruction}><span className="step-number">{index + 1}</span><div><p>{step.instruction}</p>{step.tip && <aside className="tip"><strong>Kitchen tip</strong>{step.tip}</aside>}</div></li>)}</ol>}
      {tab === 'Notes' && <div className="notes"><h2>From our kitchen</h2><p>{recipe.notes}</p><hr /><p className="eyebrow">Source</p><p>{recipe.source.label}</p></div>}
    </section>
  </div>
}
