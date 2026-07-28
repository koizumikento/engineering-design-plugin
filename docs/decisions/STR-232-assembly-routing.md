# STR-232: CadQuery parts / build123d assemblies routing

- Status: Superseded by STR-229
- Date: 2026-07-28
- Decision: Historical scoped-routing decision; replaced by build123d unification
- Linear: [STR-232](https://linear.app/straydev/issue/STR-232/phase-2a-機械cadを用途別ルーティングしアセンブリのみbuild123dを採用する)

## Context

STR-228 established that both CadQuery and build123d can produce equivalent
neutral STEP geometry. STR-231 then measured 60 independent agent generations
and found no first-run accuracy or repair-count advantage for build123d. That
evidence does not justify replacing the working CadQuery part workflow.

The `earthtojake/text-to-cad` review identified a narrower advantage:
build123d exposes native labeled shapes, explicit `Location`/`Axis` objects and
source-level joints that suit assemblies whose intent is expressed as
relationships between part-local datums. Its surrounding `cadpy` runtime is
designed around those objects; the published material does not demonstrate a
CadQuery-vs-build123d generation-accuracy benchmark.

## Decision

The production mechanical CAD skill uses deterministic routing:

| Design intent | Engine |
|---|---|
| Monolithic part or single manufactured body | CadQuery |
| Static geometry without meaningful inter-part relationships | CadQuery |
| Separately manufactured, purchased, or movable parts placed by named datums, transforms, or joints | build123d |
| Multi-solid intermediate without assembly semantics | CadQuery |

The agent selects one route before modeling. Failure does not trigger an
implicit engine fallback.

## Historical production boundary

STR-232 originally used a skill-local build123d runtime and runner to coexist
with the root engine. Those paths were removed by STR-229. Current production
uses root `pyproject.toml`, root `uv.lock`, and `scripts/cad_runner.py`;
STR-228/STR-231 PoC runners remain evaluation-only.

A build123d assembly source publishes:

- a labeled `Shape`, normally a `Compound`;
- `cad_metadata` describing units, coordinates and source relationships;
- `cad_expectations` for topology, envelope and component placement.

The runner validates source geometry, exports STEP/STL, reimports STEP, checks
direct-child labels and resolved transforms, evaluates expectations, and
records source/runtime provenance.

## STEP semantics

build123d joints are source-level one-time placement operations. The STEP
artifact must preserve the resolved static geometry, occurrence labels and
transforms. It is not claimed to preserve a live editable joint constraint.

## Consequences

This decision was implemented briefly, then superseded by the user's explicit
choice to avoid permanent dual-engine management. STR-229 removes routing,
the isolated runtime, and production CadQuery compatibility in favor of one
root build123d environment and one runner.

See [STR-229 decision](STR-229-build123d-unification.md).

## Evidence

- [STR-228 decision](STR-228-build123d-migration.md)
- [STR-231 benchmark](STR-231-agent-generation-benchmark.md)
- `examples/build123d-enclosure-assembly/`
- `tests/test_build123d_production.py`
- [text-to-cad CAD skill](https://github.com/earthtojake/text-to-cad/blob/main/skills/cad/SKILL.md)
- [text-to-cad AssemblyHelper](https://github.com/earthtojake/text-to-cad/blob/main/packages/cadpy/src/cadpy/assembly.py)
- [build123d advantages over CadQuery](https://build123d.readthedocs.io/en/latest/introduction.html#advantages-over-cadquery)
- [build123d joints](https://build123d.readthedocs.io/en/latest/joints.html)
