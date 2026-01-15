import { describe, it, expect } from 'vitest'

import { ITEM_VARIANT_STYLES, MENU_ANIMATIONS } from './types'

describe('radix-dropdown styles', () => {
  it('defines item variants', () => {
    expect(Object.keys(ITEM_VARIANT_STYLES)).toEqual(['default', 'destructive'])
    expect(ITEM_VARIANT_STYLES.destructive).toContain('text-error')
  })

  it('defines menu animations for all sides', () => {
    expect(MENU_ANIMATIONS.side).toHaveProperty('top')
    expect(MENU_ANIMATIONS.side).toHaveProperty('right')
    expect(MENU_ANIMATIONS.side).toHaveProperty('bottom')
    expect(MENU_ANIMATIONS.side).toHaveProperty('left')
  })
})
