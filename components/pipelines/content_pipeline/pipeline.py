"""
Content Pipeline Core

Main pipeline orchestrator that executes phases in sequence with
dependency tracking, quality gates, and comprehensive result aggregation.

Author: Library extraction from weekly_zeitgeist_analysis.py
License: MIT
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Type, Union

from .phases import (
    Phase,
    PhaseType,
    PhaseStatus,
    PhaseResult,
    PhaseConfig,
    BasePhase,
    DownloadPhase,
    DownloadConfig,
    TranscribePhase,
    TranscribeConfig,
    AnalyzePhase,
    AnalyzeConfig,
    SynthesizePhase,
    DraftPhase,
    StylePhase,
    SlopDetectPhase,
    SlopDetectConfig,
    ImageGenPhase,
    CommitPhase,
    DeployPhase,
)

logger = logging.getLogger(__name__)


# Default phase order for standard content pipeline
DEFAULT_PHASE_ORDER = [
    PhaseType.DOWNLOAD,
    PhaseType.TRANSCRIBE,
    PhaseType.ANALYZE,
    PhaseType.SYNTHESIZE,
    PhaseType.DRAFT,
    PhaseType.STYLE,
    PhaseType.SLOP_DETECT,
    PhaseType.IMAGE_GEN,
    PhaseType.COMMIT,
    PhaseType.DEPLOY,
]

# Phase type to class mapping
PHASE_REGISTRY: Dict[PhaseType, Type[BasePhase]] = {
    PhaseType.DOWNLOAD: DownloadPhase,
    PhaseType.TRANSCRIBE: TranscribePhase,
    PhaseType.ANALYZE: AnalyzePhase,
    PhaseType.SYNTHESIZE: SynthesizePhase,
    PhaseType.DRAFT: DraftPhase,
    PhaseType.STYLE: StylePhase,
    PhaseType.SLOP_DETECT: SlopDetectPhase,
    PhaseType.IMAGE_GEN: ImageGenPhase,
    PhaseType.COMMIT: CommitPhase,
    PhaseType.DEPLOY: DeployPhase,
}


@dataclass
class QualityGate:
    """Quality gate that can block pipeline progression."""

    name: str
    check_fn: Callable[[Dict[str, Any]], bool]
    error_message: str = "Quality gate failed"
    after_phase: Optional[PhaseType] = None


@dataclass
class PipelineConfig:
    """Configuration for the content pipeline."""

    name: str = "content-pipeline"

    # Phase selection
    phases: List[PhaseType] = field(default_factory=lambda: DEFAULT_PHASE_ORDER.copy())
    skip_phases: List[PhaseType] = field(default_factory=list)

    # Phase-specific configs
    phase_configs: Dict[PhaseType, PhaseConfig] = field(default_factory=dict)

    # Directories
    base_dir: Optional[Path] = None
    download_dir: Optional[Path] = None
    transcript_dir: Optional[Path] = None
    analysis_dir: Optional[Path] = None
    blog_dir: Optional[Path] = None

    # Quality gates
    quality_gates: List[QualityGate] = field(default_factory=list)

    # Execution settings
    fail_fast: bool = True  # Stop on first failure
    parallel_phases: List[List[PhaseType]] = field(default_factory=list)  # Phases to run in parallel

    # Hooks
    on_phase_start: Optional[Callable[[PhaseType], None]] = None
    on_phase_complete: Optional[Callable[[PhaseResult], None]] = None
    on_pipeline_complete: Optional[Callable[["PipelineResult"], None]] = None

    def __post_init__(self):
        """Set up directory defaults from base_dir."""
        if self.base_dir:
            base = Path(self.base_dir) if isinstance(self.base_dir, str) else self.base_dir
            self.download_dir = self.download_dir or base / "downloads"
            self.transcript_dir = self.transcript_dir or base / "transcripts"
            self.analysis_dir = self.analysis_dir or base / "analysis"
            self.blog_dir = self.blog_dir or base / "drafts"

    def get_phase_config(self, phase_type: PhaseType) -> Optional[PhaseConfig]:
        """Get configuration for a specific phase."""
        return self.phase_configs.get(phase_type)


@dataclass
class PipelineResult:
    """Result from running the complete pipeline."""

    config: PipelineConfig
    success: bool = False
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    phase_results: Dict[PhaseType, PhaseResult] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None

    @property
    def duration_seconds(self) -> Optional[float]:
        """Total pipeline duration in seconds."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None

    @property
    def completed_phases(self) -> List[PhaseType]:
        """List of successfully completed phases."""
        return [
            pt for pt, pr in self.phase_results.items()
            if pr.status == PhaseStatus.COMPLETED
        ]

    @property
    def failed_phases(self) -> List[PhaseType]:
        """List of failed phases."""
        return [
            pt for pt, pr in self.phase_results.items()
            if pr.status == PhaseStatus.FAILED
        ]

    def get_phase_output(self, phase_type: PhaseType) -> Optional[Any]:
        """Get output from a specific phase."""
        result = self.phase_results.get(phase_type)
        return result.output if result else None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "name": self.config.name,
            "success": self.success,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_seconds": self.duration_seconds,
            "completed_phases": [p.value for p in self.completed_phases],
            "failed_phases": [p.value for p in self.failed_phases],
            "phase_results": {
                pt.value: pr.to_dict() for pt, pr in self.phase_results.items()
            },
            "error": self.error,
        }

    def summary(self) -> str:
        """Generate human-readable summary."""
        lines = [
            f"Pipeline: {self.config.name}",
            f"Status: {'SUCCESS' if self.success else 'FAILED'}",
            f"Duration: {self.duration_seconds:.1f}s" if self.duration_seconds else "Duration: N/A",
            f"Completed: {len(self.completed_phases)}/{len(self.phase_results)} phases",
        ]

        if self.failed_phases:
            lines.append(f"Failed phases: {', '.join(p.value for p in self.failed_phases)}")

        if self.error:
            lines.append(f"Error: {self.error}")

        return "\n".join(lines)


class ContentPipeline:
    """
    Async content pipeline orchestrator.

    Executes phases in sequence with:
    - Configurable phase selection
    - Quality gates between phases
    - Shared context passing
    - Comprehensive result tracking

    Usage:
        config = PipelineConfig(
            name="weekly-zeitgeist",
            phases=[PhaseType.DOWNLOAD, PhaseType.TRANSCRIBE, PhaseType.ANALYZE],
            phase_configs={
                PhaseType.DOWNLOAD: DownloadConfig(sources=["@channel"]),
            },
        )
        pipeline = ContentPipeline(config)
        result = await pipeline.run()
    """

    def __init__(
        self,
        config: Optional[PipelineConfig] = None,
        phases: Optional[Dict[PhaseType, Phase]] = None,
    ):
        """
        Initialize pipeline.

        Args:
            config: Pipeline configuration
            phases: Optional custom phase implementations
        """
        self.config = config or PipelineConfig()
        self._phases: Dict[PhaseType, Phase] = phases or {}
        self._context: Dict[str, Any] = {}
        self._result: Optional[PipelineResult] = None

        # Initialize default phases if not provided
        self._initialize_phases()

        logger.info(f"ContentPipeline '{self.config.name}' initialized with {len(self._phases)} phases")

    def _initialize_phases(self) -> None:
        """Initialize phase instances from config."""
        for phase_type in self.config.phases:
            if phase_type in self._phases:
                continue  # Custom phase already provided

            if phase_type in PHASE_REGISTRY:
                phase_class = PHASE_REGISTRY[phase_type]
                phase_config = self.config.get_phase_config(phase_type)
                self._phases[phase_type] = phase_class(phase_config)
            else:
                logger.warning(f"No implementation for phase type: {phase_type}")

    def set_phase(self, phase_type: PhaseType, phase: Phase) -> None:
        """
        Set a custom phase implementation.

        Args:
            phase_type: Type of phase to replace
            phase: Custom phase instance
        """
        self._phases[phase_type] = phase

    def add_quality_gate(
        self,
        name: str,
        check_fn: Callable[[Dict[str, Any]], bool],
        after_phase: Optional[PhaseType] = None,
        error_message: str = "Quality gate failed",
    ) -> None:
        """
        Add a quality gate to the pipeline.

        Args:
            name: Gate name for logging
            check_fn: Function that takes context and returns True if passed
            after_phase: Phase after which to run the gate (None = run after every phase)
            error_message: Message to log if gate fails
        """
        gate = QualityGate(
            name=name,
            check_fn=check_fn,
            after_phase=after_phase,
            error_message=error_message,
        )
        self.config.quality_gates.append(gate)

    async def run(
        self,
        initial_context: Optional[Dict[str, Any]] = None,
    ) -> PipelineResult:
        """
        Execute the pipeline.

        Args:
            initial_context: Initial context data to pass to phases

        Returns:
            PipelineResult with all phase results and final context
        """
        self._result = PipelineResult(
            config=self.config,
            started_at=datetime.now(),
            context=initial_context or {},
        )
        self._context = self._result.context.copy()

        # Add directory configs to context
        if self.config.download_dir:
            self._context["download_dir"] = self.config.download_dir
        if self.config.transcript_dir:
            self._context["transcript_dir"] = self.config.transcript_dir
        if self.config.analysis_dir:
            self._context["analysis_dir"] = self.config.analysis_dir
        if self.config.blog_dir:
            self._context["blog_dir"] = self.config.blog_dir

        logger.info(f"Starting pipeline '{self.config.name}' with {len(self.config.phases)} phases")

        try:
            for phase_type in self.config.phases:
                # Skip if in skip list
                if phase_type in self.config.skip_phases:
                    logger.info(f"Skipping phase: {phase_type.value}")
                    continue

                # Get phase instance
                phase = self._phases.get(phase_type)
                if not phase:
                    logger.warning(f"Phase not found: {phase_type.value}")
                    continue

                # Execute phase
                result = await self._execute_phase(phase_type, phase)
                self._result.phase_results[phase_type] = result

                # Update context with phase output
                if result.output and isinstance(result.output, dict):
                    self._context.update(result.output)

                # Check phase result
                if result.status == PhaseStatus.FAILED:
                    logger.error(f"Phase {phase_type.value} failed: {result.error}")
                    if self.config.fail_fast:
                        self._result.error = f"Phase {phase_type.value} failed: {result.error}"
                        break

                # Run quality gates
                gate_passed = await self._run_quality_gates(phase_type)
                if not gate_passed and self.config.fail_fast:
                    self._result.error = f"Quality gate failed after {phase_type.value}"
                    break

            # Determine overall success
            self._result.success = len(self._result.failed_phases) == 0

        except Exception as e:
            logger.exception(f"Pipeline error: {e}")
            self._result.error = str(e)
            self._result.success = False

        finally:
            self._result.completed_at = datetime.now()
            self._result.context = self._context.copy()

            if self.config.on_pipeline_complete:
                try:
                    self.config.on_pipeline_complete(self._result)
                except Exception as e:
                    logger.error(f"on_pipeline_complete hook error: {e}")

        logger.info(self._result.summary())
        return self._result

    async def _execute_phase(
        self,
        phase_type: PhaseType,
        phase: Phase,
    ) -> PhaseResult:
        """Execute a single phase with hooks."""
        logger.info(f"Executing phase: {phase_type.value}")

        if self.config.on_phase_start:
            try:
                self.config.on_phase_start(phase_type)
            except Exception as e:
                logger.error(f"on_phase_start hook error: {e}")

        result = await phase.execute(self._context)

        if self.config.on_phase_complete:
            try:
                self.config.on_phase_complete(result)
            except Exception as e:
                logger.error(f"on_phase_complete hook error: {e}")

        return result

    async def _run_quality_gates(self, after_phase: PhaseType) -> bool:
        """
        Run quality gates after a phase.

        Args:
            after_phase: The phase that just completed

        Returns:
            True if all gates passed
        """
        for gate in self.config.quality_gates:
            # Run gate if it's for this phase or for all phases
            if gate.after_phase is not None and gate.after_phase != after_phase:
                continue
            try:
                passed = gate.check_fn(self._context)
                if not passed:
                    logger.error(f"Quality gate '{gate.name}' failed: {gate.error_message}")
                    return False
                logger.debug(f"Quality gate '{gate.name}' passed")
            except Exception as e:
                logger.error(f"Quality gate '{gate.name}' error: {e}")
                return False

        return True

    async def run_single_phase(
        self,
        phase_type: PhaseType,
        context: Optional[Dict[str, Any]] = None,
    ) -> PhaseResult:
        """
        Run a single phase in isolation.

        Useful for testing or re-running a specific phase.

        Args:
            phase_type: Phase to run
            context: Context to pass to the phase

        Returns:
            PhaseResult from the phase
        """
        phase = self._phases.get(phase_type)
        if not phase:
            return PhaseResult(
                phase_type=phase_type,
                status=PhaseStatus.FAILED,
                error=f"Phase not found: {phase_type.value}",
            )

        return await phase.execute(context or {})

    def get_context(self) -> Dict[str, Any]:
        """Get current pipeline context."""
        return self._context.copy()

    def get_result(self) -> Optional[PipelineResult]:
        """Get most recent pipeline result."""
        return self._result


def create_standard_pipeline(
    sources: List[str],
    base_dir: Union[str, Path],
    slop_threshold: float = 0.05,
    skip_deploy: bool = True,
) -> ContentPipeline:
    """
    Create a standard content pipeline with sensible defaults.

    Args:
        sources: List of content sources (YouTube channels, RSS feeds, etc.)
        base_dir: Base directory for all pipeline outputs
        slop_threshold: Threshold for slop detection (default 5%)
        skip_deploy: Whether to skip deployment phase (default True for safety)

    Returns:
        Configured ContentPipeline instance
    """
    base_path = Path(base_dir) if isinstance(base_dir, str) else base_dir

    skip_phases = []
    if skip_deploy:
        skip_phases.append(PhaseType.DEPLOY)

    config = PipelineConfig(
        name="standard-content-pipeline",
        base_dir=base_path,
        skip_phases=skip_phases,
        phase_configs={
            PhaseType.DOWNLOAD: DownloadConfig(
                sources=sources,
                max_downloads_per_source=3,
            ),
            PhaseType.TRANSCRIBE: TranscribeConfig(
                model="small",
                language="en",
                delete_audio_after=True,
            ),
            PhaseType.ANALYZE: AnalyzeConfig(
                models=["gemini", "claude"],
                parallel=True,
            ),
            PhaseType.SLOP_DETECT: SlopDetectConfig(
                threshold=slop_threshold,
            ),
        },
    )

    # Add slop quality gate
    pipeline = ContentPipeline(config)
    pipeline.add_quality_gate(
        name="slop-threshold",
        check_fn=lambda ctx: ctx.get("passed", True),
        after_phase=PhaseType.SLOP_DETECT,
        error_message=f"Content failed slop detection (threshold: {slop_threshold})",
    )

    return pipeline
