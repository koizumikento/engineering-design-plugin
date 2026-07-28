# STR-231 engine-neutral generation contract

This contract is shared by every CadQuery and build123d generation trial. It
defines the observable result; it does not prescribe an API, modeling sequence,
selector syntax, or source-code structure.

## Inputs and isolation

1. A trial receives this contract, exactly one file from `specs/`, and the
   assigned engine name.
2. The trial must not read another case, a reference implementation, a previous
   trial, or an artifact produced by another engine.
3. All dimensions are nominal millimetres. Angles are degrees.
4. A fresh process and output directory must be used for every trial.

## Required deliverables

The trial must create:

- `model.py`: executable source using only the assigned engine and its normal
  runtime dependencies.
- `model.step`: the final result as AP203, AP214, or AP242 STEP.
- `result.json`: UTF-8 JSON containing `engine`, `case_id`, `success`, and
  `repair_round`. When `success` is false it must also contain `error`.

`model.step` is the sole geometry authority. A source assertion, screenshot,
STL mesh, engine-native object, feature name, color, or STEP entity ordering
must never be accepted as evidence that a requirement passed.

## Coordinate and shape rules

- Use a right-handed world coordinate system: +X right, +Y rearward, +Z up.
- The datum and all coordinates are stated explicitly in each specification.
- Do not translate or rotate the completed model before export.
- Closed solids are required. Sheets, shells, meshes, compounds containing
  non-solid members, and duplicate coincident solids fail.
- Touching components intended to be one part must be boolean-fused into one
  solid. Assembly components must remain separate solids.
- Hidden helper geometry must not be exported.
- Chamfers, fillets, draft, text, cosmetic grooves, and other features must not
  be added unless the case explicitly requires them.

## Neutral STEP evaluation

The evaluator must import `model.step` into a geometry kernel independent of
the generating engine and run these checks:

1. STEP import succeeds and every expected component is a valid closed solid.
2. Overall bounding box and solid count match `manifest.json`.
3. Each solid is matched geometrically, never by STEP order or name. A
   multi-solid case is matched by bounding box, then volume.
4. Total and per-solid volume fall within the declared inclusive ranges.
5. Cylindrical faces satisfy the declared axis, radius, and axial span.
   Coaxial face fragments may be aggregated when their union covers the span.
6. Point probes classify as declared. `inside` means strictly inside material;
   `outside` means strictly outside material, including a hole or cavity.
7. Every requirement ID in a specification is represented by at least one
   manifest check.

The default tolerances in `manifest.json` apply unless a check overrides them:

- linear/bounding-box: 0.05 mm
- cylindrical radius: 0.05 mm
- axis direction: 0.1 degrees, with parallel and antiparallel equivalent
- axial endpoints: 0.05 mm
- point classification boundary clearance: 0.20 mm
- volume: the explicit inclusive range in each case

A point within the boundary-clearance tolerance of a face is an evaluator
fixture error, not a generation pass or failure. The supplied probes are
designed to avoid this condition.

## Trial and repair policy

- First submission is evaluated before any repair prompt.
- No manual source or geometry edits are allowed.
- At most two repair rounds may use only the machine-readable failure report.
- The evaluator records first-run pass, final pass, repair count, failure
  categories, elapsed time, and token usage separately.
- A case passes only when every mandatory manifest check passes.
