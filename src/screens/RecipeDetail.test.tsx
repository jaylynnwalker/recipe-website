import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { recipes } from '../data'
import { RecipeDetail } from './RecipeDetail'

describe('RecipeDetail', () => {
  it('switches tabs and scales quantities', async () => {
    const user = userEvent.setup()
    render(<RecipeDetail recipe={recipes[0]} onBack={vi.fn()} onAddToDeck={vi.fn()} onEdit={vi.fn()} onMadeThis={vi.fn()} />)
    expect(screen.getByText(/1½/)).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Increase servings' }))
    expect(screen.getByText(/1.88/)).toBeInTheDocument()
    await user.click(screen.getByRole('tab', { name: 'Instructions' }))
    expect(screen.getByText(/Heat the oven/)).toBeInTheDocument()
  })

  it('does not render an empty cuisine badge for imported recipes', () => {
    const recipe = { ...recipes[0], cuisine: '   ' }
    const { container } = render(<RecipeDetail recipe={recipe} onBack={vi.fn()} onAddToDeck={vi.fn()} onEdit={vi.fn()} onMadeThis={vi.fn()} />)

    expect(screen.getByText('Our Rotation')).toBeInTheDocument()
    expect(container.querySelectorAll('.tag-row span')).toHaveLength(1)
    expect(container.querySelector('.tag-row')?.textContent).toBe('Our Rotation')
  })

  it('displays and scales primary and alternative measurements while preserving package details', async () => {
    const user = userEvent.setup()
    const recipe = { ...recipes[0], baseServings: 4, ingredients: [{ quantity: 226, unit: 'g', name: 'Flour', alternativeMeasurements: [{ quantity: 2, unit: 'cup' }] }, { quantity: 2, unit: 'can', name: 'Beans', packageDetail: '15 oz each' }] }
    render(<RecipeDetail recipe={recipe} onBack={vi.fn()} onAddToDeck={vi.fn()} onEdit={vi.fn()} onMadeThis={vi.fn()} />)
    expect(screen.getByText('Flour').closest('span')).toHaveTextContent('226 g (2 cup) Flour')
    expect(screen.getByText('Beans').closest('span')).toHaveTextContent('2 can (15 oz each) Beans')
    await user.click(screen.getByRole('button', { name: 'Increase servings' }))
    expect(screen.getByText('Flour').closest('span')).toHaveTextContent('282½ g (2½ cup) Flour')
    expect(screen.getByText('Beans').closest('span')).toHaveTextContent('2½ can (15 oz each) Beans')
  })

  it('shows yield and calculates total time with additional time once', () => {
    const recipe = { ...recipes[0], prepMinutes: 20, cookMinutes: 15, additionalTimeMinutes: 15, additionalTimeLabel: 'Resting', baseServings: 12, yieldUnit: 'rotis' }
    render(<RecipeDetail recipe={recipe} onBack={vi.fn()} onAddToDeck={vi.fn()} onEdit={vi.fn()} onMadeThis={vi.fn()} />)
    expect(screen.getByText('Resting 15 min')).toBeInTheDocument()
    expect(screen.getByText('Total 50 min')).toBeInTheDocument()
    expect(screen.getByText('12 rotis')).toBeInTheDocument()
  })
})
