# STR-236: build123d STEP inspection contract

## Status

Accepted.

## Decision

Add `scripts/cad_inspect.py` as the single read-only STEP inspection
entrypoint, with `refs`, `measure`, `align`, `frame`, and `diff` subcommands.
The implementation uses only the pinned root build123d/OCP runtime and does not
vendor `cadpy`, AssemblyHelper, a viewer, or a constraint solver.

`cad_expectations` remains the source-authored contract for checks intended to
survive regeneration. Selector-based inspection stays a separate JSON
contract because STEP face and edge ordinals are artifact-local and can change
after topology edits. A source workflow may preserve inspection JSON as
evidence, but must rediscover selectors after regeneration.

The runner report now records the STEP SHA-256. When an inspection target has a
matching sibling runner report, inspection output carries source hash, STEP
hash, units, runtime, and explicit match flags.

## Selector model

- occurrences: `#o1`, `#o1.2`;
- solids: `#o1.2.s1`;
- faces: `#o1.2.s1.f3`;
- edges: `#o1.2.s1.e7`;
- single-solid aliases: `#s1`, `#f3`, `#e7`;
- unique occurrence labels: `label:<label>`.

Ambiguous and missing selectors fail. Labels distinguish occurrences from
owned shapes; aggregate root topology is not duplicated when child
occurrences own the solids.

## Consequences

- STEP inspection is reproducible inside one artifact and runtime.
- Alignment output is diagnostic and never mutates source or STEP.
- High-level diffs detect unintended envelope, topology, label, transform, and
  major-plane changes without claiming feature-history equivalence.
- Fit-critical requirements still need explicit measurements and tolerances.
- Topology changes require selector rediscovery.
