import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { recipes } from '../data'
import { RecipeDetail } from './RecipeDetail'

describe('RecipeDetail', () => {
  it('switches tabs and scales quantities', async () => {
    const user = userEvent.setup()
    render(<RecipeDetail recipe={recipes[0]} onBack={vi.fn()} onAddToDeck={vi.fn()} />)
    expect(screen.getByText(/1½/)).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Increase servings' }))
    expect(screen.getByText(/1.88/)).toBeInTheDocument()
    await user.click(screen.getByRole('tab', { name: 'Instructions' }))
    expect(screen.getByText(/Heat the oven/)).toBeInTheDocument()
  })
})
