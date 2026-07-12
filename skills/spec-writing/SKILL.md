---
name: spec-writing
description: Create or refine reviewable Markdown specifications for mechanical, electronic, or PCB-enclosure integrated designs. Use when requirements must be elicited, made testable, assigned identifiers and verification methods, or recorded under specs/ before or alongside engineering work. Do not use for implementation-only requests with already sufficient requirements.
---

# Engineering Specification Writing

## Workflow

1. Inspect the request, existing specifications, drawings, datasheets, models, and repository conventions before asking questions.
2. Classify the design as mechanical, circuit, or integrated, and state the intended maturity: concept, prototype, or production handoff.
3. Separate supplied facts, derived requirements, assumptions, constraints, and unresolved items. Do not silently convert an example or rule of thumb into a requirement.
4. Ask only for missing information that materially changes safety, architecture, interfaces, manufacturing, or acceptance. For low-risk exploratory work, proceed with clearly labeled assumptions.
5. Copy the closest template from `templates/spec/` and replace placeholders. Store the result as:
   - `specs/<project>-spec.md` for a mechanical or circuit design
   - `specs/<project>-integrated-spec.md` for a coupled mechanical/electronic design
6. Give each normative requirement a stable ID. Record the source or rationale, acceptance criterion, and verification method: inspection, analysis, demonstration, or test.
7. Define interfaces with units, coordinate frame, datum, direction, min/nominal/max values, tolerance, and ownership on both sides.
8. Record each TBD/TBR with an owner, resolution action, and due milestone. Do not represent unresolved values as approved.
9. Run the quality gate below and report the remaining assumptions and blocking decisions.

## Quality gate

- Each requirement expresses one obligation and has a unique ID.
- Quantitative limits include units, conditions, and tolerance or min/max bounds.
- Functional requirements state what is needed; implementation choices are constraints only when genuinely required.
- Interface values use the same coordinate system and datum on both sides.
- Every requirement has a feasible success criterion and verification method.
- Safety, regulatory, environmental, and manufacturing claims cite the applicable current source and edition.
- Conflicts, derived values, assumptions, TBDs, and TBRs are visible.
- The requested outputs and release maturity are explicit.

## Readiness

- `Draft`: suitable for exploration; implementation may proceed only with assumptions reported.
- `Review`: major requirements exist, but listed decisions remain open.
- `Approved`: the named reviewer or user has accepted the baseline and its unresolved-item disposition.

Do not require formal approval for harmless concept work the user explicitly asked to explore. Do require a decision before irreversible, safety-critical, compliance-sensitive, or production-release work when an unresolved item can materially change the result.

## References

- Read `references/spec-templates.md` for requirement syntax, traceability, verification planning, and template guidance.
- Read the target design skill's focused references when a requirement depends on a current standard, manufacturing process, component datasheet, or tool capability.
