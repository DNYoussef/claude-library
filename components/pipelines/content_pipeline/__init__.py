"""
Content Pipeline Component

A configurable, async multi-phase content processing pipeline.
Extracted from the weekly_zeitgeist_analysis.py for reusable content automation.

Features:
- Async phase execution with dependency tracking
- Configurable phases (download, transcribe, analyze, synthesize, etc.)
- Quality gates between phases
- Multi-model analysis support
- Pluggable phase implementations

Usage:
    from library.components.pipelines.content_pipeline import (
        ContentPipeline,
        PipelineConfig,
        Phase,
        PhaseType,
    )

    config = PipelineConfig(
        name="my-pipeline",
        phases=[PhaseType.DOWNLOAD, PhaseType.TRANSCRIBE, PhaseType.ANALYZE],
    )
    pipeline = ContentPipeline(config)
    results = await pipeline.run()

LEGO Principle: Import types from library.common.types
"""

from .pipeline import (
    ContentPipeline,
    PipelineConfig,
    PipelineResult,
    PhaseResult,
)
from .phases import (
    Phase,
    PhaseType,
    PhaseStatus,
    DownloadPhase,
    TranscribePhase,
    AnalyzePhase,
    SynthesizePhase,
    DraftPhase,
    StylePhase,
    SlopDetectPhase,
    ImageGenPhase,
    CommitPhase,
    DeployPhase,
)

__all__ = [
    # Pipeline core
    "ContentPipeline",
    "PipelineConfig",
    "PipelineResult",
    "PhaseResult",
    # Phases
    "Phase",
    "PhaseType",
    "PhaseStatus",
    "DownloadPhase",
    "TranscribePhase",
    "AnalyzePhase",
    "SynthesizePhase",
    "DraftPhase",
    "StylePhase",
    "SlopDetectPhase",
    "ImageGenPhase",
    "CommitPhase",
    "DeployPhase",
]
