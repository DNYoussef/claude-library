import { describe, it, expect } from 'vitest'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const targetPath = path.join(__dirname, 'index.ts')
const exportsList = ['DEFAULT_3_COLUMN_CONFIG', 'DEFAULT_4_COLUMN_CONFIG', 'DEFAULT_5_COLUMN_CONFIG', 'DEV_PIPELINE_CONFIG', 'SCRUM_COLUMN_CONFIG', 'createLocalStoragePersistenceAdapter', 'findItemInColumns', 'organizeItemsByColumn', 'selectColumnCounts', 'selectItemById', 'selectTotalCount', 'useTaskKanban']

describe('kanban-store', () => {
  it('has source file', () => {
    expect(fs.existsSync(targetPath)).toBe(true)
  })

  it('contains declared exports in source', () => {
    // LIB-005: Fail fast if no exports declared - prevents tautological test
    expect(exportsList.length, 'exportsList must not be empty - declare exports to test').toBeGreaterThan(0)
    const source = fs.readFileSync(targetPath, 'utf8')
    for (const name of exportsList) {
      expect(source).toContain(name)
    }
  })
})
