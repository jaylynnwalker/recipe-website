import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { api } from './api'
import { App } from './App'
import { recipes } from './data'

vi.mock('./api', () => ({
  api: {
    recipes: vi.fn(), pantry: vi.fn(), deck: vi.fn(), groceryList: vi.fn(), inbox: vi.fn(), aiUsage: vi.fn(), classifications: vi.fn(), units: vi.fn(), importPhotos: vi.fn(), aiExtractImport: vi.fn(),
  },
}))

describe('App navigation', () => {
  beforeEach(() => {
    vi.mocked(api.recipes).mockResolvedValue([recipes[0]])
    vi.mocked(api.pantry).mockResolvedValue([])
    vi.mocked(api.deck).mockResolvedValue([])
    vi.mocked(api.groceryList).mockResolvedValue({ id: 'list', updatedAt: '', items: [], excludedStaples: [] })
    vi.mocked(api.inbox).mockResolvedValue([])
    vi.mocked(api.aiUsage).mockResolvedValue({ month: '2026-11', spent_usd: 0, reserved_usd: 0, budget_usd: 10, warning_usd: 8, warning: false, blocked: false, model: 'test', configured: false, disclaimer: '' })
    vi.mocked(api.classifications).mockResolvedValue({ categories: [], cuisines: [], tags: [] })
    vi.mocked(api.units).mockResolvedValue({ options: [], aliases: {} })
  })

  it('switches pages immediately and clears a higher-priority recipe workflow', async () => {
    const user = userEvent.setup()
    render(<App />)
    await screen.findByRole('heading', { name: 'Welcome back' })

    await user.click(screen.getAllByRole('button', { name: 'Recipes' })[0])
    expect(await screen.findByRole('heading', { name: 'Recipes' })).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: '+ Add recipe' }))
    expect(screen.getByRole('heading', { name: 'New Recipe' })).toBeInTheDocument()

    const groceriesNavigation = screen.getByRole('button', { name: 'Grocery List' })
    await user.click(groceriesNavigation)
    expect(await screen.findByRole('heading', { name: 'Grocery List' })).toBeInTheDocument()
    expect(screen.queryByRole('heading', { name: 'New Recipe' })).not.toBeInTheDocument()
    await waitFor(() => expect(groceriesNavigation).toHaveClass('active'))

    await user.click(screen.getAllByRole('button', { name: 'Recipes' })[0])
    expect(screen.getByText(recipes[0].title)).toBeInTheDocument()
  })

  it('automatically extracts an uploaded photo and opens the populated review form', async () => {
    const user = userEvent.setup()
    const pending = { id: 'photo-1', sourceType: 'photo' as const, sourceUrl: null, status: 'Ready for Review' as const, title: 'Photo recipe', draft: { title: 'Photo recipe', description: '', status: 'Want to Try' as const, cuisine: '', tags: [], categories: [], prep_minutes: 0, cook_minutes: 0, base_servings: 4, ingredients: [], steps: [], notes: '', source: { type: 'photo', label: 'Uploaded photos', url: null, page: null } }, errorMessage: null, duplicateRecipeId: null, savedRecipeId: null, assets: [{ id: 'asset', url: '/media/card.jpg', name: 'card.jpg', media_type: 'image/jpeg', position: 0 }], createdAt: '', updatedAt: 'one' }
    const extracted = { ...pending, title: 'Family Soup', updatedAt: 'two', draft: { ...pending.draft, title: 'Family Soup', ingredients: [{ name: 'Carrots', quantity: 2, unit: 'cup', note: null, optional: false }], steps: [{ instruction: 'Simmer.', tip: null }] } }
    vi.mocked(api.importPhotos).mockResolvedValue(pending)
    vi.mocked(api.aiExtractImport).mockResolvedValue(extracted)
    render(<App />)
    await screen.findByRole('heading', { name: 'Welcome back' })
    await user.click(screen.getAllByRole('button', { name: 'Recipes' })[0])
    await user.click(screen.getByRole('button', { name: '+ Add recipe' }))
    const photo = new File(['photo'], 'card.jpg', { type: 'image/jpeg' })
    await user.upload(screen.getByLabelText('Recipe photos'), photo)
    fireEvent.submit(screen.getByRole('button', { name: 'Upload & extract with AI' }).closest('form')!)
    expect(await screen.findByRole('heading', { name: 'Review imported recipe' })).toBeInTheDocument()
    await waitFor(() => expect(api.aiExtractImport).toHaveBeenCalledWith('photo-1'))
    expect(await screen.findByDisplayValue('Family Soup')).toBeInTheDocument()
    expect(screen.getByText(/Extraction complete/)).toBeInTheDocument()
  })
})
