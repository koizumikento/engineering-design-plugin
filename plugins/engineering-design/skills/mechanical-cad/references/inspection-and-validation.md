# STEP inspection and validation

Use this reference for every generated STEP artifact and whenever a task asks
for geometry references, dimensions, alignment, frames, or before/after
comparison.

## Entrypoint

The repository provides one read-only build123d inspection CLI:

```bash
uv run python scripts/cad_inspect.py \
  {refs|measure|align|frame|diff} ...
```

STEP and STP are the primary inputs. JSON is the default machine-readable
contract. Add `--format text` for a short human summary. The CLI imports and
reads an artifact but never edits the STEP file or source.

## Artifact-local selectors

Discover selectors from the exact artifact before using them:

```bash
uv run python scripts/cad_inspect.py refs outputs/model.step --topology
```

Selector forms are:

```text
#o1                 root occurrence
#o1.2               child occurrence
#o1.2.s1            solid owned by that occurrence
#o1.2.s1.f3         face
#o1.2.s1.e7         edge
```

A single-solid artifact also exposes `#s1`, `#f3`, and `#e7` convenience
aliases. `label:<component-label>` resolves an occurrence only when exactly one
occurrence has that label. A missing or duplicate label is an error.

Selectors are local to one STEP file. They may change after a Boolean, fillet,
topology edit, export from another CAD system, or component-hierarchy change.
Do not store an arbitrary face or edge ordinal as permanent source design
intent. Re-run `refs` after regenerating or changing topology.

Default `refs` output includes:

- occurrence labels, transforms, and topology;
- owned solids;
- major axis-aligned planar faces;
- high-area planar and cylindrical positioning candidates;
- STEP hash, runtime, units, and any matching runner-report provenance.

Use `--topology` only when face or edge selectors are needed.

## Measurement

Measure a selector bounding-box extent:

```bash
uv run python scripts/cad_inspect.py measure outputs/model.step \
  --from '#s1' --extent x --expected 40 --tolerance 0.01
```

Measure between reference points:

```bash
uv run python scripts/cad_inspect.py measure outputs/model.step \
  --from '#o1.s1.f5' --to '#o1.s1.f6' \
  --axis z --expected 12 --tolerance 0.01
```

For a planar face, the point is its center. For a cylindrical face, the point
is the reported axis position. Other references use their center. Axis
measurements are signed `to - from`; `--axis distance` returns Euclidean
distance. Output includes units, expected value, tolerance, delta, and
pass/fail when `--expected` is supplied.

## Read-only alignment

Compute the translation a selected moving reference would need:

```bash
uv run python scripts/cad_inspect.py align outputs/assembly.step \
  --moving '#o1.2.s1.f1' --target '#o1.1.s1.f6' \
  --mode flush --axis z --tolerance 0.01
```

Modes:

- `flush`: two planar faces; returns an axis translation and verifies that
  their normals are parallel;
- `center`: occurrences, solids, faces, or edges; returns the center-to-center
  translation, optionally limited to one axis;
- `coaxial`: two cylindrical faces; returns the transverse translation needed
  to align their parallel axes.

The delta is diagnostic. Apply corrections in build123d source, regenerate,
and re-inspect. This command is not a constraint solver or persistent STEP
mate.

## World frames

Inspect an occurrence or selected geometric reference:

```bash
uv run python scripts/cad_inspect.py frame \
  outputs/assembly.step 'label:lid'
```

The result includes the owning occurrence's world position and orientation,
the selection position, and a planar normal or cylindrical axis when
available. Use it to verify component transforms, axis directions, and
part-local-to-world placement.

## Before/after diff

For modification and repair tasks:

```bash
uv run python scripts/cad_inspect.py diff \
  outputs/before.step outputs/after.step --tolerance 0.01
```

The diff reports:

- bounding-box and volume deltas;
- topology-count deltas;
- added and removed occurrence labels;
- component position and orientation deltas;
- added and removed major-plane signatures.

This is an artifact summary diff, not feature-history reconstruction. Use
specific `measure`, `align`, and `frame` checks for fit-critical invariants.

## Validation sequence

1. Generate STEP with `scripts/cad_runner.py` and require successful reimport.
2. Run `refs` and confirm scale, labels, solids, and positioning candidates.
3. Run `measure` for each specified dimension or clearance that the command can
   represent.
4. Run `align` for flush, centered, or coaxial interfaces.
5. Run `frame` for component transforms and direction-sensitive requirements.
6. Run `diff` for a modification that may affect unrelated geometry.
7. Review previews and convert visual concerns into an applicable deterministic
   check.

Keep `cad_expectations` for source-authored checks that should remain stable
across regenerations, such as envelope, topology counts, and labeled component
positions. Keep selector-based inspection as a separate JSON result because
face and edge selectors are artifact-local. Do not add local topology ordinals
to `cad_expectations`.

## Provenance and limitations

When the STEP sits next to a runner report at
`reports/<step-stem>-cad-summary.json`, inspection output includes the report's
source hash, STEP hash, runtime, units, and whether they match the inspected
artifact. A missing or stale report is not silently treated as matching.

These commands verify geometric facts only. They do not prove tolerance
certification, manufacturability, structural safety, watertightness, fatigue
life, or regulatory compliance.

## Upstream provenance

Adapted to build123d 0.11.1 and this repository's runner from:

- [text-to-cad inspection and validation](https://github.com/earthtojake/text-to-cad/blob/fdbb4b4fb62d95ae298cfe9a46fdc7092bdaf423/skills/cad/references/inspection-and-validation.md)
- [text-to-cad inspect implementation](https://github.com/earthtojake/text-to-cad/tree/fdbb4b4fb62d95ae298cfe9a46fdc7092bdaf423/skills/cad/scripts/inspect)
