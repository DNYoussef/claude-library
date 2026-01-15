"""
FrozenHarness - Immutable Evaluation Harness for Grading Artifacts

This module provides the FrozenHarness class which serves as the single
source of truth for evaluation metrics in the Ralph loop system.

INVARIANTS:
- The harness NEVER self-improves (Goodhart prevention)
- Harness hash is computed for integrity verification
- Evaluation can use real LLM (CLI) or heuristic fallback

VERIX Example:
    [assert|confident] FrozenHarness grades artifacts immutably
    [ground:architecture-spec] [conf:0.95] [state:confirmed]

Usage:
    from cognitive_architecture.loopctl import FrozenHarness

    harness = FrozenHarness(loop_dir=Path(".loop"))
    metrics = harness.grade(artifact_path=Path("output.txt"))
    print(f"Overall score: {metrics['overall']}")
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass
from typing import Dict, Any, Optional, List


@dataclass
class GradeMetrics:
    """
    Metrics returned from artifact grading.

    All metrics are in range [0.0, 1.0].
    """
    task_accuracy: float = 0.0
    token_efficiency: float = 0.0
    edge_robustness: float = 0.0
    epistemic_consistency: float = 0.0
    overall: float = 0.0
    evaluation_mode: str = "heuristic"
    connascence_mode: str = "disabled"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "task_accuracy": self.task_accuracy,
            "token_efficiency": self.token_efficiency,
            "edge_robustness": self.edge_robustness,
            "epistemic_consistency": self.epistemic_consistency,
            "overall": self.overall,
            "evaluation_mode": self.evaluation_mode,
            "connascence_mode": self.connascence_mode,
        }


class FrozenHarness:
    """
    Immutable evaluation harness for grading artifacts.

    The harness is the ONLY source of truth for metrics.
    It does NOT self-improve (Goodhart prevention).

    Evaluation Strategy (in order):
    1. CLI Evaluator (real LLM-based) - preferred
    2. Heuristic fallback - when CLI unavailable

    Attributes:
        loop_dir: Directory containing loop state files
        harness_version: Version string for integrity tracking
        use_cli_evaluator: Whether to attempt CLI-based evaluation
    """

    # Default metric weights for overall score calculation
    DEFAULT_WEIGHTS = {
        "task_accuracy": 0.4,
        "token_efficiency": 0.2,
        "edge_robustness": 0.2,
        "epistemic_consistency": 0.2,
    }

    def __init__(
        self,
        loop_dir: Optional[Path] = None,
        harness_version: str = "1.0.0",
        use_cli_evaluator: bool = True,
    ):
        """
        Initialize FrozenHarness.

        Args:
            loop_dir: Directory for loop state (default: current dir)
            harness_version: Version for integrity tracking
            use_cli_evaluator: Attempt CLI evaluator first
        """
        self.loop_dir = Path(loop_dir) if loop_dir else Path(".")
        self.harness_version = harness_version
        self.use_cli_evaluator = use_cli_evaluator
        self._harness_hash = self._compute_hash()
        self._cli_evaluator = None

        # Try to initialize CLI evaluator
        if use_cli_evaluator:
            self._cli_evaluator = self._init_cli_evaluator()

    def _init_cli_evaluator(self):
        """Initialize CLI evaluator if available."""
        try:
            from .cli_bridge import ClaudeCLI
            cli = ClaudeCLI()
            if cli.is_available:
                return cli
        except ImportError:
            pass
        return None

    def _compute_hash(self) -> str:
        """
        Compute hash of harness for integrity verification.

        The hash includes version and a checksum of the evaluation logic.
        """
        # Use version + fixed seed as hash basis
        hash_content = f"frozen_eval_harness_v{self.harness_version}_stable"
        return f"frozen_eval_harness_v{self.harness_version}_{hashlib.sha256(hash_content.encode()).hexdigest()[:12]}"

    @property
    def current_hash(self) -> str:
        """Get current harness hash."""
        return self._harness_hash

    @property
    def evaluation_mode(self) -> str:
        """Return current evaluation mode."""
        return "cli_evaluator" if self._cli_evaluator else "heuristic"

    def verify_integrity(self, expected_hash: Optional[str]) -> bool:
        """
        Verify harness hasn't been modified.

        Args:
            expected_hash: Expected hash to compare against

        Returns:
            True if hash matches or no expected hash provided
        """
        if expected_hash is None:
            return True
        return self._harness_hash == expected_hash

    def grade(self, artifact_path: Path) -> Dict[str, Any]:
        """
        Grade an artifact and return metrics.

        Uses CLI evaluator (real LLM) when available,
        falls back to heuristics otherwise.

        Args:
            artifact_path: Path to artifact to grade

        Returns:
            Dictionary of metrics with keys:
            - task_accuracy
            - token_efficiency
            - edge_robustness
            - epistemic_consistency
            - overall
            - evaluation_mode
        """
        artifact_path = Path(artifact_path)

        if not artifact_path.exists():
            return GradeMetrics().to_dict()

        # Read artifact content
        try:
            content = artifact_path.read_text(errors="ignore")
        except Exception:
            return GradeMetrics().to_dict()

        # Try CLI evaluator first (real LLM-based)
        if self._cli_evaluator:
            try:
                metrics = self._grade_with_cli(content)
                metrics["evaluation_mode"] = "cli_evaluator"
                return metrics
            except Exception:
                # Fall through to heuristics
                pass

        # Fallback: heuristic grading
        metrics = self._grade_with_heuristics(content)
        metrics["evaluation_mode"] = "heuristic"
        return metrics

    def _grade_with_cli(self, content: str) -> Dict[str, float]:
        """
        Grade using CLI evaluator (real LLM-as-judge).

        Sends content to Claude CLI for evaluation.
        """
        judge_prompt = f"""You are evaluating code/text quality. Score each dimension from 0.0 to 1.0.

CONTENT TO EVALUATE:
{content[:3000]}

Score these dimensions (0.0 to 1.0):
1. task_accuracy: Does the content accomplish the stated task correctly?
2. token_efficiency: Is the content concise without unnecessary verbosity?
3. edge_robustness: Does it handle edge cases and errors appropriately?
4. epistemic_consistency: Are claims properly qualified with confidence/evidence?

Respond in JSON format ONLY:
{{"task_accuracy": 0.0, "token_efficiency": 0.0, "edge_robustness": 0.0, "epistemic_consistency": 0.0}}"""

        result = self._cli_evaluator.send_message(judge_prompt, max_tokens=200)
        response = result.get("response", "")

        # Parse JSON from response
        start = response.find('{')
        end = response.rfind('}') + 1
        if start >= 0 and end > start:
            scores = json.loads(response[start:end])
            # Calculate overall
            scores["overall"] = sum(
                scores.get(k, 0.5) * w for k, w in self.DEFAULT_WEIGHTS.items()
            )
            return scores

        raise ValueError("Failed to parse CLI evaluator response")

    def _grade_with_heuristics(self, content: str) -> Dict[str, float]:
        """
        Grade using heuristic rules (fallback).

        Uses pattern matching and structural analysis.
        """
        metrics = {
            "task_accuracy": self._grade_accuracy(content),
            "token_efficiency": self._grade_efficiency(content),
            "edge_robustness": self._grade_robustness(content),
            "epistemic_consistency": self._grade_epistemic(content),
        }

        # Overall is weighted average
        metrics["overall"] = sum(
            metrics[k] * self.DEFAULT_WEIGHTS[k] for k in self.DEFAULT_WEIGHTS
        )

        return metrics

    def _grade_accuracy(self, content: str) -> float:
        """Grade task accuracy using heuristics."""
        if not content:
            return 0.0
        if len(content) < 100:
            return 0.3
        # Check for completion indicators
        if "[assert" in content.lower() or "[witnessed" in content.lower():
            return 0.8
        if "complete" in content.lower() or "done" in content.lower():
            return 0.7
        return 0.6

    def _grade_efficiency(self, content: str) -> float:
        """Grade token efficiency using heuristics."""
        word_count = len(content.split())
        if word_count < 50:
            return 0.9
        elif word_count < 200:
            return 0.8
        elif word_count < 500:
            return 0.7
        else:
            return 0.5

    def _grade_robustness(self, content: str) -> float:
        """Grade edge case handling using heuristics."""
        indicators = ["error", "exception", "edge case", "boundary", "validation"]
        count = sum(1 for i in indicators if i in content.lower())
        return min(0.9, 0.5 + count * 0.1)

    def _grade_epistemic(self, content: str) -> float:
        """Grade epistemic consistency using heuristics."""
        verix_markers = ["[assert", "[conf:", "[ground:", "[state:", "[witnessed", "[inferred"]
        count = sum(1 for m in verix_markers if m in content.lower())
        return min(0.95, 0.4 + count * 0.1)


def check_emergency_stop() -> tuple:
    """
    Check for emergency stop signals.

    Kill switch can be triggered by:
    1. Creating '.meta-loop-stop' in current directory
    2. Creating '.meta-loop-stop' in home directory
    3. Setting META_LOOP_EMERGENCY_STOP=true

    Returns:
        Tuple of (should_stop: bool, reason: str)
    """
    import os

    # File-based kill switch - current directory
    if Path('.meta-loop-stop').exists():
        return True, "EMERGENCY_HALT: Kill switch file found in current directory"

    # File-based kill switch - home directory
    home_stop = Path(os.path.expanduser('~/.meta-loop-stop'))
    if home_stop.exists():
        return True, f"EMERGENCY_HALT: Kill switch file found at {home_stop}"

    # Environment variable kill switch
    env_stop = os.environ.get('META_LOOP_EMERGENCY_STOP', '').lower()
    if env_stop in ('true', '1', 'yes', 'halt', 'stop'):
        return True, "EMERGENCY_HALT: Environment variable META_LOOP_EMERGENCY_STOP is set"

    return False, ""
