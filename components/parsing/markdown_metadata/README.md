# Markdown Metadata Parser

Zero-dependency TypeScript library for parsing YAML frontmatter from Markdown files.

Extracted from Context Cascade `create-skill-cache.js`.

## Installation

Copy this directory to your project or import directly:

```typescript
import { parseFrontmatter, parseMarkdown } from './markdown-metadata';
```

## Features

- YAML frontmatter extraction
- Multiline value handling
- Automatic type detection (string, number, boolean, array)
- File path inference for skill names
- Zero dependencies (Node.js stdlib only)
- Full TypeScript type definitions

## Quick Start

### Parse Frontmatter

```typescript
import { parseFrontmatter } from './markdown-metadata';

const content = `---
name: my-skill
version: 1.0
enabled: true
tags: [typescript, parser, yaml]
---
# My Skill

Content here...`;

const frontmatter = parseFrontmatter(content);
// {
//   name: 'my-skill',
//   version: 1.0,
//   enabled: true,
//   tags: ['typescript', 'parser', 'yaml']
// }
```

### Parse Complete Markdown

```typescript
import { parseMarkdown } from './markdown-metadata';

const result = parseMarkdown(content);
// {
//   frontmatter: { name: 'my-skill', ... },
//   content: '# My Skill\n\nContent here...',
//   hasFrontmatter: true,
//   rawFrontmatter: 'name: my-skill\nversion: 1.0\n...'
// }
```

### Extract Skill Metadata

```typescript
import { extractSkillMetadata } from './markdown-metadata';

const metadata = extractSkillMetadata('/path/to/skills/build-feature/SKILL.md');
// {
//   name: 'build-feature',
//   description: 'Complete feature development workflow.',
//   frontmatter: { ... },
//   sourcePath: '/path/to/skills/build-feature/SKILL.md'
// }
```

### Find Skill Files

```typescript
import { findMarkdownFiles } from './markdown-metadata';

const files = findMarkdownFiles('/path/to/skills', 'SKILL.md');
// [
//   { path: '/path/to/skills/delivery/build-feature/SKILL.md', name: 'SKILL.md', directory: 'build-feature' },
//   { path: '/path/to/skills/quality/code-review/SKILL.md', name: 'SKILL.md', directory: 'code-review' },
//   ...
// ]
```

### Serialize Frontmatter

```typescript
import { serializeFrontmatter, createMarkdown } from './markdown-metadata';

const yaml = serializeFrontmatter({
  name: 'new-skill',
  version: 2,
  enabled: true,
  tags: ['a', 'b']
});
// '---\nname: new-skill\nversion: 2\nenabled: true\ntags: [a, b]\n---'

const markdown = createMarkdown(
  { name: 'new-skill', version: 1 },
  '# New Skill\n\nDescription here.'
);
```

## API Reference

### Types

| Type | Description |
|------|-------------|
| `FrontmatterValue` | `string \| number \| boolean \| string[] \| null` |
| `Frontmatter` | `Record<string, FrontmatterValue>` |
| `ParseResult` | Result containing frontmatter, content, and metadata |
| `ParseOptions` | Options for parsing (detectTypes, trimValues, etc.) |
| `SkillExtractionOptions` | Options for skill metadata extraction |
| `SkillMetadata` | Extracted skill name, description, frontmatter |
| `FileSearchResult` | File path, name, and directory |

### Core Functions

| Function | Description |
|----------|-------------|
| `detectType(value)` | Detects and converts string to appropriate type |
| `parseFrontmatter(content, options?)` | Parses YAML frontmatter from content |
| `parseMarkdown(content, options?)` | Parses markdown and separates frontmatter from body |

### Skill Extraction Functions

| Function | Description |
|----------|-------------|
| `inferSkillName(filePath, fallback?)` | Infers skill name from file path |
| `getSkillName(filePath, frontmatter?, fallback?)` | Gets skill name from frontmatter or path |
| `getShortDescription(frontmatter, content, maxLength?)` | Extracts short description |
| `extractSkillMetadata(filePath, options?)` | Extracts complete skill metadata |

### File Discovery Functions

| Function | Description |
|----------|-------------|
| `findMarkdownFiles(dir, filename?, results?)` | Recursively finds markdown files |
| `isValidSkillName(name, maxLength?)` | Validates skill name for filesystem |

### Serialization Functions

| Function | Description |
|----------|-------------|
| `serializeFrontmatter(frontmatter)` | Converts frontmatter object to YAML string |
| `createMarkdown(frontmatter, content)` | Creates complete markdown document |

## Type Detection

The parser automatically detects these types:

| Input | Output Type | Example |
|-------|-------------|---------|
| `'42'` | `number` | `42` |
| `'3.14'` | `number` | `3.14` |
| `'true'` / `'false'` | `boolean` | `true` / `false` |
| `'[a, b, c]'` | `string[]` | `['a', 'b', 'c']` |
| `'null'` / `'~'` | `null` | `null` |
| `'"quoted"'` | `string` | `'quoted'` |
| anything else | `string` | as-is |

## Parse Options

```typescript
interface ParseOptions {
  detectTypes?: boolean;     // Auto-detect types (default: true)
  trimValues?: boolean;      // Trim whitespace (default: true)
  handleMultiline?: boolean; // Handle indented continuations (default: true)
  typeDetector?: (value: string) => FrontmatterValue; // Custom type detector
}
```

## Multiline Values

The parser handles YAML multiline values using indentation:

```yaml
---
description:
  This is a long description
  that spans multiple lines
  and will be joined with spaces.
---
```

Result: `{ description: 'This is a long description that spans multiple lines and will be joined with spaces.' }`

## Skill Name Inference

The parser infers skill names from file paths:

```
/path/to/skills/delivery/build-feature/SKILL.md
                         ^^^^^^^^^^^^^ -> 'build-feature'
```

Priority order:
1. `frontmatter.name`
2. `frontmatter.skill`
3. `frontmatter.title` (converted to slug)
4. Parent directory name

## License

MIT

## Origin

Extracted from Context Cascade v3.1.1
Source: `C:\Users\17175\claude-code-plugins\context-cascade\scripts\create-skill-cache.js`
