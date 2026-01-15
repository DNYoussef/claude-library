"""
Auditor Base Pattern

Abstract base class for building structured auditors that emit
results with confidence scores, action recommendations, and
evidential claims.

Features:
- Structured output format with confidence and grounds
- Action class recommendations (ACCEPT, REJECT, TUNE, etc.)
- Confidence ceiling enforcement
- Extensible for domain-specific auditors

Usage:
    class MyAuditor(BaseAuditor):
        auditor_type = "my_auditor"

        def audit(self, artifact, eval_report, runtime_config):
            # Analyze artifact
            claims = ["[assert|confident] Found issue [conf:0.85]"]
            return AuditorResult(
                auditor_type=self.auditor_type,
                verix={"illocution": "warn", "affect": "concerned"},
                claims=claims,
                would_change_if=["issue resolved"],
                action_class=ActionClass.CODE_FIX.value,
                confidence=0.85,
                grounds=["artifact:line=42"],
            )

Source: Extracted from context-cascade/cognitive-architecture/integration/auditors.py
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any, Optional
from enum import Enum


# Confidence ceilings by evidence type
CONFIDENCE_CEILINGS = {
    "definition": 0.95,
    "policy": 0.90,
    "observation": 0.95,
    "research": 0.85,
    "report": 0.70,
    "inference": 0.70,
}


class Illocution(Enum):
    """Illocutionary force of an auditor claim."""
    ASSERT = "assert"       # Factual statement
    RECOMMEND = "recommend" # Suggestion
    WARN = "warn"           # Warning about issues
    REJECT = "reject"       # Rejection with reason


class Affect(Enum):
    """Affective stance of an auditor claim."""
    CONFIDENT = "confident"     # High certainty
    UNCERTAIN = "uncertain"     # Low certainty
    CONCERNED = "concerned"     # Issue detected


class ActionClass(Enum):
    """Recommended action after audit."""
    TUNE_VECTOR = "TUNE_VECTOR"           # Adjust parameters
    CHANGE_MODE = "CHANGE_MODE"           # Switch operating mode
    EDIT_PROMPTBUILDER = "EDIT_PROMPTBUILDER"  # Modify prompt
    CODE_FIX = "CODE_FIX"                 # Fix code issue
    TEST_ADD = "TEST_ADD"                 # Add tests
    ACCEPT = "ACCEPT"                     # Approve artifact
    REJECT = "REJECT"                     # Reject artifact


@dataclass
class AuditorResult:
    """
    Standard output format for all auditors.

    Attributes:
        auditor_type: Type identifier for the auditor
        verix: Dict with illocution and affect
        claims: List of structured claims with evidence
        would_change_if: Conditions that would change the result
        action_class: Recommended action (from ActionClass enum)
        confidence: Confidence score (0.0 to 1.0)
        grounds: Evidence supporting the claims
        vcl: VCL compliance metadata (evidence type, aspect, ceiling)
    """
    auditor_type: str
    verix: Dict[str, str]
    claims: List[str]
    would_change_if: List[str]
    action_class: str
    confidence: float
    grounds: List[str]
    vcl: Dict[str, Any] = field(default_factory=lambda: {
        "evd_type": "observation",
        "asp_type": "sov",
        "confidence_ceiling": 0.95,
    })

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    def enforce_confidence_ceiling(self) -> "AuditorResult":
        """
        Enforce confidence ceiling based on evidence type.

        Caps confidence at the ceiling for the declared evidence type.
        This ensures epistemic honesty - inference can't claim
        observation-level confidence.

        Returns:
            Self with confidence capped at ceiling
        """
        evd_type = self.vcl.get("evd_type", "inference")
        ceiling = CONFIDENCE_CEILINGS.get(evd_type, 0.70)

        if self.confidence <= ceiling:
            self.vcl["confidence_ceiling"] = ceiling
            return self

        self.confidence = ceiling
        self.vcl["confidence_capped"] = True
        self.vcl["confidence_ceiling"] = ceiling
        return self


class BaseAuditor:
    """
    Abstract base class for all auditors.

    Subclasses must implement:
        - auditor_type: Class attribute identifying the auditor
        - audit(): Method that performs the audit and returns AuditorResult

    The audit method receives:
        - artifact: The content to audit (string, code, document, etc.)
        - eval_report: Evaluation metrics from a harness (optional context)
        - runtime_config: Current configuration (optional context)

    Example:
        class SecurityAuditor(BaseAuditor):
            auditor_type = "security"

            def audit(self, artifact, eval_report, runtime_config):
                # Check for security issues
                vulnerabilities = self._scan(artifact)

                if vulnerabilities:
                    return AuditorResult(
                        auditor_type=self.auditor_type,
                        verix={"illocution": "warn", "affect": "concerned"},
                        claims=[f"Found {len(vulnerabilities)} vulnerabilities"],
                        would_change_if=["vulnerabilities fixed"],
                        action_class=ActionClass.CODE_FIX.value,
                        confidence=0.90,
                        grounds=[f"vuln:{v.id}" for v in vulnerabilities],
                    )
                else:
                    return AuditorResult(
                        auditor_type=self.auditor_type,
                        verix={"illocution": "assert", "affect": "confident"},
                        claims=["No security issues found"],
                        would_change_if=[],
                        action_class=ActionClass.ACCEPT.value,
                        confidence=0.85,
                        grounds=["scan:clean"],
                    )
    """

    auditor_type: str = "base"

    def audit(
        self,
        artifact: str,
        eval_report: Optional[Dict[str, Any]] = None,
        runtime_config: Optional[Dict[str, Any]] = None,
    ) -> AuditorResult:
        """
        Audit an artifact and return structured result.

        Args:
            artifact: The artifact content to audit
            eval_report: Optional harness evaluation report
            runtime_config: Optional current configuration

        Returns:
            AuditorResult with claims, confidence, and recommendations

        Raises:
            NotImplementedError: Must be implemented by subclass
        """
        raise NotImplementedError("Subclasses must implement audit()")
