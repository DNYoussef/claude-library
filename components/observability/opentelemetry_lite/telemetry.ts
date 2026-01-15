/**
 * OpenTelemetry-Lite Telemetry Framework
 *
 * Zero-dependency, OpenTelemetry-compatible tracing and logging.
 * Extracted from Context Cascade Phase 6.3 Observability Stack.
 *
 * @module opentelemetry-lite/telemetry
 * @version 1.1.0
 */

// =============================================================================
// Semantic Conventions (L1: Standard attribute names for OpenTelemetry)
// =============================================================================

/**
 * Standard semantic convention attribute names
 * Based on OpenTelemetry Semantic Conventions
 */
export const SemanticAttributes = {
  // Service attributes
  SERVICE_NAME: 'service.name',
  SERVICE_VERSION: 'service.version',
  SERVICE_INSTANCE_ID: 'service.instance.id',

  // HTTP attributes
  HTTP_METHOD: 'http.method',
  HTTP_URL: 'http.url',
  HTTP_STATUS_CODE: 'http.status_code',
  HTTP_ROUTE: 'http.route',
  HTTP_TARGET: 'http.target',
  HTTP_HOST: 'http.host',
  HTTP_SCHEME: 'http.scheme',
  HTTP_USER_AGENT: 'http.user_agent',
  HTTP_REQUEST_CONTENT_LENGTH: 'http.request_content_length',
  HTTP_RESPONSE_CONTENT_LENGTH: 'http.response_content_length',

  // Database attributes
  DB_SYSTEM: 'db.system',
  DB_CONNECTION_STRING: 'db.connection_string',
  DB_USER: 'db.user',
  DB_NAME: 'db.name',
  DB_STATEMENT: 'db.statement',
  DB_OPERATION: 'db.operation',

  // Network attributes
  NET_PEER_NAME: 'net.peer.name',
  NET_PEER_IP: 'net.peer.ip',
  NET_PEER_PORT: 'net.peer.port',
  NET_HOST_NAME: 'net.host.name',
  NET_HOST_IP: 'net.host.ip',
  NET_HOST_PORT: 'net.host.port',
  NET_TRANSPORT: 'net.transport',

  // Exception attributes
  EXCEPTION_TYPE: 'exception.type',
  EXCEPTION_MESSAGE: 'exception.message',
  EXCEPTION_STACKTRACE: 'exception.stacktrace',

  // General attributes
  PEER_SERVICE: 'peer.service',
  CODE_FUNCTION: 'code.function',
  CODE_NAMESPACE: 'code.namespace',
  CODE_FILEPATH: 'code.filepath',
  CODE_LINENO: 'code.lineno',

  // Messaging attributes
  MESSAGING_SYSTEM: 'messaging.system',
  MESSAGING_DESTINATION: 'messaging.destination',
  MESSAGING_OPERATION: 'messaging.operation',
  MESSAGING_MESSAGE_ID: 'messaging.message_id',

  // RPC attributes
  RPC_SYSTEM: 'rpc.system',
  RPC_SERVICE: 'rpc.service',
  RPC_METHOD: 'rpc.method',
} as const;

// =============================================================================
// Type Definitions
// =============================================================================

/**
 * Log level enumeration with numeric values for comparison
 */
export enum LogLevel {
  DEBUG = 0,
  INFO = 1,
  WARN = 2,
  ERROR = 3,
  FATAL = 4
}

/**
 * Span status codes (OpenTelemetry compatible)
 */
export enum SpanStatus {
  UNSET = 'UNSET',
  OK = 'OK',
  ERROR = 'ERROR'
}

/**
 * Telemetry configuration options
 */
export interface TelemetryConfig {
  /** Enable/disable telemetry collection */
  enabled: boolean;
  /** Minimum log level to record */
  logLevel: keyof typeof LogLevel;
  /** Numeric log level for direct comparison (computed from logLevel) */
  logLevelNumeric: number;
  /** Enable distributed tracing */
  traceEnabled: boolean;
  /** Enable metrics collection */
  metricsEnabled: boolean;
  /** Log output format: 'json' or 'text' */
  logFormat: 'json' | 'text';
  /** Maximum log file size in bytes before rotation */
  maxLogSize: number;
  /** Maximum number of rotated log files to keep */
  maxLogFiles: number;
  /** Interval in ms between buffer flushes */
  flushInterval: number;
  /** Log directory path (optional, for file-based logging) */
  logDir?: string;
  /** Maximum completed spans to keep in memory (H2 fix) */
  maxCompletedSpans: number;
  /** Span timeout in milliseconds for orphaned spans (H3 fix) */
  spanTimeoutMs: number;
  /** Add console exporter by default (M5 fix - default false) */
  addConsoleExporter: boolean;
}

/**
 * Span event structure
 */
export interface SpanEvent {
  name: string;
  timestamp: number;
  attributes: Record<string, unknown>;
}

/**
 * Span link structure (for linking related traces)
 */
export interface SpanLink {
  traceId: string;
  spanId: string;
  attributes?: Record<string, unknown>;
}

/**
 * Span options for creating new spans
 */
export interface SpanOptions {
  /** Parent trace ID (for distributed tracing) */
  traceId?: string;
  /** Parent span ID (for child spans) */
  parentSpanId?: string | null;
  /** Initial attributes */
  attributes?: Record<string, unknown>;
  /** Links to related spans */
  links?: SpanLink[];
}

/**
 * Serialized span for export
 */
export interface SpanJSON {
  traceId: string;
  spanId: string;
  parentSpanId: string | null;
  name: string;
  startTime: number;
  endTime: number | null;
  duration: number | null;
  status: SpanStatus;
  statusMessage?: string;
  attributes: Record<string, unknown>;
  events: SpanEvent[];
  links: SpanLink[];
}

/**
 * Log entry structure
 */
export interface LogEntry {
  timestamp: string;
  level: string;
  service: string;
  message: string;
  trace_id?: string;
  span_id?: string;
  [key: string]: unknown;
}

/**
 * Counter metric structure
 */
export interface CounterMetric {
  name: string;
  labels: Record<string, string>;
  value: number;
  lastUpdated: number;
}

/**
 * Gauge metric structure
 */
export interface GaugeMetric {
  name: string;
  labels: Record<string, string>;
  value: number;
  lastUpdated: number;
}

/**
 * Histogram metric structure
 */
export interface HistogramMetric {
  name: string;
  labels: Record<string, string>;
  values: number[];
  count: number;
  sum: number;
  min: number | null;
  max: number | null;
  lastUpdated: number;
}

/**
 * All metrics collection
 */
export interface AllMetrics {
  counters: Record<string, CounterMetric>;
  gauges: Record<string, GaugeMetric>;
  histograms: Record<string, HistogramMetric>;
}

/**
 * Span exporter interface
 */
export interface SpanExporter {
  export(span: Span): void;
}

/**
 * Telemetry instance interface
 */
export interface TelemetryInstance {
  tracer: Tracer;
  metrics: MetricsCollector;
  logger: StructuredLogger;
  startSpan: (name: string, options?: SpanOptions) => Span;
  endSpan: (span: Span) => Span;
  increment: (name: string, value?: number, labels?: Record<string, string>) => void;
  gauge: (name: string, value: number, labels?: Record<string, string>) => void;
  histogram: (name: string, value: number, labels?: Record<string, string>) => void;
  log: (level: string, message: string, context?: Record<string, unknown>) => void;
  shutdown: () => void;
}

// =============================================================================
// Default Configuration
// =============================================================================

/**
 * Default telemetry configuration
 */
export const DEFAULT_TELEMETRY_CONFIG: TelemetryConfig = {
  enabled: true,
  logLevel: 'INFO',
  logLevelNumeric: LogLevel.INFO,
  traceEnabled: true,
  metricsEnabled: true,
  logFormat: 'json',
  maxLogSize: 10 * 1024 * 1024, // 10MB
  maxLogFiles: 5,
  flushInterval: 5000,
  maxCompletedSpans: 10000,
  spanTimeoutMs: 5 * 60 * 1000, // 5 minutes
  addConsoleExporter: false
};

// =============================================================================
// ID Generation (OpenTelemetry Compatible)
// =============================================================================

/**
 * Generate a cryptographically random hex string
 * @param bytes - Number of random bytes
 * @returns Hex string of specified length
 * @throws Error if crypto API is unavailable (H1 fix: no weak fallback)
 */
function randomHex(bytes: number): string {
  if (typeof crypto === 'undefined' || !crypto.getRandomValues) {
    throw new Error(
      'Cryptographic API unavailable. OpenTelemetry-Lite requires a secure ' +
      'random number generator. Ensure you are running in an environment ' +
      'that supports the Web Crypto API or Node.js crypto module.'
    );
  }
  const array = new Uint8Array(bytes);
  crypto.getRandomValues(array);
  return Array.from(array)
    .map(b => b.toString(16).padStart(2, '0'))
    .join('');
}

/**
 * Generate OpenTelemetry-compatible trace ID (32-char hex, 128-bit)
 * @returns 32-character hex string
 */
export function generateTraceId(): string {
  return randomHex(16);
}

/**
 * Generate OpenTelemetry-compatible span ID (16-char hex, 64-bit)
 * @returns 16-character hex string
 */
export function generateSpanId(): string {
  return randomHex(8);
}

// =============================================================================
// Span Class
// =============================================================================

/**
 * Span class for distributed tracing
 *
 * Represents a unit of work within a trace. Spans can be nested to show
 * parent-child relationships and can contain events and attributes.
 *
 * @example
 * ```typescript
 * const span = new Span('database-query', {
 *   attributes: { 'db.system': 'postgresql' }
 * });
 * span.setAttribute('db.statement', 'SELECT * FROM users');
 * span.addEvent('query-start');
 * // ... perform work ...
 * span.setStatus(SpanStatus.OK);
 * span.end();
 * ```
 */
export class Span {
  /** Span name/operation */
  public readonly name: string;
  /** Trace ID (shared across related spans) */
  public readonly traceId: string;
  /** Unique span ID */
  public readonly spanId: string;
  /** Parent span ID (null for root spans) */
  public readonly parentSpanId: string | null;
  /** Start timestamp in milliseconds */
  public readonly startTime: number;
  /** End timestamp in milliseconds (null if not ended) */
  public endTime: number | null = null;
  /** Duration in milliseconds (null if not ended) */
  public duration: number | null = null;
  /** Span status */
  public status: SpanStatus = SpanStatus.UNSET;
  /** Status message (optional) */
  public statusMessage?: string;
  /** Span attributes (key-value metadata) */
  public attributes: Record<string, unknown>;
  /** Span events (timestamped logs within the span) */
  public events: SpanEvent[] = [];
  /** Links to related spans */
  public links: SpanLink[] = [];

  constructor(name: string, options: SpanOptions = {}) {
    this.name = name;
    this.traceId = options.traceId || generateTraceId();
    this.spanId = generateSpanId();
    this.parentSpanId = options.parentSpanId ?? null;
    this.startTime = Date.now();
    this.attributes = options.attributes || {};
    this.links = options.links || [];
  }

  /**
   * Set a single attribute
   * @param key - Attribute key
   * @param value - Attribute value
   * @returns this (for chaining)
   */
  setAttribute(key: string, value: unknown): this {
    this.attributes[key] = value;
    return this;
  }

  /**
   * Set multiple attributes at once
   * @param attrs - Object containing attributes
   * @returns this (for chaining)
   */
  setAttributes(attrs: Record<string, unknown>): this {
    Object.assign(this.attributes, attrs);
    return this;
  }

  /**
   * Add an event to the span
   * @param name - Event name
   * @param attributes - Event attributes
   * @returns this (for chaining)
   */
  addEvent(name: string, attributes: Record<string, unknown> = {}): this {
    this.events.push({
      name,
      timestamp: Date.now(),
      attributes
    });
    return this;
  }

  /**
   * Add a link to another span
   * @param traceId - Linked trace ID
   * @param spanId - Linked span ID
   * @param attributes - Link attributes
   * @returns this (for chaining)
   */
  addLink(traceId: string, spanId: string, attributes?: Record<string, unknown>): this {
    this.links.push({ traceId, spanId, attributes });
    return this;
  }

  /**
   * Set the span status
   * @param status - Status code
   * @param message - Optional status message
   * @returns this (for chaining)
   */
  setStatus(status: SpanStatus, message?: string): this {
    this.status = status;
    if (message) {
      this.statusMessage = message;
    }
    return this;
  }

  /**
   * End the span (records end time and calculates duration)
   * @returns this (for chaining)
   */
  end(): this {
    this.endTime = Date.now();
    this.duration = this.endTime - this.startTime;
    return this;
  }

  /**
   * Check if span has ended
   * @returns true if span has been ended
   */
  isEnded(): boolean {
    return this.endTime !== null;
  }

  /**
   * Convert span to JSON for export
   * @returns Serialized span object
   */
  toJSON(): SpanJSON {
    return {
      traceId: this.traceId,
      spanId: this.spanId,
      parentSpanId: this.parentSpanId,
      name: this.name,
      startTime: this.startTime,
      endTime: this.endTime,
      duration: this.duration,
      status: this.status,
      statusMessage: this.statusMessage,
      attributes: this.attributes,
      events: this.events,
      links: this.links
    };
  }
}

// =============================================================================
// Tracer Class
// =============================================================================

/**
 * Tracer class for creating and managing spans
 *
 * Central component for distributed tracing. Creates spans, manages their
 * lifecycle, and exports completed spans to configured exporters.
 *
 * @example
 * ```typescript
 * const tracer = new Tracer('my-service');
 * tracer.addExporter(new ConsoleSpanExporter());
 *
 * const span = tracer.startSpan('http-request');
 * span.setAttribute('http.method', 'GET');
 * // ... perform work ...
 * tracer.endSpan(span);
 * ```
 */
export class Tracer {
  /** Service name for this tracer */
  public readonly serviceName: string;
  /** Tracer configuration */
  public readonly config: TelemetryConfig;
  /** Currently active (unfinished) spans */
  private activeSpans: Map<string, Span> = new Map();
  /** Completed spans (for batch export) */
  private completedSpans: Span[] = [];
  /** Registered exporters */
  private exporters: SpanExporter[] = [];
  /** Timer for orphaned span cleanup (H3 fix) */
  private orphanCleanupTimer: ReturnType<typeof setInterval> | null = null;

  constructor(serviceName: string, config: Partial<TelemetryConfig> = {}) {
    this.serviceName = serviceName;
    this.config = { ...DEFAULT_TELEMETRY_CONFIG, ...config };
    // Compute numeric log level if logLevel was provided but logLevelNumeric was not
    if (config.logLevel && !config.logLevelNumeric) {
      this.config.logLevelNumeric = LogLevel[this.config.logLevel] ?? LogLevel.INFO;
    }
    // Start orphan span cleanup timer (H3 fix)
    this.startOrphanCleanup();
  }

  /**
   * Start the orphaned span cleanup timer (H3 fix)
   * Automatically ends spans that have been active longer than spanTimeoutMs
   */
  private startOrphanCleanup(): void {
    // Check every minute for orphaned spans
    const checkInterval = Math.min(60000, this.config.spanTimeoutMs / 2);
    this.orphanCleanupTimer = setInterval(() => {
      const now = Date.now();
      const timeout = this.config.spanTimeoutMs;
      for (const [spanId, span] of this.activeSpans) {
        if (now - span.startTime > timeout) {
          // Mark as timed out and end
          span.setStatus(SpanStatus.ERROR, 'Span timed out (orphaned)');
          span.setAttribute('span.timeout', true);
          span.setAttribute('span.timeout_ms', timeout);
          this.endSpan(span);
        }
      }
    }, checkInterval);
  }

  /**
   * Stop the orphaned span cleanup timer
   */
  stopOrphanCleanup(): void {
    if (this.orphanCleanupTimer) {
      clearInterval(this.orphanCleanupTimer);
      this.orphanCleanupTimer = null;
    }
  }

  /**
   * Prune completed spans to stay within maxCompletedSpans limit (H2 fix)
   */
  private pruneCompletedSpans(): void {
    const max = this.config.maxCompletedSpans;
    if (this.completedSpans.length > max) {
      // Remove oldest spans (from the beginning)
      const toRemove = this.completedSpans.length - max;
      this.completedSpans.splice(0, toRemove);
    }
  }

  /**
   * Start a new span
   * @param name - Span name/operation
   * @param options - Span options
   * @returns New span instance
   */
  startSpan(name: string, options: SpanOptions = {}): Span {
    const span = new Span(name, options);
    span.setAttribute('service.name', this.serviceName);
    this.activeSpans.set(span.spanId, span);
    return span;
  }

  /**
   * End a span and export it
   * @param span - Span to end
   * @returns The ended span
   */
  endSpan(span: Span): Span {
    span.end();
    this.activeSpans.delete(span.spanId);
    this.completedSpans.push(span);

    // Prune completed spans to prevent memory leak (H2 fix)
    this.pruneCompletedSpans();

    // Export to all registered exporters
    for (const exporter of this.exporters) {
      exporter.export(span);
    }

    return span;
  }

  /**
   * Create a child span from a parent span
   * @param parent - Parent span
   * @param name - Child span name
   * @returns New child span
   */
  startChildSpan(parent: Span, name: string): Span {
    return this.startSpan(name, {
      traceId: parent.traceId,
      parentSpanId: parent.spanId
    });
  }

  /**
   * Add an exporter for completed spans
   * @param exporter - Exporter instance
   */
  addExporter(exporter: SpanExporter): void {
    this.exporters.push(exporter);
  }

  /**
   * Remove an exporter
   * @param exporter - Exporter to remove
   * @returns true if exporter was found and removed
   */
  removeExporter(exporter: SpanExporter): boolean {
    const index = this.exporters.indexOf(exporter);
    if (index !== -1) {
      this.exporters.splice(index, 1);
      return true;
    }
    return false;
  }

  /**
   * Get all completed spans
   * @returns Array of completed spans
   */
  getCompletedSpans(): Span[] {
    return [...this.completedSpans];
  }

  /**
   * Get all active (unfinished) spans
   * @returns Array of active spans
   */
  getActiveSpans(): Span[] {
    return Array.from(this.activeSpans.values());
  }

  /**
   * Get a specific active span by ID
   * @param spanId - Span ID to find
   * @returns Span or undefined
   */
  getActiveSpan(spanId: string): Span | undefined {
    return this.activeSpans.get(spanId);
  }

  /**
   * Clear completed spans from memory
   */
  clearSpans(): void {
    this.completedSpans = [];
  }

  /**
   * Get span count statistics
   * @returns Object with active and completed counts
   */
  getStats(): { active: number; completed: number } {
    return {
      active: this.activeSpans.size,
      completed: this.completedSpans.length
    };
  }
}

// =============================================================================
// Metrics Collector
// =============================================================================

/**
 * Metrics collector for counters, gauges, and histograms
 *
 * Collects and aggregates metrics with support for labeled dimensions.
 * Can export to Prometheus format.
 *
 * @example
 * ```typescript
 * const metrics = new MetricsCollector('my-service');
 *
 * // Counter (monotonic)
 * metrics.incrementCounter('http_requests_total', 1, { method: 'GET' });
 *
 * // Gauge (point-in-time)
 * metrics.setGauge('active_connections', 42);
 *
 * // Histogram (distribution)
 * metrics.recordHistogram('request_duration_ms', 150, { endpoint: '/api' });
 * ```
 */
export class MetricsCollector {
  /** Service name for metric labeling */
  public readonly serviceName: string;
  /** Counter metrics */
  private counters: Map<string, CounterMetric> = new Map();
  /** Gauge metrics */
  private gauges: Map<string, GaugeMetric> = new Map();
  /** Histogram metrics */
  private histograms: Map<string, HistogramMetric> = new Map();

  constructor(serviceName: string) {
    this.serviceName = serviceName;
  }

  /**
   * Generate a unique key for a metric with labels
   */
  private makeKey(name: string, labels: Record<string, string>): string {
    const labelStr = Object.entries(labels)
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([k, v]) => `${k}=${v}`)
      .join(',');
    return `${name}{${labelStr}}`;
  }

  /**
   * Format labels for Prometheus output
   */
  private formatLabels(labels: Record<string, string>): string {
    if (Object.keys(labels).length === 0) return '';
    const pairs = Object.entries(labels).map(([k, v]) => `${k}="${v}"`);
    return `{${pairs.join(',')}}`;
  }

  /**
   * Increment a counter metric
   * @param name - Counter name
   * @param value - Value to add (default: 1)
   * @param labels - Dimension labels
   */
  incrementCounter(name: string, value: number = 1, labels: Record<string, string> = {}): void {
    this.validateMetricName(name);
    const key = this.makeKey(name, labels);
    const current = this.counters.get(key) || { name, labels, value: 0, lastUpdated: 0 };
    current.value += value;
    current.lastUpdated = Date.now();
    this.counters.set(key, current);
  }

  /**
   * Set a gauge metric value
   * @param name - Gauge name
   * @param value - Current value
   * @param labels - Dimension labels
   */
  setGauge(name: string, value: number, labels: Record<string, string> = {}): void {
    this.validateMetricName(name);
    const key = this.makeKey(name, labels);
    this.gauges.set(key, {
      name,
      labels,
      value,
      lastUpdated: Date.now()
    });
  }

  /**
   * Validate metric name against Prometheus naming conventions (L3 fix)
   * @param name - Metric name to validate
   * @throws Error if name is invalid
   */
  private validateMetricName(name: string): void {
    // Prometheus metric name regex: [a-zA-Z_:][a-zA-Z0-9_:]*
    const validNameRegex = /^[a-zA-Z_:][a-zA-Z0-9_:]*$/;
    if (!validNameRegex.test(name)) {
      throw new Error(
        `Invalid metric name: "${name}". Metric names must match [a-zA-Z_:][a-zA-Z0-9_:]* ` +
        '(start with letter, underscore, or colon; contain only letters, digits, underscores, and colons)'
      );
    }
    // Warn about reserved prefixes
    if (name.startsWith('__')) {
      throw new Error(
        `Invalid metric name: "${name}". Names starting with "__" are reserved for internal use.`
      );
    }
  }

  /**
   * Record a histogram value
   * @param name - Histogram name
   * @param value - Value to record
   * @param labels - Dimension labels
   */
  recordHistogram(name: string, value: number, labels: Record<string, string> = {}): void {
    this.validateMetricName(name);
    const key = this.makeKey(name, labels);
    const histogram = this.histograms.get(key) || {
      name,
      labels,
      values: [],
      count: 0,
      sum: 0,
      min: null,  // M1 fix: Initialize to null instead of Infinity
      max: null,  // M1 fix: Initialize to null instead of -Infinity
      lastUpdated: 0
    };

    histogram.values.push(value);
    histogram.count++;
    histogram.sum += value;
    // M1 fix: Handle null comparison for min/max
    histogram.min = histogram.min === null ? value : Math.min(histogram.min, value);
    histogram.max = histogram.max === null ? value : Math.max(histogram.max, value);
    histogram.lastUpdated = Date.now();

    this.histograms.set(key, histogram);
  }

  /**
   * Get a counter value
   * @param name - Counter name
   * @param labels - Dimension labels
   * @returns Counter value or 0
   */
  getCounter(name: string, labels: Record<string, string> = {}): number {
    const key = this.makeKey(name, labels);
    return this.counters.get(key)?.value ?? 0;
  }

  /**
   * Get a gauge value
   * @param name - Gauge name
   * @param labels - Dimension labels
   * @returns Gauge value or undefined
   */
  getGauge(name: string, labels: Record<string, string> = {}): number | undefined {
    const key = this.makeKey(name, labels);
    return this.gauges.get(key)?.value;
  }

  /**
   * Get histogram statistics
   * @param name - Histogram name
   * @param labels - Dimension labels
   * @returns Histogram stats or undefined
   */
  getHistogram(name: string, labels: Record<string, string> = {}): Omit<HistogramMetric, 'values'> | undefined {
    const key = this.makeKey(name, labels);
    const hist = this.histograms.get(key);
    if (!hist) return undefined;
    const { values: _values, ...stats } = hist;
    return stats;
  }

  /**
   * Get all metrics
   * @returns Object containing all counters, gauges, and histograms
   */
  getMetrics(): AllMetrics {
    return {
      counters: Object.fromEntries(this.counters),
      gauges: Object.fromEntries(this.gauges),
      histograms: Object.fromEntries(this.histograms)
    };
  }

  /**
   * Export metrics in Prometheus format
   * @returns Prometheus-formatted string
   */
  toPrometheus(): string {
    let output = '';
    const seenMetrics = new Set<string>();

    // Counters
    for (const [, counter] of this.counters) {
      const labels = this.formatLabels(counter.labels);
      // L2 fix: Add HELP comment (only once per metric name)
      if (!seenMetrics.has(counter.name)) {
        output += `# HELP ${counter.name} Counter metric for ${counter.name}\n`;
        output += `# TYPE ${counter.name} counter\n`;
        seenMetrics.add(counter.name);
      }
      output += `${counter.name}${labels} ${counter.value}\n`;
    }

    // Gauges
    for (const [, gauge] of this.gauges) {
      const labels = this.formatLabels(gauge.labels);
      // L2 fix: Add HELP comment (only once per metric name)
      if (!seenMetrics.has(gauge.name)) {
        output += `# HELP ${gauge.name} Gauge metric for ${gauge.name}\n`;
        output += `# TYPE ${gauge.name} gauge\n`;
        seenMetrics.add(gauge.name);
      }
      output += `${gauge.name}${labels} ${gauge.value}\n`;
    }

    // Histograms
    for (const [, hist] of this.histograms) {
      const labels = this.formatLabels(hist.labels);
      // L2 fix: Add HELP comment (only once per metric name)
      if (!seenMetrics.has(hist.name)) {
        output += `# HELP ${hist.name} Histogram metric for ${hist.name}\n`;
        output += `# TYPE ${hist.name} histogram\n`;
        seenMetrics.add(hist.name);
      }
      output += `${hist.name}_count${labels} ${hist.count}\n`;
      output += `${hist.name}_sum${labels} ${hist.sum}\n`;
      // M1 fix: Handle null min/max in export (skip if null)
      if (hist.min !== null) {
        output += `${hist.name}_min${labels} ${hist.min}\n`;
      }
      if (hist.max !== null) {
        output += `${hist.name}_max${labels} ${hist.max}\n`;
      }
    }

    return output;
  }

  /**
   * Reset all metrics
   */
  reset(): void {
    this.counters.clear();
    this.gauges.clear();
    this.histograms.clear();
  }
}

// =============================================================================
// Structured Logger
// =============================================================================

/**
 * Structured logger with configurable levels and rotation support
 *
 * Provides structured JSON logging with trace context propagation.
 * Supports buffered writes and log rotation.
 *
 * @example
 * ```typescript
 * const logger = new StructuredLogger('my-service', { logLevel: 'DEBUG' });
 *
 * logger.info('Request received', { path: '/api/users', method: 'GET' });
 * logger.error('Database error', { error: err.message, traceId: span.traceId });
 *
 * // Graceful shutdown
 * logger.shutdown();
 * ```
 */
export class StructuredLogger {
  /** Service name for log entries */
  public readonly serviceName: string;
  /** Logger configuration */
  public readonly config: TelemetryConfig;
  /** Log buffer for batched writes */
  private buffer: LogEntry[] = [];
  /** Flush timer handle */
  private flushTimer: ReturnType<typeof setInterval> | null = null;
  /** Custom output handler (for non-console output) */
  private outputHandler?: (entry: LogEntry) => void;
  /** Custom flush handler (for file writes) */
  private flushHandler?: (entries: LogEntry[]) => void;

  constructor(serviceName: string, config: Partial<TelemetryConfig> = {}) {
    this.serviceName = serviceName;
    this.config = { ...DEFAULT_TELEMETRY_CONFIG, ...config };
    // M2 fix: Compute numeric log level if not already set
    if (config.logLevel && !config.logLevelNumeric) {
      this.config.logLevelNumeric = LogLevel[this.config.logLevel] ?? LogLevel.INFO;
    }
    this.startFlushTimer();
  }

  /**
   * Set a custom output handler for log entries
   * @param handler - Function to call for each log entry
   */
  setOutputHandler(handler: (entry: LogEntry) => void): void {
    this.outputHandler = handler;
  }

  /**
   * Set a custom flush handler for batched writes
   * @param handler - Function to call on flush with buffered entries
   */
  setFlushHandler(handler: (entries: LogEntry[]) => void): void {
    this.flushHandler = handler;
  }

  /**
   * Log a message at the specified level
   * @param level - Log level
   * @param message - Log message
   * @param context - Additional context
   */
  log(level: string, message: string, context: Record<string, unknown> = {}): void {
    const levelNum = LogLevel[level.toUpperCase() as keyof typeof LogLevel] ?? LogLevel.INFO;
    // M2 fix: Use pre-computed numeric level for direct comparison (no string lookup)
    const configLevel = this.config.logLevelNumeric;

    if (levelNum < configLevel) return;

    const entry: LogEntry = {
      timestamp: new Date().toISOString(),
      level: level.toUpperCase(),
      service: this.serviceName,
      message,
      ...context
    };

    // Add trace context if present
    if (context.traceId) {
      entry.trace_id = context.traceId as string;
    }
    if (context.spanId) {
      entry.span_id = context.spanId as string;
    }

    this.buffer.push(entry);

    // Output to console or custom handler
    if (this.outputHandler) {
      this.outputHandler(entry);
    } else if (this.config.logFormat === 'json') {
      console.log(JSON.stringify(entry));
    } else {
      console.log(`[${entry.timestamp}] ${entry.level} ${entry.message}`);
    }
  }

  /** Log at DEBUG level */
  debug(message: string, context: Record<string, unknown> = {}): void {
    this.log('debug', message, context);
  }

  /** Log at INFO level */
  info(message: string, context: Record<string, unknown> = {}): void {
    this.log('info', message, context);
  }

  /** Log at WARN level */
  warn(message: string, context: Record<string, unknown> = {}): void {
    this.log('warn', message, context);
  }

  /** Log at ERROR level */
  error(message: string, context: Record<string, unknown> = {}): void {
    this.log('error', message, context);
  }

  /** Log at FATAL level */
  fatal(message: string, context: Record<string, unknown> = {}): void {
    this.log('fatal', message, context);
  }

  /**
   * Log with trace context from a span
   * @param level - Log level
   * @param message - Log message
   * @param span - Span for trace context
   * @param context - Additional context
   */
  logWithSpan(level: string, message: string, span: Span, context: Record<string, unknown> = {}): void {
    this.log(level, message, {
      ...context,
      traceId: span.traceId,
      spanId: span.spanId
    });
  }

  /**
   * Start the automatic flush timer
   */
  private startFlushTimer(): void {
    if (this.config.flushInterval > 0) {
      this.flushTimer = setInterval(() => {
        // M3 fix: Add try-catch to prevent timer leak on error
        try {
          this.flush();
        } catch (error) {
          // Log error but don't crash - timer continues running
          console.error('[StructuredLogger] Flush error:', error);
        }
      }, this.config.flushInterval);
    }
  }

  /**
   * Stop the automatic flush timer
   */
  stopFlushTimer(): void {
    if (this.flushTimer) {
      clearInterval(this.flushTimer);
      this.flushTimer = null;
    }
  }

  /**
   * Flush the log buffer
   */
  flush(): void {
    if (this.buffer.length === 0) return;

    if (this.flushHandler) {
      this.flushHandler([...this.buffer]);
    }

    this.buffer = [];
  }

  /**
   * Get current buffer contents (for testing/debugging)
   * @returns Copy of buffered log entries
   */
  getBuffer(): LogEntry[] {
    return [...this.buffer];
  }

  /**
   * Get buffer size
   * @returns Number of buffered entries
   */
  getBufferSize(): number {
    return this.buffer.length;
  }

  /**
   * Shutdown the logger gracefully
   */
  shutdown(): void {
    this.stopFlushTimer();
    this.flush();
  }
}

// =============================================================================
// Span Exporters
// =============================================================================

/**
 * Console exporter for spans (useful for development/debugging)
 */
export class ConsoleSpanExporter implements SpanExporter {
  export(span: Span): void {
    console.log(JSON.stringify({
      type: 'span',
      ...span.toJSON()
    }));
  }
}

/**
 * In-memory exporter for spans (useful for testing)
 * M4 fix: Added maxSpans parameter to prevent unbounded storage
 */
export class InMemorySpanExporter implements SpanExporter {
  private spans: SpanJSON[] = [];
  /** Maximum spans to store (M4 fix) */
  private readonly maxSpans: number;

  /**
   * Create an in-memory span exporter
   * @param maxSpans - Maximum number of spans to store (default: 1000)
   */
  constructor(maxSpans: number = 1000) {
    this.maxSpans = maxSpans;
  }

  export(span: Span): void {
    this.spans.push(span.toJSON());
    // M4 fix: Prune oldest spans if over limit
    if (this.spans.length > this.maxSpans) {
      const toRemove = this.spans.length - this.maxSpans;
      this.spans.splice(0, toRemove);
    }
  }

  /** Get all exported spans */
  getSpans(): SpanJSON[] {
    return [...this.spans];
  }

  /** Clear exported spans */
  clear(): void {
    this.spans = [];
  }

  /** Get span count */
  count(): number {
    return this.spans.length;
  }

  /** Get the maximum spans limit */
  getMaxSpans(): number {
    return this.maxSpans;
  }
}

/**
 * Callback exporter for spans (for custom integrations)
 */
export class CallbackSpanExporter implements SpanExporter {
  private callback: (span: SpanJSON) => void;

  constructor(callback: (span: SpanJSON) => void) {
    this.callback = callback;
  }

  export(span: Span): void {
    this.callback(span.toJSON());
  }
}

// =============================================================================
// Factory Function
// =============================================================================

/**
 * Create a complete telemetry instance with tracer, metrics, and logger
 *
 * This is the recommended way to initialize telemetry for a service.
 *
 * @param serviceName - Name of the service
 * @param config - Configuration options
 * @returns Telemetry instance with convenience methods
 *
 * @example
 * ```typescript
 * const telemetry = createTelemetry('my-service', { logLevel: 'DEBUG' });
 *
 * // Start a trace
 * const span = telemetry.startSpan('http-request');
 *
 * // Record metrics
 * telemetry.increment('requests_total');
 * telemetry.histogram('request_duration_ms', 150);
 *
 * // Log with trace context
 * telemetry.log('info', 'Processing request', { traceId: span.traceId });
 *
 * // End trace
 * telemetry.endSpan(span);
 *
 * // Cleanup
 * telemetry.shutdown();
 * ```
 */
export function createTelemetry(serviceName: string, config: Partial<TelemetryConfig> = {}): TelemetryInstance {
  const mergedConfig = { ...DEFAULT_TELEMETRY_CONFIG, ...config };
  const tracer = new Tracer(serviceName, mergedConfig);
  const metrics = new MetricsCollector(serviceName);
  const logger = new StructuredLogger(serviceName, mergedConfig);

  // M5 fix: Only add console exporter if explicitly enabled (default false)
  if (mergedConfig.addConsoleExporter) {
    tracer.addExporter(new ConsoleSpanExporter());
  }

  return {
    tracer,
    metrics,
    logger,

    // Convenience methods
    startSpan: (name: string, options?: SpanOptions) => tracer.startSpan(name, options),
    endSpan: (span: Span) => tracer.endSpan(span),
    increment: (name: string, value?: number, labels?: Record<string, string>) =>
      metrics.incrementCounter(name, value, labels),
    gauge: (name: string, value: number, labels?: Record<string, string>) =>
      metrics.setGauge(name, value, labels),
    histogram: (name: string, value: number, labels?: Record<string, string>) =>
      metrics.recordHistogram(name, value, labels),
    log: (level: string, message: string, context?: Record<string, unknown>) =>
      logger.log(level, message, context),

    shutdown: () => {
      // Stop tracer's orphan cleanup timer
      tracer.stopOrphanCleanup();
      logger.shutdown();
    }
  };
}
