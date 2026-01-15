"""
VERIX Epistemic Notation Parser and Validator (Standalone)

==============================================================================
IMPORTANT DISCLAIMER
==============================================================================
This module provides STRUCTURED EPISTEMIC NOTATION, not formal verification.

What this IS:
- A notation system for expressing claims with confidence levels
- A parser for structured epistemic statements
- A validator for claim consistency and grounding
- Useful for forcing explicit reasoning and evidence tracking

What this is NOT:
- Formal verification using SMT solvers (Z3, Marabou, etc.)
- Mathematical proof generation
- The academic "VeriX" framework from NeurIPS 2023
==============================================================================

VERIX provides a structured way to express epistemic claims with:
- AGENT: Who makes the claim (model, user, system, doc, process)
- ILLOCUTION: What speech act is being performed (assert, query, etc.)
- AFFECT: Emotional valence (neutral, positive, negative, uncertain)
- CONTENT: The actual claim being made
- GROUND: Source/evidence supporting the claim
- CONFIDENCE: Numeric confidence level (0.0 - 1.0)
- STATE: Claim status (provisional, confirmed, retracted)

Grammar:
STATEMENT := [AGENT] + ILLOCUTION + AFFECT + CONTENT + GROUND + CONFIDENCE + STATE

Compression Levels:
- L0 (AI<->AI): Emoji shorthand for machine communication
- L1 (AI+Human Inspector): Annotated format with explicit markers
- L2 (Human Reader): Natural language (lossy)

Usage:
    from verix_parser import (
        VerixParser, VerixValidator, VerixClaim,
        create_claim, format_claim,
        Illocution, Affect, State, Agent, MetaLevel,
        CompressionLevel, VerixStrictness
    )

    # Parse existing VERIX text
    parser = VerixParser()
    claims = parser.parse("[assert|neutral] This is true [ground:test] [conf:0.8] [state:confirmed]")

    # Create new claims
    claim = create_claim("This is my assertion", confidence=0.85, ground="direct observation")

    # Format at different compression levels
    l0 = format_claim(claim, CompressionLevel.L0_AI_AI)
    l1 = format_claim(claim, CompressionLevel.L1_AI_HUMAN)
    l2 = format_claim(claim, CompressionLevel.L2_HUMAN)

    # Validate claims
    validator = VerixValidator()
    is_valid, violations = validator.validate(claims)
"""

from dataclasses import dataclass
from typing import Optional, List, Tuple, Dict, Any
from enum import Enum
import re
import logging

# M2 fix: Configure logging for exception tracking
logger = logging.getLogger(__name__)

__version__ = "1.0.0"
VERSION = __version__  # L1 fix: Explicit VERSION constant for module introspection

# Constants
MAX_INPUT_LENGTH = 100000  # H1 fix: Maximum input length to prevent ReDoS attacks
MAX_CLAIMS_LIMIT = 1000    # M3 fix: Maximum claims to prevent memory exhaustion
L0_CONTENT_TRUNCATION_LENGTH = 20  # L3 fix: Magic number extraction for to_l0()

__all__ = [
    # Enums
    "Illocution",
    "Affect",
    "State",
    "Agent",
    "MetaLevel",
    "VerixStrictness",
    "CompressionLevel",
    # Data classes
    "VerixClaim",
    "PromptConfig",
    # Classes
    "VerixParser",
    "VerixValidator",
    # Functions
    "create_claim",
    "create_meta_claim",
    "create_meta_verix_claim",
    "format_claim",
    # Constants (L1 fix)
    "VERSION",
    "MAX_INPUT_LENGTH",
    "MAX_CLAIMS_LIMIT",
    "L0_CONTENT_TRUNCATION_LENGTH",
]


# =============================================================================
# ENUMS
# =============================================================================


class Illocution(Enum):
    """
    Speech act types from speech act theory.

    Determines what the speaker is trying to DO with the utterance.
    """
    ASSERT = "assert"      # Making a factual claim
    QUERY = "query"        # Asking a question
    DIRECT = "direct"      # Giving an instruction
    COMMIT = "commit"      # Making a promise/commitment
    EXPRESS = "express"    # Expressing emotion/attitude


class Affect(Enum):
    """
    Emotional valence markers.

    Indicates the speaker's emotional stance toward the content.
    """
    NEUTRAL = "neutral"      # No emotional loading
    POSITIVE = "positive"    # Favorable stance
    NEGATIVE = "negative"    # Unfavorable stance
    UNCERTAIN = "uncertain"  # Epistemic uncertainty


class State(Enum):
    """
    Claim lifecycle states.

    Tracks whether a claim is still being evaluated, confirmed, or retracted.
    """
    PROVISIONAL = "provisional"  # Initial claim, may be revised
    CONFIRMED = "confirmed"      # Claim verified, high confidence
    RETRACTED = "retracted"      # Claim withdrawn/invalidated


class Agent(Enum):
    """
    Agent identity markers.

    Disambiguates WHO makes each claim.
    """
    MODEL = "model"      # AI model making claim
    USER = "user"        # User's stated claim
    SYSTEM = "system"    # System-generated (hooks, config)
    DOC = "doc"          # From documentation
    PROCESS = "process"  # From running code/computation


class MetaLevel(Enum):
    """
    Meta-level markers for Hofstadter-style self-reference.

    Level 1 (OBJECT): Claims about the world/domain
    Level 2 (META): Claims about other claims
    Level 3 (META_VERIX): Claims about VERIX notation itself
    """
    OBJECT = "object"           # Level 1: Claims about the world (default)
    META = "meta"               # Level 2: Claims about claims
    META_VERIX = "meta:verix"   # Level 3: Claims about VERIX itself

    @classmethod
    def from_string(cls, s: Optional[str]) -> "MetaLevel":
        """Parse meta-level from string marker."""
        if s is None:
            return cls.OBJECT
        s_lower = s.lower().strip()
        if s_lower == "meta:verix":
            return cls.META_VERIX
        elif s_lower == "meta":
            return cls.META
        return cls.OBJECT

    def to_marker(self) -> Optional[str]:
        """Return the VERIX marker string for this level."""
        if self == MetaLevel.OBJECT:
            return None  # No marker for object-level claims
        elif self == MetaLevel.META:
            return "[meta]"
        elif self == MetaLevel.META_VERIX:
            return "[meta:verix]"
        return None


# Import config enums from cognitive_config (canonical source) with fallback
_config_imported = False

try:
    from library.components.cognitive.cognitive_config.cognitive_config import (
        VerixStrictness, CompressionLevel
    )
    _config_imported = True
except ImportError:
    pass

if not _config_imported:
    try:
        from cognitive_config.cognitive_config import VerixStrictness, CompressionLevel
        _config_imported = True
    except ImportError:
        pass

if not _config_imported:
    # Fallback for standalone usage (LEGO pattern)
    class VerixStrictness(Enum):
        """VERIX compliance strictness levels."""
        RELAXED = 0    # Only illocution required
        MODERATE = 1   # Illocution + confidence required
        STRICT = 2     # All fields required

    class CompressionLevel(Enum):
        """VERIX output compression levels."""
        L0_AI_AI = 0      # Emoji shorthand (machine-to-machine)
        L1_AI_HUMAN = 1   # Annotated format (human inspector)
        L2_HUMAN = 2      # Natural language (end user, lossy)


# =============================================================================
# DATA CLASSES
# =============================================================================


@dataclass
class PromptConfig:
    """
    Configuration for VERIX epistemic notation requirements.

    Controls how strict the VERIX compliance checking is and
    what format the output should use.
    """
    verix_strictness: VerixStrictness = VerixStrictness.MODERATE
    compression_level: CompressionLevel = CompressionLevel.L1_AI_HUMAN
    require_ground: bool = True      # Require source/evidence citations
    require_confidence: bool = True  # Require confidence values
    max_claim_depth: int = 3         # Maximum nested ground depth
    require_confidence_decrease: bool = True  # Confidence must decrease toward base

    def is_strict(self) -> bool:
        """Check if running in strict mode."""
        return self.verix_strictness == VerixStrictness.STRICT

    def is_relaxed(self) -> bool:
        """Check if running in relaxed mode."""
        return self.verix_strictness == VerixStrictness.RELAXED


@dataclass
class VerixClaim:
    """
    Parsed VERIX claim with all components.

    Represents a single epistemic statement that can be validated
    and tracked through the system.

    Attributes:
        illocution: Speech act type (assert, query, direct, commit, express)
        affect: Emotional valence (neutral, positive, negative, uncertain)
        content: The actual claim text
        ground: Source/evidence (required if config says so)
        confidence: Numeric confidence 0.0 - 1.0
        state: Claim status (provisional, confirmed, retracted)
        raw_text: Original unparsed text
        claim_id: Unique identifier for claim references
        agent: Who makes this claim
        meta_level: Hofstadter meta-level
    """
    illocution: Illocution
    affect: Affect
    content: str
    ground: Optional[str]
    confidence: float
    state: State
    raw_text: str
    claim_id: Optional[str] = None
    agent: Optional[Agent] = None
    meta_level: MetaLevel = MetaLevel.OBJECT

    def is_high_confidence(self, threshold: float = 0.8) -> bool:
        """Check if claim meets confidence threshold."""
        return self.confidence >= threshold

    def is_grounded(self) -> bool:
        """Check if claim has evidence/source."""
        return self.ground is not None and len(self.ground.strip()) > 0

    def to_l0(self) -> str:
        """
        Compress claim to L0 format (shorthand).

        Format: {agent_prefix}{illocution_char}{affect_char}{confidence%}:{content[:20]}

        Example: MA+85:This is my claim...
        """
        agent_map = {
            Agent.MODEL: "M",
            Agent.USER: "U",
            Agent.SYSTEM: "S",
            Agent.DOC: "D",
            Agent.PROCESS: "P",
        }
        illocution_map = {
            Illocution.ASSERT: "A",
            Illocution.QUERY: "?",
            Illocution.DIRECT: "!",
            Illocution.COMMIT: "C",
            Illocution.EXPRESS: "E",
        }
        affect_map = {
            Affect.NEUTRAL: ".",
            Affect.POSITIVE: "+",
            Affect.NEGATIVE: "-",
            Affect.UNCERTAIN: "~",
        }
        agent_prefix = agent_map.get(self.agent, "") if self.agent else ""
        conf_pct = int(self.confidence * 100)
        # L3 fix: Use constant instead of magic number
        if len(self.content) > L0_CONTENT_TRUNCATION_LENGTH:
            short_content = self.content[:L0_CONTENT_TRUNCATION_LENGTH] + "..."
        else:
            short_content = self.content
        return f"{agent_prefix}{illocution_map[self.illocution]}{affect_map[self.affect]}{conf_pct}:{short_content}"

    def to_l1(self) -> str:
        """
        Format claim as L1 (annotated format for human inspector).

        Format: [meta:X] [agent:X] [id:X] [illocution|affect] content [ground:source] [conf:N.N] [state:state]

        Example: [agent:model] [assert|neutral] This is true [ground:test] [conf:0.85] [state:confirmed]
        """
        parts = []
        # Add meta-level marker if not object-level
        meta_marker = self.meta_level.to_marker()
        if meta_marker:
            parts.append(meta_marker)
        if self.agent:
            parts.append(f"[agent:{self.agent.value}]")
        if self.claim_id:
            parts.append(f"[id:{self.claim_id}]")
        parts.append(f"[{self.illocution.value}|{self.affect.value}]")
        parts.append(self.content)
        if self.ground:
            parts.append(f"[ground:{self.ground}]")
        parts.append(f"[conf:{self.confidence:.2f}]")
        parts.append(f"[state:{self.state.value}]")
        return " ".join(parts)

    def is_meta(self) -> bool:
        """Check if this is a meta-level claim."""
        return self.meta_level != MetaLevel.OBJECT

    def is_meta_verix(self) -> bool:
        """Check if this claim is about VERIX itself."""
        return self.meta_level == MetaLevel.META_VERIX

    def to_l2(self) -> str:
        """
        Format claim as L2 (natural language, lossy).

        Converts to readable prose, losing some precision.

        Example: "I'm fairly confident that this is true (based on test)."
        """
        # M4 fix: Adjusted ranges to properly handle edge cases (0.9 and 1.0)
        # Using <= for upper bound on last range to include 1.0
        confidence_words = [
            (0.0, 0.3, "I'm quite uncertain, but"),
            (0.3, 0.5, "I think"),
            (0.5, 0.7, "I believe"),
            (0.7, 0.9, "I'm fairly confident that"),
            (0.9, 1.01, "I'm highly confident that"),  # 1.01 to include exactly 1.0
        ]

        conf_phrase = "I think"  # default
        for low, high, phrase in confidence_words:
            if low <= self.confidence < high:
                conf_phrase = phrase
                break

        # Add agent attribution if set
        agent_phrase = ""
        if self.agent:
            agent_phrases = {
                Agent.MODEL: "The model claims",
                Agent.USER: "The user states",
                Agent.SYSTEM: "The system reports",
                Agent.DOC: "Documentation indicates",
                Agent.PROCESS: "Process output shows",
            }
            agent_phrase = agent_phrases.get(self.agent, "") + " "
            conf_phrase = conf_phrase.lower()

        ground_phrase = ""
        if self.ground:
            ground_phrase = f" (based on {self.ground})"

        return f"{agent_phrase}{conf_phrase} {self.content}{ground_phrase}."

    def to_dict(self) -> Dict[str, Any]:
        """Convert claim to dictionary representation."""
        return {
            "illocution": self.illocution.value,
            "affect": self.affect.value,
            "content": self.content,
            "ground": self.ground,
            "confidence": self.confidence,
            "state": self.state.value,
            "raw_text": self.raw_text,
            "claim_id": self.claim_id,
            "agent": self.agent.value if self.agent else None,
            "meta_level": self.meta_level.value,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VerixClaim":
        """
        Create claim from dictionary representation.

        Args:
            data: Dictionary containing claim fields. Required keys: 'illocution',
                  'affect', 'content'. Optional keys: 'ground', 'confidence',
                  'state', 'raw_text', 'claim_id', 'agent', 'meta_level'.

        Returns:
            VerixClaim instance.

        Raises:
            KeyError: If required keys are missing, with informative message.
            ValueError: If enum values are invalid.
        """
        # H2 fix: Explicit key validation with informative error messages
        required_keys = ['illocution', 'affect', 'content']
        missing_keys = [key for key in required_keys if key not in data]
        if missing_keys:
            raise KeyError(
                f"Missing required keys in VerixClaim.from_dict(): {missing_keys}. "
                f"Required keys are: {required_keys}"
            )

        return cls(
            illocution=Illocution(data["illocution"]),
            affect=Affect(data["affect"]),
            content=data["content"],
            ground=data.get("ground"),
            confidence=data.get("confidence", 0.5),
            state=State(data.get("state", "provisional")),
            raw_text=data.get("raw_text", ""),
            claim_id=data.get("claim_id"),
            agent=Agent(data["agent"]) if data.get("agent") else None,
            meta_level=MetaLevel(data.get("meta_level", "object")),
        )


# =============================================================================
# PARSER
# =============================================================================


class VerixParser:
    """Parse VERIX-formatted text into VerixClaim objects.

    Supports both L0 and L1 formats. L2 cannot be reliably parsed
    back into structured claims.

    Attributes:
        config: PromptConfig for default values when parsing incomplete claims.

    Example:
        parser = VerixParser()
        claims = parser.parse(text)
        single = parser.parse_single(line)
    """

    # L1 format pattern: [meta:X] [agent:X] [id:X] [illocution|affect] content [ground:...] [conf:N.N] [state:...]
    L1_PATTERN = re.compile(
        r'(?:\[(?P<meta>meta(?::verix)?)\]\s*)?'
        r'(?:\[agent:(?P<agent>\w+)\]\s*)?'
        r'(?:\[id:(?P<claim_id>[\w\-]+)\]\s*)?'
        r'\[(?P<illocution>\w+)\|(?P<affect>\w+)\]'
        r'\s*(?P<content>.+?)'
        r'(?:\s*\[ground:(?P<ground>[^\]]+)\])?'
        r'(?:\s*\[conf:(?P<confidence>[\d.]+)\])?'
        r'(?:\s*\[state:(?P<state>\w+)\])?'
        r'\s*$',
        re.MULTILINE
    )

    # L0 format pattern: {A}{I}{A}{NNN}:{content} where first A is optional agent
    L0_PATTERN = re.compile(
        r'^(?P<agent>[MUSDP])?(?P<illocution>[A?!CE])(?P<affect>[.+\-~])(?P<confidence>\d+):(?P<content>.+)$',
        re.MULTILINE
    )

    def __init__(self, config: Optional[PromptConfig] = None):
        """
        Initialize parser with optional config for defaults.

        Args:
            config: PromptConfig for default values when parsing incomplete claims
        """
        self.config = config or PromptConfig()

    def parse(self, text: str) -> List[VerixClaim]:
        """Extract all VERIX claims from text.

        Tries L1 format first, then L0 format.

        Args:
            text: Text containing VERIX-formatted claims.

        Returns:
            List of parsed VerixClaim objects.

        Raises:
            ValueError: If input exceeds MAX_INPUT_LENGTH (ReDoS protection).
        """
        # H1 fix: Input length validation to prevent ReDoS attacks
        if len(text) > MAX_INPUT_LENGTH:
            raise ValueError(
                f"Input text length ({len(text)}) exceeds maximum allowed "
                f"({MAX_INPUT_LENGTH}). This limit prevents regex denial-of-service attacks."
            )

        claims = []

        # Try L1 format
        for match in self.L1_PATTERN.finditer(text):
            claim = self._parse_l1_match(match)
            if claim:
                claims.append(claim)

        # If no L1 claims, try L0 format
        if not claims:
            for match in self.L0_PATTERN.finditer(text):
                claim = self._parse_l0_match(match)
                if claim:
                    claims.append(claim)

        return claims

    def parse_single(self, text: str) -> Optional[VerixClaim]:
        """
        Parse a single VERIX statement.

        Args:
            text: Single VERIX-formatted claim

        Returns:
            VerixClaim if parsing succeeds, None otherwise
        """
        claims = self.parse(text)
        return claims[0] if claims else None

    def _parse_l1_match(self, match: re.Match) -> Optional[VerixClaim]:
        """Parse an L1 format regex match into VerixClaim.

        Args:
            match: Regex match object from L1_PATTERN.

        Returns:
            VerixClaim if parsing succeeds, None otherwise.
        """
        try:
            # Extract meta-level if present
            meta_str = match.group("meta")
            meta_level = MetaLevel.from_string(meta_str)

            # Extract agent if present
            agent_str = match.group("agent")
            agent = Agent(agent_str.lower()) if agent_str else None

            claim_id = match.group("claim_id")
            illocution = Illocution(match.group("illocution").lower())
            affect = Affect(match.group("affect").lower())
            content = match.group("content").strip()
            ground = match.group("ground")
            confidence_str = match.group("confidence")
            confidence = float(confidence_str) if confidence_str else 0.5
            # M1 fix: Clamp confidence to valid range [0.0, 1.0]
            confidence = max(0.0, min(1.0, confidence))
            state_str = match.group("state")
            state = State(state_str.lower()) if state_str else State.PROVISIONAL

            return VerixClaim(
                illocution=illocution,
                affect=affect,
                content=content,
                ground=ground,
                confidence=confidence,
                state=state,
                raw_text=match.group(0),
                claim_id=claim_id,
                agent=agent,
                meta_level=meta_level,
            )
        except (ValueError, KeyError) as e:
            # M2 fix: Log exception instead of silently swallowing
            logger.warning(
                "Failed to parse L1 VERIX claim: %s. Match text: %s",
                str(e),
                match.group(0)[:100] if match else "N/A"
            )
            return None

    def _parse_l0_match(self, match: re.Match) -> Optional[VerixClaim]:
        """Parse an L0 format regex match into VerixClaim.

        Args:
            match: Regex match object from L0_PATTERN.

        Returns:
            VerixClaim if parsing succeeds, None otherwise.
        """
        try:
            agent_map = {
                "M": Agent.MODEL,
                "U": Agent.USER,
                "S": Agent.SYSTEM,
                "D": Agent.DOC,
                "P": Agent.PROCESS,
            }
            illocution_map = {
                "A": Illocution.ASSERT,
                "?": Illocution.QUERY,
                "!": Illocution.DIRECT,
                "C": Illocution.COMMIT,
                "E": Illocution.EXPRESS,
            }
            affect_map = {
                ".": Affect.NEUTRAL,
                "+": Affect.POSITIVE,
                "-": Affect.NEGATIVE,
                "~": Affect.UNCERTAIN,
            }

            # Extract agent if present
            agent_char = match.group("agent")
            agent = agent_map.get(agent_char) if agent_char else None

            illocution = illocution_map[match.group("illocution")]
            affect = affect_map[match.group("affect")]
            confidence = int(match.group("confidence")) / 100.0
            # M1 fix: Clamp confidence to valid range [0.0, 1.0]
            confidence = max(0.0, min(1.0, confidence))
            content = match.group("content").strip()

            return VerixClaim(
                illocution=illocution,
                affect=affect,
                content=content,
                ground=None,  # L0 doesn't include ground
                confidence=confidence,
                state=State.PROVISIONAL,  # L0 doesn't include state
                raw_text=match.group(0),
                agent=agent,
            )
        except (ValueError, KeyError) as e:
            # M2 fix: Log exception instead of silently swallowing
            logger.warning(
                "Failed to parse L0 VERIX claim: %s. Match text: %s",
                str(e),
                match.group(0)[:100] if match else "N/A"
            )
            return None


# =============================================================================
# VALIDATOR
# =============================================================================


class VerixValidator:
    """
    Validate VERIX compliance in responses.

    Checks that claims meet the requirements specified in PromptConfig,
    including required fields, confidence calibration, and ground chains.

    Usage:
        validator = VerixValidator()
        is_valid, violations = validator.validate(claims)
        score = validator.compliance_score(claims)
    """

    def __init__(self, config: Optional[PromptConfig] = None):
        """
        Initialize validator with configuration.

        Args:
            config: PromptConfig specifying validation requirements
        """
        self.config = config or PromptConfig()

    def validate(self, claims: List[VerixClaim]) -> Tuple[bool, List[str]]:
        """
        Validate a list of claims against configuration requirements.

        Args:
            claims: List of VerixClaim objects to validate

        Returns:
            Tuple of (is_valid, list_of_violations)
        """
        violations = []

        for i, claim in enumerate(claims):
            claim_violations = self._validate_single(claim, i)
            violations.extend(claim_violations)

        # Check inter-claim consistency
        if len(claims) <= 1:
            return len(violations) == 0, violations

        consistency_violations = self._check_consistency(claims)
        violations.extend(consistency_violations)

        # Detect ground cycles
        cycles = self.detect_ground_cycles(claims)
        for cycle in cycles:
            violations.append(f"Circular ground reference detected: {cycle}")

        return len(violations) == 0, violations

    def _validate_single(self, claim: VerixClaim, index: int) -> List[str]:
        """Validate a single claim."""
        violations = []
        prefix = f"Claim {index + 1}"

        # Agent-based strictness multiplier
        agent_strictness = self._get_agent_strictness(claim.agent)

        # Check required ground
        if self.config.require_ground and not claim.is_grounded():
            agent_str = claim.agent.value if claim.agent else 'unknown'
            if agent_strictness >= 0.8:
                violations.append(f"{prefix}: Missing ground/evidence (agent={agent_str})")
            else:
                violations.append(f"{prefix}: Missing ground (agent={agent_str}, ground required by config)")

        # Check confidence range
        if not (0.0 <= claim.confidence <= 1.0):
            violations.append(f"{prefix}: Confidence {claim.confidence} outside [0, 1] range")

        # Agent-adjusted confidence ceiling
        max_confidence = self._get_agent_confidence_ceiling(claim.agent)
        if claim.confidence > max_confidence:
            violations.append(
                f"{prefix}: Confidence {claim.confidence:.2f} exceeds ceiling {max_confidence:.2f} "
                f"for agent={claim.agent.value if claim.agent else 'unknown'}"
            )

        # Check strictness requirements
        if self.config.verix_strictness == VerixStrictness.STRICT:
            if not claim.ground and agent_strictness >= 0.7:
                violations.append(f"{prefix}: STRICT mode requires ground field")
            if claim.state == State.PROVISIONAL and claim.confidence > 0.8:
                violations.append(
                    f"{prefix}: High confidence ({claim.confidence}) with provisional state"
                )

        # Meta-level handling
        meta_violations = self._validate_meta_level(claim, index)
        violations.extend(meta_violations)

        return violations

    def _get_agent_strictness(self, agent: Optional[Agent]) -> float:
        """
        Get strictness multiplier based on agent type.

        MODEL claims require highest standards (AI should be precise).
        USER claims are most trusted (human input).

        Returns:
            Strictness multiplier 0.0-1.0 (higher = stricter)
        """
        if agent is None:
            return 0.7  # Default: moderate strictness

        strictness_map = {
            Agent.MODEL: 1.0,    # AI claims: strictest
            Agent.DOC: 0.9,      # Documentation: high standards
            Agent.PROCESS: 0.8,  # Computed: reliable but verify
            Agent.SYSTEM: 0.6,   # System-generated: trusted
            Agent.USER: 0.4,     # User input: most lenient
        }
        return strictness_map.get(agent, 0.7)

    def _get_agent_confidence_ceiling(self, agent: Optional[Agent]) -> float:
        """
        Get maximum allowed confidence based on agent type.

        Different agents have different epistemic authority.

        Returns:
            Maximum confidence allowed for this agent type
        """
        if agent is None:
            return 0.95  # Default ceiling

        ceiling_map = {
            Agent.MODEL: 0.95,   # AI can be highly confident
            Agent.DOC: 0.98,     # Documentation is authoritative
            Agent.PROCESS: 0.99, # Computed values are precise
            Agent.SYSTEM: 0.95,  # System claims are reliable
            Agent.USER: 1.0,     # User claims unrestricted
        }
        return ceiling_map.get(agent, 0.95)

    def _validate_meta_level(self, claim: VerixClaim, index: int) -> List[str]:
        """
        Validate and handle meta-level claims.

        META_VERIX claims (about VERIX itself) require special attention.
        Self-referential claims are flagged for review.

        Returns:
            List of violations for meta-level issues
        """
        violations = []
        prefix = f"Claim {index + 1}"

        # META_VERIX claims: stricter requirements
        if claim.meta_level == MetaLevel.META_VERIX:
            # META_VERIX claims should have high evidence standards
            if not claim.is_grounded():
                violations.append(
                    f"{prefix}: META_VERIX claim requires ground (claims about VERIX must be justified)"
                )
            # Confidence ceiling for self-referential claims
            if claim.confidence > 0.85:
                violations.append(
                    f"{prefix}: META_VERIX confidence {claim.confidence:.2f} exceeds 0.85 ceiling "
                    f"(self-referential claims require epistemic humility)"
                )

        return violations

    def _check_consistency(self, claims: List[VerixClaim]) -> List[str]:
        """Check consistency across multiple claims."""
        violations = []

        # Check for contradicting confidence levels on same content
        content_confidence: Dict[str, Tuple[float, int]] = {}
        for i, claim in enumerate(claims):
            normalized = claim.content.lower().strip()
            if normalized in content_confidence:
                prev_conf, prev_idx = content_confidence[normalized]
                if abs(claim.confidence - prev_conf) > 0.3:
                    violations.append(
                        f"Inconsistent confidence for same content: "
                        f"Claim {prev_idx + 1} ({prev_conf:.2f}) vs "
                        f"Claim {i + 1} ({claim.confidence:.2f})"
                    )
            else:
                content_confidence[normalized] = (claim.confidence, i)

        # Check for retracted claims referenced by confirmed claims
        retracted_content = {
            claim.content.lower().strip()
            for claim in claims
            if claim.state == State.RETRACTED
        }

        for i, claim in enumerate(claims):
            if claim.state != State.CONFIRMED:
                continue
            if claim.ground and claim.ground.lower().strip() in retracted_content:
                violations.append(
                    f"Claim {i + 1}: Confirmed claim references retracted content"
                )

        return violations

    def detect_ground_cycles(self, claims: List[VerixClaim]) -> List[str]:
        """Detect circular dependencies in claim ground references.

        Builds a directed graph where edges represent ground references between
        claims (via claim_id). Uses DFS to find cycles, which indicate circular
        reasoning (e.g., claim-a grounds claim-b which grounds claim-a).

        Args:
            claims: List of VerixClaim objects to analyze.

        Returns:
            List of cycle descriptions (e.g., "claim-a -> claim-b -> claim-a").

        Raises:
            ValueError: If claims count exceeds MAX_CLAIMS_LIMIT (memory protection).
        """
        # M3 fix: Add maximum claims limit to prevent memory exhaustion
        if len(claims) > MAX_CLAIMS_LIMIT:
            raise ValueError(
                f"Claims count ({len(claims)}) exceeds maximum allowed "
                f"({MAX_CLAIMS_LIMIT}). This limit prevents memory exhaustion attacks."
            )

        # Build claim_id -> claim mapping
        id_to_claim: Dict[str, VerixClaim] = {}
        for claim in claims:
            if claim.claim_id:
                id_to_claim[claim.claim_id] = claim

        # Build adjacency list: claim_id -> list of referenced claim_ids
        graph: Dict[str, List[str]] = {}
        for claim in claims:
            if claim.claim_id:
                graph[claim.claim_id] = []
                if claim.ground:
                    ground_lower = claim.ground.lower().strip()
                    for other_id in id_to_claim.keys():
                        if other_id.lower() in ground_lower:
                            graph[claim.claim_id].append(other_id)

        # DFS cycle detection
        cycles: List[str] = []
        visited: set = set()
        rec_stack: set = set()
        path: List[str] = []

        def dfs(node: str) -> None:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    dfs(neighbor)
                elif neighbor in rec_stack:
                    # Found cycle - extract it from path
                    cycle_start = path.index(neighbor)
                    cycle_nodes = path[cycle_start:] + [neighbor]
                    cycle_str = " -> ".join(cycle_nodes)
                    if cycle_str not in cycles:
                        cycles.append(cycle_str)

            path.pop()
            rec_stack.remove(node)

        # Run DFS from each unvisited node
        for node in graph.keys():
            if node not in visited:
                dfs(node)

        return cycles

    def compliance_score(self, claims: List[VerixClaim]) -> float:
        """
        Calculate overall compliance score (0.0 - 1.0).

        Higher score means better compliance with VERIX requirements.

        Args:
            claims: List of VerixClaim objects

        Returns:
            Float score from 0.0 (no compliance) to 1.0 (full compliance)
        """
        if not claims:
            return 0.0

        total_points = 0.0
        max_points = 0.0

        for claim in claims:
            # Points for having ground
            max_points += 1.0
            if claim.is_grounded():
                total_points += 1.0

            # Points for confidence in valid range
            max_points += 1.0
            if 0.0 <= claim.confidence <= 1.0:
                total_points += 1.0

            # Points for non-provisional state
            max_points += 0.5
            if claim.state != State.PROVISIONAL:
                total_points += 0.5

            # Points for content not being empty
            max_points += 0.5
            if claim.content.strip():
                total_points += 0.5

            # Bonus points for having agent marker
            max_points += 0.25
            if claim.agent:
                total_points += 0.25

        # Inter-claim consistency bonus
        _, violations = self.validate(claims)
        consistency_penalty = len(violations) * 0.1
        total_points = max(0, total_points - consistency_penalty)

        return total_points / max_points if max_points > 0 else 0.0


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================


def format_claim(
    claim: VerixClaim,
    compression: CompressionLevel = CompressionLevel.L1_AI_HUMAN
) -> str:
    """
    Format a claim at the specified compression level.

    Args:
        claim: The claim to format
        compression: Target compression level (L0, L1, or L2)

    Returns:
        Formatted string representation

    Examples:
        >>> claim = create_claim("This is true", confidence=0.85)
        >>> format_claim(claim, CompressionLevel.L0_AI_AI)
        'A.85:This is true'
        >>> format_claim(claim, CompressionLevel.L1_AI_HUMAN)
        '[assert|neutral] This is true [conf:0.85] [state:provisional]'
        >>> format_claim(claim, CompressionLevel.L2_HUMAN)
        "I'm fairly confident that This is true."
    """
    if compression == CompressionLevel.L0_AI_AI:
        return claim.to_l0()
    elif compression == CompressionLevel.L1_AI_HUMAN:
        return claim.to_l1()
    else:
        return claim.to_l2()


def create_claim(
    content: str,
    illocution: Illocution = Illocution.ASSERT,
    affect: Affect = Affect.NEUTRAL,
    ground: Optional[str] = None,
    confidence: float = 0.5,
    state: State = State.PROVISIONAL,
    agent: Optional[Agent] = None,
    meta_level: MetaLevel = MetaLevel.OBJECT,
    claim_id: Optional[str] = None,
) -> VerixClaim:
    """
    Create a new VERIX claim with sensible defaults.

    Args:
        content: The claim content (required)
        illocution: Speech act type (default: ASSERT)
        affect: Emotional valence (default: NEUTRAL)
        ground: Evidence/source (default: None)
        confidence: Confidence level 0-1 (default: 0.5)
        state: Claim state (default: PROVISIONAL)
        agent: Who makes this claim (default: None)
        meta_level: Hofstadter meta-level (default: OBJECT)
        claim_id: Optional unique identifier

    Returns:
        New VerixClaim instance

    Examples:
        >>> claim = create_claim("The sky is blue", confidence=0.95, ground="direct observation")
        >>> claim.to_l1()
        '[assert|neutral] The sky is blue [ground:direct observation] [conf:0.95] [state:provisional]'
    """
    return VerixClaim(
        illocution=illocution,
        affect=affect,
        content=content,
        ground=ground,
        confidence=confidence,
        state=state,
        raw_text="",
        agent=agent,
        meta_level=meta_level,
        claim_id=claim_id,
    )


def create_meta_claim(
    content: str,
    about_claim: Optional[VerixClaim] = None,
    ground: Optional[str] = None,
    confidence: float = 0.5,
) -> VerixClaim:
    """
    Create a meta-level claim about another claim.

    Args:
        content: The meta-claim content
        about_claim: The claim this is about (for auto-grounding)
        ground: Explicit ground (overrides about_claim)
        confidence: Confidence level

    Returns:
        New VerixClaim at META level

    Example:
        >>> original = create_claim("The sky is blue", claim_id="claim-1")
        >>> meta = create_meta_claim("This claim is well-supported", about_claim=original)
    """
    actual_ground = ground
    if about_claim and not ground:
        if about_claim.claim_id:
            actual_ground = f"claim:{about_claim.claim_id}"
        else:
            actual_ground = f"claim:{about_claim.content[:30]}..."

    return VerixClaim(
        illocution=Illocution.ASSERT,
        affect=Affect.NEUTRAL,
        content=content,
        ground=actual_ground,
        confidence=confidence,
        state=State.PROVISIONAL,
        raw_text="",
        agent=Agent.MODEL,
        meta_level=MetaLevel.META,
    )


def create_meta_verix_claim(
    content: str,
    ground: Optional[str] = None,
    confidence: float = 0.5,
) -> VerixClaim:
    """
    Create a claim about VERIX notation itself.

    This is the highest meta-level - claims about the notation system.

    Args:
        content: The meta-VERIX claim content
        ground: Evidence/source for the claim
        confidence: Confidence level

    Returns:
        New VerixClaim at META_VERIX level

    Example:
        >>> claim = create_meta_verix_claim(
        ...     "VERIX compression levels trade precision for readability",
        ...     ground="verix-spec-v1.0",
        ...     confidence=0.8
        ... )
    """
    return VerixClaim(
        illocution=Illocution.ASSERT,
        affect=Affect.NEUTRAL,
        content=content,
        ground=ground or "verix-spec",
        confidence=confidence,
        state=State.PROVISIONAL,
        raw_text="",
        agent=Agent.SYSTEM,
        meta_level=MetaLevel.META_VERIX,
    )


# =============================================================================
# MODULE SELF-TEST
# =============================================================================


if __name__ == "__main__":
    # Quick self-test when run directly
    print("VERIX Parser Self-Test")
    print("=" * 50)

    # Test L1 parsing
    test_l1 = "[agent:model] [assert|neutral] This is a test claim [ground:self-test] [conf:0.85] [state:confirmed]"
    parser = VerixParser()
    claims = parser.parse(test_l1)
    print(f"\nParsed L1: {len(claims)} claims")
    if claims:
        print(f"  Content: {claims[0].content}")
        print(f"  Confidence: {claims[0].confidence}")
        print(f"  Agent: {claims[0].agent}")

    # Test L0 parsing
    test_l0 = "MA+85:This is a test"
    claims_l0 = parser.parse(test_l0)
    print(f"\nParsed L0: {len(claims_l0)} claims")
    if claims_l0:
        print(f"  Content: {claims_l0[0].content}")
        print(f"  Confidence: {claims_l0[0].confidence}")

    # Test claim creation
    claim = create_claim(
        "Test claim creation",
        confidence=0.9,
        ground="self-test",
        agent=Agent.MODEL
    )
    print(f"\nCreated claim:")
    print(f"  L0: {claim.to_l0()}")
    print(f"  L1: {claim.to_l1()}")
    print(f"  L2: {claim.to_l2()}")

    # Test validation
    validator = VerixValidator()
    is_valid, violations = validator.validate([claim])
    print(f"\nValidation: {'PASS' if is_valid else 'FAIL'}")
    for v in violations:
        print(f"  - {v}")

    score = validator.compliance_score([claim])
    print(f"Compliance score: {score:.2f}")

    print("\n" + "=" * 50)
    print("Self-test complete!")
