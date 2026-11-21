import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { recipes } from '../data'
import { Library } from './Library'

describe('Library category filtering', () => {
  it('finds a recipe by any of its categories', async () => {
    const user = userEvent.setup()
    const categorized = { ...recipes[0], title: 'Black Bean Soup', categories: ['Soup', 'Main Dish'] }
    render(<Library recipes={[categorized, { ...recipes[1], categories: ['Dessert'] }]} initialSearch="" onOpenRecipe={vi.fn()} onAddRecipe={vi.fn()} onAddToDeck={vi.fn()} deckRecipeIds={[]} />)

    const search = screen.getByRole('textbox', { name: 'Search recipes' })
    await user.type(search, 'Main Dish')
    expect(screen.getByText('Black Bean Soup')).toBeInTheDocument()
    expect(screen.queryByText(recipes[1].title)).not.toBeInTheDocument()

    await user.clear(search)
    await user.selectOptions(screen.getByRole('combobox', { name: 'Filter by category' }), 'Soup')
    expect(screen.getByText('Black Bean Soup')).toBeInTheDocument()
    expect(screen.queryByText(recipes[1].title)).not.toBeInTheDocument()
  })
})
