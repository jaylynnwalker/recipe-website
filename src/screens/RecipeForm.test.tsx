import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { recipes } from '../data'
import { RecipeForm } from './RecipeForm'

describe('RecipeForm', () => {
  const classifications = { cuisines: ['Italian'], categories: ['Dinner'], tags: ['Quick'] }
  const units = { options: ['tsp', 'tbsp', 'cup', 'mL', 'whole', 'clove', 'slice', 'can'], aliases: { teaspoons: 'tsp', cups: 'cup', cloves: 'clove', ml: 'mL' } }

  it('displays a searchable multi-select protein field', async () => {
    const user = userEvent.setup()
    render(<RecipeForm classifications={classifications} units={units} onSave={vi.fn()} onCancel={vi.fn()} />)
    expect(screen.getByLabelText('Proteins')).toBeInTheDocument()
    await user.type(screen.getByLabelText('Proteins'), 'Chicken')
    await user.keyboard('{Enter}')
    expect(screen.getByText('Chicken')).toBeInTheDocument()
  })

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

  it('keeps an unknown imported yield blank and asks for it before saving', async () => {
    const user = userEvent.setup()
    const onSave = vi.fn().mockResolvedValue(undefined)
    const incomplete = { ...recipes[0], baseServings: null }
    render(<RecipeForm recipe={incomplete} mode="review" sourceType="instagram" classifications={classifications} units={units} onSave={onSave} onCancel={vi.fn()} />)
    expect(screen.getByLabelText('Yield amount')).toHaveValue(null)
    await user.click(screen.getByRole('button', { name: 'Save recipe' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Enter a yield amount between 1 and 100 before saving.')
    expect(onSave).not.toHaveBeenCalled()
    await user.type(screen.getByLabelText('Yield amount'), '3')
    await user.click(screen.getByRole('button', { name: 'Save recipe' }))
    expect(onSave).toHaveBeenCalledWith(expect.objectContaining({ base_servings: 3 }), undefined)
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
    await user.type(screen.getByLabelText('Categories'), 'Weeknight Dinner')
    await user.keyboard('{Enter}')
    await user.type(screen.getByLabelText('Categories'), 'Soup')
    await user.click(screen.getByRole('button', { name: 'Add category' }))
    await user.type(screen.getByLabelText('Tags'), ' quick ')
    await user.keyboard('{Enter}')
    await user.type(screen.getByLabelText('Tags'), 'Vegetarian')
    await user.click(screen.getByRole('button', { name: 'Add tag' }))
    await user.click(screen.getByRole('button', { name: 'Save recipe' }))
    expect(onSave).toHaveBeenCalledWith(expect.objectContaining({
      cuisine: 'Italian',
      categories: ['Weeknight Dinner', 'Soup'],
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

  it('preserves all existing categories when editing', async () => {
    const user = userEvent.setup()
    const onSave = vi.fn().mockResolvedValue(undefined)
    render(<RecipeForm recipe={{ ...recipes[0], categories: ['Soup', 'Main Dish'] }} classifications={{ ...classifications, categories: ['Soup', 'Main Dish'] }} units={units} onSave={onSave} onCancel={vi.fn()} />)
    expect(screen.getByText('Soup')).toBeInTheDocument()
    expect(screen.getByText('Main Dish')).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Save recipe' }))
    expect(onSave).toHaveBeenCalledWith(expect.objectContaining({ categories: ['Soup', 'Main Dish'] }), undefined)
  })

  it('adds alternative measurements and package details without changing the ingredient name', async () => {
    const user = userEvent.setup()
    const onSave = vi.fn().mockResolvedValue(undefined)
    render(<RecipeForm classifications={classifications} units={units} onSave={onSave} onCancel={vi.fn()} />)
    await user.type(screen.getByLabelText('Recipe title'), 'Beans')
    await user.type(screen.getByLabelText('Ingredient 1'), 'Black beans')
    await user.type(screen.getByLabelText('Quantity 1'), '2')
    await user.type(screen.getByLabelText('Unit 1'), 'can')
    await user.type(screen.getByLabelText('Package detail 1'), '15 oz each')
    await user.click(screen.getByRole('button', { name: '+ Add alternative measurement' }))
    await user.type(screen.getByLabelText('Alternative quantity 1.1'), '30')
    await user.type(screen.getByLabelText('Alternative unit 1.1'), 'oz')
    await user.type(screen.getByLabelText('Instruction 1'), 'Drain.')
    await user.click(screen.getByRole('button', { name: 'Save recipe' }))
    expect(onSave).toHaveBeenCalledWith(expect.objectContaining({ ingredients: [expect.objectContaining({ name: 'Black beans', package_detail: '15 oz each', alternative_measurements: [{ quantity: 30, unit: 'oz' }] })] }), undefined)
  })

  it('allows AI extraction during review and confirms before replacing edits', async () => {
    const user = userEvent.setup()
    const onExtract = vi.fn().mockResolvedValue(undefined)
    const confirm = vi.spyOn(window, 'confirm').mockReturnValue(false)
    render(<RecipeForm recipe={recipes[0]} mode="review" sourceType="photo" classifications={classifications} units={units} onSave={vi.fn()} onExtract={onExtract} onCancel={vi.fn()} />)
    await user.clear(screen.getByLabelText('Recipe title'))
    await user.type(screen.getByLabelText('Recipe title'), 'My edited title')
    await user.click(screen.getByRole('button', { name: 'Extract with AI' }))
    expect(confirm).toHaveBeenCalledWith('Re-extracting will replace your unsaved edits. Continue?')
    expect(onExtract).not.toHaveBeenCalled()
    confirm.mockReturnValue(true)
    await user.click(screen.getByRole('button', { name: 'Extract with AI' }))
    expect(onExtract).toHaveBeenCalledOnce()
  })

  it('preserves review fields and displays feedback when extraction fails', async () => {
    const user = userEvent.setup()
    const onExtract = vi.fn().mockRejectedValue(new Error('failed'))
    render(<RecipeForm recipe={recipes[0]} mode="review" sourceType="web" classifications={classifications} units={units} onSave={vi.fn()} onExtract={onExtract} extractionError="Extraction failed. Current details are unchanged." onCancel={vi.fn()} />)
    await user.clear(screen.getByLabelText('Recipe title'))
    await user.type(screen.getByLabelText('Recipe title'), 'Keep this title')
    vi.spyOn(window, 'confirm').mockReturnValue(true)
    await user.click(screen.getByRole('button', { name: 'Extract with AI' }))
    expect(screen.getByLabelText('Recipe title')).toHaveValue('Keep this title')
    expect(screen.getByRole('alert')).toHaveTextContent('Current details are unchanged')
  })
})
