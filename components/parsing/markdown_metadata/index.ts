/**
 * Markdown Metadata Parser - Public API
 *
 * @module markdown-metadata
 * @version 1.0.0
 */

export {
  // Type Definitions
  type FrontmatterValue,
  type Frontmatter,
  type ParseResult,
  type ParseOptions,
  type SkillExtractionOptions,
  type SkillMetadata,
  type FileSearchResult,

  // Core Parsing
  detectType,
  parseFrontmatter,
  parseMarkdown,

  // Skill Metadata Extraction
  inferSkillName,
  getSkillName,
  getShortDescription,
  extractSkillMetadata,

  // File Discovery
  findMarkdownFiles,
  isValidSkillName,

  // Serialization
  serializeFrontmatter,
  createMarkdown
} from './markdown_metadata';
