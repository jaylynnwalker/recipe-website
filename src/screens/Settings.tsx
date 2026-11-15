import { useState, type FormEvent } from 'react'

export function Settings({ staples, onChange, onBack }: { staples: string[]; onChange: (staples: string[]) => void; onBack: () => void }) {
  const [ingredient, setIngredient] = useState('')
  const addStaple = (event: FormEvent) => {
    event.preventDefault()
    const value = ingredient.trim()
    if (value && !staples.some((staple) => staple.toLowerCase() === value.toLowerCase())) onChange([...staples, value])
    setIngredient('')
  }

  return <div className="page settings-page">
    <button className="back-button mobile-settings-back" onClick={onBack}>← Back home</button>
    <header className="page-header"><div><p className="eyebrow">Shared preferences</p><h1>Household Settings</h1><p>Changes here apply to everyone in Our Kitchen.</p></div></header>
    <section className="settings-card">
      <div className="settings-heading"><div><p className="eyebrow">Ingredients always on hand</p><h2>Pantry Staples</h2></div><span>{staples.length} staples</span></div>
      <p className="settings-explainer">Staples are normally excluded when a grocery list is generated. They are also considered available when you use What Can I Make?</p>
      <div className="ingredient-chips" aria-label="Current pantry staples">{staples.map((staple) => <span className="ingredient-chip" key={staple}>{staple}<button aria-label={`Remove ${staple}`} onClick={() => onChange(staples.filter((item) => item !== staple))}>×</button></span>)}</div>
      <form className="add-ingredient-form" onSubmit={addStaple}><label htmlFor="new-staple">Add a pantry staple</label><div><input id="new-staple" value={ingredient} onChange={(event) => setIngredient(event.target.value)} placeholder="e.g. canned tomatoes" /><button className="primary" type="submit" disabled={!ingredient.trim()}>Add staple</button></div></form>
    </section>
  </div>
}
