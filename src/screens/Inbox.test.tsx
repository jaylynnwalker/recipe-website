import { fireEvent, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import type { InboxRecord } from '../api'
import { Inbox } from './Inbox'

const draft = { title: 'Imported Soup', description: '', status: 'Want to Try' as const, cuisine: '', protein: '', tags: [], categories: [], prep_minutes: 0, cook_minutes: 0, base_servings: 4, ingredients: [], steps: [], notes: '', source: { type: 'web', label: 'example.com', url: 'https://example.com/soup', page: null } }
const item: InboxRecord = { id: 'inbox-1', sourceType: 'web', sourceUrl: 'https://example.com/soup', status: 'Ready for Review', title: 'Imported Soup', draft, errorMessage: null, duplicateRecipeId: 'recipe-1', savedRecipeId: null, assets: [], createdAt: '', updatedAt: '' }
const props = { items: [item], onManual: vi.fn(), onImportUrl: vi.fn(), onImportPhotos: vi.fn(), onReview: vi.fn(), onRetry: vi.fn(), onAiExtract: vi.fn(), onDelete: vi.fn() }

describe('Inbox', () => {
  it('shows persistent status and duplicate warnings and opens review', async () => {
    const user = userEvent.setup()
    const onReview = vi.fn()
    render(<Inbox {...props} onReview={onReview} />)
    expect(screen.getByText('Ready for Review')).toBeInTheDocument()
    expect(screen.getByText(/Potential duplicate/)).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Review' }))
    expect(onReview).toHaveBeenCalledWith(item)
  })

  it('submits a recipe URL', async () => {
    const user = userEvent.setup()
    const onImportUrl = vi.fn().mockResolvedValue(undefined)
    render(<Inbox {...props} items={[]} onImportUrl={onImportUrl} />)
    await user.type(screen.getByLabelText('Recipe URL'), 'https://example.com/recipe')
    await user.click(screen.getByRole('button', { name: 'Save & extract' }))
    expect(onImportUrl).toHaveBeenCalledWith('https://example.com/recipe')
  })

  it('can start a manual recipe from the shared creation choices', async () => {
    const user = userEvent.setup()
    const onManual = vi.fn()
    render(<Inbox {...props} items={[]} onManual={onManual} />)
    await user.click(screen.getByRole('button', { name: 'Start a blank recipe' }))
    expect(onManual).toHaveBeenCalledOnce()
  })

  it('accepts recipe photos through the shared creation choices', async () => {
    const user = userEvent.setup()
    const onImportPhotos = vi.fn().mockResolvedValue(undefined)
    render(<Inbox {...props} items={[]} onImportPhotos={onImportPhotos} />)
    const photo = new File(['photo'], 'card.jpg', { type: 'image/jpeg' })
    await user.upload(screen.getByLabelText('Recipe photos'), photo)
    const upload = screen.getByRole('button', { name: 'Save 1 photo' })
    fireEvent.submit(upload.closest('form')!)
    expect(onImportPhotos).toHaveBeenCalledWith([photo])
  })
})
