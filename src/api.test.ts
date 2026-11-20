import { afterEach, describe, expect, it, vi } from 'vitest'
import { api } from './api'

afterEach(() => vi.unstubAllGlobals())

describe('grocery API mapping', () => {
  it('maps the preview response to the frontend field names', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(JSON.stringify({
      additions: ['2 lb carrots'], updates: [], removals: [], excluded_staples: ['Salt'], unchanged_count: 3,
    }), { status: 200, headers: { 'Content-Type': 'application/json' } })))

    await expect(api.previewGroceryUpdate()).resolves.toEqual({
      additions: ['2 lb carrots'], updates: [], removals: [], excludedStaples: ['Salt'], unchangedCount: 3,
    })
  })
})
