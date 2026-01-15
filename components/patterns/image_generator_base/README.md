# Image Generator Base Component

Abstract base class for image generation with 13-dimension composition.

## Features

- Abstract generator pattern
- 13-dimension visual composition framework
- Prompt engineering utilities
- Quality scoring
- Style consistency enforcement

## Usage

```python
from generator_base import (
    BaseImageGenerator,
    CompositionConfig,
    GenerationResult
)

class DALLEGenerator(BaseImageGenerator):
    """DALL-E implementation example."""

    def __init__(self, api_key: str):
        super().__init__()
        self.api_key = api_key

    async def generate(
        self,
        prompt: str,
        config: CompositionConfig
    ) -> GenerationResult:
        # Build enhanced prompt using 13 dimensions
        enhanced = self.build_prompt(prompt, config)

        # Call DALL-E API
        response = await self._call_api(enhanced)

        return GenerationResult(
            image_url=response.url,
            prompt_used=enhanced,
            quality_score=self.score_composition(config)
        )

# Configuration
config = CompositionConfig(
    subject_placement="rule_of_thirds",
    lighting="dramatic_rim",
    color_palette="complementary",
    depth_of_field="shallow",
    texture="organic",
    mood="contemplative",
    perspective="eye_level",
    negative_space="balanced",
    focal_point="center_left",
    movement="static",
    contrast="high",
    scale="medium",
    style="photorealistic"
)

# Generate
generator = DALLEGenerator(api_key="...")
result = await generator.generate("A mountain landscape", config)
```

## 13-Dimension Framework

| Dimension | Values | Description |
|-----------|--------|-------------|
| subject_placement | rule_of_thirds, centered, golden_ratio | Main subject position |
| lighting | natural, dramatic, soft, rim | Light source and quality |
| color_palette | complementary, analogous, monochromatic | Color harmony |
| depth_of_field | shallow, deep, selective | Focus range |
| texture | smooth, organic, geometric | Surface quality |
| mood | serene, dynamic, mysterious | Emotional tone |
| perspective | eye_level, bird, worm | Camera angle |
| negative_space | minimal, balanced, dominant | Empty space usage |
| focal_point | center, thirds_left, thirds_right | Visual anchor |
| movement | static, implied, dynamic | Motion suggestion |
| contrast | low, medium, high | Tonal range |
| scale | intimate, medium, epic | Size relationship |
| style | photorealistic, illustrative, abstract | Visual style |
