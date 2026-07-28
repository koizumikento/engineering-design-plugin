# CAD repair loop

Use this reference when source execution, geometry construction, STEP
validation, expectation checks, or preview generation fails.

## Loop

1. Read the complete failing command and report.
2. Classify the failure before editing.
3. Change the smallest source section responsible for the failure.
4. Rerun the failed command.
5. Rerun every downstream check affected by that change.
6. Regenerate previews when visible geometry changed.
7. Report any remaining unsupported or failed claim.

Do not suppress an exception, weaken an expectation without a specification
change, or export geometry already known to be invalid.

## Failure classes

### Source loading

Symptoms include syntax errors, missing imports, module side effects, or a
missing/unsupported published result.

Check that the module:

- compiles;
- imports only available dependencies;
- publishes a build123d `Shape` or `BuildPart`;
- publishes dictionaries for `cad_metadata` and `cad_expectations` when used.

### Invalid or missing geometry

Check for open profiles, zero or negative dimensions, a subtraction tool that
misses its target, construction geometry returned as the result, and invalid
intermediate solids. Rebuild from the last known valid feature.

### Boolean failure

Avoid coincident tool and target faces. Extend through-cut tools beyond both
target faces, combine repeated tools when practical, and isolate the failing
addition or subtraction in a named intermediate value.

### Fillet or chamfer failure

Apply edge treatments after major additions and cuts. Reduce the radius or
length, narrow the selected edge set, and verify that upstream Boolean
operations did not create tiny unintended edges.

### Scale or envelope mismatch

Check units, radius-versus-diameter mistakes, sign and axis selection,
primitive alignment, extrusion direction, and the documented origin. Compare
the runner's bounding box with the CAD brief.

### Missing or extra feature

Check feature mode, cut depth, pattern count, placement signs, and whether a
later operation removed or fused the feature unexpectedly. Do not rely on an
arbitrary topology index after changing geometry.

### Topology or expectation mismatch

Confirm that the expectation represents the approved design rather than an
obsolete implementation detail. Fix source when the geometry is wrong. Change
the expectation only when the controlling requirement or intended contract
changed.

### Joint or placement mismatch

Check:

- fixed/root versus moving joint direction;
- part-local joint locations and axes;
- explicit `Location` translation and rotation;
- component labels;
- symmetric placement signs;
- assembly hierarchy and expected component bounds.

Regenerate from source. Never patch the exported STEP as the design fix.

### STEP export or reimport failure

Confirm the source BREP is valid, the output path is writable, STEP export
completed, and reimport uses the pinned root runtime. A successful source model
does not override a failed neutral-artifact check.

### Preview failure

Confirm that a valid STEP/STL/source target exists, the suffix is supported,
and the output directory is writable. Retry a single isometric view before the
multi-view packet. If rendering remains unavailable, report it and rely only
on deterministic checks that actually ran.

## Repair scope

For changes that might affect unrelated geometry, compare the before/after
source parameters, runner summaries, expectations, and previews. Until the
dedicated inspection `diff` capability exists, do not claim a geometric diff
that the current runner cannot calculate.

## Unresolved failures

Report:

- the failing class and command;
- the smallest repair attempted;
- which artifact, if any, remains usable;
- which validation claims cannot be made;
- the next source-level correction or missing evidence.

## Provenance

Adapted to this repository's build123d runner from:

- [text-to-cad repair loop](https://github.com/earthtojake/text-to-cad/blob/fdbb4b4fb62d95ae298cfe9a46fdc7092bdaf423/skills/cad/references/repair-loop.md)
