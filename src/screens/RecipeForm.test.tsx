import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { RecipeForm } from './RecipeForm'

describe('RecipeForm', () => {
  it('builds a recipe payload from the manual form', async () => {
    const user = userEvent.setup()
    const onSave = vi.fn().mockResolvedValue(undefined)
    render(<RecipeForm onSave={onSave} onCancel={vi.fn()} />)
    await user.type(screen.getByLabelText('Recipe title'), 'Weeknight Soup')
    await user.type(screen.getByLabelText('Ingredient 1'), 'Carrots')
    await user.type(screen.getByLabelText('Quantity 1'), '2')
    await user.type(screen.getByLabelText('Instruction 1'), 'Simmer until tender.')
    await user.click(screen.getByRole('button', { name: 'Save recipe' }))
    expect(onSave).toHaveBeenCalledWith(expect.objectContaining({
      title: 'Weeknight Soup',
      ingredients: [expect.objectContaining({ name: 'Carrots', quantity: 2 })],
      steps: [{ instruction: 'Simmer until tender.', tip: null }],
    }), undefined)
  })
})
