# STR-229: build123d unification

- Status: Accepted
- Date: 2026-07-28
- Decision: use build123d as the only production mechanical CAD engine
- Linear: [STR-229](https://linear.app/straydev/issue/STR-229/phase-2-機械cad基盤をbuild123dへ統一する)
- Supersedes: [STR-232](STR-232-assembly-routing.md)

## Context

STR-231 found no generation-accuracy difference between CadQuery and build123d.
STR-232 initially used that result to retain CadQuery for parts while adopting
build123d for assemblies. That created permanent duplication in dependencies,
runners, references, examples, templates, tests, and agent routing.

The user selected management simplicity over backward compatibility and
explicitly removed existing CadQuery compatibility from scope.

## Decision

Production mechanical CAD uses:

- Python 3.11.x;
- build123d 0.11.1;
- `build123d_occt` as the repository-facing name for build123d's OCCT binding;
- root `pyproject.toml` and `uv.lock`;
- `scripts/cad_runner.py` for parts and assemblies;
- `scripts/preview_generator.py` for STEP/STL/source previews;
- build123d-only skill instructions, references, examples, and templates.

There is no production engine router or CadQuery fallback. Historical
CadQuery/build123d material under `pocs/build123d-migration/` remains evidence,
not a supported workflow.

## Model contract

A source module publishes a build123d `Shape` as `result`. Assemblies use a
labeled `Compound`. The module may publish `cad_metadata` and
`cad_expectations`. The runner validates source BREP, exports STEP/STL,
reimports STEP, checks bbox/topology/component labels and transforms, evaluates
expectations, and records source/runtime provenance.

## Consequences

- One production Python/OCCT environment and one mechanical runner.
- Reports and source use `build123d_occt`; upstream distribution names are
  confined to the generated dependency lock.
- No compatibility guarantee for former CadQuery source or commands.
- Python support narrows to 3.11.x.
- STEP remains the engine-neutral handoff to preview and integration.
- PoC benchmarks remain reproducible only through their own historical setup.

## Verification

- `tests/test_build123d_production.py`
- all production mechanical examples and templates execute through the same root runner
- source and reimported STEP BREP checks
- source expectations for topology, envelope, labels, and component placement
- STEP preview smoke test
