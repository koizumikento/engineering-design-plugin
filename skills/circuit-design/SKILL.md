---
name: circuit-design
description: Create, revise, execute, and validate SKiDL-based electronic circuit designs, BOM/ERC artifacts, KiCad 9 schematics, and optional ngspice/PySpice analyses. Use for component-level connectivity, power and signal conditioning, interfaces, schematic generation, or simulation planning. Do not use for PCB layout, safety/EMC certification, or production approval without the required downstream evidence.
---

# Circuit Design with SKiDL

## Workflow

1. Inspect the specification, existing SKiDL/KiCad sources, component datasheets, power tree, I/O definitions, and required deliverables. If inputs are incomplete, create a short design brief with operating conditions and clearly labeled assumptions.
2. Define min/nominal/max electrical conditions, startup/fault states, source/load impedances, accuracy/noise/bandwidth goals, environmental limits, and acceptance criteria before selecting values.
3. Select exact manufacturer part numbers when behavior, pinout, package, model, or lifecycle matters. Verify symbol pin numbers, unit mapping, footprint, polarity, ratings, and model provenance against primary documentation.
4. Build explicit SKiDL nets and interfaces. Add stable `tag=` values, named rails, connectors/test points at external boundaries, decoupling, unused-unit treatment, and intentional no-connect or ERC exceptions with rationale.
5. Keep formulas and derived values near named parameters. Check worst-case stress and tolerance, not only nominal arithmetic. Do not reuse cookbook values without validating them against the chosen part and operating conditions.
6. Compile and generate the standard logical artifacts from the repository root:

   ```bash
   uv run python -m py_compile <input.py>
   uv run python skills/circuit-design/scripts/skidl_runner.py <input.py> -o <outputs/>
   ```

7. Generate a KiCad 9 schematic with the repository exporter when its topology is supported:

   ```bash
   uv run python skills/circuit-design/scripts/kicad_sch_export.py <input.py> -o <outputs/>
   ```

   Current SKiDL also provides `generate_schematic()` for KiCad schematics. Prefer that native path for general circuits when it produces a readable result, and treat the repository exporter as a tested compatibility path rather than claiming universal coverage.
8. If `kicad-cli` is available, validate the generated schematic independently:

   ```bash
   kicad-cli sch erc --exit-code-violations --format json -o <outputs/reports/project-kicad-erc.json> <outputs/kicad/project/project.kicad_sch>
   ```

9. Run only the analyses required by the specification. Use models whose source, version, pin order, and applicability are recorded:

   ```bash
   uv run python skills/circuit-design/scripts/pyspice_sim.py <input.py> -o <outputs/> --dc
   uv run python skills/circuit-design/scripts/pyspice_sim.py <input.py> -o <outputs/> --ac
   uv run python skills/circuit-design/scripts/pyspice_sim.py <input.py> -o <outputs/> --tran
   ```

10. Compare ERC and simulation results with explicit acceptance criteria. Report unmodeled behavior, convergence changes, datasheet dependencies, remaining warnings, and downstream PCB/layout/thermal/EMC work.

## Deliverables and source ownership

- SKiDL Python: logical connectivity and parameterized design definition.
- KiCad `.kicad_sch`/`.kicad_pro`: review and PCB-handoff artifact; do not edit it independently without deciding how changes return to SKiDL.
- BOM: procurement-oriented fields should include manufacturer and MPN when available; a symbol/value-only BOM is preliminary.
- Netlist: generate only when a downstream tool explicitly requires it; modern KiCad does not require a legacy netlist for its normal schematic-to-PCB flow.
- Simulation: evidence for the modeled scenarios only, not proof of hardware compliance.

## Reference routing

- `references/skidl-api.md`: SKiDL 2.2/KiCad 9 patterns, Circuit ownership, tags, ERC, and outputs.
- `references/kicad-v9-workflow.md`: native schematic validation, CLI ERC/BOM, and source-of-truth rules.
- `references/circuit-patterns.md`: design-review checklists and equations for common circuit classes.
- `references/spice-guide.md`: model provenance, analysis selection, corners, measurements, and convergence.
