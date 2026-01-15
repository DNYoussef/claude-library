# Library Drift Audit

Component-by-component audit of library component drift across repos. Compares
imports and on-disk copies of `.claude/library` components against each repo.

## Features

- Scans the library catalog to enumerate components
- Finds `library.components.<domain>.<component>` imports
- Locates component copies in repos and diffs file content
- Outputs drift report + per-repo deployment checklists
- Prioritizes CI/test scaffolding in the checklist output

## Usage

```bash
python C:\Users\17175\.claude\library\components\observability\library_drift_audit\library_drift_audit.py ^
  --catalog C:\Users\17175\.claude\library\catalog.json ^
  --status C:\Users\17175\Desktop\2026-AI-EXOSKELETON\2026-EXOSKELETON-STATUS.json ^
  --output-report C:\Users\17175\Desktop\2026-AI-EXOSKELETON\2026-EXOSKELETON-DRIFT-AUDIT.md ^
  --output-checklists C:\Users\17175\Desktop\2026-AI-EXOSKELETON\2026-EXOSKELETON-DEPLOYMENT-CHECKLISTS.md
```
