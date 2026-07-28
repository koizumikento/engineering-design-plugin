# CAD brief

Use this reference before writing or changing build123d source. The brief is an
internal working note, not a form that the user must complete.

## Purpose

Reduce ambiguity before modeling by recording the design inputs, controlling
dimensions, coordinate system, output paths, and checks that will decide
whether the result is acceptable.

Classify the request as one of:

- new part;
- new assembly;
- modification of an existing source;
- inspection or explanation of an existing artifact;
- export of an already validated design.

## Input precedence

Use the most authoritative dimensioned source available:

1. approved specification;
2. current manufacturer drawing or model;
3. applicable standard;
4. dimensioned technical drawing supplied for the task;
5. measured value;
6. explicitly labeled estimate.

An image without a stated scale communicates appearance and feature intent,
not dimensions. If one reliable dimension is present, other proportions may
be estimated for a concept model and must be recorded as assumptions.

When prose, drawings, and models disagree:

- prefer dimensioned information over visual proportions;
- do not silently choose between conflicting dimensioned sources;
- record the conflicting values, sources, and affected feature;
- ask one focused question when the conflict changes fit, safety, interfaces,
  compliance, or whether the model can be built.

## Reading technical drawings

Before extracting dimensions, identify:

- units, revision, projection convention, and general notes;
- front, top, side, section, detail, and isometric views;
- datum features and the model axes represented by each view;
- multiplicity and typical-feature notation;
- hole, counterbore, countersink, thread, depth, and tolerance callouts.

Use section and detail views for internal features. Convert every controlling
callout into a named source parameter and, when the current runner can measure
it, a `cad_expectations` check. Record unsupported checks as not yet verified
rather than treating them as passing.

## Brief content

Keep the brief concise:

```text
CAD brief:
- Model and task type:
- Inputs and revisions:
- Units:
- Coordinate convention:
- Manufacturing intent:
- Overall envelope:
- Functional features:
- Positioning and mating datums:
- Source and output paths:
- Validation targets:
- Assumptions:
- Conflicts or unresolved items:
```

For a modification, add:

```text
- Intended change:
- Geometry that must remain unchanged:
- Before/after evidence:
```

For an assembly, add:

```text
- Fixed/root component:
- Child labels:
- Part-local frames:
- Mating faces or axes:
- Required static placement or motion pose:
```

## Ready-to-model gate

Start implementation when the brief establishes:

- a source path and requested output paths;
- units and a local coordinate convention;
- named controlling parameters;
- the part/assembly boundary and feature plan;
- expected topology, envelope, labels, or component placement;
- meaningful assumptions and unresolved risks.

Missing low-risk cosmetic values may remain assumptions. Missing fit-critical,
safety-critical, pressure-bearing, medical, or compliance information must not
be invented.

## Provenance

Adapted for this repository's build123d runner from:

- [text-to-cad CAD brief](https://github.com/earthtojake/text-to-cad/blob/fdbb4b4fb62d95ae298cfe9a46fdc7092bdaf423/skills/cad/references/cad-brief.md)
