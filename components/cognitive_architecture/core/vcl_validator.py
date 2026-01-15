"""
VCL (VERILINGUA Cognitive Language) Validator v3.1.1

Validates VCL-formatted output against the 7-slot canonical format,
enforces confidence ceilings, detects epistemic cosplay, and ensures
immutable safety bounds.

VCL 7-Slot Order (FIXED):
  HON -> MOR -> COM -> CLS -> EVD -> ASP -> SPC

Compression Levels:
  L0: Full VCL notation (AI<->AI internal)
  L1: VCL headers + English prose (audit trail)
  L2: Pure English (human delivery) - DEFAULT

Hard Constraints:
  - EVD enforcement >= 1 (IMMUTABLE)
  - ASP enforcement >= 1 (IMMUTABLE)
  - No epistemic cosplay
  - Confidence <= ceiling(EVD_type)
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
import re
import hashlib


# =============================================================================
# ENUMS AND CONSTANTS
# =============================================================================

class VCLSlot(Enum):
    """VCL 7-slot types in canonical order."""
    HON = "HON"  # Honorific (Japanese)
    MOR = "MOR"  # Morphological (Arabic)
    COM = "COM"  # Compositional (German)
    CLS = "CLS"  # Classifier (Chinese)
    EVD = "EVD"  # Evidential (Turkish)
    ASP = "ASP"  # Aspectual (Russian)
    SPC = "SPC"  # Spatial (Guugu Yimithirr)


class EVDType(Enum):
    """Evidence types with Turkish-inspired markers."""
    DEFINITION = "definition"    # -DI (tanim)
    POLICY = "policy"            # -DI (politika)
    OBSERVATION = "observation"  # -DI (gozlem)
    RESEARCH = "research"        # -mis (arastirma)
    REPORT = "report"            # -mis (rapor)
    INFERENCE = "inference"      # -dir (cikarim)


class ASPType(Enum):
    """Aspect types with Russian-inspired markers."""
    PERFECTIVE = "sov"      # Complete (sovershenniy)
    IMPERFECTIVE = "nesov"  # Ongoing (nesovershenniy)


class HONLevel(Enum):
    """Honorific levels (Japanese keigo)."""
    TEINEIGO = "teineigo"    # Polite (standard)
    KENJOUGO = "kenjougo"    # Humble
    SONKEIGO = "sonkeigo"    # Respectful
    FUTSUU = "futsuu"        # Casual


class CompressionLevel(Enum):
    """Output compression levels."""
    L0_INTERNAL = "L0"  # Full VCL notation
    L1_AUDIT = "L1"     # VCL headers + English
    L2_HUMAN = "L2"     # Pure English (DEFAULT)


# =============================================================================
# CONFIDENCE CEILINGS (EVD type determines max confidence)
# =============================================================================

CONFIDENCE_CEILINGS: Dict[EVDType, float] = {
    EVDType.DEFINITION: 0.95,
    EVDType.POLICY: 0.90,
    EVDType.OBSERVATION: 0.95,
    EVDType.RESEARCH: 0.85,
    EVDType.REPORT: 0.70,
    EVDType.INFERENCE: 0.70,
}

# Synthetic constructs get lower ceiling
SYNTHETIC_CEILING = 0.80


# =============================================================================
# VCL SLOT MARKERS (Multilingual)
# =============================================================================

EVD_MARKERS = {
    EVDType.DEFINITION: {
        "marker": "-DI",
        "trilingual": "tanim|teigi|tanim",  # AR|JP|TR
    },
    EVDType.POLICY: {
        "marker": "-DI",
        "trilingual": "siyasa|houshin|politika",
    },
    EVDType.OBSERVATION: {
        "marker": "-DI",
        "trilingual": "mushahada|kansoku|gozlem",
    },
    EVDType.RESEARCH: {
        "marker": "-mis",
        "trilingual": "bahth|kenkyu|arastirma",
    },
    EVDType.REPORT: {
        "marker": "-mis",
        "trilingual": "manqul|houkoku|rapor",
    },
    EVDType.INFERENCE: {
        "marker": "-dir",
        "trilingual": "istidlal|suiron|cikarim",
    },
}

ASP_MARKERS = {
    ASPType.PERFECTIVE: {
        "marker": "sov",
        "symbol": "filled_circle",  # Using ASCII
    },
    ASPType.IMPERFECTIVE: {
        "marker": "nesov",
        "symbol": "empty_circle",
    },
}


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class VCLStatement:
    """A parsed VCL statement with all 7 slots."""
    raw_text: str

    # 7 Slots (None if not present)
    hon: Optional[str] = None
    mor: Optional[str] = None
    com: Optional[str] = None
    cls: Optional[str] = None
    evd: Optional[Tuple[EVDType, str]] = None  # (type, source)
    asp: Optional[Tuple[ASPType, Optional[str]]] = None  # (type, criteria)
    spc: Optional[str] = None

    # VERIX metadata
    confidence: float = 0.5
    ground: Optional[str] = None
    state: str = "provisional"

    # Content
    content: str = ""

    def get_evd_type(self) -> Optional[EVDType]:
        """Get the EVD type if present."""
        return self.evd[0] if self.evd else None

    def get_asp_type(self) -> Optional[ASPType]:
        """Get the ASP type if present."""
        return self.asp[0] if self.asp else None


@dataclass
class ValidationResult:
    """Result of VCL validation."""
    passed: bool
    checks: Dict[str, bool]
    violations: List[str] = field(default_factory=list)
    vcl_compliance_score: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "passed": self.passed,
            "checks": self.checks,
            "violations": self.violations,
            "vcl_compliance_score": self.vcl_compliance_score,
        }


@dataclass
class VCLConfig:
    """VCL configuration for validation."""
    # Slot enforcement levels (0=permissive, 1=conditional, 2=strict)
    hon_enforcement: int = 1
    mor_enforcement: int = 1
    com_enforcement: int = 1
    cls_enforcement: int = 0
    evd_enforcement: int = 2  # IMMUTABLE >= 1
    asp_enforcement: int = 2  # IMMUTABLE >= 1
    spc_enforcement: int = 0

    # VERIX settings
    compression: CompressionLevel = CompressionLevel.L2_HUMAN
    require_ground: bool = True
    require_confidence: bool = True

    # Output language
    output_language: str = "english"

    def enforce_safety_bounds(self) -> "VCLConfig":
        """Enforce immutable safety bounds. Returns self for chaining."""
        # EVD and ASP enforcement cannot be lowered below 1
        self.evd_enforcement = max(1, self.evd_enforcement)
        self.asp_enforcement = max(1, self.asp_enforcement)
        return self


# =============================================================================
# VCL VALIDATOR
# =============================================================================

class VCLValidator:
    """
    Validates VCL compliance for outputs.

    Enforces:
    - 7-slot order (HON -> MOR -> COM -> CLS -> EVD -> ASP -> SPC)
    - Confidence ceilings by EVD type
    - Epistemic cosplay detection
    - Immutable safety bounds (EVD >= 1, ASP >= 1)
    - L2 English purity for human output
    """

    SLOT_ORDER = [VCLSlot.HON, VCLSlot.MOR, VCLSlot.COM,
                  VCLSlot.CLS, VCLSlot.EVD, VCLSlot.ASP, VCLSlot.SPC]

    # Patterns for detecting VCL notation in L2 output (should not be present)
    VCL_NOTATION_PATTERNS = [
        r'\[\[[\w:]+\]\]',           # [[EVD:...]]
        r'\[EVD:',                    # [EVD:
        r'\[ASP:',                    # [ASP:
        r'\[HON:',                    # [HON:
        r'sov\.',                     # Russian aspect marker
        r'nesov\.',                   # Russian aspect marker
        r'-DI<',                      # Turkish evidential
        r'-mis<',                     # Turkish evidential
        r'-dir<',                     # Turkish evidential
    ]

    # VERIX notation patterns (allowed in L1, not in L2)
    VERIX_L1_PATTERNS = [
        r'\[[\w]+\|[\w]+\]',          # [assert|confident]
        r'\[ground:[\w\-:=\.]+\]',    # [ground:...]
        r'\[conf:[\d\.]+\]',          # [conf:0.95]
        r'\[state:[\w]+\]',           # [state:confirmed]
    ]

    def __init__(self, config: Optional[VCLConfig] = None):
        """Initialize validator with optional config."""
        self.config = config or VCLConfig()
        self.config.enforce_safety_bounds()

    def validate(self, output: str, config: Optional[VCLConfig] = None) -> ValidationResult:
        """
        Validate output against VCL requirements.

        Args:
            output: The output text to validate
            config: Optional config override

        Returns:
            ValidationResult with all check details
        """
        cfg = config or self.config
        cfg.enforce_safety_bounds()

        checks = {
            "slot_order_correct": self._check_slot_order(output),
            "evd_present": self._check_evd_present(output, cfg),
            "asp_present": self._check_asp_present(output, cfg),
            "confidence_ceiling_respected": self._check_confidence_ceiling(output),
            "no_epistemic_cosplay": self._check_no_cosplay(output),
            "l2_english_output": self._check_l2_english(output, cfg),
            "no_bracket_collision": self._check_bracket_collision(output),
            "immutable_bounds_enforced": self._check_immutable_bounds(cfg),
        }

        violations = []
        for check_name, passed in checks.items():
            if not passed:
                violations.append(f"FAILED: {check_name}")

        vcl_compliance = sum(checks.values()) / len(checks) if checks else 0.0

        return ValidationResult(
            passed=all(checks.values()),
            checks=checks,
            violations=violations,
            vcl_compliance_score=vcl_compliance,
        )

    def _check_slot_order(self, output: str) -> bool:
        """
        Check if VCL slots appear in correct order.

        Fixed order: HON -> MOR -> COM -> CLS -> EVD -> ASP -> SPC
        """
        # Find positions of each slot marker
        slot_positions = {}
        for slot in self.SLOT_ORDER:
            # Look for [[SLOT:...]] or [SLOT:...] patterns
            pattern = rf'\[+{slot.value}:'
            match = re.search(pattern, output, re.IGNORECASE)
            if match:
                slot_positions[slot] = match.start()

        # If no slots found, consider it valid (L2 output)
        if not slot_positions:
            return True

        # Check order
        last_pos = -1
        for slot in self.SLOT_ORDER:
            if slot in slot_positions:
                if slot_positions[slot] < last_pos:
                    return False
                last_pos = slot_positions[slot]

        return True

    def _check_evd_present(self, output: str, config: VCLConfig) -> bool:
        """
        Check if EVD (evidential) marker is present when required.

        EVD enforcement >= 1 means EVD must be present for factual claims.
        """
        if config.evd_enforcement < 1:
            return True  # Not required

        # For L2 output, check for naturalized evidence markers
        if config.compression == CompressionLevel.L2_HUMAN:
            evidence_phrases = [
                r'\bi (directly )?(observed|verified|witnessed|saw)\b',
                r'\baccording to\b',
                r'\bresearch (indicates|shows|suggests)\b',
                r'\bit\'?s reported that\b',
                r'\bi (infer|deduce|conclude) that\b',
                r'\bbased on\b',
                r'\[ground:',  # VERIX ground marker
            ]
            for phrase in evidence_phrases:
                if re.search(phrase, output, re.IGNORECASE):
                    return True
            # If output is short or non-factual, allow
            if len(output) < 50:
                return True
            return False

        # For L0/L1, check for explicit EVD markers
        evd_patterns = [r'\[+EVD:', r'-DI<', r'-mis<', r'-dir<']
        for pattern in evd_patterns:
            if re.search(pattern, output, re.IGNORECASE):
                return True

        return False

    def _check_asp_present(self, output: str, config: VCLConfig) -> bool:
        """
        Check if ASP (aspectual) marker is present when required.

        ASP enforcement >= 1 means completion status must be marked.
        """
        if config.asp_enforcement < 1:
            return True

        # For L2 output, check for naturalized aspect markers
        if config.compression == CompressionLevel.L2_HUMAN:
            aspect_phrases = [
                r'\b(complete|done|finished|succeeded|failed)\b',
                r'\b(in progress|ongoing|working on|processing)\b',
                r'\b(partial(ly)?|started|begun)\b',
                r'\[state:',  # VERIX state marker
            ]
            for phrase in aspect_phrases:
                if re.search(phrase, output, re.IGNORECASE):
                    return True
            # Short outputs may not need aspect
            if len(output) < 50:
                return True
            return False

        # For L0/L1, check for explicit ASP markers
        asp_patterns = [r'\[+ASP:', r'sov\.', r'nesov\.']
        for pattern in asp_patterns:
            if re.search(pattern, output, re.IGNORECASE):
                return True

        return False

    def _check_confidence_ceiling(self, output: str) -> bool:
        """
        Check if confidence values respect EVD type ceilings.

        Rule: confidence <= ceiling(EVD_type)
        """
        # Extract confidence values
        conf_pattern = r'\[conf:(\d+\.?\d*)\]'
        conf_matches = re.findall(conf_pattern, output)

        if not conf_matches:
            return True  # No explicit confidence, valid

        # Extract EVD type
        evd_type = self._extract_evd_type(output)
        if not evd_type:
            # Default to inference ceiling (most restrictive)
            ceiling = CONFIDENCE_CEILINGS[EVDType.INFERENCE]
        else:
            ceiling = CONFIDENCE_CEILINGS.get(evd_type, 0.70)

        # Check all confidence values
        for conf_str in conf_matches:
            try:
                conf = float(conf_str)
                if conf > ceiling:
                    return False
            except ValueError:
                continue

        return True

    def _extract_evd_type(self, output: str) -> Optional[EVDType]:
        """Extract EVD type from output."""
        # Check for explicit EVD markers
        if re.search(r'observation|gozlem|kansoku|mushahada|-DI.*gozlem', output, re.IGNORECASE):
            return EVDType.OBSERVATION
        if re.search(r'research|arastirma|kenkyu|-mis.*arastirma', output, re.IGNORECASE):
            return EVDType.RESEARCH
        if re.search(r'report(ed)?|rapor|houkoku|-mis.*rapor', output, re.IGNORECASE):
            return EVDType.REPORT
        if re.search(r'infer(red)?|cikarim|suiron|-dir', output, re.IGNORECASE):
            return EVDType.INFERENCE
        if re.search(r'definition|tanim|teigi', output, re.IGNORECASE):
            return EVDType.DEFINITION
        if re.search(r'policy|politika|houshin', output, re.IGNORECASE):
            return EVDType.POLICY

        # Check VERIX ground markers
        ground_pattern = r'\[ground:([\w\-:=\.]+)\]'
        ground_match = re.search(ground_pattern, output)
        if ground_match:
            ground = ground_match.group(1).lower()
            if 'witnessed' in ground or 'observed' in ground:
                return EVDType.OBSERVATION
            if 'research' in ground:
                return EVDType.RESEARCH
            if 'reported' in ground:
                return EVDType.REPORT
            if 'inferred' in ground:
                return EVDType.INFERENCE

        return None

    def _check_no_cosplay(self, output: str) -> bool:
        """
        Detect epistemic cosplay violations.

        Cosplay = claiming higher epistemic status than evidence warrants.

        Violations:
        - EVD=observation but no observation ground
        - STATE=complete but no completion criteria
        - High confidence (>0.85) from inference/report
        """
        violations = []

        # Check observation claims without observation ground
        if re.search(r'i (directly )?(observed|witnessed|saw)', output, re.IGNORECASE):
            # Must have observation-type ground
            if not re.search(r'\[ground:.*observed|witnessed|read.*code|ran.*test', output, re.IGNORECASE):
                # Allow if it's actually describing an observation
                if not re.search(r'i ran|i executed|i checked|i verified', output, re.IGNORECASE):
                    violations.append("observation_without_ground")

        # Check complete state without criteria
        if re.search(r'\[state:complete\]|\bASP:sov\.', output, re.IGNORECASE):
            # Should have completion criteria
            if not re.search(r'criteria|passed|succeeded|done:', output, re.IGNORECASE):
                violations.append("complete_without_criteria")

        # Check high confidence from weak evidence
        conf_pattern = r'\[conf:(\d+\.?\d*)\]'
        conf_matches = re.findall(conf_pattern, output)
        evd_type = self._extract_evd_type(output)

        if evd_type in [EVDType.INFERENCE, EVDType.REPORT]:
            for conf_str in conf_matches:
                try:
                    conf = float(conf_str)
                    if conf > 0.85:
                        violations.append(f"high_confidence_{conf}_from_{evd_type.value}")
                except ValueError:
                    continue

        return len(violations) == 0

    def _check_l2_english(self, output: str, config: VCLConfig) -> bool:
        """
        Check if L2 output is pure English (no VCL notation leaked).

        This is the DEFAULT for human-facing output.
        """
        if config.compression != CompressionLevel.L2_HUMAN:
            return True  # Not L2, VCL notation allowed

        # Check for leaked VCL notation
        for pattern in self.VCL_NOTATION_PATTERNS:
            if re.search(pattern, output, re.IGNORECASE):
                return False

        # L1 VERIX markers are allowed in L2 for auditability
        # (ground, conf, state markers are acceptable)

        return True

    def _check_bracket_collision(self, output: str) -> bool:
        """
        Check for delimiter collisions.

        [ ] is reserved for VERIX confidence ONLY, not inside VCL slot bodies.
        """
        # Find VCL slot bodies - match [[SLOT:content]]
        # Use non-greedy match to find the slot body
        slot_pattern = r'\[\[(\w+):([^\]]*(?:\][^\]])*[^\]]*)\]\]'
        matches = re.findall(slot_pattern, output)

        for slot_name, slot_body in matches:
            # Check if [ ] appears inside slot body (collision)
            # But allow < > which are valid for trilingual markers
            if '[' in slot_body or ']' in slot_body:
                return False

        # Also check for malformed patterns with nested brackets
        malformed_pattern = r'\[\[\w+:[^\]]*\[[^\]]*\][^\]]*\]\]'
        if re.search(malformed_pattern, output):
            return False

        return True

    def _check_immutable_bounds(self, config: VCLConfig) -> bool:
        """
        Check that immutable safety bounds are enforced.

        EVD_enforcement >= 1 (ALWAYS)
        ASP_enforcement >= 1 (ALWAYS)
        """
        return config.evd_enforcement >= 1 and config.asp_enforcement >= 1


# =============================================================================
# L2 NATURALIZATION (VCL -> English)
# =============================================================================

class L2Naturalizer:
    """
    Converts VCL notation to natural English (L2 compression).

    This is the DEFAULT output mode for human-facing delivery.
    """

    # VCL -> English mapping table
    NATURALIZATION_TABLE = {
        # EVD types
        "EVD:-DI<observation>": "I directly observed",
        "EVD:-DI<gozlem>": "I directly observed",
        "EVD:-mis<research>": "Research indicates",
        "EVD:-mis<arastirma>": "Research indicates",
        "EVD:-mis<report>": "It's reported that",
        "EVD:-mis<rapor>": "It's reported that",
        "EVD:-dir<inference>": "I infer that",
        "EVD:-dir<cikarim>": "I infer that",

        # ASP types
        "ASP:sov.": "Complete.",
        "ASP:nesov.": "In progress.",

        # HON levels
        "HON:kenjougo": "",  # Humble (affects phrasing)
        "HON:sonkeigo": "",  # Formal (affects phrasing)
        "HON:teineigo": "",  # Standard polite
        "HON:futsuu": "",    # Casual

        # Confidence ranges
        "[conf:0.95]": "I'm highly confident that",
        "[conf:0.90]": "I'm fairly confident that",
        "[conf:0.85]": "I believe",
        "[conf:0.70]": "I believe, with some uncertainty,",
        "[conf:0.50]": "I think",
        "[conf:0.40]": "This is speculative,",

        # State
        "[state:confirmed]": "",
        "[state:provisional]": "",
        "[state:complete]": "Done.",
        "[state:ongoing]": "Working on it.",
    }

    def naturalize(self, vcl_output: str) -> str:
        """
        Convert VCL notation to natural English.

        Args:
            vcl_output: Text with VCL notation

        Returns:
            Pure English text (L2)
        """
        result = vcl_output

        # STEP 1: Remove VCL markers FIRST (before any replacements)
        # Remove double-bracket VCL markers [[SLOT:...]]
        # Match [[HON:teineigo]], [[EVD:-DI<gozlem>]], etc.
        result = re.sub(r'\[\[HON:[^\]]+\]\]', '', result)
        result = re.sub(r'\[\[MOR:[^\]]+\]\]', '', result)
        result = re.sub(r'\[\[COM:[^\]]+\]\]', '', result)
        result = re.sub(r'\[\[CLS:[^\]]+\]\]', '', result)
        result = re.sub(r'\[\[EVD:[^\]]+\]\]', '', result)
        result = re.sub(r'\[\[ASP:[^\]]+\]\]', '', result)
        result = re.sub(r'\[\[SPC:[^\]]+\]\]', '', result)

        # Generic double-bracket removal - matches anything like [[X:Y]]
        result = re.sub(r'\[\[[A-Z]+:[^\]]+\]\]', '', result)

        # Remove single-bracket VCL markers [SLOT:...]
        result = re.sub(r'\[HON:[^\]]+\]', '', result)
        result = re.sub(r'\[MOR:[^\]]+\]', '', result)
        result = re.sub(r'\[COM:[^\]]+\]', '', result)
        result = re.sub(r'\[CLS:[^\]]+\]', '', result)
        result = re.sub(r'\[EVD:[^\]]+\]', '', result)
        result = re.sub(r'\[ASP:[^\]]+\]', '', result)
        result = re.sub(r'\[SPC:[^\]]+\]', '', result)

        # Generic single-bracket removal for slot markers
        result = re.sub(r'\[[A-Z]{3}:[^\]]+\]', '', result)

        # STEP 2: Apply naturalization mappings for remaining patterns
        for vcl_pattern, english in self.NATURALIZATION_TABLE.items():
            result = result.replace(vcl_pattern, english)

        # STEP 3: Clean up any remaining empty brackets or artifacts
        result = re.sub(r'\[\[\]\]', '', result)  # Remove [[]]
        result = re.sub(r'\[\]', '', result)       # Remove []

        # Clean up whitespace
        result = re.sub(r'\s+', ' ', result).strip()

        return result

    def naturalize_confidence(self, confidence: float) -> str:
        """Convert confidence value to natural language."""
        if confidence >= 0.95:
            return "I'm highly confident that"
        elif confidence >= 0.85:
            return "I'm fairly confident that"
        elif confidence >= 0.70:
            return "I believe"
        elif confidence >= 0.50:
            return "I think"
        elif confidence >= 0.30:
            return "I suspect"
        else:
            return "This is quite speculative, but"

    def naturalize_evd(self, evd_type: EVDType) -> str:
        """Convert EVD type to natural language prefix."""
        mapping = {
            EVDType.OBSERVATION: "I directly observed that",
            EVDType.RESEARCH: "Research indicates that",
            EVDType.REPORT: "It's reported that",
            EVDType.INFERENCE: "I infer that",
            EVDType.DEFINITION: "By definition,",
            EVDType.POLICY: "According to policy,",
        }
        return mapping.get(evd_type, "")

    def naturalize_asp(self, asp_type: ASPType, criteria: Optional[str] = None) -> str:
        """Convert ASP type to natural language."""
        if asp_type == ASPType.PERFECTIVE:
            if criteria:
                return f"Complete. ({criteria})"
            return "Complete."
        else:
            return "In progress."


# =============================================================================
# CLUSTER SIGNATURE FOR DSPY CACHING
# =============================================================================

def compute_cluster_signature(config: VCLConfig) -> str:
    """
    Compute stable hash for prompt clustering (DSPy caching).

    CRITICAL: Cache keys MUST include config hash to prevent
    cache pollution across configurations.

    Args:
        config: VCL configuration

    Returns:
        8-character hex hash
    """
    components = [
        f"EVD:{config.evd_enforcement}",
        f"ASP:{config.asp_enforcement}",
        f"HON:{config.hon_enforcement}",
        f"MOR:{config.mor_enforcement}",
        f"COM:{config.com_enforcement}",
        f"CLS:{config.cls_enforcement}",
        f"SPC:{config.spc_enforcement}",
        f"compress:{config.compression.value}",
        f"ground:{config.require_ground}",
        f"conf:{config.require_confidence}",
    ]

    # Sort for stability
    signature = "|".join(sorted(components))
    return hashlib.md5(signature.encode()).hexdigest()[:8]


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def validate_vcl(output: str, config: Optional[VCLConfig] = None) -> ValidationResult:
    """
    Convenience function to validate VCL output.

    Args:
        output: Text to validate
        config: Optional VCL configuration

    Returns:
        ValidationResult
    """
    validator = VCLValidator(config)
    return validator.validate(output)


def naturalize_to_l2(vcl_output: str) -> str:
    """
    Convenience function to convert VCL to English L2.

    Args:
        vcl_output: Text with VCL notation

    Returns:
        Pure English text
    """
    naturalizer = L2Naturalizer()
    return naturalizer.naturalize(vcl_output)


def enforce_safety_bounds(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enforce immutable safety bounds on config dict.

    EVD_enforcement >= 1 (CANNOT be lowered)
    ASP_enforcement >= 1 (CANNOT be lowered)

    Args:
        config: Configuration dictionary

    Returns:
        Config with safety bounds enforced
    """
    config = config.copy()

    # Handle nested vcl_slots structure
    if "vcl_slots" in config:
        slots = config["vcl_slots"]
        evd = slots.get("EVD")
        if evd is not None:
            if isinstance(evd, dict):
                evd["enforcement"] = max(1, evd.get("enforcement", 1))
            else:
                slots["EVD"] = {"enforcement": max(1, evd)}

        asp = slots.get("ASP")
        if asp is not None:
            if isinstance(asp, dict):
                asp["enforcement"] = max(1, asp.get("enforcement", 1))
            else:
                slots["ASP"] = {"enforcement": max(1, asp)}

    # Handle flat vector14 structure
    if "vector14" in config:
        v = config["vector14"]
        if len(v) >= 6:
            v[4] = max(1, v[4])  # EVD at index 4
            v[5] = max(1, v[5])  # ASP at index 5

    return config
