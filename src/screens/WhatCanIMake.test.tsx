import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { recipes } from '../data'
import { WhatCanIMake } from './WhatCanIMake'

describe('What Can I Make', () => {
  it('includes pantry staples by default and separates sample result types', async () => {
    const user = userEvent.setup()
    render(<WhatCanIMake staples={['Olive oil', 'Garlic']} recipes={recipes} onOpenRecipe={vi.fn()} onBack={vi.fn()} />)

    expect(screen.getByRole('checkbox', { name: 'Include my pantry staples' })).toBeChecked()
    await user.click(screen.getByRole('button', { name: 'Find Recipes' }))

    expect(screen.getByRole('heading', { name: 'Matching Saved Recipes' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Potential Recipe Ideas' })).toBeInTheDocument()
    expect(screen.getByText(/no AI request has been made/i)).toBeInTheDocument()
  })

  it('adds and removes individual ingredients', async () => {
    const user = userEvent.setup()
    render(<WhatCanIMake staples={['Olive oil']} recipes={recipes} onOpenRecipe={vi.fn()} onBack={vi.fn()} />)

    await user.type(screen.getByLabelText('Additional ingredients'), 'mushrooms')
    await user.click(screen.getByRole('button', { name: 'Add' }))
    expect(screen.getByText('mushrooms')).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Remove mushrooms' }))
    expect(screen.queryByText('mushrooms')).not.toBeInTheDocument()
  })
})
