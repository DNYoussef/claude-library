import { describe, it, expect } from 'vitest'

import { CSS_TOKENS } from './types'

describe('design-system tokens', () => {
  it('exposes semantic token groups', () => {
    expect(CSS_TOKENS).toHaveProperty('surfaces')
    expect(CSS_TOKENS).toHaveProperty('borders')
    expect(CSS_TOKENS).toHaveProperty('text')
    expect(CSS_TOKENS).toHaveProperty('semantic')
  })

  it('uses tailwind-style class tokens', () => {
    expect(CSS_TOKENS.surfaces.primary.startsWith('bg-')).toBe(true)
    expect(CSS_TOKENS.borders.default.startsWith('border-')).toBe(true)
    expect(CSS_TOKENS.text.primary.startsWith('text-')).toBe(true)
  })
})
