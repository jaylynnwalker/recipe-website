import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { RecipeForm } from './RecipeForm'

describe('RecipeForm', () => {
  const classifications = { cuisines: ['Italian'], categories: ['Dinner'], tags: ['Quick'] }
  const units = { options: ['tsp', 'tbsp', 'cup', 'mL', 'whole', 'clove', 'slice', 'can'], aliases: { teaspoons: 'tsp', cups: 'cup', cloves: 'clove', ml: 'mL' } }

  it('builds a recipe payload from the manual form', async () => {
    const user = userEvent.setup()
    const onSave = vi.fn().mockResolvedValue(undefined)
    render(<RecipeForm classifications={classifications} units={units} onSave={onSave} onCancel={vi.fn()} />)
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

  it('supports selecting and creating normalized classifications', async () => {
    const user = userEvent.setup()
    const onSave = vi.fn().mockResolvedValue(undefined)
    render(<RecipeForm classifications={classifications} units={units} onSave={onSave} onCancel={vi.fn()} />)
    await user.type(screen.getByLabelText('Recipe title'), 'Tomato Pasta')
    await user.type(screen.getByLabelText('Ingredient 1'), 'Tomatoes')
    await user.type(screen.getByLabelText('Instruction 1'), 'Simmer.')
    await user.type(screen.getByLabelText('Cuisine'), ' italian ')
    await user.tab()
    await user.type(screen.getByLabelText('Category'), 'Weeknight Dinner')
    await user.type(screen.getByLabelText('Tags'), ' quick ')
    await user.keyboard('{Enter}')
    await user.type(screen.getByLabelText('Tags'), 'Vegetarian')
    await user.click(screen.getByRole('button', { name: 'Add tag' }))
    await user.click(screen.getByRole('button', { name: 'Save recipe' }))
    expect(onSave).toHaveBeenCalledWith(expect.objectContaining({
      cuisine: 'Italian',
      categories: ['Weeknight Dinner'],
      tags: ['Quick', 'Vegetarian'],
    }), undefined)
  })

  it('normalizes common aliases and preserves custom units', async () => {
    const user = userEvent.setup()
    const onSave = vi.fn().mockResolvedValue(undefined)
    render(<RecipeForm classifications={classifications} units={units} onSave={onSave} onCancel={vi.fn()} />)
    await user.type(screen.getByLabelText('Recipe title'), 'Seasoned Rice')
    await user.type(screen.getByLabelText('Ingredient 1'), 'Salt')
    await user.type(screen.getByLabelText('Quantity 1'), '2')
    await user.type(screen.getByLabelText('Unit 1'), 'teaspoons')
    await user.type(screen.getByLabelText('Instruction 1'), 'Stir.')
    await user.click(screen.getByRole('button', { name: '+ Add ingredient' }))
    await user.type(screen.getByLabelText('Ingredient 2'), 'Saffron')
    await user.type(screen.getByLabelText('Unit 2'), 'threads')
    await user.click(screen.getByRole('button', { name: 'Save recipe' }))
    expect(onSave).toHaveBeenCalledWith(expect.objectContaining({ ingredients: [
      expect.objectContaining({ unit: 'tsp' }), expect.objectContaining({ unit: 'threads' }),
    ] }), undefined)
  })
})
