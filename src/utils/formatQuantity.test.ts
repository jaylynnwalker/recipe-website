import { describe, expect, it } from 'vitest'
import { formatQuantity } from './formatQuantity'

describe('formatQuantity', () => {
  it('formats cooking quantities', () => {
    expect(formatQuantity(1.5)).toBe('1½')
    expect(formatQuantity(0.25)).toBe('¼')
    expect(formatQuantity(3)).toBe('3')
    expect(formatQuantity(1.3333)).toBe('1⅓')
  })
})
