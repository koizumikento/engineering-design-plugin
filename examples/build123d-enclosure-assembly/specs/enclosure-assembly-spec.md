# Enclosure assembly example specification

- Status: approved example
- Units: mm
- Purpose: verify the unified build123d runner with a labeled assembly

## Requirements

| ID | Requirement | Verification |
|---|---|---|
| ASM-001 | The assembly contains separately labeled `base` and `lid` solids. | STEP reimport label and solid-count check |
| ASM-002 | The base remains fixed at the assembly origin. | Reimported component position |
| ASM-003 | The lid underside is rigidly seated at base Z = 4 mm. | Reimported lid position and bounding box |
| ASM-004 | The resolved assembly envelope is 60 × 40 × 7 mm. | Reimported bounding box |
| ASM-005 | Source placement uses named build123d joints; the STEP file is only required to preserve the resolved static placement. | Source review and STEP report |

This example does not claim that STEP preserves a live or editable joint constraint.
