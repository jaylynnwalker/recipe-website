import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { WhatCanIMake } from './WhatCanIMake'

const props = { staples: ['Olive oil', 'Garlic'], onOpenRecipe: vi.fn(), onReviewIdea: vi.fn(), onBack: vi.fn() }

describe('What Can I Make', () => {
  it('includes pantry staples by default and renders saved API matches', async () => {
    const user = userEvent.setup()
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, status: 200, json: async () => ({ saved_matches: [], generated_ideas: [] }) }))
    render(<WhatCanIMake {...props} />)

    expect(screen.getByRole('checkbox', { name: 'Include my pantry staples' })).toBeChecked()
    await user.click(screen.getByRole('button', { name: 'Find Saved Recipes' }))
    expect(fetch).toHaveBeenCalledWith('/api/ai/what-can-i-make', expect.objectContaining({ method: 'POST' }))
  })

  it('adds and removes individual ingredients', async () => {
    const user = userEvent.setup()
    render(<WhatCanIMake {...props} staples={['Olive oil']} />)

    await user.type(screen.getByLabelText('Additional ingredients'), 'mushrooms')
    await user.click(screen.getByRole('button', { name: 'Add' }))
    expect(screen.getByText('mushrooms')).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Remove mushrooms' }))
    expect(screen.queryByText('mushrooms')).not.toBeInTheDocument()
  })
})
