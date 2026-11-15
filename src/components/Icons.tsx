import type { ReactNode } from 'react'

type IconName = 'home' | 'recipes' | 'deck' | 'groceries' | 'inbox' | 'search' | 'sparkles' | 'clock' | 'plus' | 'minus' | 'arrow'

const paths: Record<IconName, ReactNode> = {
  home: <><path d="m3 11 9-8 9 8"/><path d="M5 10v10h14V10"/><path d="M9 20v-6h6v6"/></>,
  recipes: <><path d="M4 4.5A2.5 2.5 0 0 1 6.5 2H20v17H6.5A2.5 2.5 0 0 0 4 21.5z"/><path d="M4 4.5v17"/><path d="M8 6h8"/><path d="M8 10h6"/></>,
  deck: <><path d="M5 3v18"/><path d="M19 3v18"/><path d="M3 8h18"/><path d="M3 16h18"/><path d="M8 3v18"/><path d="M16 3v18"/></>,
  groceries: <><path d="M4 7h16l-1.5 14h-13z"/><path d="M8 7a4 4 0 0 1 8 0"/><path d="M8 11v1"/><path d="M16 11v1"/></>,
  inbox: <><path d="M4 4h16v16H4z"/><path d="m4 14 4-4 4 4 4-4 4 4"/><path d="M12 3v7"/><path d="m9 7 3 3 3-3"/></>,
  search: <><circle cx="11" cy="11" r="7"/><path d="m20 20-4-4"/></>,
  sparkles: <><path d="m12 3 1.4 3.6L17 8l-3.6 1.4L12 13l-1.4-3.6L7 8l3.6-1.4z"/><path d="m18 14 .8 2.2L21 17l-2.2.8L18 20l-.8-2.2L15 17l2.2-.8z"/><path d="m5 13 .8 2.2L8 16l-2.2.8L5 19l-.8-2.2L2 16l2.2-.8z"/></>,
  clock: <><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></>,
  plus: <><path d="M12 5v14"/><path d="M5 12h14"/></>,
  minus: <path d="M5 12h14"/>,
  arrow: <><path d="M5 12h14"/><path d="m14 7 5 5-5 5"/></>,
}

export function Icon({ name, size = 22 }: { name: IconName; size?: number }) {
  return <svg aria-hidden="true" className="icon" width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">{paths[name]}</svg>
}
