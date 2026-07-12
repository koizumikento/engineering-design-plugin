# Engineering Design Skills Architecture

## Objective

自然言語要望から、traceable requirements、parametric design artifacts、tool-based checks、evidence-backed handoffを一貫して生成する。スキルは専門家の承認、規格本文、試験、製造工程能力を代替しない。

## Design principles

1. `skills/` is the source of truth.
2. `SKILL.md` keeps only core workflow and routing; detailed knowledge lives in focused `references/`.
3. Facts, requirements, design choices, assumptions, and unresolved items remain distinguishable.
4. Every normative requirement connects to an acceptance criterion, verification method, and evidence.
5. Generic rules of thumb never masquerade as standards or component-specific values.
6. Generated artifacts are independently parsed, measured, or inspected when the toolchain allows it.
7. Missing or unsupported integration data remains `NOT_EVALUATED`, not `PASS`.

## End-to-end flow

```text
request / source artifacts
          |
          v
spec-writing: IDs, sources, interfaces, acceptance, verification
          |
          +--------------------+
          |                    |
          v                    v
mechanical-cad             circuit-design
CadQuery/STEP/report       SKiDL/KiCad/BOM/ERC/SPICE
          |                    |
          +----------+---------+
                     v
integration: common frame, tolerance, envelope, evidence
                     |
                     v
PASS / FAIL / CONDITIONAL / NOT EVALUATED + next evidence
```

Concept work may proceed with visible assumptions. Production, safety, compliance, or irreversible work requires resolution of decisions that materially affect the result.

## Skill contracts

### `spec-writing`

Input:

- natural-language need
- existing spec/drawing/datasheet/model when present

Output:

- `specs/<project>-spec.md`
- `specs/<project>-integrated-spec.md`

Required structure:

- document maturity and status
- stable requirement/interface IDs
- source or rationale
- units, conditions, tolerances/limits
- assumptions/TBD/TBR with owner and resolution
- verification matrix

### `mechanical-cad`

Input:

- approved spec or internal CAD brief
- mating-part source geometry/drawings
- manufacturing and output requirements

Outputs:

- CadQuery Python
- STEP primary neutral geometry
- purpose-specific STL/3MF/DXF/SVG/PNG
- CAD summary JSON

Checks:

```bash
uv run python -m py_compile input.py
uv run python scripts/cadquery_runner.py input.py -o outputs/ --report --fail-on-invalid
uv run python scripts/preview_generator.py outputs/input.step -o outputs/ --all-views
```

Shape validity, dimensions, topology, visible geometry, assembly transform, tolerance stack, and process-specific constraints are separate checks.

### `circuit-design`

Input:

- electrical requirements and interfaces
- exact component sources when part-specific behavior matters

Outputs:

- SKiDL Python as logical design definition
- BOM, SKiDL ERC and design summary
- KiCad 9 schematic/project for review and PCB handoff
- optional netlist and simulation evidence

Checks:

```bash
uv run python -m py_compile input.py
uv run python skills/circuit-design/scripts/skidl_runner.py input.py -o outputs/
uv run python skills/circuit-design/scripts/kicad_sch_export.py input.py -o outputs/
kicad-cli sch erc --exit-code-violations --format json -o outputs/reports/project-kicad-erc.json outputs/kicad/project/project.kicad_sch
```

The custom exporter has bounded topology coverage. SKiDL native `generate_schematic()` is a current alternative. Both require visual and KiCad ERC review.

### `integration`

Input:

- integrated spec and interface table
- PCB/enclosure/component geometry and revisions when available
- acceptance thresholds from requirements

Output:

- `outputs/<project>-integration-report.md`

Text screening:

```bash
uv run python scripts/integration_checker.py specs/project-integrated-spec.md -o outputs/ --json
```

The checker evaluates parsed nominal dimensions only. 3D collision/minimum-gap, dynamic/service envelopes, worst-case tolerance, thermal, EMC/ESD, vibration, ingress, and compliance require additional methods.

## Artifact ownership

| Artifact | Role |
|---|---|
| specification Markdown | requirements/interface baseline |
| CadQuery Python | parametric mechanical definition |
| STEP | neutral mechanical exchange and integration geometry |
| SKiDL Python | logical circuit definition |
| KiCad schematic/project | readable ECAD review and PCB handoff |
| STL/3MF/DXF/SVG/PNG | purpose-specific derivatives |
| JSON/CSV/plots/reports | verification evidence with stated scope |

Do not edit two supposed sources of truth independently. If generated KiCad or CAD exchange data becomes the editable master, record the transition and reverse-flow plan.

## Reference policy

- Prefer current official documentation, manufacturer datasheets/models, standards bodies, and approved process guides.
- Record version/revision and retrieval date for unstable sources.
- Do not copy paid standards tables into the repo.
- Label calculations and inferences separately from source facts.
- Cite exact MPN documentation for pinout, footprint, thermal, stability, opening, and mating geometry.

Current source families used by references include CadQuery official docs, SKiDL official docs, KiCad 9 docs, ngspice/PySpice docs, NASA Systems Engineering Handbook, and JSA/IEC official standards catalogs.

## Plugin packaging

```text
.agents/plugins/marketplace.json
  source.path -> ./plugins/engineering-design

plugins/engineering-design/.codex-plugin/plugin.json
  skills -> ./../../skills/
```

`plugins/engineering-design/skills/` and `.agents/plugins/engineering-design/skills/` copies are intentionally absent. The repo-local marketplace and plugin package point to the committed `skills/` source of truth.

Plugin metadata is presentation/install information only. Operational instructions stay in `skills/*/SKILL.md`; UI metadata stays in `skills/*/agents/openai.yaml`.

## Validation

For every skill change:

1. validate all skill folders with `quick_validate.py`;
2. check reference links and repository-relative paths;
3. compile changed Python scripts;
4. execute affected helper entrypoints against representative examples;
5. inspect generated reports/artifacts;
6. verify plugin manifest and marketplace JSON structure;
7. review `git diff` for unintended copied workflow logic.
