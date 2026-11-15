import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'
import { Groceries } from './Groceries'

describe('Groceries', () => {
  it('collapses and expands grocery sections', async () => {
    const user = userEvent.setup()
    render(<Groceries />)
    const produce = screen.getByRole('button', { name: /Produce/ })

    expect(screen.getByText('2 lemons')).toBeInTheDocument()
    await user.click(produce)
    expect(screen.queryByText('2 lemons')).not.toBeInTheDocument()
    expect(produce).toHaveAttribute('aria-expanded', 'false')

    await user.click(produce)
    expect(screen.getByText('2 lemons')).toBeInTheDocument()
  })

  it('reviews excluded staples and adds one back to the list', async () => {
    const user = userEvent.setup()
    render(<Groceries staples={['Olive oil', 'Garlic']} />)

    await user.click(screen.getByRole('button', { name: /Pantry staples excluded/ }))
    await user.click(screen.getAllByRole('button', { name: '+ Add' })[0])

    expect(screen.getByRole('heading', { name: /Staples to restock/ })).toBeInTheDocument()
    expect(screen.getAllByText('Olive oil')).toHaveLength(2)
  })
})
