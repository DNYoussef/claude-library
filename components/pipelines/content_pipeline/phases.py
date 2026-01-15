"""
Content Pipeline Phase Definitions

Individual phase implementations for the content pipeline.
Each phase is async, configurable, and follows the Phase protocol.

Phases:
1. Download - Fetch content from sources (YouTube, RSS, etc.)
2. Transcribe - Convert audio/video to text
3. Analyze - Multi-model AI analysis
4. Synthesize - Combine analyses into zeitgeist
5. Draft - Generate blog/content draft
6. Style - Apply writing style template
7. SlopDetect - Quality gate for AI-generated patterns
8. ImageGen - Generate visual assets
9. Commit - Git commit and version control
10. Deploy - Push to production

Author: Library extraction from weekly_zeitgeist_analysis.py
License: MIT
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable

logger = logging.getLogger(__name__)


class PhaseType(Enum):
    """Standard phase types in a content pipeline."""

    DOWNLOAD = "download"
    TRANSCRIBE = "transcribe"
    ANALYZE = "analyze"
    SYNTHESIZE = "synthesize"
    DRAFT = "draft"
    STYLE = "style"
    SLOP_DETECT = "slop_detect"
    IMAGE_GEN = "image_gen"
    COMMIT = "commit"
    DEPLOY = "deploy"
    CUSTOM = "custom"


class PhaseStatus(Enum):
    """Execution status for a phase."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class PhaseResult:
    """Result from executing a phase."""

    phase_type: PhaseType
    status: PhaseStatus
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    output: Any = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def duration_seconds(self) -> Optional[float]:
        """Calculate phase duration in seconds."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "phase_type": self.phase_type.value,
            "status": self.status.value,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_seconds": self.duration_seconds,
            "error": self.error,
            "metadata": self.metadata,
        }


@runtime_checkable
class Phase(Protocol):
    """Protocol for pipeline phases."""

    phase_type: PhaseType

    async def execute(self, context: Dict[str, Any]) -> PhaseResult:
        """
        Execute the phase with the given context.

        Args:
            context: Shared pipeline context with data from previous phases

        Returns:
            PhaseResult with status and output
        """
        ...

    def validate_input(self, context: Dict[str, Any]) -> bool:
        """
        Validate that required inputs are present in context.

        Args:
            context: Pipeline context to validate

        Returns:
            True if inputs are valid
        """
        ...


@dataclass
class PhaseConfig:
    """Base configuration for all phases."""

    enabled: bool = True
    timeout_seconds: int = 300
    retry_count: int = 0
    retry_delay_seconds: int = 5
    required_inputs: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class BasePhase(ABC):
    """Base implementation for phases with common functionality."""

    def __init__(self, config: Optional[PhaseConfig] = None):
        self.config = config or PhaseConfig()

    @property
    @abstractmethod
    def phase_type(self) -> PhaseType:
        """Return the phase type."""
        ...

    def validate_input(self, context: Dict[str, Any]) -> bool:
        """Validate required inputs are in context."""
        for key in self.config.required_inputs:
            if key not in context:
                logger.warning(f"Missing required input: {key}")
                return False
        return True

    async def execute(self, context: Dict[str, Any]) -> PhaseResult:
        """Execute with retry and timeout handling."""
        result = PhaseResult(
            phase_type=self.phase_type,
            status=PhaseStatus.PENDING,
        )

        if not self.config.enabled:
            result.status = PhaseStatus.SKIPPED
            return result

        if not self.validate_input(context):
            result.status = PhaseStatus.FAILED
            result.error = "Input validation failed"
            return result

        result.started_at = datetime.now()
        result.status = PhaseStatus.RUNNING

        attempts = 0
        max_attempts = max(1, self.config.retry_count + 1)

        while attempts < max_attempts:
            try:
                output = await asyncio.wait_for(
                    self._execute_impl(context),
                    timeout=self.config.timeout_seconds,
                )
                result.output = output
                result.status = PhaseStatus.COMPLETED
                break
            except asyncio.TimeoutError:
                result.error = f"Phase timed out after {self.config.timeout_seconds}s"
                attempts += 1
            except Exception as e:
                result.error = str(e)
                attempts += 1
                logger.warning(f"Phase {self.phase_type.value} attempt {attempts} failed: {e}")

            if attempts < max_attempts:
                await asyncio.sleep(self.config.retry_delay_seconds)

        if result.status != PhaseStatus.COMPLETED:
            result.status = PhaseStatus.FAILED

        result.completed_at = datetime.now()
        return result

    @abstractmethod
    async def _execute_impl(self, context: Dict[str, Any]) -> Any:
        """Actual phase implementation. Override in subclasses."""
        ...


# =============================================================================
# CONCRETE PHASE IMPLEMENTATIONS
# =============================================================================


@dataclass
class DownloadConfig(PhaseConfig):
    """Configuration for download phase."""

    sources: List[str] = field(default_factory=list)
    download_dir: Optional[Path] = None
    max_downloads_per_source: int = 5
    date_range: str = "today-7days"
    archive_file: Optional[Path] = None
    audio_format: str = "mp3"


class DownloadPhase(BasePhase):
    """Phase for downloading content from sources."""

    def __init__(self, config: Optional[DownloadConfig] = None):
        super().__init__(config or DownloadConfig())
        self._config: DownloadConfig = self.config  # type narrowing

    @property
    def phase_type(self) -> PhaseType:
        return PhaseType.DOWNLOAD

    async def _execute_impl(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Download content from configured sources."""
        sources = self._config.sources or context.get("sources", [])
        download_dir = self._config.download_dir or context.get("download_dir", Path("./downloads"))

        if isinstance(download_dir, str):
            download_dir = Path(download_dir)
        download_dir.mkdir(parents=True, exist_ok=True)

        downloaded = []
        errors = []

        for source in sources:
            try:
                files = await self._download_source(source, download_dir)
                downloaded.extend(files)
            except Exception as e:
                errors.append({"source": source, "error": str(e)})
                logger.error(f"Failed to download from {source}: {e}")

        return {
            "downloaded_files": downloaded,
            "download_count": len(downloaded),
            "errors": errors,
            "download_dir": str(download_dir),
        }

    async def _download_source(self, source: str, download_dir: Path) -> List[Dict[str, Any]]:
        """Download from a single source using yt-dlp."""
        # This is a simplified implementation - extend as needed
        output_template = str(download_dir / "%(uploader)s/%(upload_date)s_%(title)s.%(ext)s")

        cmd = [
            "yt-dlp",
            source,
            "--output", output_template,
            "--format", "bestaudio[ext=m4a]/bestaudio/best",
            "--extract-audio",
            "--audio-format", self._config.audio_format,
            "--max-downloads", str(self._config.max_downloads_per_source),
            "--restrict-filenames",
            "--no-playlist",
            "--write-info-json",
            "--ignore-errors",
        ]

        if self._config.archive_file:
            cmd.extend(["--download-archive", str(self._config.archive_file)])

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            logger.warning(f"yt-dlp returned {proc.returncode}: {stderr.decode()}")

        # Find downloaded files
        downloaded = []
        for audio_file in download_dir.rglob(f"*.{self._config.audio_format}"):
            downloaded.append({
                "path": str(audio_file),
                "source": source,
                "filename": audio_file.name,
            })

        return downloaded


@dataclass
class TranscribeConfig(PhaseConfig):
    """Configuration for transcription phase."""

    model: str = "small"
    language: str = "en"
    device: str = "auto"  # auto, cpu, cuda
    output_dir: Optional[Path] = None
    delete_audio_after: bool = False


class TranscribePhase(BasePhase):
    """Phase for transcribing audio to text."""

    def __init__(self, config: Optional[TranscribeConfig] = None):
        super().__init__(config or TranscribeConfig())
        self._config: TranscribeConfig = self.config

    @property
    def phase_type(self) -> PhaseType:
        return PhaseType.TRANSCRIBE

    async def _execute_impl(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Transcribe audio files from previous phase."""
        downloaded = context.get("downloaded_files", [])
        output_dir = self._config.output_dir or context.get("transcript_dir", Path("./transcripts"))

        if isinstance(output_dir, str):
            output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        transcripts = []

        for file_info in downloaded:
            audio_path = Path(file_info["path"])
            if not audio_path.exists():
                continue

            transcript_path = output_dir / f"{audio_path.stem}_transcript.json"

            # Skip if already transcribed
            if transcript_path.exists():
                transcripts.append({
                    "audio_path": str(audio_path),
                    "transcript_path": str(transcript_path),
                    "cached": True,
                })
                continue

            try:
                transcript = await self._transcribe_file(audio_path, transcript_path)
                transcripts.append({
                    "audio_path": str(audio_path),
                    "transcript_path": str(transcript_path),
                    "text_length": len(transcript.get("text", "")),
                    "cached": False,
                })

                if self._config.delete_audio_after:
                    audio_path.unlink(missing_ok=True)

            except Exception as e:
                logger.error(f"Failed to transcribe {audio_path}: {e}")

        return {
            "transcripts": transcripts,
            "transcript_count": len(transcripts),
            "output_dir": str(output_dir),
        }

    async def _transcribe_file(self, audio_path: Path, output_path: Path) -> Dict[str, Any]:
        """Transcribe a single audio file using whisper."""
        import json

        # Try using whisper via CLI for better isolation
        cmd = [
            "whisper",
            str(audio_path),
            "--model", self._config.model,
            "--language", self._config.language,
            "--output_format", "json",
            "--output_dir", str(output_path.parent),
        ]

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        await proc.communicate()

        # Whisper outputs to audio_path.stem.json
        whisper_output = output_path.parent / f"{audio_path.stem}.json"

        if whisper_output.exists():
            with open(whisper_output, "r", encoding="utf-8") as f:
                transcript = json.load(f)
            whisper_output.rename(output_path)
            return transcript

        return {"text": "", "error": "Transcription failed"}


@dataclass
class AnalyzeConfig(PhaseConfig):
    """Configuration for analysis phase."""

    models: List[str] = field(default_factory=lambda: ["gemini", "codex", "claude"])
    parallel: bool = True
    analysis_dir: Optional[Path] = None
    max_text_length: int = 40000


class AnalyzePhase(BasePhase):
    """Phase for multi-model AI analysis."""

    def __init__(
        self,
        config: Optional[AnalyzeConfig] = None,
        model_router: Optional[Any] = None,  # ModelRouter from ai/model-router
    ):
        super().__init__(config or AnalyzeConfig())
        self._config: AnalyzeConfig = self.config
        self.model_router = model_router

    @property
    def phase_type(self) -> PhaseType:
        return PhaseType.ANALYZE

    async def _execute_impl(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze transcripts using multiple models."""
        import json

        transcripts = context.get("transcripts", [])
        analysis_dir = self._config.analysis_dir or context.get("analysis_dir", Path("./analysis"))

        if isinstance(analysis_dir, str):
            analysis_dir = Path(analysis_dir)
        analysis_dir.mkdir(parents=True, exist_ok=True)

        analyses = []

        for transcript_info in transcripts:
            transcript_path = Path(transcript_info["transcript_path"])
            if not transcript_path.exists():
                continue

            with open(transcript_path, "r", encoding="utf-8") as f:
                transcript = json.load(f)

            text = transcript.get("text", "")[:self._config.max_text_length]

            if self._config.parallel:
                analysis = await self._analyze_parallel(text, transcript_path.stem)
            else:
                analysis = await self._analyze_sequential(text, transcript_path.stem)

            # Save analysis
            analysis_path = analysis_dir / f"{transcript_path.stem}_analysis.json"
            with open(analysis_path, "w", encoding="utf-8") as f:
                json.dump(analysis, f, indent=2)

            analyses.append({
                "transcript_path": str(transcript_path),
                "analysis_path": str(analysis_path),
                "models_used": list(analysis.get("model_results", {}).keys()),
            })

        return {
            "analyses": analyses,
            "analysis_count": len(analyses),
            "analysis_dir": str(analysis_dir),
        }

    async def _analyze_parallel(self, text: str, task_id: str) -> Dict[str, Any]:
        """Run analysis across models in parallel."""
        if self.model_router:
            # Use model router if available
            return await self.model_router.analyze_parallel(text, self._config.models)

        # Fallback: simple parallel execution
        tasks = []
        for model in self._config.models:
            tasks.append(self._analyze_with_model(text, model, task_id))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        model_results = {}
        for model, result in zip(self._config.models, results):
            if isinstance(result, Exception):
                model_results[model] = {"error": str(result)}
            else:
                model_results[model] = result

        return {
            "task_id": task_id,
            "model_results": model_results,
            "analyzed_at": datetime.now().isoformat(),
        }

    async def _analyze_sequential(self, text: str, task_id: str) -> Dict[str, Any]:
        """Run analysis across models sequentially."""
        model_results = {}

        for model in self._config.models:
            try:
                result = await self._analyze_with_model(text, model, task_id)
                model_results[model] = result
            except Exception as e:
                model_results[model] = {"error": str(e)}

        return {
            "task_id": task_id,
            "model_results": model_results,
            "analyzed_at": datetime.now().isoformat(),
        }

    async def _analyze_with_model(self, text: str, model: str, task_id: str) -> Dict[str, Any]:
        """Analyze text with a specific model."""
        # Placeholder - integrate with model-router component
        return {
            "model": model,
            "analysis": f"Analysis placeholder for {model}",
            "task_id": task_id,
        }


@dataclass
class SynthesizeConfig(PhaseConfig):
    """Configuration for synthesis phase."""

    synthesis_model: str = "claude"
    output_dir: Optional[Path] = None


class SynthesizePhase(BasePhase):
    """Phase for synthesizing analyses into unified insights."""

    def __init__(self, config: Optional[SynthesizeConfig] = None):
        super().__init__(config or SynthesizeConfig())
        self._config: SynthesizeConfig = self.config

    @property
    def phase_type(self) -> PhaseType:
        return PhaseType.SYNTHESIZE

    async def _execute_impl(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Synthesize all analyses into a zeitgeist."""
        analyses = context.get("analyses", [])

        # Collect all insights
        all_topics = []
        all_insights = []

        # Placeholder synthesis logic
        return {
            "common_themes": all_topics[:10],
            "key_insights": all_insights[:10],
            "synthesis_model": self._config.synthesis_model,
            "synthesized_at": datetime.now().isoformat(),
        }


@dataclass
class DraftConfig(PhaseConfig):
    """Configuration for draft generation phase."""

    draft_model: str = "claude"
    max_words: int = 1200
    output_dir: Optional[Path] = None


class DraftPhase(BasePhase):
    """Phase for generating content draft."""

    def __init__(self, config: Optional[DraftConfig] = None):
        super().__init__(config or DraftConfig())
        self._config: DraftConfig = self.config

    @property
    def phase_type(self) -> PhaseType:
        return PhaseType.DRAFT

    async def _execute_impl(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a draft from the synthesis."""
        synthesis = context.get("synthesis", {})
        output_dir = self._config.output_dir or context.get("blog_dir", Path("./drafts"))

        if isinstance(output_dir, str):
            output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Placeholder draft generation
        draft_path = output_dir / f"draft_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"

        return {
            "draft_path": str(draft_path),
            "word_count": 0,
            "generated_at": datetime.now().isoformat(),
        }


@dataclass
class StyleConfig(PhaseConfig):
    """Configuration for style application phase."""

    style_template_path: Optional[Path] = None
    max_iterations: int = 5


class StylePhase(BasePhase):
    """Phase for applying writing style template."""

    def __init__(self, config: Optional[StyleConfig] = None):
        super().__init__(config or StyleConfig())
        self._config: StyleConfig = self.config

    @property
    def phase_type(self) -> PhaseType:
        return PhaseType.STYLE

    async def _execute_impl(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Apply style template to draft."""
        draft_path = context.get("draft_path")

        return {
            "styled_path": draft_path,
            "iterations": 0,
            "style_applied": False,
        }


@dataclass
class SlopDetectConfig(PhaseConfig):
    """Configuration for slop detection phase."""

    threshold: float = 0.05  # 5% slop threshold
    patterns: List[str] = field(default_factory=lambda: [
        "in the ever-evolving",
        "as we navigate",
        "it's worth noting",
        "at the end of the day",
        "game-changer",
        "paradigm shift",
        "leverage",
        "synergy",
        "transformative",
        "unprecedented",
    ])


class SlopDetectPhase(BasePhase):
    """Phase for detecting AI-generated slop patterns."""

    def __init__(self, config: Optional[SlopDetectConfig] = None):
        super().__init__(config or SlopDetectConfig())
        self._config: SlopDetectConfig = self.config

    @property
    def phase_type(self) -> PhaseType:
        return PhaseType.SLOP_DETECT

    async def _execute_impl(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Run slop detection on content."""
        content_path = context.get("styled_path") or context.get("draft_path")

        if not content_path:
            return {"passed": False, "error": "No content to analyze"}

        content_path = Path(content_path)
        if not content_path.exists():
            return {"passed": False, "error": f"File not found: {content_path}"}

        content = content_path.read_text(encoding="utf-8").lower()
        word_count = len(content.split())

        found_patterns = []
        for pattern in self._config.patterns:
            if pattern.lower() not in content:
                continue
            found_patterns.append(pattern)

        slop_score = len(found_patterns) / (word_count / 100) if word_count > 0 else 0
        passed = slop_score < self._config.threshold

        return {
            "passed": passed,
            "slop_score": round(slop_score, 4),
            "threshold": self._config.threshold,
            "patterns_found": found_patterns,
            "pattern_count": len(found_patterns),
            "word_count": word_count,
        }


@dataclass
class ImageGenConfig(PhaseConfig):
    """Configuration for image generation phase."""

    width: int = 1024
    height: int = 576
    style: str = "professional"
    output_dir: Optional[Path] = None


class ImageGenPhase(BasePhase):
    """Phase for generating visual assets."""

    def __init__(self, config: Optional[ImageGenConfig] = None):
        super().__init__(config or ImageGenConfig())
        self._config: ImageGenConfig = self.config

    @property
    def phase_type(self) -> PhaseType:
        return PhaseType.IMAGE_GEN

    async def _execute_impl(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate images for content."""
        # Placeholder - integrate with image generation
        return {
            "generated": False,
            "prompt": "",
            "image_path": None,
        }


@dataclass
class CommitConfig(PhaseConfig):
    """Configuration for git commit phase."""

    repo_dir: Optional[Path] = None
    auto_push: bool = False
    commit_prefix: str = "feat(blog):"


class CommitPhase(BasePhase):
    """Phase for git commit operations."""

    def __init__(self, config: Optional[CommitConfig] = None):
        super().__init__(config or CommitConfig())
        self._config: CommitConfig = self.config

    @property
    def phase_type(self) -> PhaseType:
        return PhaseType.COMMIT

    async def _execute_impl(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Commit changes to git."""
        repo_dir = self._config.repo_dir or context.get("repo_dir")

        if not repo_dir:
            return {"committed": False, "error": "No repo_dir specified"}

        # Placeholder git operations
        return {
            "committed": False,
            "pushed": False,
            "commit_hash": None,
        }


@dataclass
class DeployConfig(PhaseConfig):
    """Configuration for deployment phase."""

    deploy_target: str = "railway"
    wait_for_completion: bool = True


class DeployPhase(BasePhase):
    """Phase for deploying to production."""

    def __init__(self, config: Optional[DeployConfig] = None):
        super().__init__(config or DeployConfig())
        self._config: DeployConfig = self.config

    @property
    def phase_type(self) -> PhaseType:
        return PhaseType.DEPLOY

    async def _execute_impl(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Deploy to production."""
        # Placeholder deployment
        return {
            "deployed": False,
            "target": self._config.deploy_target,
            "url": None,
        }
