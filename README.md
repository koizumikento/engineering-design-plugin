# Engineering Design Agent Skills

[![CI](https://github.com/koizumikento/engineering-design-plugin/actions/workflows/ci.yml/badge.svg)](https://github.com/koizumikento/engineering-design-plugin/actions/workflows/ci.yml)

自然言語の要望を、検証可能な仕様、build123d機械モデル、SKiDL/KiCad回路、PCB・筐体統合チェックへつなぐCodex向けスキル集です。

`skills/` が唯一の運用正本です。各 `SKILL.md` は中核ワークフロー、`references/` は必要時だけ読む技術資料、`agents/openai.yaml` はUIメタデータを保持します。

## Skills

| Skill | 主な責務 | 主な成果物 |
|---|---|---|
| `spec-writing` | 要求抽出、ID、根拠、interface、検証計画 | `specs/*.md` |
| `mechanical-cad` | build123d部品・アセンブリ、STEP-first検証 | `.py`, STEP, STL, PNG, JSON report |
| `circuit-design` | SKiDL回路、BOM/ERC、KiCad 9、任意simulation | `.py`, BOM, ERC, `.kicad_sch`, simulation |
| `integration` | PCB・筐体の座標、取付、開口、envelope整合 | integration report |

設計値は承認済み仕様、メーカー一次資料、現行規格、工程能力の順に根拠を持たせます。genericな肉厚、穴径、開口、pull-up、decoupling値を規格値として扱いません。

## Setup

前提:

- `uv`
- Python 3.11.x（repository default: 3.11.4）
- KiCad 9（KiCad schematic validationを行う場合）
- ngspice（SPICE analysisを行う場合）
- optional: VTK（PNG preview）

```bash
uv sync
```

環境確認:

```bash
uv run python -c "import build123d, skidl; print(build123d.__version__, skidl.__version__)"
kicad-cli --version
ngspice --version
```

## Codex plugin

repo-local marketplaceは `.agents/plugins/marketplace.json` です。entryは `plugins/engineering-design` を指し、そのmanifestがrepo rootの `skills/` を参照します。client別のskillコピーやsymlinkは置きません。

```text
.agents/plugins/marketplace.json
        -> plugins/engineering-design/.codex-plugin/plugin.json
        -> skills/
```

- plugin manifest: `plugins/engineering-design/.codex-plugin/plugin.json`
- installer互換manifest: `plugins/engineering-design/plugin.json`
- source of truth: `skills/`

Plugin Directoryで `Engineering Design` をinstallまたは再installし、新しいtaskで更新後のskillsを試してください。

Plugin release versionは2.0.0です。Python helper projectの0.3.0とは役割が異なり、`scripts/validate_release.py`がmanifest、marketplace、skill source-of-truthをまとめて検証します。

## Workflow

### 1. Specification

`spec-writing` は要求ごとにID、source/rationale、acceptance、verification methodを付けます。低riskのconceptは仮定を明記して進められますが、production、安全、法規、不可逆変更に影響する未決事項は解消してからreleaseします。

Templates:

- `templates/spec/mechanical-spec.md`
- `templates/spec/circuit-spec.md`
- `templates/spec/integrated-spec.md`

### 2. Mechanical CAD

```bash
uv run python -m py_compile input.py
uv run python scripts/cad_runner.py input.py -o outputs/ --report --fail-on-check
```

単一部品とアセンブリの両方でbuild123d Pythonをparameterized design definition、STEPをneutral geometry exchange、STL/3MF/DXF/SVG/PNGを用途別の派生成果物として扱います。runnerはSTEPを再importし、BREP、部品label、resolved transform、source-defined expectationを検証します。validityは寸法、干渉、強度、工程適合を自動保証しません。

```bash
uv run python scripts/preview_generator.py outputs/input.step -o outputs/ --all-views
```

### 3. Circuit design

```bash
uv run python -m py_compile input.py
uv run python skills/circuit-design/scripts/skidl_runner.py input.py -o outputs/
uv run python skills/circuit-design/scripts/kicad_sch_export.py input.py -o outputs/
```

repository exporterは確認済みtopology向けです。一般回路ではSKiDL 2.2の `generate_schematic()` も候補にし、生成後にKiCad 9で独立検証します。

```bash
kicad-cli sch erc --exit-code-violations --format json -o outputs/reports/project-kicad-erc.json outputs/kicad/project/project.kicad_sch
```

Optional:

```bash
uv run python skills/circuit-design/scripts/skidl_runner.py input.py -o outputs/ --netlist
uv run python skills/circuit-design/scripts/pyspice_sim.py input.py -o outputs/ --dc
uv run python skills/circuit-design/scripts/pyspice_sim.py input.py -o outputs/ --ac
uv run python skills/circuit-design/scripts/pyspice_sim.py input.py -o outputs/ --tran
```

Simulationは使用modelとscenarioの範囲だけを立証します。MPN、pin mapping、model revision、corner、acceptance criterionを記録してください。

### 4. PCB-enclosure integration

```bash
uv run python scripts/integration_checker.py specs/project-integrated-spec.md -o outputs/ --json
```

CLI overrideは承認済み要求または明記した工程仮定から与えます。

```bash
uv run python scripts/integration_checker.py specs/project-integrated-spec.md -o outputs/ --clearance 1.2 --z-clearance 1.0 --tolerance 0.25 --fail-on-fail
```

checkerはMarkdownの公称寸法screeningです。3D interference、最悪公差、plug/latch/cable/tool envelope、thermal、EMC/ESD、IP testを評価しません。未評価項目はreportに残ります。

## Repository layout

```text
engineering-design-plugin/
├── .agents/plugins/marketplace.json
├── plugins/engineering-design/
│   ├── .codex-plugin/plugin.json
│   └── plugin.json
├── skills/
│   ├── spec-writing/
│   ├── mechanical-cad/
│   ├── circuit-design/
│   └── integration/
├── scripts/
├── templates/
├── examples/
├── pocs/
└── docs/
```

`skills/circuit-design/scripts/` は回路固有helper、root `scripts/` は共有helperです。

## Examples

- `examples/calibration-block`: build123d validation/report/preview
- `examples/build123d-enclosure-assembly`: build123d named-joint assembly and STEP reimport validation
- `examples/sensor-enclosure`: enclosure model
- `examples/voltage-divider`, `rc-lowpass-filter`: passive circuit examples
- `examples/non-inverting-amplifier`, `inverting-amplifier`: op-amp examples
- `examples/linear-regulator`, `led-driver`: power/load examples
- `examples/iot-device`: mechanical/electronic integrated example

Examplesは教育・回帰用であり、部品値、開口、IP表現、製造公差をそのままproduction designへ流用しないでください。

## Technical evaluations

- `pocs/build123d-migration`: STR-228/STR-231の過去比較evidence
- `docs/decisions/STR-228-build123d-migration.md`: comparison evidence and migration decision
- `docs/decisions/STR-231-agent-generation-benchmark.md`: 60-trial agent-generation accuracy decision
- `docs/decisions/STR-229-build123d-unification.md`: build123d単一基盤の最終decision
- `docs/decisions/STR-232-assembly-routing.md`: superseded用途別routing decision

STR-228/STR-231のPoCは過去の比較evidenceとしてproduction workflowから隔離したまま保持します。productionはrootのbuild123d runtimeと`scripts/cad_runner.py`だけを使用します。

## Validation and release gate

PRと`main` pushでは、read-onlyのGitHub Actionsがlocked Python 3.11環境、plugin metadata、skill構造、production CAD regression、STEP再import、preview smoke testを検証します。ローカルでは同じgateを次の順に実行します。

```bash
uv sync --frozen
uv run python scripts/validate_release.py
uv run python -m unittest discover -s tests
```

## References

- build123d: `skills/mechanical-cad/references/`
- SKiDL/KiCad/ngspice: `skills/circuit-design/references/`
- requirements and verification: `skills/spec-writing/references/spec-templates.md`
- interface control and integration: `skills/integration/references/interface-spec.md`
- architecture: `docs/engineering-design-plugin-spec.md`

規格本文は同梱しません。referenceは公式カタログと一次資料へのsource mapとして使い、案件ごとに適用版と本文を確認します。

## License

MIT License
