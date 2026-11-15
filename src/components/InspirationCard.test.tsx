import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { recipes } from '../data'
import { InspirationCard } from './InspirationCard'

describe('InspirationCard', () => {
  it('opens the recipe and can add it directly to Meals on Deck', async () => {
    const user = userEvent.setup()
    const onOpen = vi.fn()
    const onAddToDeck = vi.fn()
    render(<InspirationCard suggestion={{ recipe: recipes[0], reason: 'Forgotten Favorite' }} onOpen={onOpen} onAddToDeck={onAddToDeck} isOnDeck={false} />)

    expect(screen.getByText('Forgotten Favorite')).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: `Open ${recipes[0].title}` }))
    await user.click(screen.getByRole('button', { name: '+ Add to Deck' }))

    expect(onOpen).toHaveBeenCalledOnce()
    expect(onAddToDeck).toHaveBeenCalledOnce()
  })

  it('shows when the recipe is already on deck', () => {
    render(<InspirationCard suggestion={{ recipe: recipes[0], reason: 'Rediscover' }} onOpen={vi.fn()} onAddToDeck={vi.fn()} isOnDeck />)
    expect(screen.getByRole('button', { name: 'On deck' })).toBeDisabled()
  })
})
