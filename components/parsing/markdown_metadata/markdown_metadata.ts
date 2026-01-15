/**
 * Markdown Metadata Parser
 *
 * Extracted from Context Cascade create-skill-cache.js
 * Zero dependencies - uses Node.js stdlib only
 *
 * Features:
 * - YAML frontmatter extraction
 * - Multiline value handling
 * - Type detection (string, number, boolean, array)
 * - File path inference for skill names
 *
 * @module markdown-metadata
 * @version 1.0.0
 * @license MIT
 */

import * as fs from 'fs';
import * as path from 'path';

// ============================================================================
// Type Definitions
// ============================================================================

/**
 * Supported value types in frontmatter
 *
 * Represents the possible types that can be extracted from YAML frontmatter:
 * - string: Plain text values
 * - number: Integer or floating-point numeric values
 * - boolean: true/false values
 * - string[]: Array of strings (YAML flow sequences)
 * - null: Explicit null, empty values, or ~ notation
 */
export type FrontmatterValue = string | number | boolean | string[] | null;

/**
 * Parsed frontmatter as key-value record
 */
export type Frontmatter = Record<string, FrontmatterValue>;

/**
 * Result of parsing a markdown file
 */
export interface ParseResult {
  /** Extracted frontmatter metadata */
  frontmatter: Frontmatter | null;
  /** Content after frontmatter (body) */
  content: string;
  /** Whether frontmatter was found */
  hasFrontmatter: boolean;
  /** Raw frontmatter string (between --- delimiters) */
  rawFrontmatter: string | null;
}

/**
 * Options for frontmatter parsing
 */
export interface ParseOptions {
  /** Whether to detect and convert types (default: true) */
  detectTypes?: boolean;
  /** Whether to trim values (default: true) */
  trimValues?: boolean;
  /** Whether to handle multiline values (default: true) */
  handleMultiline?: boolean;
  /** Custom type detector function */
  typeDetector?: (value: string) => FrontmatterValue;
}

/**
 * Options for extracting skill metadata
 */
export interface SkillExtractionOptions extends ParseOptions {
  /** Fallback name if none found */
  fallbackName?: string;
  /** Maximum description length before truncation */
  maxDescriptionLength?: number;
}

/**
 * Extracted skill metadata
 */
export interface SkillMetadata {
  /** Skill name (from frontmatter or inferred from path) */
  name: string;
  /** Short description (first sentence or truncated) */
  description: string;
  /** Full frontmatter */
  frontmatter: Frontmatter | null;
  /** Source file path */
  sourcePath: string;
}

/**
 * Result of finding markdown files
 */
export interface FileSearchResult {
  /** Full path to the file */
  path: string;
  /** File name */
  name: string;
  /** Parent directory name */
  directory: string;
}

// ============================================================================
// Type Detection
// ============================================================================

/**
 * Detects and converts a string value to its appropriate type
 *
 * @param value - Raw string value from frontmatter
 * @returns Typed value (string, number, boolean, array, or null)
 *
 * @example
 * detectType('42')           // 42 (number)
 * detectType('true')         // true (boolean)
 * detectType('[a, b, c]')    // ['a', 'b', 'c'] (string[])
 * detectType('hello world')  // 'hello world' (string)
 */
export function detectType(value: string): FrontmatterValue {
  if (value === null || value === undefined) {
    return null;
  }

  const trimmed = value.trim();

  // Empty string
  if (trimmed === '') {
    return null;
  }

  // Null/undefined literals
  if (trimmed === 'null' || trimmed === '~') {
    return null;
  }

  // Boolean detection
  if (trimmed === 'true' || trimmed === 'True' || trimmed === 'TRUE') {
    return true;
  }
  if (trimmed === 'false' || trimmed === 'False' || trimmed === 'FALSE') {
    return false;
  }

  // Number detection (integers and floats)
  if (/^-?\d+$/.test(trimmed)) {
    const num = parseInt(trimmed, 10);
    if (!isNaN(num) && isFinite(num)) {
      return num;
    }
  }
  if (/^-?\d+\.\d+$/.test(trimmed)) {
    const num = parseFloat(trimmed);
    if (!isNaN(num) && isFinite(num)) {
      return num;
    }
  }

  // Array detection (YAML flow sequence: [a, b, c])
  if (trimmed.startsWith('[') && trimmed.endsWith(']')) {
    const inner = trimmed.slice(1, -1);
    if (inner.trim() === '') {
      return [];
    }
    return inner.split(',').map(item => item.trim());
  }

  // Quoted string - remove quotes
  if ((trimmed.startsWith('"') && trimmed.endsWith('"')) ||
      (trimmed.startsWith("'") && trimmed.endsWith("'"))) {
    return trimmed.slice(1, -1);
  }

  // Default: return as string
  return trimmed;
}

// ============================================================================
// Core Parsing Functions
// ============================================================================

/**
 * Parses YAML frontmatter from markdown content
 *
 * Handles:
 * - Standard YAML key: value pairs
 * - Multiline values (indented continuation)
 * - Type detection for strings, numbers, booleans, arrays
 *
 * @param content - Raw markdown content
 * @param options - Parsing options
 * @returns Parsed frontmatter object or null if not found
 *
 * @example
 * const content = `---
 * name: my-skill
 * version: 1.0
 * enabled: true
 * ---
 * # Content here`;
 *
 * const fm = parseFrontmatter(content);
 * // { name: 'my-skill', version: 1.0, enabled: true }
 */
export function parseFrontmatter(
  content: string,
  options: ParseOptions = {}
): Frontmatter | null {
  const {
    detectTypes = true,
    trimValues = true,
    handleMultiline = true,
    typeDetector = detectType
  } = options;

  // Normalize line endings to LF before processing (M1 fix)
  const normalizedContent = content.replace(/\r\n/g, '\n').replace(/\r/g, '\n');

  // Match frontmatter block: --- at start, content, ---
  const match = normalizedContent.match(/^---\n([\s\S]*?)\n---/);
  if (!match) {
    return null;
  }

  const frontmatter: Frontmatter = {};
  const lines = match[1].split('\n');

  let currentKey: string | null = null;
  let inMultiline = false;
  let multilineValue: string[] = [];

  for (const line of lines) {
    // Handle multiline continuation
    if (handleMultiline && inMultiline) {
      if (line.startsWith('  ') || line.startsWith('\t')) {
        multilineValue.push(trimValues ? line.trim() : line);
        continue;
      } else {
        // End of multiline - save value
        if (currentKey) {
          const joined = multilineValue.join(' ');
          const value = trimValues ? joined.trim() : joined;
          frontmatter[currentKey] = detectTypes ? typeDetector(value) : value;
        }
        inMultiline = false;
        multilineValue = [];
      }
    }

    // Parse key: value pair
    const keyMatch = line.match(/^(\w[\w-]*?):\s*(.*)$/);
    if (keyMatch) {
      currentKey = keyMatch[1];
      let value = keyMatch[2];

      if (trimValues) {
        value = value.trim();
      }

      if (value) {
        // Single-line value
        frontmatter[currentKey] = detectTypes ? typeDetector(value) : value;
      } else if (handleMultiline) {
        // Start of multiline value
        inMultiline = true;
        multilineValue = [];
      }
    }
  }

  // Handle trailing multiline value
  if (handleMultiline && inMultiline && currentKey) {
    const joined = multilineValue.join(' ');
    const value = trimValues ? joined.trim() : joined;
    frontmatter[currentKey] = detectTypes ? typeDetector(value) : value;
  }

  return frontmatter;
}

/**
 * Parses markdown content and separates frontmatter from body
 *
 * @param content - Raw markdown content
 * @param options - Parsing options
 * @returns ParseResult with frontmatter, content, and metadata
 *
 * @example
 * const result = parseMarkdown(`---
 * title: Hello
 * ---
 * # Body content`);
 *
 * console.log(result.frontmatter); // { title: 'Hello' }
 * console.log(result.content);     // '# Body content'
 */
export function parseMarkdown(
  content: string,
  options: ParseOptions = {}
): ParseResult {
  const match = content.match(/^---\r?\n([\s\S]*?)\r?\n---\r?\n?/);

  if (!match) {
    return {
      frontmatter: null,
      content: content,
      hasFrontmatter: false,
      rawFrontmatter: null
    };
  }

  const frontmatter = parseFrontmatter(content, options);
  const bodyContent = content.slice(match[0].length);

  return {
    frontmatter,
    content: bodyContent,
    hasFrontmatter: true,
    rawFrontmatter: match[1]
  };
}

// ============================================================================
// Skill Metadata Extraction
// ============================================================================

/**
 * Infers skill name from file path
 *
 * Extracts the parent directory name as the skill name.
 * Pattern: .../skills/category/skill-name/SKILL.md -> 'skill-name'
 *
 * @param filePath - Full path to the skill file
 * @param fallback - Fallback name if inference fails
 * @returns Inferred skill name
 *
 * @example
 * inferSkillName('/path/to/skills/delivery/build-feature/SKILL.md')
 * // 'build-feature'
 */
export function inferSkillName(filePath: string, fallback: string = 'unknown-skill'): string {
  // Normalize path separators
  const parts = filePath.split(/[\/\\]/);

  // Find the file name and get parent directory
  const fileIdx = parts.findIndex(p =>
    p.toLowerCase() === 'skill.md' ||
    p.toLowerCase() === 'readme.md' ||
    p.toLowerCase().endsWith('.md')
  );

  if (fileIdx > 0) {
    return parts[fileIdx - 1];
  }

  // Last directory before file
  if (parts.length >= 2) {
    return parts[parts.length - 2];
  }

  return fallback;
}

/**
 * Extracts skill name from frontmatter or path
 *
 * Priority:
 * 1. frontmatter.name
 * 2. frontmatter.skill
 * 3. frontmatter.title (converted to slug)
 * 4. Inferred from file path
 *
 * @param filePath - Full path to the skill file
 * @param frontmatter - Parsed frontmatter (optional)
 * @param fallback - Fallback name if none found
 * @returns Skill name
 */
export function getSkillName(
  filePath: string,
  frontmatter?: Frontmatter | null,
  fallback: string = 'unknown-skill'
): string {
  if (frontmatter) {
    // Direct name field
    if (frontmatter.name && typeof frontmatter.name === 'string') {
      return frontmatter.name;
    }
    // Alternative: skill field
    if (frontmatter.skill && typeof frontmatter.skill === 'string') {
      return frontmatter.skill;
    }
    // Alternative: title field (convert to slug)
    if (frontmatter.title && typeof frontmatter.title === 'string') {
      const slug = frontmatter.title
        .toLowerCase()
        .replace(/\s+/g, '-')
        .replace(/[^a-z0-9-]/g, '');
      // H2 fix: Return fallback if slug becomes empty after sanitization
      if (slug.length > 0) {
        return slug;
      }
    }
  }

  return inferSkillName(filePath, fallback);
}

/**
 * Extracts a short description from content
 *
 * Priority:
 * 1. frontmatter.description
 * 2. First paragraph after frontmatter (first sentence)
 * 3. Truncated first paragraph
 *
 * @param frontmatter - Parsed frontmatter
 * @param content - Full markdown content
 * @param maxLength - Maximum description length (default: 300)
 * @returns Short description string
 */
export function getShortDescription(
  frontmatter: Frontmatter | null,
  content: string,
  maxLength: number = 300
): string {
  let desc = '';

  // Priority 1: Frontmatter description
  if (frontmatter && frontmatter.description) {
    desc = String(frontmatter.description);
  } else {
    // Priority 2: Extract from content body
    const afterFrontmatter = content.replace(/^---[\s\S]*?---\r?\n?/, '');

    // Get first non-heading paragraph
    const firstPara = afterFrontmatter.match(/^[^#\n].*?[.!?]/);
    if (firstPara) {
      desc = firstPara[0].trim();
    }
  }

  // Clean up whitespace
  desc = desc.replace(/\s+/g, ' ').trim();

  // Get first sentence if under limit
  const firstSentence = desc.match(/^[^.!?]*[.!?]/);
  if (firstSentence && firstSentence[0].length < maxLength) {
    return firstSentence[0].trim();
  }

  // Truncate if too long
  if (desc.length > maxLength) {
    return desc.substring(0, maxLength - 3) + '...';
  }

  return desc || 'No description available.';
}

/**
 * Extracts complete skill metadata from a markdown file
 *
 * @param filePath - Path to the skill file
 * @param options - Extraction options
 * @returns SkillMetadata object
 *
 * @example
 * const metadata = extractSkillMetadata('/path/to/SKILL.md');
 * console.log(metadata.name);        // 'my-skill'
 * console.log(metadata.description); // 'Does something useful.'
 */
export function extractSkillMetadata(
  filePath: string,
  options: SkillExtractionOptions = {}
): SkillMetadata {
  const {
    fallbackName = 'unknown-skill',
    maxDescriptionLength = 300,
    ...parseOptions
  } = options;

  const content = fs.readFileSync(filePath, 'utf8');
  const { frontmatter } = parseMarkdown(content, parseOptions);

  const name = getSkillName(filePath, frontmatter, fallbackName);
  const description = getShortDescription(frontmatter, content, maxDescriptionLength);

  return {
    name,
    description,
    frontmatter,
    sourcePath: filePath
  };
}

/**
 * Async variant of extractSkillMetadata using fs.promises (H1 fix)
 *
 * @param filePath - Path to the skill file
 * @param options - Extraction options
 * @returns Promise resolving to SkillMetadata object
 *
 * @example
 * const metadata = await extractSkillMetadataAsync('/path/to/SKILL.md');
 * console.log(metadata.name);        // 'my-skill'
 * console.log(metadata.description); // 'Does something useful.'
 */
export async function extractSkillMetadataAsync(
  filePath: string,
  options: SkillExtractionOptions = {}
): Promise<SkillMetadata> {
  const {
    fallbackName = 'unknown-skill',
    maxDescriptionLength = 300,
    ...parseOptions
  } = options;

  const content = await fs.promises.readFile(filePath, 'utf8');
  const { frontmatter } = parseMarkdown(content, parseOptions);

  const name = getSkillName(filePath, frontmatter, fallbackName);
  const description = getShortDescription(frontmatter, content, maxDescriptionLength);

  return {
    name,
    description,
    frontmatter,
    sourcePath: filePath
  };
}

// ============================================================================
// File Discovery
// ============================================================================

/**
 * Recursively finds markdown files matching a pattern
 *
 * @param dir - Directory to search
 * @param filename - File name to match (default: 'SKILL.md')
 * @param results - Accumulator for results (internal use)
 * @param maxDepth - Maximum recursion depth to prevent infinite loops (default: 10) (M2 fix)
 * @param currentDepth - Current recursion depth (internal use)
 * @returns Array of FileSearchResult objects
 *
 * @example
 * const files = findMarkdownFiles('/path/to/skills', 'SKILL.md');
 * files.forEach(f => console.log(f.path));
 *
 * // With custom depth limit
 * const shallowFiles = findMarkdownFiles('/path/to/skills', 'SKILL.md', [], 3);
 */
export function findMarkdownFiles(
  dir: string,
  filename: string = 'SKILL.md',
  results: FileSearchResult[] = [],
  maxDepth: number = 10,
  currentDepth: number = 0
): FileSearchResult[] {
  // M2 fix: Prevent infinite recursion with depth limit
  if (currentDepth >= maxDepth) {
    return results;
  }

  if (!fs.existsSync(dir)) {
    return results;
  }

  const entries = fs.readdirSync(dir, { withFileTypes: true });

  for (const entry of entries) {
    const fullPath = path.join(dir, entry.name);

    if (entry.isDirectory()) {
      // Skip hidden and backup directories
      if (!entry.name.startsWith('.') && entry.name !== 'backup' && entry.name !== 'node_modules') {
        findMarkdownFiles(fullPath, filename, results, maxDepth, currentDepth + 1);
      }
    } else if (entry.name.toLowerCase() === filename.toLowerCase()) {
      results.push({
        path: fullPath,
        name: entry.name,
        directory: path.basename(path.dirname(fullPath))
      });
    }
  }

  return results;
}

/**
 * Validates a skill name for filesystem compatibility and Claude Code spec
 *
 * @param name - Skill name to validate
 * @param maxLength - Maximum allowed length (default: 50)
 * @returns true if valid, false otherwise
 *
 * @remarks
 * M3 fix: Changed to lowercase-only to match Claude Code spec.
 * Only allows lowercase alphanumeric characters and hyphens.
 */
export function isValidSkillName(name: string, maxLength: number = 50): boolean {
  if (!name || name.length > maxLength) {
    return false;
  }
  // M3 fix: Only lowercase alphanumeric and hyphen to match Claude Code spec
  return /^[a-z0-9-]+$/.test(name);
}

// ============================================================================
// Serialization
// ============================================================================

/**
 * Serializes frontmatter back to YAML string
 *
 * @param frontmatter - Frontmatter object to serialize
 * @returns YAML string with --- delimiters
 *
 * @remarks
 * L2 fix: Keys are sorted alphabetically for reproducible output.
 *
 * @example
 * const yaml = serializeFrontmatter({ name: 'test', version: 1 });
 * // '---\nname: test\nversion: 1\n---'
 */
export function serializeFrontmatter(frontmatter: Frontmatter): string {
  const lines: string[] = ['---'];

  // L2 fix: Sort keys alphabetically for reproducible output
  const sortedKeys = Object.keys(frontmatter).sort();

  for (const key of sortedKeys) {
    const value = frontmatter[key];
    if (value === null || value === undefined) {
      lines.push(`${key}: ~`);
    } else if (Array.isArray(value)) {
      lines.push(`${key}: [${value.join(', ')}]`);
    } else if (typeof value === 'boolean') {
      lines.push(`${key}: ${value}`);
    } else if (typeof value === 'number') {
      lines.push(`${key}: ${value}`);
    } else {
      // String - quote if contains special chars
      const str = String(value);
      if (str.includes(':') || str.includes('#') || str.includes('\n')) {
        lines.push(`${key}: "${str.replace(/"/g, '\\"')}"`);
      } else {
        lines.push(`${key}: ${str}`);
      }
    }
  }

  lines.push('---');
  return lines.join('\n');
}

/**
 * Creates a markdown document with frontmatter
 *
 * @param frontmatter - Frontmatter object
 * @param content - Body content
 * @returns Complete markdown string
 */
export function createMarkdown(frontmatter: Frontmatter, content: string): string {
  return `${serializeFrontmatter(frontmatter)}\n\n${content}`;
}
