# Pipelines Domain

Components for building data and content processing pipelines.

## Components

| Component | Description |
|-----------|-------------|
| `content_pipeline/` | Content processing pipeline (YouTube to blog) |

## Usage

```python
from library.components.pipelines.content_pipeline import (
    ContentPipeline,
    PipelineConfig,
    PipelineStage,
    PipelineResult,
)

config = PipelineConfig(
    stages=[
        PipelineStage.DOWNLOAD,
        PipelineStage.TRANSCRIBE,
        PipelineStage.ANALYZE,
        PipelineStage.GENERATE,
    ],
)
pipeline = ContentPipeline(config)
result = await pipeline.run(source_url)
```

## Related Domains

- `orchestration/` - Pipeline execution and coordination
