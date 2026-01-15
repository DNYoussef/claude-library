# OpenTelemetry-Lite

Zero-dependency, OpenTelemetry-compatible telemetry framework for Node.js and browser environments.

## Overview

OpenTelemetry-Lite provides distributed tracing, metrics collection, and structured logging without any external dependencies. It generates OpenTelemetry-compatible trace and span IDs, making it easy to integrate with existing observability infrastructure.

**Source**: Extracted from Context Cascade Phase 6.3 Observability Stack

## Features

- **Distributed Tracing**: OpenTelemetry-compatible trace/span IDs (128-bit/64-bit)
- **Span Lifecycle**: Full span management with events, attributes, and links
- **Metrics Collection**: Counters, gauges, and histograms with labels
- **Structured Logging**: JSON logging with log levels and trace context
- **Prometheus Export**: Native Prometheus format export for metrics
- **Zero Dependencies**: Pure TypeScript, works everywhere
- **Configurable**: Flexible configuration for all components

## Installation

Copy the files to your project:

```
opentelemetry-lite/
  telemetry.ts   # Main implementation
  index.ts       # Exports
  README.md      # This file
```

## Quick Start

```typescript
import { createTelemetry } from './opentelemetry-lite';

// Create telemetry instance
const telemetry = createTelemetry('my-service', {
  logLevel: 'DEBUG',
  logFormat: 'json'
});

// Start a trace
const span = telemetry.startSpan('http-request');
span.setAttribute('http.method', 'GET');
span.setAttribute('http.url', '/api/users');

// Record metrics
telemetry.increment('http_requests_total', 1, { method: 'GET' });

// Log with trace context
telemetry.log('info', 'Processing request', {
  traceId: span.traceId,
  spanId: span.spanId
});

// End the span
span.setStatus(SpanStatus.OK);
telemetry.endSpan(span);

// Shutdown gracefully
telemetry.shutdown();
```

## API Reference

### ID Generation

#### `generateTraceId(): string`
Generate a 32-character hex trace ID (128-bit, OpenTelemetry compatible).

```typescript
const traceId = generateTraceId();
// e.g., "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6"
```

#### `generateSpanId(): string`
Generate a 16-character hex span ID (64-bit, OpenTelemetry compatible).

```typescript
const spanId = generateSpanId();
// e.g., "1a2b3c4d5e6f7a8b"
```

### Span Class

Represents a unit of work within a trace.

```typescript
const span = new Span('database-query', {
  traceId: parentTraceId,      // Optional: use existing trace
  parentSpanId: parentSpanId,  // Optional: create child span
  attributes: { 'db.system': 'postgresql' }
});

// Set attributes
span.setAttribute('db.statement', 'SELECT * FROM users');
span.setAttributes({ 'db.user': 'app', 'db.name': 'mydb' });

// Add events (timestamped logs within span)
span.addEvent('query-parsed');
span.addEvent('query-executed', { rowCount: 42 });

// Add links to related spans
span.addLink(otherTraceId, otherSpanId);

// Set status
span.setStatus(SpanStatus.OK);
span.setStatus(SpanStatus.ERROR, 'Connection timeout');

// End span
span.end();

// Export to JSON
const json = span.toJSON();
```

### Tracer Class

Central component for creating and managing spans.

```typescript
const tracer = new Tracer('my-service', {
  logLevel: 'INFO',
  traceEnabled: true
});

// Add exporters
tracer.addExporter(new ConsoleSpanExporter());
tracer.addExporter(new InMemorySpanExporter());

// Start spans
const span = tracer.startSpan('operation');

// Create child spans
const childSpan = tracer.startChildSpan(span, 'sub-operation');
tracer.endSpan(childSpan);
tracer.endSpan(span);

// Query spans
const active = tracer.getActiveSpans();
const completed = tracer.getCompletedSpans();
const stats = tracer.getStats(); // { active: 0, completed: 2 }

// Clear completed spans
tracer.clearSpans();
```

### MetricsCollector Class

Collects counters, gauges, and histograms.

```typescript
const metrics = new MetricsCollector('my-service');

// Counters (monotonically increasing)
metrics.incrementCounter('http_requests_total');
metrics.incrementCounter('http_requests_total', 5, { method: 'POST' });

// Gauges (point-in-time values)
metrics.setGauge('active_connections', 42);
metrics.setGauge('temperature', 23.5, { location: 'server-room' });

// Histograms (distributions)
metrics.recordHistogram('request_duration_ms', 150);
metrics.recordHistogram('request_duration_ms', 200, { endpoint: '/api' });

// Query values
const count = metrics.getCounter('http_requests_total');
const connections = metrics.getGauge('active_connections');
const hist = metrics.getHistogram('request_duration_ms');

// Export all metrics
const all = metrics.getMetrics();

// Export to Prometheus format
const prometheus = metrics.toPrometheus();

// Reset all metrics
metrics.reset();
```

### StructuredLogger Class

Structured logging with levels and trace context.

```typescript
const logger = new StructuredLogger('my-service', {
  logLevel: 'DEBUG',
  logFormat: 'json',
  flushInterval: 5000
});

// Log at different levels
logger.debug('Detailed debug info', { detail: 'value' });
logger.info('Request received', { path: '/api/users' });
logger.warn('Rate limit approaching', { current: 95, limit: 100 });
logger.error('Database error', { error: err.message });
logger.fatal('System crash', { exitCode: 1 });

// Log with trace context
logger.logWithSpan('info', 'Processing', span, { step: 1 });

// Custom output handler
logger.setOutputHandler((entry) => {
  // Send to external service
  externalLogger.send(entry);
});

// Custom flush handler for file writes
logger.setFlushHandler((entries) => {
  fs.appendFileSync('app.log', entries.map(e => JSON.stringify(e)).join('\n'));
});

// Manual flush
logger.flush();

// Graceful shutdown
logger.shutdown();
```

### Span Exporters

#### ConsoleSpanExporter
Outputs spans to console as JSON.

```typescript
const exporter = new ConsoleSpanExporter();
tracer.addExporter(exporter);
```

#### InMemorySpanExporter
Stores spans in memory (useful for testing).

```typescript
const exporter = new InMemorySpanExporter();
tracer.addExporter(exporter);

// Later...
const spans = exporter.getSpans();
const count = exporter.count();
exporter.clear();
```

#### CallbackSpanExporter
Custom callback for span export.

```typescript
const exporter = new CallbackSpanExporter((spanJson) => {
  // Send to external service
  fetch('/api/traces', {
    method: 'POST',
    body: JSON.stringify(spanJson)
  });
});
tracer.addExporter(exporter);
```

### Factory Function

#### `createTelemetry(serviceName, config?): TelemetryInstance`

Creates a complete telemetry instance with tracer, metrics, and logger.

```typescript
const telemetry = createTelemetry('my-service', {
  enabled: true,
  logLevel: 'INFO',
  traceEnabled: true,
  metricsEnabled: true,
  logFormat: 'json',
  maxLogSize: 10 * 1024 * 1024,
  maxLogFiles: 5,
  flushInterval: 5000
});

// Access components
telemetry.tracer;  // Tracer instance
telemetry.metrics; // MetricsCollector instance
telemetry.logger;  // StructuredLogger instance

// Convenience methods
telemetry.startSpan('operation');
telemetry.endSpan(span);
telemetry.increment('counter');
telemetry.gauge('gauge', 42);
telemetry.histogram('latency', 100);
telemetry.log('info', 'message');

// Cleanup
telemetry.shutdown();
```

## Configuration

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `enabled` | boolean | `true` | Enable/disable telemetry |
| `logLevel` | string | `'INFO'` | Minimum log level (DEBUG, INFO, WARN, ERROR, FATAL) |
| `traceEnabled` | boolean | `true` | Enable distributed tracing |
| `metricsEnabled` | boolean | `true` | Enable metrics collection |
| `logFormat` | string | `'json'` | Log format: 'json' or 'text' |
| `maxLogSize` | number | `10485760` | Max log file size (10MB) |
| `maxLogFiles` | number | `5` | Max rotated log files |
| `flushInterval` | number | `5000` | Buffer flush interval (ms) |
| `logDir` | string | - | Log directory path |

## Log Levels

| Level | Value | Use Case |
|-------|-------|----------|
| DEBUG | 0 | Detailed debugging information |
| INFO | 1 | General operational messages |
| WARN | 2 | Warning conditions |
| ERROR | 3 | Error conditions |
| FATAL | 4 | Critical errors requiring shutdown |

## Span Status

| Status | Description |
|--------|-------------|
| `UNSET` | Status not set (default) |
| `OK` | Operation completed successfully |
| `ERROR` | Operation failed |

## Type Exports

```typescript
// Enums
export { LogLevel, SpanStatus }

// Interfaces
export type {
  TelemetryConfig,
  SpanEvent,
  SpanLink,
  SpanOptions,
  SpanJSON,
  LogEntry,
  CounterMetric,
  GaugeMetric,
  HistogramMetric,
  AllMetrics,
  SpanExporter,
  TelemetryInstance
}

// Classes
export {
  Span,
  Tracer,
  MetricsCollector,
  StructuredLogger,
  ConsoleSpanExporter,
  InMemorySpanExporter,
  CallbackSpanExporter
}

// Functions
export {
  generateTraceId,
  generateSpanId,
  createTelemetry
}

// Constants
export { DEFAULT_TELEMETRY_CONFIG }
```

## Integration Examples

### Express.js Middleware

```typescript
import { createTelemetry, SpanStatus } from './opentelemetry-lite';

const telemetry = createTelemetry('express-app');

app.use((req, res, next) => {
  const span = telemetry.startSpan('http-request');
  span.setAttributes({
    'http.method': req.method,
    'http.url': req.url,
    'http.route': req.route?.path
  });

  res.on('finish', () => {
    span.setAttribute('http.status_code', res.statusCode);
    span.setStatus(res.statusCode < 400 ? SpanStatus.OK : SpanStatus.ERROR);
    telemetry.endSpan(span);
    telemetry.increment('http_requests_total', 1, {
      method: req.method,
      status: String(res.statusCode)
    });
  });

  next();
});
```

### Database Operations

```typescript
async function queryUsers() {
  const span = telemetry.startSpan('database-query');
  span.setAttributes({
    'db.system': 'postgresql',
    'db.name': 'users',
    'db.operation': 'SELECT'
  });

  try {
    const start = Date.now();
    const result = await db.query('SELECT * FROM users');

    span.setAttribute('db.row_count', result.rows.length);
    span.setStatus(SpanStatus.OK);
    telemetry.histogram('db_query_duration_ms', Date.now() - start);

    return result.rows;
  } catch (error) {
    span.setStatus(SpanStatus.ERROR, error.message);
    span.addEvent('error', { message: error.message });
    throw error;
  } finally {
    telemetry.endSpan(span);
  }
}
```

## License

MIT License - Part of the Context Cascade ecosystem.
