/**
 * Consensus Display Library
 *
 * A reusable React component for multi-model AI consensus.
 *
 * @packageDocumentation
 */

// =============================================================================
// MAIN COMPONENT
// =============================================================================

export {
  ConsensusDisplay,
  ConsensusDisplay as default,
  getConsensusColor,
  getModelStatusColor,
  formatConsensusStatus,
} from './ConsensusDisplay';

// =============================================================================
// TYPES
// =============================================================================

export type {
  // Model types
  ModelResult,
  ModelResultFull,
  ModelStatus,
  ModelCapabilities,

  // Consensus types
  ConsensusStatus,
  TaskType,
  ConsensusResult,
  ConsensusResultFull,

  // API types
  ConsensusRequest,
  ModelsResponse,
  ApiError,

  // Component props
  ConsensusDisplayProps,
  TaskTypeOption,

  // Hook types
  UseConsensusState,
  UseConsensusActions,
  UseConsensusReturn,

  // Utility types
  ConsensusColorConfig,
} from './types';

// =============================================================================
// CONSTANTS
// =============================================================================

export {
  DEFAULT_CONSENSUS_COLORS,
  MODEL_STATUS_COLORS,
} from './types';
