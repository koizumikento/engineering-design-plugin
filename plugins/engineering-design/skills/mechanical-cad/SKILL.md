---
name: mechanical-cad
description: Create, revise, execute, and validate parametric mechanical designs in build123d, including parts, enclosures, brackets, shafts, fixtures, assemblies, and PCB-housing geometry. Use when the requested deliverable includes CAD Python, STEP/STL exports, dimensional checks, or rendered geometry. Do not use for requirements-only work or for certifying manufacturability without process-specific evidence.
---

# Mechanical CAD with build123d

## Workflow

1. Inspect the specification, prose, reference images, technical drawings/models, existing code, and requested outputs. Classify the task as a new part, assembly, modification, inspection, or export.
2. Write a compact internal CAD brief using `references/cad-brief.md`. Record inputs/revisions, units, coordinate convention, manufacturing intent, controlling dimensions, features, datums, paths, validation targets, assumptions, and conflicts before modeling.
3. Prefer dimensioned evidence over image proportions. If two dimensioned sources conflict, report the conflict instead of silently choosing. Ask one focused question only when the conflict affects feasibility, fit, safety, interfaces, or compliance.
4. Establish the coordinate convention before modeling. Default only when unspecified: millimetres, XY base plane, +Z up, and a documented origin.
5. Separate controlling parameters from derived dimensions. Name datums, mating planes, hole patterns, keep-out envelopes, and clearances. Do not scatter magic numbers through geometry operations.
6. Select dimensions from the controlling source in this order: approved specification, manufacturer drawing/model, applicable standard, dimensioned task drawing, measured value, then explicitly labeled estimate. Never treat a generic clearance, wall, fillet, or fastener table as universally valid.
7. Choose the build123d API style:
   - Prefer Algebra mode for explicit solids, Boolean expressions, transforms, and compact parametric parts.
   - Use Builder mode when sketch/workplane context, repeated placement, or last-operation selection makes construction clearer.
   - Both styles may coexist, but the module must publish one final build123d `Shape`.
8. Create closed positive-volume solids. For assemblies, return a labeled `Compound` whose direct children have stable functional labels and explicit `Location` or source-level joint placement.
9. Publish `result`, optional `cad_metadata`, and specification-derived `cad_expectations`. Convert every controlling dimension supported by the current contract into a check; report unsupported checks as not independently verified.
10. Compile and execute from the repository root:

   ```bash
   uv run python -m py_compile <input.py>
   uv run python scripts/cad_runner.py \
     <input.py> -o <outputs/> --report --fail-on-check
   ```

11. Inspect every generated STEP with `references/inspection-and-validation.md`. Run `refs` as the baseline, then use `measure`, `align`, `frame`, and `diff` for specification-driven facts, interfaces, transforms, and modification invariants. Rediscover artifact-local selectors after topology changes.
12. For a new model or visible geometry change, review the STEP preview according to `references/snapshot-review.md`. Use one isometric view for a simple part and all views for assemblies, hidden-geometry risk, multi-axis features, or repairs:

   ```bash
   uv run python scripts/preview_generator.py \
     <outputs/model.step> -o <outputs/> --all-views
   ```

13. Compare the report's STEP reimport validity, bounding box, volume, centre of mass, topology counts, component labels/transforms, expectations, and inspection results with the CAD brief and specification. Convert visual concerns into supported deterministic checks before treating them as resolved.
14. If any stage fails, use `references/repair-loop.md`: classify it, make the smallest responsible source change, and rerun the failed and dependent checks.
15. Report generated artifacts, local selectors used, preview files reviewed or the documented skip reason, checks performed, deviations, assumptions, unsupported checks, and any manufacturing or compliance claim that remains unverified.

## Validation rules

- Require valid BREP geometry for every final solid and for the exported/reimported STEP; validity alone does not prove dimensional correctness or manufacturability.
- Verify critical dimensions against `cad_expectations` or independent measured geometry.
- Inspect minimum wall/feature sizes, tolerance stack, fit, assembly sequence, and process-specific constraints.
- Set STL tessellation deliberately for the part scale and use; do not use a mesh as the dimensional source of truth.
- Treat build123d joints as source-level placement operations. Do not claim that exported STEP preserves a live constraint.
- Treat `scripts/cad_inspect.py align` as a read-only diagnostic. Apply placement corrections in source and regenerate STEP.
- Treat face and edge selectors as artifact-local. Do not preserve arbitrary topology ordinals as source design intent.
- Do not hide source execution, Boolean, fillet, STEP reimport, label, or expectation failures.
- Do not use a preview image as dimensional proof. Tie visual findings to runner evidence or report them as unverified.
- Do not claim an IP rating, load capacity, fatigue life, thermal performance, or production readiness without the corresponding analysis/test evidence.
- If requested source data is missing, model a conservative envelope only when useful and label it as provisional.

## Reference routing

- `references/cad-brief.md`: input precedence, drawings/images, conflicts, assumptions, and pre-modeling validation targets.
- `references/build123d-api.md`: API modes, source contract, modeling patterns, labels, joints, exports, and runner.
- `references/inspection-and-validation.md`: STEP-local refs, measurements, read-only alignment, world frames, diffs, and provenance.
- `references/assembly-positioning.md`: datums, transforms, tolerance stacks, mating and motion/service envelopes.
- `references/snapshot-review.md`: required preview review, packet sizing, skip conditions, and visual-to-deterministic checks.
- `references/repair-loop.md`: failure classification, minimal source repair, dependent reruns, and unresolved reporting.
- `references/export-policy.md`: STEP, STL/3MF, DXF/SVG, and preview usage.
- `references/off-the-shelf-parts.md`: manufacturer CAD/drawing provenance and simplified envelopes.
- `references/jis-drawing.md`: current JIS source map and limits on making standards claims.
- `references/templates.md`: small reusable build123d patterns; adapt and test them rather than copying dimensions blindly.
