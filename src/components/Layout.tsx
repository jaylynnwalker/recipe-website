import type { ReactNode } from 'react'
import { Icon } from './Icons'

export type Page = 'home' | 'recipes' | 'deck' | 'groceries' | 'inbox' | 'settings' | 'make'

const items = [
  { id: 'home', label: 'Home', desktopLabel: 'Home' },
  { id: 'recipes', label: 'Recipes', desktopLabel: 'Recipes' },
  { id: 'deck', label: 'Deck', desktopLabel: 'Meals on Deck' },
  { id: 'groceries', label: 'Groceries', desktopLabel: 'Grocery List' },
  { id: 'inbox', label: 'Inbox', desktopLabel: 'Recipe Inbox' },
] as const

export function Layout({ page, onNavigate, children }: { page: Page; onNavigate: (page: Page) => void; children: ReactNode }) {
  return <div className="app-shell">
    <aside className="sidebar">
      <button className="brand" onClick={() => onNavigate('home')}><span className="brand-mark">OK</span><span>Our Kitchen</span></button>
      <nav aria-label="Main navigation">
        {items.map((item) => <button key={item.id} className={page === item.id ? 'active' : ''} onClick={() => onNavigate(item.id)}><Icon name={item.id} /><span>{item.desktopLabel}</span></button>)}
      </nav>
      <button className={`sidebar-note ${page === 'settings' ? 'active' : ''}`} onClick={() => onNavigate('settings')}><span className="avatar">J</span><div><strong>Our household</strong><small>Household settings</small></div><span aria-hidden="true">›</span></button>
    </aside>
    <main>{children}</main>
    <nav className="bottom-nav" aria-label="Main navigation">
      {items.map((item) => <button key={item.id} className={page === item.id ? 'active' : ''} onClick={() => onNavigate(item.id)}><Icon name={item.id} size={21} /><span>{item.label}</span></button>)}
    </nav>
  </div>
}
