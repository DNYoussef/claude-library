import { describe, it, expect } from 'vitest'

import { DIALOG_ANIMATIONS, DIALOG_SIZE_STYLES } from './types'

describe('radix-dialog styles', () => {
  it('defines size mappings including full', () => {
    expect(DIALOG_SIZE_STYLES).toHaveProperty('sm')
    expect(DIALOG_SIZE_STYLES).toHaveProperty('full')
    expect(DIALOG_SIZE_STYLES.full).toContain('90')
  })

  it('defines enter and exit animation classes', () => {
    expect(DIALOG_ANIMATIONS.overlay.enter).toContain('animate-in')
    expect(DIALOG_ANIMATIONS.overlay.exit).toContain('animate-out')
    expect(DIALOG_ANIMATIONS.content.enter).toContain('zoom-in')
    expect(DIALOG_ANIMATIONS.content.exit).toContain('zoom-out')
  })
})
