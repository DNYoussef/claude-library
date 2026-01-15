/**
 * QA Pipeline API Services
 *
 * Services for QA runs, Spec management, and Recovery operations.
 * Built on BaseResourceService with domain-specific extensions.
 */

import {
  ApiClient,
  query,
} from './base_service';

import type {
  QAStatusResponse,
  QAHistoryResponse,
  QARunRequest,
  QARunResponse,
  QAConfig,
  ComplexityAnalysis,
  ValidationResponse,
  SpecListResponse,
  SpecOrchestrateRequest,
  SpecOrchestrateResponse,
  SpecAssessment,
  RecoveryStatusResponse,
  SubtaskHistory,
  ClassifyErrorResponse,
  RollbackResponse,
  RecoveryHints,
  RecordAttemptRequest,
  SuccessResponse,
} from './types';

// ============ QA PIPELINE SERVICE ============

/**
 * QA Pipeline API service for test runs and configuration
 */
export class QAPipelineService {
  constructor(private client: ApiClient) {}

  private get endpoint(): string {
    return '/api/v1/qa';
  }

  /**
   * Get QA status for a spec directory
   */
  async getStatus(specDir: string, projectDir?: string): Promise<QAStatusResponse> {
    const params = query()
      .add('spec_dir', specDir)
      .add('project_dir', projectDir);
    return this.client.get<QAStatusResponse>(`${this.endpoint}/status${params.build()}`);
  }

  /**
   * Get QA history for a spec directory
   */
  async getHistory(specDir: string, projectDir?: string): Promise<QAHistoryResponse> {
    const params = query()
      .add('spec_dir', specDir)
      .add('project_dir', projectDir);
    return this.client.get<QAHistoryResponse>(`${this.endpoint}/history${params.build()}`);
  }

  /**
   * Run QA pipeline
   */
  async run(request: QARunRequest): Promise<QARunResponse> {
    return this.client.post<QARunResponse>(`${this.endpoint}/run`, request);
  }

  /**
   * Get status of a specific QA run
   */
  async getRunStatus(runId: string): Promise<QARunResponse> {
    return this.client.get<QARunResponse>(`${this.endpoint}/run/${runId}`);
  }

  /**
   * Get QA configuration
   */
  async getConfig(): Promise<QAConfig> {
    return this.client.get<QAConfig>(`${this.endpoint}/config`);
  }

  /**
   * Update QA configuration
   */
  async updateConfig(config: Partial<QAConfig>): Promise<QAConfig> {
    return this.client.put<QAConfig>(`${this.endpoint}/config`, config);
  }

  /**
   * Get all active QA runs
   */
  async getActiveRuns(): Promise<Record<string, QARunResponse>> {
    return this.client.get<Record<string, QARunResponse>>(`${this.endpoint}/active-runs`);
  }

  /**
   * Check if there are any active runs
   */
  async hasActiveRuns(): Promise<boolean> {
    const runs = await this.getActiveRuns();
    return Object.keys(runs).length > 0;
  }

  /**
   * Wait for a run to complete with exponential backoff
   */
  async waitForRun(
    runId: string,
    options?: { pollInterval?: number; timeout?: number; maxInterval?: number }
  ): Promise<QARunResponse> {
    const { pollInterval = 2000, timeout = 300000, maxInterval = 30000 } = options || {};
    const startTime = Date.now();
    let currentInterval = pollInterval;

    while (Date.now() - startTime < timeout) {
      const status = await this.getRunStatus(runId);
      if (status.status === 'completed' || status.status === 'failed' || status.status === 'cancelled') {
        return status;
      }

      // Add jitter (0-25% random variation) to prevent thundering herd
      const jitter = currentInterval * (Math.random() * 0.25);
      const waitTime = Math.min(currentInterval + jitter, maxInterval);

      await new Promise(resolve => setTimeout(resolve, waitTime));

      // Exponential backoff: double the interval each iteration, capped at maxInterval
      currentInterval = Math.min(currentInterval * 2, maxInterval);
    }

    throw new Error(`QA run ${runId} did not complete within ${timeout}ms`);
  }

  /**
   * Run QA and wait for completion
   */
  async runAndWait(
    request: QARunRequest,
    options?: { pollInterval?: number; timeout?: number }
  ): Promise<QARunResponse> {
    const response = await this.run(request);
    return this.waitForRun(response.run_id, options);
  }
}

// ============ SPEC PIPELINE SERVICE ============

/**
 * Spec Pipeline API service for specification management and orchestration
 */
export class SpecPipelineService {
  constructor(private client: ApiClient) {}

  private get endpoint(): string {
    return '/api/v1/spec';
  }

  /**
   * Analyze complexity of a specification
   */
  async analyzeComplexity(specDir: string, projectDir?: string): Promise<ComplexityAnalysis> {
    const params = query()
      .add('spec_dir', specDir)
      .add('project_dir', projectDir);
    return this.client.get<ComplexityAnalysis>(`${this.endpoint}/analyze${params.build()}`);
  }

  /**
   * Validate a specification
   */
  async validate(
    specDir: string,
    projectDir?: string,
    autoFix = false
  ): Promise<ValidationResponse> {
    const params = query()
      .add('spec_dir', specDir)
      .add('project_dir', projectDir)
      .add('auto_fix', autoFix);
    return this.client.get<ValidationResponse>(`${this.endpoint}/validate${params.build()}`);
  }

  /**
   * Orchestrate specification execution
   */
  async orchestrate(request: SpecOrchestrateRequest): Promise<SpecOrchestrateResponse> {
    return this.client.post<SpecOrchestrateResponse>(`${this.endpoint}/orchestrate`, request);
  }

  /**
   * Get orchestration status
   */
  async getOrchestrateStatus(runId: string): Promise<SpecOrchestrateResponse> {
    return this.client.get<SpecOrchestrateResponse>(`${this.endpoint}/orchestrate/${runId}`);
  }

  /**
   * List specifications in a project
   */
  async listSpecs(projectDir: string): Promise<SpecListResponse> {
    return this.client.get<SpecListResponse>(
      `${this.endpoint}/list?project_dir=${encodeURIComponent(projectDir)}`
    );
  }

  /**
   * Get all active spec runs
   */
  async getActiveRuns(): Promise<Record<string, SpecOrchestrateResponse>> {
    return this.client.get<Record<string, SpecOrchestrateResponse>>(`${this.endpoint}/active-runs`);
  }

  /**
   * Get comprehensive spec assessment
   */
  async getAssessment(specDir: string, projectDir?: string): Promise<SpecAssessment> {
    const params = query()
      .add('spec_dir', specDir)
      .add('project_dir', projectDir);
    return this.client.get<SpecAssessment>(`${this.endpoint}/assessment${params.build()}`);
  }

  /**
   * Check if specification is valid
   */
  async isValid(specDir: string, projectDir?: string): Promise<boolean> {
    const result = await this.validate(specDir, projectDir);
    return result.valid;
  }

  /**
   * Get complexity level
   */
  async getComplexityLevel(
    specDir: string,
    projectDir?: string
  ): Promise<'simple' | 'standard' | 'complex'> {
    const result = await this.analyzeComplexity(specDir, projectDir);
    return result.complexity;
  }

  /**
   * Wait for orchestration to complete with exponential backoff
   */
  async waitForOrchestration(
    runId: string,
    options?: { pollInterval?: number; timeout?: number; maxInterval?: number }
  ): Promise<SpecOrchestrateResponse> {
    const { pollInterval = 5000, timeout = 600000, maxInterval = 60000 } = options || {};
    const startTime = Date.now();
    let currentInterval = pollInterval;

    while (Date.now() - startTime < timeout) {
      const status = await this.getOrchestrateStatus(runId);
      if (status.status === 'completed' || status.status === 'error') {
        return status;
      }

      // Add jitter (0-25% random variation) to prevent thundering herd
      const jitter = currentInterval * (Math.random() * 0.25);
      const waitTime = Math.min(currentInterval + jitter, maxInterval);

      await new Promise(resolve => setTimeout(resolve, waitTime));

      // Exponential backoff: double the interval each iteration, capped at maxInterval
      currentInterval = Math.min(currentInterval * 2, maxInterval);
    }

    throw new Error(`Orchestration ${runId} did not complete within ${timeout}ms`);
  }

  /**
   * Orchestrate and wait for completion
   */
  async orchestrateAndWait(
    request: SpecOrchestrateRequest,
    options?: { pollInterval?: number; timeout?: number }
  ): Promise<SpecOrchestrateResponse> {
    const response = await this.orchestrate({ ...request, background: true });
    return this.waitForOrchestration(response.run_id, options);
  }
}

// ============ RECOVERY SERVICE ============

/**
 * Recovery API service for rollback and error recovery operations
 */
export class RecoveryService {
  constructor(private client: ApiClient) {}

  private get endpoint(): string {
    return '/api/v1/recovery';
  }

  /**
   * Get recovery status for a spec
   */
  async getStatus(specDir: string, projectDir?: string): Promise<RecoveryStatusResponse> {
    const params = query()
      .add('spec_dir', specDir)
      .add('project_dir', projectDir);
    return this.client.get<RecoveryStatusResponse>(`${this.endpoint}/status${params.build()}`);
  }

  /**
   * Trigger rollback
   */
  async rollback(specDir: string, projectDir?: string): Promise<RollbackResponse> {
    return this.client.post<RollbackResponse>(`${this.endpoint}/rollback`, {
      spec_dir: specDir,
      project_dir: projectDir,
    });
  }

  /**
   * Clear stuck subtasks
   */
  async clearStuck(
    specDir: string,
    projectDir?: string
  ): Promise<{ success: boolean; cleared_count: number; message: string }> {
    return this.client.post<{ success: boolean; cleared_count: number; message: string }>(
      `${this.endpoint}/clear-stuck`,
      { spec_dir: specDir, project_dir: projectDir }
    );
  }

  /**
   * Reset recovery state
   */
  async reset(
    specDir: string,
    projectDir?: string
  ): Promise<{ success: boolean; stuck_cleared: number; subtasks_reset: number; message: string }> {
    return this.client.post<{ success: boolean; stuck_cleared: number; subtasks_reset: number; message: string }>(
      `${this.endpoint}/reset`,
      { spec_dir: specDir, project_dir: projectDir }
    );
  }

  /**
   * Get subtask history
   */
  async getSubtaskHistory(
    subtaskId: string,
    specDir: string,
    projectDir?: string
  ): Promise<SubtaskHistory> {
    const params = query()
      .add('spec_dir', specDir)
      .add('project_dir', projectDir);
    return this.client.get<SubtaskHistory>(`${this.endpoint}/history/${subtaskId}${params.build()}`);
  }

  /**
   * Classify an error
   */
  async classifyError(
    errorMessage: string,
    specDir: string,
    subtaskId?: string,
    projectDir?: string
  ): Promise<ClassifyErrorResponse> {
    return this.client.post<ClassifyErrorResponse>(`${this.endpoint}/classify`, {
      error_message: errorMessage,
      spec_dir: specDir,
      subtask_id: subtaskId,
      project_dir: projectDir,
    });
  }

  /**
   * Record an attempt
   */
  async recordAttempt(request: RecordAttemptRequest): Promise<SuccessResponse> {
    return this.client.post<SuccessResponse>(`${this.endpoint}/record-attempt`, request);
  }

  /**
   * Record a good commit
   */
  async recordGoodCommit(
    specDir: string,
    commit: string,
    projectDir?: string
  ): Promise<SuccessResponse> {
    return this.client.post<SuccessResponse>(`${this.endpoint}/record-good-commit`, {
      spec_dir: specDir,
      commit,
      project_dir: projectDir,
    });
  }

  /**
   * Get recovery hints for a subtask
   */
  async getHints(
    subtaskId: string,
    specDir: string,
    projectDir?: string
  ): Promise<RecoveryHints> {
    const params = query()
      .add('spec_dir', specDir)
      .add('project_dir', projectDir);
    return this.client.get<RecoveryHints>(`${this.endpoint}/hints/${subtaskId}${params.build()}`);
  }

  /**
   * Check if recovery is available
   */
  async isRecoveryAvailable(specDir: string, projectDir?: string): Promise<boolean> {
    const status = await this.getStatus(specDir, projectDir);
    return status.recovery_available;
  }

  /**
   * Check if there are stuck subtasks
   */
  async hasStuckSubtasks(specDir: string, projectDir?: string): Promise<boolean> {
    const status = await this.getStatus(specDir, projectDir);
    return status.stuck_subtasks > 0;
  }

  /**
   * Get recommended action based on current state
   */
  async getRecommendedAction(
    specDir: string,
    projectDir?: string
  ): Promise<'continue' | 'rollback' | 'reset' | 'manual'> {
    const status = await this.getStatus(specDir, projectDir);

    if (!status.has_recovery_state) {
      return 'continue';
    }

    if (status.stuck_subtasks > 3) {
      return 'reset';
    }

    if (status.stuck_subtasks > 0 && status.recovery_available) {
      return 'rollback';
    }

    if (status.stuck_subtasks > 0) {
      return 'manual';
    }

    return 'continue';
  }
}

// ============ QA SERVICE FACADE ============

/**
 * Unified QA service providing access to all sub-services
 */
export class QAService {
  public readonly pipeline: QAPipelineService;
  public readonly spec: SpecPipelineService;
  public readonly recovery: RecoveryService;

  constructor(client: ApiClient) {
    this.pipeline = new QAPipelineService(client);
    this.spec = new SpecPipelineService(client);
    this.recovery = new RecoveryService(client);
  }

  /**
   * Get comprehensive status for a spec
   */
  async getFullStatus(specDir: string, projectDir?: string): Promise<{
    qa: QAStatusResponse;
    validation: ValidationResponse;
    complexity: ComplexityAnalysis;
    recovery: RecoveryStatusResponse;
  }> {
    const [qa, validation, complexity, recovery] = await Promise.all([
      this.pipeline.getStatus(specDir, projectDir),
      this.spec.validate(specDir, projectDir),
      this.spec.analyzeComplexity(specDir, projectDir),
      this.recovery.getStatus(specDir, projectDir),
    ]);

    return { qa, validation, complexity, recovery };
  }

  /**
   * Run full QA cycle: validate, run tests, handle recovery
   */
  async runFullCycle(
    specDir: string,
    projectDir?: string,
    options?: { autoRecover?: boolean; pollInterval?: number; timeout?: number }
  ): Promise<{
    validation: ValidationResponse;
    qaRun: QARunResponse;
    recovered?: boolean;
  }> {
    const { autoRecover = true, ...waitOptions } = options || {};

    // Validate first
    const validation = await this.spec.validate(specDir, projectDir, autoRecover);
    if (!validation.valid) {
      throw new Error(`Specification validation failed: ${validation.issues.length} issues found`);
    }

    // Run QA
    const qaRun = await this.pipeline.runAndWait(
      { spec_dir: specDir, project_dir: projectDir },
      waitOptions
    );

    // Check if recovery needed
    if (qaRun.status === 'failed' && autoRecover) {
      const recoveryStatus = await this.recovery.getStatus(specDir, projectDir);
      if (recoveryStatus.recovery_available) {
        await this.recovery.rollback(specDir, projectDir);
        return { validation, qaRun, recovered: true };
      }
    }

    return { validation, qaRun, recovered: false };
  }

  /**
   * Check overall health of a spec
   */
  async checkHealth(
    specDir: string,
    projectDir?: string
  ): Promise<'healthy' | 'warning' | 'critical' | 'unknown'> {
    const assessment = await this.spec.getAssessment(specDir, projectDir);
    return assessment.overall_health;
  }
}

// ============ FACTORY FUNCTIONS ============

/**
 * Create a QA Pipeline service instance
 */
export function createQAPipelineService(client: ApiClient): QAPipelineService {
  return new QAPipelineService(client);
}

/**
 * Create a Spec Pipeline service instance
 */
export function createSpecPipelineService(client: ApiClient): SpecPipelineService {
  return new SpecPipelineService(client);
}

/**
 * Create a Recovery service instance
 */
export function createRecoveryService(client: ApiClient): RecoveryService {
  return new RecoveryService(client);
}

/**
 * Create a unified QA service instance
 */
export function createQAService(client: ApiClient): QAService {
  return new QAService(client);
}
