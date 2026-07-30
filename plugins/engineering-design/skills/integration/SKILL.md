---
name: integration
description: Validate mechanical-electrical interfaces between a PCB, enclosure, connectors, controls, cables, thermal features, and mounting hardware. Use when checking board-to-enclosure fit, coordinate transforms, mounting alignment, keep-outs, access, assembly/service envelopes, or interface traceability. Do not use a text-only screening result as proof of full 3D interference, thermal, EMC, ingress, or compliance performance.
---

# PCB-Enclosure Integration

## Workflow

1. Collect the integrated specification, PCB outline/stackup, mounting-hole coordinates, component and connector envelopes, enclosure geometry, hardware drawings, cable bend/service envelopes, and applicable acceptance criteria.
2. Define one assembly coordinate frame and transform every PCB and enclosure datum into it. Record axis directions, origin, units, board side, and reference surfaces; do not compare unlabeled coordinate pairs.
3. Build an interface control table with stable IDs. For each interface record both owners, source revision, nominal geometry, tolerance, required clearance/alignment, verification method, and evidence.
4. Run the text-spec screening check when the specification contains machine-readable dimensions:

   ```bash
   uv run python scripts/integration_checker.py <specs/project-integrated-spec.md> -o <outputs/> --json
   ```

   Pass `--clearance` and `--tolerance` only from the approved requirement or documented process assumption. The checker is a screening tool; missing data or unsupported checks must remain visible and must not become a pass.
5. When STEP/BREP/board 3D data is available, perform geometric checks in the common frame: containment, minimum gap, mounting alignment, connector/opening overlap, component-to-lid/wall clearance, fastener/tool access, cable and user-access envelopes, and assembly path.
6. Review non-geometric interfaces: power/grounding, heat path, airflow, sealing surfaces, vent/sensor exposure, ESD/EMC features, labeling, serviceability, and manufacturing sequence. Route specialist analysis or testing where required.
7. Classify every result as pass, fail, conditional, or not evaluated. Link it to the requirement and evidence; do not collapse unknowns into a single overall pass.
8. Produce `outputs/<project>-integration-report.md` with assumptions, source revisions, coordinate convention, margins, conflicts, unsupported checks, and corrective actions.

## Minimum checks

- PCB outline and thickness versus enclosure and insertion path.
- Mounting-hole/boss position, diameter, fastener stack, and tolerance accumulation.
- Top-side and bottom-side component envelopes versus lid, floor, walls, and hardware.
- Connector datum and opening size, including plug shell, latch, finger/tool access, and cable bend radius.
- Controls, indicators, antennas, sensors, vents, and exposed surfaces.
- Assembly order, removable parts, screw/tool approach, rework and service access.
- Heat sources, heat paths, airflow obstruction, and temperature-sensitive parts.
- Sealing path and penetrations when an ingress requirement exists; rating requires the applicable test evidence.

## Reference routing

- Read `references/interface-spec.md` for coordinate frames, interface tables, tolerance stacks, envelopes, verification methods, and current standards-source guidance.
- Read the mechanical and circuit references for process-specific geometry, exact component data, schematic boundaries, or simulation evidence.
