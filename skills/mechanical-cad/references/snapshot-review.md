# Snapshot review

Use this reference after generating a new STEP artifact or changing visible
geometry.

## Policy

Preview review complements deterministic geometry checks. It can reveal
missing features, reversed placement, unexpected proportions, or an
unintended opening, but an image alone does not prove a dimension or fit.

Generate and inspect a preview whenever valid visible geometry was created or
changed:

```bash
uv run python scripts/preview_generator.py \
  <outputs/model.step> -o <outputs/> --view iso
```

Use the multi-view packet when the model has semantic or hidden-geometry risk:

```bash
uv run python scripts/preview_generator.py \
  <outputs/model.step> -o <outputs/> --all-views
```

The current packet contains isometric, front, top, and right views.

## Choosing views

One isometric view is normally enough for a simple static part with features
on one main plane.

Use all views for:

- assemblies or multiple labeled components;
- holes, slots, or bosses on more than one axis;
- shells, internal cavities, bores, or open enclosures;
- repeated patterns, ribs, gussets, standoffs, or cutouts;
- a repair following Boolean, fillet, placement, or geometry failure;
- reference-image reproduction or any task where visible form is an
  acceptance concern.

The renderer does not currently create section or exploded views. Do not claim
that hidden geometry was reviewed when the available views cannot show it.
Use topology, bounding-box, component-placement, and `cad_expectations`
evidence for the checks the runner supports.

## Skip conditions

A saved preview may be skipped only when:

- no visible geometry changed;
- the task only reads or explains an existing artifact;
- source execution or STEP generation failed before a valid artifact existed.

Report the skip reason and the deterministic evidence that was still
available. Do not skip a preview merely because the BREP and expectations
passed.

## Converting visual findings

Treat visual review as diagnosis:

- apparent pattern asymmetry -> check controlling offsets and expectations;
- an offset component -> use `cad_inspect.py frame` and check its transform;
- a missing feature -> check topology and the corresponding named parameter;
- a suspicious cavity or through-hole -> discover a local selector and use
  `cad_inspect.py measure`, or report that the dimension is not independently
  verified;
- an apparently misaligned interface -> use `cad_inspect.py align`;
- unexpected proportions -> compare the report envelope with the CAD brief.

Change source, regenerate STEP, rerun the failed deterministic checks, and
create a new preview only when the repair changed visible geometry.

## Reporting

State:

- which preview files and views were reviewed;
- any visual concern found;
- which deterministic result supports its resolution;
- any hidden or unsupported geometry that remains unverified.

## Provenance

Adapted to the repository's current preview capabilities from:

- [text-to-cad snapshot review](https://github.com/earthtojake/text-to-cad/blob/fdbb4b4fb62d95ae298cfe9a46fdc7092bdaf423/skills/cad/references/snapshot-review.md)
