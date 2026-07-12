---
name: mechanical-cad
description: Create, revise, execute, and validate parametric mechanical designs in CadQuery, including enclosures, brackets, shafts, fixtures, assemblies, and PCB-housing geometry. Use when the requested deliverable includes CadQuery Python, STEP/STL/DXF/SVG exports, dimensional checks, or rendered geometry. Do not use for requirements-only work or for certifying manufacturability without process-specific evidence.
---

# Mechanical CAD with CadQuery

## Workflow

1. Inspect the specification, mating-part drawings/models, existing code, and required output formats. If no specification exists, write a compact internal CAD brief containing purpose, maturity, units, manufacturing process, envelope, datums, interfaces, acceptance criteria, and assumptions.
2. Establish the coordinate convention before modeling. Default only when unspecified: millimetres, XY base plane, +Z up, and a documented assembly origin.
3. Separate design parameters from derived dimensions. Name datums, mating planes, hole patterns, keep-out envelopes, and clearances. Do not scatter magic numbers through selectors or Boolean operations.
4. Select dimensions from the controlling source in this order: approved specification, manufacturer drawing/model, applicable standard, measured value, then explicitly labeled estimate. Never treat a generic clearance, wall, fillet, or fastener table as universally valid.
5. Create a closed positive-volume solid or a named `cq.Assembly`. Prefer stable construction geometry and selectors tied to datums over fragile topology order such as an unexplained `edges()[3]`.
6. Keep the CadQuery Python source as the parametric design definition. Treat STEP as the primary neutral geometry exchange artifact and mesh/2D/image formats as purpose-specific derivatives.
7. Compile and execute from the repository root:

   ```bash
   uv run python -m py_compile <input.py>
   uv run python scripts/cadquery_runner.py <input.py> -o <outputs/> --report --fail-on-invalid
   ```

8. For a new model or visible geometry change, generate multiple views and inspect them:

   ```bash
   uv run python scripts/preview_generator.py <outputs/model.step> -o <outputs/> --all-views
   ```

9. Compare the report's bounding box, volume, centre of mass, topology counts, and exported files with the specification. For assemblies, also check transforms, mating faces, fastener/tool access, cable/service envelopes, and collisions using available component geometry.
10. Report generated artifacts, checks performed, deviations, assumptions, and any manufacturing or compliance claim that remains unverified.

## Validation rules

- Require `isValid()` for every final solid; validity alone does not prove dimensional correctness or manufacturability.
- Verify critical dimensions independently from the same parameters or measured geometry.
- Inspect minimum wall/feature sizes, tolerance stack, fit, assembly sequence, and process-specific constraints.
- Set STL/3MF tessellation deliberately for the part scale and use; do not use a mesh as the dimensional source of truth.
- Do not claim an IP rating, load capacity, fatigue life, thermal performance, or production readiness without the corresponding analysis/test evidence.
- If the requested source data is missing, model a conservative envelope only when useful and label it as provisional.

## Reference routing

- `references/cadquery-api.md`: current CadQuery patterns, selectors, assemblies, exports, and validation.
- `references/assembly-positioning.md`: datums, transforms, tolerance stacks, mating and motion/service envelopes.
- `references/export-policy.md`: STEP, STL/3MF, DXF/SVG, and preview usage.
- `references/off-the-shelf-parts.md`: manufacturer CAD/drawing provenance and simplified envelopes.
- `references/jis-drawing.md`: current JIS source map and limits on making standards claims.
- `references/templates.md`: small reusable modeling patterns; adapt and test them rather than copying dimensions blindly.
