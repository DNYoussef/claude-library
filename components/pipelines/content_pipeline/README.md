# Content Pipeline Component

A configurable, async multi-phase content processing pipeline for automating content creation workflows.

## Overview

This component provides a reusable framework for building content pipelines that:
- Download content from various sources (YouTube, RSS, etc.)
- Transcribe audio/video to text
- Analyze content using multiple AI models
- Synthesize insights into unified outputs
- Generate drafts with style application
- Run quality gates (slop detection)
- Manage deployment

## Installation

```python
from library.components.pipelines.content_pipeline import (
    ContentPipeline,
    PipelineConfig,
    PhaseType,
    create_standard_pipeline,
)
```

## Quick Start

### Basic Pipeline

```python
import asyncio
from pathlib import Path

# Create a standard pipeline with defaults
pipeline = create_standard_pipeline(
    sources=["@youtube_channel", "@another_channel"],
    base_dir=Path("./content-output"),
    slop_threshold=0.05,
)

# Run the pipeline
result = await pipeline.run()

print(result.summary())
```

### Custom Configuration

```python
from library.components.pipelines.content_pipeline import (
    ContentPipeline,
    PipelineConfig,
    PhaseType,
    DownloadConfig,
    AnalyzeConfig,
    SlopDetectConfig,
)

config = PipelineConfig(
    name="my-custom-pipeline",
    phases=[
        PhaseType.DOWNLOAD,
        PhaseType.TRANSCRIBE,
        PhaseType.ANALYZE,
        PhaseType.SLOP_DETECT,
    ],
    base_dir=Path("./output"),
    phase_configs={
        PhaseType.DOWNLOAD: DownloadConfig(
            sources=["@channel1", "@channel2"],
            max_downloads_per_source=5,
            audio_format="mp3",
        ),
        PhaseType.ANALYZE: AnalyzeConfig(
            models=["gemini", "codex", "claude"],
            parallel=True,
        ),
        PhaseType.SLOP_DETECT: SlopDetectConfig(
            threshold=0.03,  # 3% slop threshold
            patterns=[
                "paradigm shift",
                "game-changer",
                "leverage",
            ],
        ),
    },
    fail_fast=True,
)

pipeline = ContentPipeline(config)
result = await pipeline.run()
```

## Phases

### Available Phases

| Phase | Type | Description |
|-------|------|-------------|
| Download | `PhaseType.DOWNLOAD` | Fetch content from sources using yt-dlp |
| Transcribe | `PhaseType.TRANSCRIBE` | Convert audio to text using Whisper |
| Analyze | `PhaseType.ANALYZE` | Multi-model AI analysis |
| Synthesize | `PhaseType.SYNTHESIZE` | Combine analyses into zeitgeist |
| Draft | `PhaseType.DRAFT` | Generate content draft |
| Style | `PhaseType.STYLE` | Apply writing style template |
| SlopDetect | `PhaseType.SLOP_DETECT` | Quality gate for AI patterns |
| ImageGen | `PhaseType.IMAGE_GEN` | Generate visual assets |
| Commit | `PhaseType.COMMIT` | Git commit and version control |
| Deploy | `PhaseType.DEPLOY` | Push to production |

### Phase Configuration

Each phase has its own configuration dataclass:

```python
# Download configuration
DownloadConfig(
    sources=["@channel"],
    download_dir=Path("./downloads"),
    max_downloads_per_source=5,
    date_range="today-7days",
    audio_format="mp3",
)

# Transcribe configuration
TranscribeConfig(
    model="small",  # whisper model size
    language="en",
    delete_audio_after=True,
)

# Analyze configuration
AnalyzeConfig(
    models=["gemini", "codex", "claude"],
    parallel=True,
    max_text_length=40000,
)

# Slop detection configuration
SlopDetectConfig(
    threshold=0.05,  # 5%
    patterns=["paradigm shift", "leverage", ...],
)
```

## Quality Gates

Add quality gates to enforce standards between phases:

```python
pipeline = ContentPipeline(config)

# Add a custom quality gate
pipeline.add_quality_gate(
    name="min-word-count",
    check_fn=lambda ctx: ctx.get("word_count", 0) >= 500,
    after_phase=PhaseType.DRAFT,
    error_message="Draft too short (min 500 words)",
)

# Slop detection gate (built-in pattern)
pipeline.add_quality_gate(
    name="slop-threshold",
    check_fn=lambda ctx: ctx.get("slop_score", 1.0) < 0.05,
    after_phase=PhaseType.SLOP_DETECT,
    error_message="Content failed slop detection",
)
```

## Custom Phases

Implement custom phases using the `Phase` protocol:

```python
from library.components.pipelines.content_pipeline import (
    BasePhase,
    PhaseType,
    PhaseConfig,
    PhaseResult,
)
from dataclasses import dataclass

@dataclass
class MyCustomConfig(PhaseConfig):
    my_setting: str = "default"

class MyCustomPhase(BasePhase):
    def __init__(self, config: MyCustomConfig = None):
        super().__init__(config or MyCustomConfig())

    @property
    def phase_type(self) -> PhaseType:
        return PhaseType.CUSTOM

    async def _execute_impl(self, context: dict) -> dict:
        # Your custom logic here
        return {"my_output": "value"}

# Register custom phase
pipeline.set_phase(PhaseType.CUSTOM, MyCustomPhase())
```

## Pipeline Results

```python
result = await pipeline.run()

# Check success
if result.success:
    print("Pipeline completed successfully!")
else:
    print(f"Pipeline failed: {result.error}")

# Access phase results
for phase_type, phase_result in result.phase_results.items():
    print(f"{phase_type.value}: {phase_result.status.value}")
    if phase_result.output:
        print(f"  Output: {phase_result.output}")

# Get specific phase output
slop_result = result.get_phase_output(PhaseType.SLOP_DETECT)
print(f"Slop score: {slop_result['slop_score']}")

# Export results
import json
with open("pipeline_results.json", "w") as f:
    json.dump(result.to_dict(), f, indent=2)
```

## Integration with Model Router

The Analyze phase can integrate with the `ai/model-router` component:

```python
from library.components.ai.model_router import ModelRouter, RouterConfig

# Create model router
router = ModelRouter(RouterConfig(
    providers=["gemini", "claude", "codex"],
    fallback_enabled=True,
))

# Pass to analyze phase
analyze_phase = AnalyzePhase(
    config=AnalyzeConfig(models=["gemini", "claude"]),
    model_router=router,
)

pipeline.set_phase(PhaseType.ANALYZE, analyze_phase)
```

## Hooks

Add hooks for monitoring and logging:

```python
def on_phase_start(phase_type):
    print(f"Starting phase: {phase_type.value}")

def on_phase_complete(result):
    print(f"Completed: {result.phase_type.value} ({result.status.value})")

def on_pipeline_complete(result):
    send_notification(f"Pipeline {result.config.name}: {result.success}")

config = PipelineConfig(
    name="monitored-pipeline",
    on_phase_start=on_phase_start,
    on_phase_complete=on_phase_complete,
    on_pipeline_complete=on_pipeline_complete,
)
```

## Directory Structure

The pipeline creates the following structure:

```
base_dir/
  downloads/           # Downloaded audio files
    channel1/
    channel2/
  transcripts/         # Transcribed JSON files
  analysis/            # Analysis results per model
  drafts/              # Generated content drafts
```

## LEGO Compatibility

This component follows LEGO principles:
- Imports shared types from `library.common.types`
- Async patterns throughout
- Configurable via dataclasses
- Protocol-based phase interface for extensibility

## Dependencies

- asyncio (stdlib)
- pathlib (stdlib)
- yt-dlp (for download phase)
- whisper (for transcribe phase)

## Source

Extracted from: `C:\Users\17175\scripts\content-pipeline\weekly_zeitgeist_analysis.py`
