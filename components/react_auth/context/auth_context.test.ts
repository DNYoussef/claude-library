import { describe, it, expect } from 'vitest'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const targetPath = path.join(__dirname, 'index.ts')
const exportsList = ['useHasPermission', 'useHasRole', 'useIsAuthenticated', 'useUser']

describe('auth-context', () => {
  it('has source file', () => {
    expect(fs.existsSync(targetPath)).toBe(true)
  })

  it('contains declared exports in source', () => {
    if (exportsList.length === 0) return
    const source = fs.readFileSync(targetPath, 'utf8')
    for (const name of exportsList) {
      expect(source).toContain(name)
    }
  })
})
