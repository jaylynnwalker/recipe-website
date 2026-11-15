import { useState } from 'react'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { Settings } from './Settings'

function SettingsHarness() {
  const [staples, setStaples] = useState(['Olive oil', 'Garlic'])
  return <Settings staples={staples} onChange={setStaples} onBack={vi.fn()} />
}

describe('Settings pantry staples', () => {
  it('adds and removes pantry staples using local state', async () => {
    const user = userEvent.setup()
    render(<SettingsHarness />)

    await user.type(screen.getByLabelText('Add a pantry staple'), 'Rice')
    await user.click(screen.getByRole('button', { name: 'Add staple' }))
    expect(screen.getByText('Rice')).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Remove Garlic' }))
    expect(screen.queryByText('Garlic')).not.toBeInTheDocument()
  })
})
