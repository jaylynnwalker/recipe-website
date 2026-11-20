import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import type { GroceryListRecord } from '../api'
import { Groceries } from './Groceries'

const list: GroceryListRecord = {
  id: 'list-1', updatedAt: '2026-11-14',
  items: [
    { id: '1', label: '2 lemons', name: 'lemons', quantity: 2, unit: null, category: 'Produce', checked: false, manual: false },
    { id: '2', label: 'Parmesan', name: 'parmesan', quantity: null, unit: null, category: 'Dairy & eggs', checked: true, manual: false },
  ],
  excludedStaples: [{ id: 'staple-1', name: 'Olive oil' }, { id: 'staple-2', name: 'Garlic' }],
}
const props = { list, onPreview: vi.fn().mockResolvedValue({ additions: [], updates: [], removals: [], excludedStaples: [], unchangedCount: 2 }), onApply: vi.fn(), onToggle: vi.fn(), onAdd: vi.fn(), onEdit: vi.fn(), onDelete: vi.fn(), onAddBack: vi.fn() }

describe('Groceries', () => {
  it('collapses and expands grocery sections', async () => {
    const user = userEvent.setup()
    render(<Groceries {...props} />)
    const produce = screen.getByRole('button', { name: /Produce/ })
    expect(screen.getByText('2 lemons')).toBeInTheDocument()
    await user.click(produce)
    expect(screen.queryByText('2 lemons')).not.toBeInTheDocument()
    expect(produce).toHaveAttribute('aria-expanded', 'false')
  })

  it('reviews excluded staples and requests an add-back', async () => {
    const user = userEvent.setup()
    const onAddBack = vi.fn().mockResolvedValue(undefined)
    render(<Groceries {...props} onAddBack={onAddBack} />)
    await user.click(screen.getByRole('button', { name: /Pantry staples excluded/ }))
    await user.click(screen.getAllByRole('button', { name: '+ Add' })[0])
    expect(onAddBack).toHaveBeenCalledWith(list.excludedStaples[0])
  })

  it('allows grocery items to be checked off', async () => {
    const user = userEvent.setup()
    const onToggle = vi.fn().mockResolvedValue(undefined)
    render(<Groceries {...props} onToggle={onToggle} />)
    await user.click(screen.getByRole('checkbox', { name: /2 lemons/ }))
    expect(onToggle).toHaveBeenCalledWith(list.items[0])
  })

  it('shows proposed changes before applying them', async () => {
    const user = userEvent.setup()
    render(<Groceries {...props} onPreview={vi.fn().mockResolvedValue({ additions: ['2 carrots'], updates: [], removals: ['Old item'], excludedStaples: ['Salt'], unchangedCount: 1 })} />)
    await user.click(screen.getByRole('button', { name: 'Review deck changes' }))
    expect(await screen.findByText('2 carrots')).toBeInTheDocument()
    expect(screen.getByText('Old item')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Apply update' })).toBeInTheDocument()
  })

  it('keeps the current list visible when preview generation fails', async () => {
    const user = userEvent.setup()
    render(<Groceries {...props} onPreview={vi.fn().mockRejectedValue(new Error('Unable to generate preview'))} />)
    await user.click(screen.getByRole('button', { name: 'Review deck changes' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Unable to generate preview')
    expect(screen.getByText('2 lemons')).toBeInTheDocument()
    expect(screen.getByText('Parmesan')).toBeInTheDocument()
  })

  it('keeps the current list and review open when applying fails', async () => {
    const user = userEvent.setup()
    render(<Groceries {...props} onApply={vi.fn().mockRejectedValue(new Error('Update failed'))} />)
    await user.click(screen.getByRole('button', { name: 'Review deck changes' }))
    await user.click(await screen.findByRole('button', { name: 'Apply update' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Update failed')
    expect(screen.getByRole('region', { name: 'Grocery list update review' })).toBeInTheDocument()
    expect(screen.getByText('2 lemons')).toBeInTheDocument()
  })
})
