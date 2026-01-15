# Consensus Display

A reusable React component for running and displaying multi-model AI consensus. Query multiple LLMs simultaneously and visualize agreement levels.

## Features

- Multi-model consensus visualization
- Configurable API endpoints
- Custom task types support
- Real-time model availability status
- Detailed per-model response breakdown
- Error handling with retry functionality
- Full TypeScript support
- Custom fetch function support (for auth)

## Installation

Copy the component files to your project:

```
consensus-display/
  ConsensusDisplay.tsx  # Main component
  types.ts              # TypeScript definitions
  index.ts              # Exports
  README.md             # This file
```

## Usage

### Basic Usage

```tsx
import { ConsensusDisplay } from './consensus-display';

function App() {
  return (
    <ConsensusDisplay
      apiBase="https://api.example.com"
    />
  );
}
```

### With Callbacks

```tsx
import { ConsensusDisplay, ConsensusResult } from './consensus-display';

function App() {
  const handleComplete = (result: ConsensusResult) => {
    console.log('Consensus reached:', result.consensus_reached);
    console.log('Confidence:', result.consensus_confidence);
  };

  const handleError = (error: Error) => {
    console.error('Consensus failed:', error.message);
  };

  return (
    <ConsensusDisplay
      apiBase="https://api.example.com"
      onConsensusComplete={handleComplete}
      onError={handleError}
    />
  );
}
```

### Custom Task Types

```tsx
import { ConsensusDisplay, TaskTypeOption } from './consensus-display';

const customTaskTypes: TaskTypeOption[] = [
  { value: 'general', label: 'General Query' },
  { value: 'validation', label: 'Data Validation' },
  { value: 'code_review', label: 'Code Review' },
  { value: 'security_audit', label: 'Security Audit' },
  { value: 'fact_checking', label: 'Fact Check' },
];

function App() {
  return (
    <ConsensusDisplay
      apiBase="https://api.example.com"
      taskTypes={customTaskTypes}
      initialTaskType="code_review"
    />
  );
}
```

### With Authentication

```tsx
import { ConsensusDisplay } from './consensus-display';

function App() {
  const authHeaders = {
    'Authorization': `Bearer ${getToken()}`,
  };

  return (
    <ConsensusDisplay
      apiBase="https://api.example.com"
      headers={authHeaders}
    />
  );
}
```

### Custom Fetch Function

```tsx
import { ConsensusDisplay } from './consensus-display';

function App() {
  // Custom fetch with interceptors, retries, etc.
  const customFetch: typeof fetch = async (url, options) => {
    const token = await refreshTokenIfNeeded();
    return fetch(url, {
      ...options,
      headers: {
        ...options?.headers,
        'Authorization': `Bearer ${token}`,
      },
    });
  };

  return (
    <ConsensusDisplay
      apiBase="https://api.example.com"
      fetchFn={customFetch}
    />
  );
}
```

## Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `apiBase` | `string` | *required* | Base URL for the consensus API |
| `taskTypes` | `TaskTypeOption[]` | Default types | Task type options for dropdown |
| `onConsensusComplete` | `(result: ConsensusResult) => void` | - | Callback when consensus completes |
| `onError` | `(error: Error) => void` | - | Callback on error |
| `className` | `string` | `''` | Additional CSS class |
| `initialPrompt` | `string` | `''` | Initial prompt value |
| `initialTaskType` | `TaskType` | `'general'` | Initial task type |
| `hideModelStatus` | `boolean` | `false` | Hide model status badges |
| `placeholder` | `string` | Default text | Textarea placeholder |
| `textareaRows` | `number` | `3` | Textarea row count |
| `disabled` | `boolean` | `false` | Disable component |
| `fetchFn` | `typeof fetch` | `fetch` | Custom fetch function |
| `headers` | `Record<string, string>` | `{}` | Custom headers for API calls |

## API Requirements

The component expects the following API endpoints:

### GET /api/v1/consensus/models/

Returns available models:

```json
{
  "models": [
    {
      "name": "Claude",
      "available": true,
      "model_id": "claude-3-opus"
    },
    {
      "name": "GPT-4",
      "available": true,
      "model_id": "gpt-4-turbo"
    }
  ]
}
```

### POST /api/v1/consensus/run/

Request:
```json
{
  "prompt": "What is the capital of France?",
  "task_type": "general"
}
```

Response:
```json
{
  "consensus_id": "abc123",
  "run_id": "run_456",
  "prompt_preview": "What is the capital...",
  "consensus_reached": "unanimous",
  "consensus_confidence": 0.98,
  "models_agree": 3,
  "total_models": 3,
  "execution_time_ms": 1250,
  "results": {
    "Claude": {
      "success": true,
      "response_preview": "Paris is the capital...",
      "confidence": 0.99,
      "execution_ms": 450,
      "error": null
    },
    "GPT-4": {
      "success": true,
      "response_preview": "The capital of France...",
      "confidence": 0.98,
      "execution_ms": 520,
      "error": null
    }
  }
}
```

## Consensus Status Levels

| Status | Description | Color |
|--------|-------------|-------|
| `unanimous` | All models agree | Green (#22c55e) |
| `majority` | >66% agreement | Lime (#84cc16) |
| `weak_majority` | >50% agreement | Yellow (#eab308) |
| `none` | No agreement | Red (#ef4444) |
| `insufficient` | Not enough responses | Gray (#94a3b8) |

## Styling

The component uses CSS classes for styling. Include appropriate styles in your stylesheet:

```css
.consensus-display {
  /* Container styles */
}

.consensus-header {
  /* Header section */
}

.model-status-row {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.model-status-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.25rem 0.5rem;
  border: 1px solid;
  border-radius: 9999px;
  font-size: 0.75rem;
}

.model-status-dot {
  width: 0.5rem;
  height: 0.5rem;
  border-radius: 50%;
}

.consensus-input {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.consensus-type-select {
  /* Select dropdown */
}

.consensus-textarea {
  /* Textarea input */
  resize: vertical;
}

.consensus-run-btn {
  /* Run button */
}

.consensus-run-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.error-with-retry {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem;
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 0.375rem;
}

.error-message {
  color: #dc2626;
  flex: 1;
}

.retry-btn {
  /* Retry button */
}

.consensus-result {
  /* Results container */
}

.consensus-summary {
  /* Summary section */
}

.consensus-status {
  display: inline-block;
  padding: 0.25rem 0.75rem;
  border-radius: 0.375rem;
  color: white;
  font-weight: 600;
  text-transform: uppercase;
}

.consensus-stats {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
}

.consensus-stat {
  font-size: 0.875rem;
}

.model-responses {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.model-response {
  border: 1px solid #e5e7eb;
  border-radius: 0.375rem;
  overflow: hidden;
}

.model-response.success {
  border-color: #86efac;
}

.model-response.failed {
  border-color: #fca5a5;
}

.model-response-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 0.75rem;
  background: #f9fafb;
}

.model-name {
  font-weight: 600;
  flex: 1;
}

.model-confidence {
  color: #059669;
}

.model-time {
  color: #6b7280;
  font-size: 0.75rem;
}

.model-error {
  color: #dc2626;
}

.model-response-body {
  padding: 0.75rem;
}

.model-response-body pre {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
  font-family: inherit;
}

.error-text {
  color: #dc2626;
}

.no-response {
  color: #9ca3af;
  font-style: italic;
}
```

## TypeScript Types

All types are exported from `index.ts`:

```tsx
import type {
  ModelResult,
  ModelStatus,
  ConsensusResult,
  ConsensusStatus,
  TaskType,
  ConsensusDisplayProps,
  TaskTypeOption,
} from './consensus-display';
```

## Exported Items

### Components
- `ConsensusDisplay` - Main component
- `default` - Default export (same as ConsensusDisplay)

### Functions
- `getConsensusColor(status, colors?)` - Get color for consensus status
- `getModelStatusColor(available)` - Get color for model availability
- `formatConsensusStatus(status)` - Format status for display

### Types
- `ModelResult` - Single model result
- `ModelResultFull` - Extended model result
- `ModelStatus` - Model availability status
- `ModelCapabilities` - Model capability flags
- `ConsensusStatus` - Consensus level union type
- `TaskType` - Task type union type
- `ConsensusResult` - Consensus run result
- `ConsensusResultFull` - Extended consensus result
- `ConsensusRequest` - API request payload
- `ModelsResponse` - Models endpoint response
- `ApiError` - API error response
- `ConsensusDisplayProps` - Component props
- `TaskTypeOption` - Task type dropdown option
- `UseConsensusState` - Hook state type
- `UseConsensusActions` - Hook actions type
- `UseConsensusReturn` - Hook return type
- `ConsensusColorConfig` - Color configuration type

### Constants
- `DEFAULT_CONSENSUS_COLORS` - Default status colors
- `MODEL_STATUS_COLORS` - Model availability colors

## License

MIT
