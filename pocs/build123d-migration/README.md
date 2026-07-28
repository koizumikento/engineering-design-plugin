# build123d migration PoC

This directory is the isolated proof of concept for Linear issue `STR-228`.
It does not change the repository's production CAD engine.

The PoC compares equivalent CadQuery and build123d models through exported
STEP artifacts. The root project owns the CadQuery execution environment; this
nested project owns the pinned build123d environment so their OCCT packages do
not conflict.

## Environments

- CadQuery baseline: repository root `pyproject.toml` and `uv.lock`
- build123d candidate: this directory's `pyproject.toml`, `.python-version`, and
  `uv.lock`

## Representative models

- calibration block
- L-bracket
- PCB enclosure
- sensor enclosure

Run `scripts/run.py` from the repository root after syncing both environments:

```bash
uv sync
uv sync --project pocs/build123d-migration
uv run python pocs/build123d-migration/scripts/run.py
```

Generated STEP, STL, JSON, and PNG files are written below
`outputs/build123d-migration-poc/` and are intentionally not source artifacts.

The final decision is recorded in
`docs/decisions/STR-228-build123d-migration.md` and
`docs/decisions/STR-231-agent-generation-benchmark.md`. The technical PoC
passed, but the 60-trial agent-generation benchmark found no accuracy
advantage for build123d. Production therefore remains on CadQuery.

## Agent-generation benchmark

The `benchmark/` directory contains the engine-neutral contract, ten
specifications, equivalent engine guides, 60 independently generated
first-submission sources, neutral STEP checks, and compact committed results.

Run the source-blind benchmark after syncing both environments:

```bash
uv run python pocs/build123d-migration/benchmark/scripts/run_benchmark.py
```

Generated STEP and detailed attempt reports are written to
`outputs/str231-agent-benchmark/`. Compact source and prompt hashes plus the
aggregate decision metrics are committed below `benchmark/results/`.

Run the automated integration test with:

```bash
uv run python -m unittest tests.test_build123d_migration_poc
uv run python -m unittest tests.test_str231_benchmark
```
