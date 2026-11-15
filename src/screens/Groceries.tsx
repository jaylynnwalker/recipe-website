import { useState } from 'react'

const initial = [
  { category: 'Produce', items: ['2 lemons', '1 lb baby potatoes', 'Fresh basil', '1 cucumber'] },
  { category: 'Meat & seafood', items: ['1½ lb boneless chicken thighs', '12 oz salmon'] },
  { category: 'Dairy', items: ['½ cup heavy cream', 'Parmesan'] },
  { category: 'Pantry', items: ['12 oz rigatoni', '1 can crushed tomatoes'] },
]

export function Groceries({ staples = ['Olive oil', 'Garlic', 'Salt', 'Black pepper'] }: { staples?: string[] }) {
  const [checked, setChecked] = useState<string[]>(['Parmesan'])
  const [collapsed, setCollapsed] = useState<string[]>([])
  const [showExcluded, setShowExcluded] = useState(false)
  const [addedBack, setAddedBack] = useState<string[]>([])
  const total = initial.flatMap((group) => group.items).length + addedBack.length
  const toggleSection = (category: string) => setCollapsed((current) =>
    current.includes(category) ? current.filter((value) => value !== category) : [...current, category],
  )
  return <div className="page"><header className="page-header"><div><p className="eyebrow">Shared household list</p><h1>Grocery List</h1><p>Current list · {total - checked.length} items remaining</p></div><button className="secondary">Review deck changes</button></header>
    <div className="grocery-banner"><span>✓</span><p><strong>Your list is a saved snapshot.</strong> Meals on Deck can change without changing this list.</p><button>Update list</button></div>
    <section className="excluded-staples"><button className="excluded-summary" aria-expanded={showExcluded} onClick={() => setShowExcluded(!showExcluded)}><span><strong>Pantry staples excluded</strong><small>{staples.length - addedBack.length} items kept off this list</small></span><span aria-hidden="true">{showExcluded ? '⌃' : '⌄'}</span></button>{showExcluded && <div className="excluded-list"><p>Staples are excluded by default. Add one back when you need to restock it.</p><div className="ingredient-chips">{staples.map((staple) => <span className={`excluded-chip ${addedBack.includes(staple) ? 'added' : ''}`} key={staple}>{staple}<button disabled={addedBack.includes(staple)} onClick={() => setAddedBack([...addedBack, staple])}>{addedBack.includes(staple) ? 'Added' : '+ Add'}</button></span>)}</div></div>}</section>
    {addedBack.length > 0 && <section className="restock-items"><h2>Staples to restock <span>{addedBack.length}</span></h2>{addedBack.map((item) => <label className={checked.includes(item) ? 'checked' : ''} key={item}><input type="checkbox" checked={checked.includes(item)} onChange={() => setChecked((current) => current.includes(item) ? current.filter((value) => value !== item) : [...current, item])} /><span>{item}</span><button aria-label={`Remove ${item}`} onClick={() => setAddedBack(addedBack.filter((value) => value !== item))}>×</button></label>)}</section>}
    <div className="grocery-groups">{initial.map((group) => {
      const isCollapsed = collapsed.includes(group.category)
      const sectionId = `grocery-${group.category.toLowerCase().replaceAll(/[^a-z]+/g, '-')}`
      return <section key={group.category}>
        <h2><button className="grocery-section-toggle" aria-expanded={!isCollapsed} aria-controls={sectionId} onClick={() => toggleSection(group.category)}><span>{group.category}<small>{group.items.length}</small></span><span className="collapse-icon" aria-hidden="true">⌄</span></button></h2>
        {!isCollapsed && <div id={sectionId}>{group.items.map((item) => <label className={checked.includes(item) ? 'checked' : ''} key={item}><input type="checkbox" checked={checked.includes(item)} onChange={() => setChecked((current) => current.includes(item) ? current.filter((value) => value !== item) : [...current, item])} /><span>{item}</span><button aria-label={`Edit ${item}`}>•••</button></label>)}</div>}
      </section>
    })}</div>
    <button className="add-grocery">+ Add an item</button>
  </div>
}
