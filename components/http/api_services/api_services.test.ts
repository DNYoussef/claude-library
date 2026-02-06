import { describe, it, expect } from 'vitest'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const targetPath = path.join(__dirname, 'index.ts')
const exportsList = ['ApiClient', 'BaseResourceService', 'CalendarService', 'IdeasService', 'NotesService', 'ProductivityService', 'QAPipelineService', 'QAService', 'QueryBuilder', 'RecoveryService', 'SpecPipelineService', 'createApiClient', 'createAuthenticatedClient', 'createCalendarService', 'createClientFromEnv', 'createIdeasService', 'createNotesService', 'createProductivityService', 'createQAPipelineService', 'createQAService', 'createRecoveryService', 'createServicesFromEnv', 'createSpecPipelineService', 'getFieldError', 'getValidationErrors', 'isApiError', 'isForbidden', 'isHttpStatus', 'isNotFound', 'isTimeout', 'isUnauthorized', 'isValidationError', 'query']

describe('api-services', () => {
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
