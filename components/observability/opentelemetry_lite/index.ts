/**
 * OpenTelemetry-Lite
 *
 * Zero-dependency, OpenTelemetry-compatible telemetry framework.
 * Provides distributed tracing, metrics collection, and structured logging.
 *
 * @packageDocumentation
 * @module opentelemetry-lite
 * @version 1.0.0
 */

// =============================================================================
// Enums
// =============================================================================

export {
  LogLevel,
  SpanStatus
} from './telemetry';

// =============================================================================
// Types & Interfaces
// =============================================================================

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
} from './telemetry';

// =============================================================================
// Constants
// =============================================================================

export {
  DEFAULT_TELEMETRY_CONFIG
} from './telemetry';

// =============================================================================
// ID Generation
// =============================================================================

export {
  generateTraceId,
  generateSpanId
} from './telemetry';

// =============================================================================
// Core Classes
// =============================================================================

export {
  Span,
  Tracer,
  MetricsCollector,
  StructuredLogger
} from './telemetry';

// =============================================================================
// Exporters
// =============================================================================

export {
  ConsoleSpanExporter,
  InMemorySpanExporter,
  CallbackSpanExporter
} from './telemetry';

// =============================================================================
// Factory
// =============================================================================

export {
  createTelemetry
} from './telemetry';

// =============================================================================
// Default Export
// =============================================================================

export { createTelemetry as default } from './telemetry';
