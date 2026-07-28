---
name: mechanical-cad
description: Create, revise, execute, and validate parametric mechanical designs in build123d, including parts, enclosures, brackets, shafts, fixtures, assemblies, and PCB-housing geometry. Use when the requested deliverable includes CAD Python, STEP/STL exports, dimensional checks, or rendered geometry. Do not use for requirements-only work or for certifying manufacturability without process-specific evidence.
---

# Mechanical CAD with build123d

## Workflow

1. Inspect the specification, mating-part drawings/models, existing code, and required output formats. If no specification exists, write a compact internal CAD brief containing purpose, maturity, units, manufacturing process, envelope, datums, interfaces, acceptance criteria, and assumptions.
2. Establish the coordinate convention before modeling. Default only when unspecified: millimetres, XY base plane, +Z up, and a documented origin.
3. Separate controlling parameters from derived dimensions. Name datums, mating planes, hole patterns, keep-out envelopes, and clearances. Do not scatter magic numbers through geometry operations.
4. Select dimensions from the controlling source in this order: approved specification, manufacturer drawing/model, applicable standard, measured value, then explicitly labeled estimate. Never treat a generic clearance, wall, fillet, or fastener table as universally valid.
5. Choose the build123d API style:
   - Prefer Algebra mode for explicit solids, Boolean expressions, transforms, and compact parametric parts.
   - Use Builder mode when sketch/workplane context, repeated placement, or last-operation selection makes construction clearer.
   - Both styles may coexist, but the module must publish one final build123d `Shape`.
6. Create closed positive-volume solids. For assemblies, return a labeled `Compound` whose direct children have stable functional labels and explicit `Location` or source-level joint placement.
7. Publish `result`, optional `cad_metadata`, and specification-derived `cad_expectations`. Keep build123d Python as the parametric design definition and STEP as the primary neutral exchange artifact.
8. Compile and execute from the repository root:

   ```bash
   uv run python -m py_compile <input.py>
   uv run python scripts/cad_runner.py \
     <input.py> -o <outputs/> --report --fail-on-check
   ```

9. For a new model or visible geometry change, generate multiple views from the STEP artifact and inspect them:

   ```bash
   uv run python scripts/preview_generator.py \
     <outputs/model.step> -o <outputs/> --all-views
   ```

10. Compare the report's STEP reimport validity, bounding box, volume, centre of mass, topology counts, component labels/transforms, and expectation checks with the specification.
11. Report generated artifacts, checks performed, deviations, assumptions, and any manufacturing or compliance claim that remains unverified.

## Validation rules

- Require valid BREP geometry for every final solid and for the exported/reimported STEP; validity alone does not prove dimensional correctness or manufacturability.
- Verify critical dimensions against `cad_expectations` or independent measured geometry.
- Inspect minimum wall/feature sizes, tolerance stack, fit, assembly sequence, and process-specific constraints.
- Set STL tessellation deliberately for the part scale and use; do not use a mesh as the dimensional source of truth.
- Treat build123d joints as source-level placement operations. Do not claim that exported STEP preserves a live constraint.
- Do not hide source execution, Boolean, fillet, STEP reimport, label, or expectation failures.
- Do not claim an IP rating, load capacity, fatigue life, thermal performance, or production readiness without the corresponding analysis/test evidence.
- If requested source data is missing, model a conservative envelope only when useful and label it as provisional.

## Reference routing

- `references/build123d-api.md`: API modes, source contract, modeling patterns, labels, joints, exports, and runner.
- `references/assembly-positioning.md`: datums, transforms, tolerance stacks, mating and motion/service envelopes.
- `references/export-policy.md`: STEP, STL/3MF, DXF/SVG, and preview usage.
- `references/off-the-shelf-parts.md`: manufacturer CAD/drawing provenance and simplified envelopes.
- `references/jis-drawing.md`: current JIS source map and limits on making standards claims.
- `references/templates.md`: small reusable build123d patterns; adapt and test them rather than copying dimensions blindly.
