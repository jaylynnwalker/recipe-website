import { fireEvent, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { RecipeCreation } from './RecipeCreation'

describe('RecipeCreation', () => {
  const renderCreation = (overrides = {}) => {
    const props = { onBack: vi.fn(), onManual: vi.fn(), onImportUrl: vi.fn().mockResolvedValue(undefined), onImportPhotos: vi.fn().mockResolvedValue(undefined), ...overrides }
    render(<RecipeCreation {...props} />)
    return props
  }

  it('offers manual creation from Recipes', async () => {
    const user = userEvent.setup()
    const onManual = vi.fn()
    renderCreation({ onManual })
    await user.click(screen.getByRole('button', { name: 'Start a blank recipe' }))
    expect(onManual).toHaveBeenCalledOnce()
  })

  it('offers URL import from Recipes', async () => {
    const user = userEvent.setup()
    const onImportUrl = vi.fn().mockResolvedValue(undefined)
    renderCreation({ onImportUrl })
    await user.type(screen.getByLabelText('Recipe URL'), 'https://example.com/recipe')
    await user.click(screen.getByRole('button', { name: 'Save & extract' }))
    expect(onImportUrl).toHaveBeenCalledWith('https://example.com/recipe')
  })

  it('offers photo import from Recipes', async () => {
    const user = userEvent.setup()
    const onImportPhotos = vi.fn().mockResolvedValue(undefined)
    renderCreation({ onImportPhotos })
    const photo = new File(['photo'], 'recipe.jpg', { type: 'image/jpeg' })
    await user.upload(screen.getByLabelText('Recipe photos'), photo)
    const upload = screen.getByRole('button', { name: 'Upload & extract with AI' })
    fireEvent.submit(upload.closest('form')!)
    expect(onImportPhotos).toHaveBeenCalledWith([photo])
  })
})
