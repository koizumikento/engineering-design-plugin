# STR-406: task-scoped engineering skills

Date: 2026-09-19. Baseline: `65b478a544da47332931353b7142a7ef7dbe1876`
(plugin 2.2.0). Candidate: plugin 2.2.1 in this change.

## Change and preserved contracts

Descriptions identify the job and nearest neighboring skills. Entry points
select modeling, inspection, export, circuit/ERC, schematic, analysis, or
requirements creation/update according to the request. Existing references and
helpers remain the execution surface; no runtime dependency changes are included.

ERC failure evidence and independent KiCad checks, STEP reimport, dimensional
checks, solid clearance, preview requirements, unknown-data handling, and
approval history remain explicit. Local repair completion does not authorize
inspection-only redesign or external publication/manufacturing.

## Evaluation conditions

- Model: `gpt-6-astra`; reasoning effort: `medium`.
- CLI: `codex-cli 0.155.0-alpha.9.2`, fresh ephemeral sessions with user config ignored.
- Baseline and candidate runtime lock SHA-256:
  `ac705c68144ee06f289a1297f9aa69ea3faa51fd6de0a87f8afcabc4fa25d53a`.
- Routing: nine fixed prompts, each given only the four name/description entries;
  expected selections and assertions withheld. One run per case/version.
- This bounded classifier comparison does not isolate all host system context,
  and is not a live plugin-discovery or output-quality benchmark.

## Observed description routing

Both catalogs matched all nine cases (9/9 each). Actual ordered selections were
identical; this establishes no observed regression on these prompts, not an
accuracy improvement or statistical equivalence.

| Case ID | Baseline selection | Candidate selection |
|---|---|---|
| spec-only | spec-writing | spec-writing |
| spec-patch | spec-writing | spec-writing |
| cad-only | mechanical-cad | mechanical-cad |
| step-inspection | mechanical-cad | mechanical-cad |
| circuit-bom | circuit-design | circuit-design |
| circuit-analysis | circuit-design | circuit-design |
| pcb-fit | integration | integration |
| layout-only | none | none |
| mixed | spec-writing, integration | spec-writing, integration |

Catalog SHA-256 (sorted `name: description` entries joined with LF):

- Baseline: `9ca8bffc6428b6634c222ee8430bf64d9e4524e8b53aa9066a88af564d0848b5`.
- Candidate: `e31bc613257ded76847116d4601fa85855007d696073a6f2df30b44c52ba683c`.

Description characters (excluding `description: `) decreased from 1,588 to 707.
Whitespace-separated words across the four complete entry points decreased
from 2,364 to 1,730. These are text-size measurements, not measured workload
token savings, latency improvements, or proof of better artifacts. Raw classifier
answers/usage and failed trial logs are local ignored evaluation outputs; this
table records the observed selections without publishing those logs.

## Output-quality limitation

Six baseline tasks returned without completing local execution. Their answers
reported `blocked by policy` when reading local skill files; CLI process exit 0
was therefore not a task PASS. Subsequent generation trials were stopped.
Full old/new artifact-quality comparison, reference-read reduction, and repair
completion are `NOT_EVALUATED`. The added cases are ready for an environment
where the normal permitted tools can execute; no permission workaround was used.

Local Windows build123d import also fails while parsing a system font with
`TTLibError: Not a TrueType or OpenType font (bad sfntVersion)`. This occurs
before geometry construction and is independent of the changed skill text.
Linux validation is recorded separately; no font/runtime patch is included.

## Deterministic validation

- Windows: frozen dependency sync, package regeneration, release validator, four
  release-validation tests, and eight circuit/integration tests passed.
- Linux: `uv run python -m unittest discover -s tests` ran 33 tests in 116.777 s;
  32 passed and one historical STR-231 PoC-environment test was skipped.
  This includes production geometry/reimport, preview smoke, native schematic
  generation, ERC failure propagation, and clearance regression checks.
- Container: `ghcr.io/astral-sh/uv:python3.11-bookworm`, image digest
  `sha256:58683a39536f1f4ed2e1dd79cf155edccfb47731aba8964bd0312aac942126cf`,
  frozen project environment (Python 3.11.4). The initial bare image lacked
  `libGL.so.1`; installing `libgl1`, `libxrender1`, `libglib2.0-0`, and
  `fonts-dejavu-core` inside a disposable container enabled the test run.
- The new STEP fixture independently returned one solid and measured extents
  40, 20, and 6 mm, each passing tolerance 0.01 mm via `cad_inspect.py`.
  Fixture SHA-256 (committed LF bytes): `68663993eb1e912a213b3230403c9a62c99952778fc852308c212f2c4949f743`.
  STEP whitespace was normalized before commit; OCCT re-read confirmed the same
  dimensions and one solid afterward.
- Final `no_skill` consistency validation was checked by the focused Windows
  release tests after the Linux snapshot; remaining edits were documentation.

These checks exercise helper behavior, not autonomous agent completion. They do
not replace the blocked output-quality comparison above.

## Release decision

Keep the PR draft until the full behavior comparison required by STR-407 and
STR-412 can run. Structural checks and deterministic regressions do not establish
improved agent output quality. No other-model, hardware, manufacturing, or
compliance acceptance is claimed.

## Sources

- [OpenAI article](https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra)
- [Evaluation protocol](../skill-evaluation.md)
- [Linear plan STR-406](https://linear.app/straydev/issue/STR-406)
