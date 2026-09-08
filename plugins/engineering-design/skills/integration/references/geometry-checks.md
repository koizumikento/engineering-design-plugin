# Static PCB/enclosure geometry checks

Use a STEP assembly containing both sides of an interface. Resolve PCB origin,
board top/bottom, Z direction, units, component models, and revision before measuring.
Keep the text screening report and geometric evidence separate.

## PCB export and placement

For an existing KiCad 9/10 board, inspect `kicad-cli version` and `kicad-cli pcb
export step --help`, then export using the agreed origin, for example:

```bash
kicad-cli pcb export step --drill-origin -o outputs/pcb.step board.kicad_pcb
```

Use `--user-origin` instead when the interface specifies explicit X/Y coordinates.
Record the origin option and PCB revision. Check the export log and confirm every
required component 3D model is present. A missing model is missing evidence;
`--board-only`, `--no-components`, `--no-dnp`, and variants can change coverage.

Create a build123d source that imports both STEP files and publishes a labeled
`Compound`. Use source-derived translations and rotations, not visual alignment:

```python
from build123d import Compound, Location, import_step

pcb = import_step("outputs/pcb.step")
enclosure = import_step("outputs/enclosure.step")
pcb = pcb.moved(Location(pcb_translation_mm, pcb_rotation_deg))
pcb.label, enclosure.label = "pcb", "enclosure"
result = Compound(children=[pcb, enclosure], label="integration")
```

The two transform variables must come from the interface table. Generate the
common-frame STEP with `scripts/cad_runner.py`, then rediscover selectors with
`scripts/cad_inspect.py refs`. Measure a known datum to verify the placement.

## Executable checks

```bash
uv run python scripts/cad_inspect.py clearance outputs/integration.step --from 'label:pcb' --to 'label:enclosure' --minimum 1.0
```

Supply `--minimum` from the requirement; the value above is an example.
The command computes the true minimum shape distance and positive-volume
intersection. It reports `separated`, `touching`, or `overlapping` plus pass/fail.
Touching passes only when the required gap allows it; overlap fails even with a
zero gap requirement. Exit codes: 0 pass, 1 criterion failure, 2 invalid input.
`--tolerance` is a numerical length tolerance, not a manufacturing allowance.

Only valid solid/component selectors are accepted. A selection and its own child
cannot form an interface pair. Measurements use the imported assembly world frame,
including nested placements. The source STEP is never modified.

`measure --axis distance` measures between reference points; it is **not** the
minimum solid gap. Use `align` for mounting datums and `clearance` for envelopes.
Apply worst-case manufacturing/placement tolerances separately and record the
remaining margin. Static non-interference does not prove containment, insertion
paths, deformation, thermal behavior, EMC, or ingress performance.

## Worked example

In the source repository:

```bash
uv run python scripts/cad_runner.py examples/pcb-enclosure-clearance/src/clearance_assembly.py -o outputs/clearance/ --report --fail-on-check
uv run python scripts/cad_inspect.py refs outputs/clearance/clearance_assembly.step
uv run python scripts/cad_inspect.py clearance outputs/clearance/clearance_assembly.step --from 'label:bottom_component' --to 'label:enclosure' --minimum 1
uv run python scripts/cad_inspect.py clearance outputs/clearance/clearance_assembly.step --from 'label:top_component' --to 'label:lid' --minimum 2
```

Expected minimum gaps are 1 mm below and 2 mm above; both pass. Raising the
bottom requirement to 1.1 mm must fail. The installed plugin does not bundle
repository examples; the commands above are regression examples, not dependencies
of the runtime workflow.

Link each JSON result to its interface ID and retain the input STEP hash,
required gap, numerical tolerance, result, and unsupported checks in the report.

## Official references

- [KiCad 9 CLI](https://docs.kicad.org/9.0/en/cli/cli.html)
- [KiCad 10 CLI](https://docs.kicad.org/10.0/en/cli/cli.html)
- [build123d stable direct API](https://build123d.readthedocs.io/en/stable/direct_api_reference.html) — verified as 0.11.1 on 2026-09-08; confirm the page version before copying an API.
- [build123d v0.11.1 documentation source](https://github.com/gumyr/build123d/tree/v0.11.1/docs)
