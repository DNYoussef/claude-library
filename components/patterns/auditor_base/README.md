# Auditor Base Component

Abstract base class for building content auditors with confidence scoring.

## Features

- Abstract auditor pattern
- AuditorResult dataclass
- ActionClass recommendations (ACCEPT, REVIEW, REJECT)
- Confidence ceiling enforcement
- VERIX-compliant output format

## Usage

```python
from auditor_base import BaseAuditor, AuditorResult, ActionClass
from decimal import Decimal

class ContentAuditor(BaseAuditor):
    """Example content auditor implementation."""

    def audit(self, content: str) -> AuditorResult:
        # Your audit logic
        issues = self._find_issues(content)

        confidence = Decimal("0.85")
        confidence = self.apply_ceiling(confidence)  # Enforces max 0.95

        if len(issues) == 0:
            action = ActionClass.ACCEPT
        elif len(issues) < 3:
            action = ActionClass.REVIEW
        else:
            action = ActionClass.REJECT

        return AuditorResult(
            action=action,
            confidence=confidence,
            issues=issues,
            recommendations=["Consider X", "Review Y"]
        )

    def _find_issues(self, content: str) -> list:
        # Implementation
        return []

# Use the auditor
auditor = ContentAuditor()
result = auditor.audit("Some content to audit")

if result.action == ActionClass.ACCEPT:
    print(f"Approved with {result.confidence} confidence")
elif result.action == ActionClass.REVIEW:
    print(f"Needs review: {result.issues}")
```

## ActionClass Values

| Action | Description | Typical Threshold |
|--------|-------------|-------------------|
| ACCEPT | Content passes audit | 0 issues |
| REVIEW | Manual review needed | 1-3 issues |
| REJECT | Content fails audit | 4+ issues |

## Confidence Ceilings

Built-in ceiling of 0.95 to prevent overconfidence:

```python
raw_confidence = Decimal("0.99")
capped = self.apply_ceiling(raw_confidence)  # Returns 0.95
```
