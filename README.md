# Engineering Design Agent Skills

[![CI](https://github.com/koizumikento/engineering-design-plugin/actions/workflows/ci.yml/badge.svg)](https://github.com/koizumikento/engineering-design-plugin/actions/workflows/ci.yml)

自然言語の要望を、検証可能な仕様、build123d機械モデル、SKiDL/KiCad回路、PCB・筐体統合チェックへつなぐCodex向けスキル集です。

`skills/` が唯一の運用正本です。各 `SKILL.md` は中核ワークフロー、`references/` は必要時だけ読む技術資料、`agents/openai.yaml` はUIメタデータを保持します。

## Skills

| Skill | 主な責務 | 主な成果物 |
|---|---|---|
| `spec-writing` | 要求抽出、ID、根拠、interface、検証計画 | `specs/*.md` |
| `mechanical-cad` | build123d部品・アセンブリ、STEP-first検証 | `.py`, STEP, STL, PNG, JSON report |
| `circuit-design` | SKiDL回路、BOM/ERC、KiCad 9/10、任意simulation | `.py`, BOM, ERC, `.kicad_sch`, simulation |
| `integration` | PCB・筐体の座標、取付、開口、envelope整合 | integration report |

設計値は承認済み仕様、メーカー一次資料、現行規格、工程能力の順に根拠を持たせます。genericな肉厚、穴径、開口、pull-up、decoupling値を規格値として扱いません。

## Setup

前提:

- `uv`
- Python 3.11.x（repository default: 3.11.4）
- KiCad 9または10と対応するsymbol/footprint libraries（回路図生成・独立検証を行う場合）
- ngspice（SPICE analysisを行う場合）
- optional: VTK（PNG preview）

```bash
uv sync
```

日本語WindowsではSKiDL 2.3.0のsource buildをUTF-8で実行します。

```powershell
$env:PYTHONUTF8 = '1'
uv sync --frozen
```

環境確認:

```bash
uv run python -c "import build123d, skidl; print(build123d.__version__, skidl.__version__)"
kicad-cli version
ngspice --version
```

## Codex plugin

repo-local marketplaceは `.agents/plugins/marketplace.json` です。entryは自己完結した `plugins/engineering-design` パッケージを指します。編集元はrepo rootの `skills/`、`scripts/`、`templates/` で、`scripts/sync_codex_plugin_package.py` が配布用パッケージを同期します。

```text
.agents/plugins/marketplace.json
        -> plugins/engineering-design/.codex-plugin/plugin.json
        -> plugins/engineering-design/skills/
```

- plugin manifest: `plugins/engineering-design/.codex-plugin/plugin.json`
- installer互換manifest: `plugins/engineering-design/plugin.json`
- source of truth: `skills/`

GitHub marketplaceとして登録する場合:

```bash
codex plugin marketplace add https://github.com/koizumikento/engineering-design-plugin.git \
  --ref main \
  --sparse .agents/plugins \
  --sparse plugins/engineering-design
codex plugin add engineering-design@engineering-design
```

Plugin Directoryで `Engineering Design` をinstallまたは再installし、新しいtaskで更新後のskillsを試してください。

Plugin versionは2.2.1です。Python helper projectの0.3.0とは役割が異なり、`scripts/validate_release.py`がmanifest、marketplace、skill source-of-truthをまとめて検証します。

## Workflow

依頼に合う経路だけを選びます。十分な要求がある実装依頼で仕様書作成を必須前段にしません。CADは新規・変更／既存形状の検査／出力、回路はBOM/ERC／要求された回路図／解析を分けます。仕様の部分更新では既存IDと承認履歴を保持し、変更部分へ旧承認を自動適用しません。

実装は生成・必要な検証・範囲内の修復・影響する再検証まで、検査のみは入力を変更せず結果報告までが完了条件です。referencesは選んだ経路に応じて読みます。

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

形状を作成・変更する場合は入力を短いCAD briefへ統合し、dimensioned sourceを画像比率より優先します。検査・形式変換だけなら新しい設計briefは不要です。visible geometryを作成・変更した場合はSTEP previewを確認し、視覚的な懸念を`cad_expectations`または独立計測へ戻します。失敗時は原因を分類し、最小のsource修正後に依存checkまで再実行します。

```bash
uv run python scripts/preview_generator.py outputs/input.step -o outputs/ --view iso
```

生成したSTEPはread-only inspection CLIでartifact-local selectorを列挙し、個別寸法、flush/center/coaxial差分、world frame、変更前後を検証できます。JSONが正本で、selectorはtopology変更後の永続安定性を保証しません。

```bash
uv run python scripts/cad_inspect.py refs outputs/input.step --topology
uv run python scripts/cad_inspect.py measure outputs/input.step --from '#s1' --extent x --expected 40 --tolerance 0.01
uv run python scripts/cad_inspect.py frame outputs/input.step '#o1'
uv run python scripts/cad_inspect.py diff outputs/before.step outputs/after.step --tolerance 0.01
```

単純部品のpreviewはiso、assembly・内部形状・複数軸の特徴・修復後は`--all-views`を使います。

### 3. Circuit design

BOM/ERCだけの依頼はrunnerまで、回路図が必要な場合にexporterと独立KiCad検証を追加します。

```bash
uv run python -m py_compile input.py
uv run python skills/circuit-design/scripts/skidl_runner.py input.py -o outputs/
uv run python skills/circuit-design/scripts/kicad_sch_export.py input.py -o outputs/
```

SKiDL 2.3.0のnative `generate_schematic()` が既定です。runner/exporterの対象は既定でKiCad 9、10には `--kicad-version 10` を明示します。source/libraryも同じ版に合わせます。確認済みtopology向けの旧exporterは `--backend compatibility` で利用できます。詳細は `skills/circuit-design/references/kicad-workflow.md` を参照してください。

ERCエラー時、runnerはレポートを保存して終了コード2を返します。生成後は対象KiCadで独立ERC、BOM/接続照合、視覚確認を実施します。CLI未導入・未実行は `NOT_EVALUATED` です。

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
uv run python scripts/integration_checker.py specs/project-integrated-spec.md -o outputs/ --json --fail-on-fail
```

CLI overrideは承認済み要求または明記した工程仮定から与えます。

```bash
uv run python scripts/integration_checker.py specs/project-integrated-spec.md -o outputs/ --clearance 1.2 --z-clearance 1.0 --tolerance 0.25 --fail-on-fail
```

checkerはMarkdownの公称寸法screeningで、上面・下面のクリアランスを別々に判定します。下面部品がない場合は高さ0を明記してください。3D interference、最悪公差、plug/latch/cable/tool envelope、thermal、EMC/ESD、IP testは評価しません。

STEPの静的干渉・最小隙間は既存のinspection CLIで別途検証できます。`measure` の参照点間距離とは異なり、solid間の最小距離と体積干渉を判定します。

```bash
uv run python scripts/cad_runner.py examples/pcb-enclosure-clearance/src/clearance_assembly.py -o outputs/clearance/ --report --fail-on-check
uv run python scripts/cad_inspect.py clearance outputs/clearance/clearance_assembly.step --from 'label:bottom_component' --to 'label:enclosure' --minimum 1
```

KiCad PCBのSTEP出力・共通座標化・上下面の実行例は `skills/integration/references/geometry-checks.md` を参照してください。

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
- `examples/pcb-enclosure-clearance`: PCB上下部品・筐体・蓋のstatic clearance/interference
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
uv run python scripts/sync_codex_plugin_package.py
uv run python scripts/validate_release.py
uv run python -m unittest discover -s tests
```

4スキルの代表例・境界例は `skills/*/evals/evals.json` に保持します。旧版/新版の比較方法と証拠の記録は [スキル評価手順](docs/skill-evaluation.md) を参照してください。構造検証の成功だけで生成品質の改善を主張しません。

## References

- build123d: `skills/mechanical-cad/references/`
- SKiDL/KiCad/ngspice: `skills/circuit-design/references/`
- requirements and verification: `skills/spec-writing/references/spec-templates.md`
- interface control and integration: `skills/integration/references/interface-spec.md`
- architecture: `docs/engineering-design-plugin-spec.md`

規格本文は同梱しません。referenceは公式カタログと一次資料へのsource mapとして使い、案件ごとに適用版と本文を確認します。

## License

MIT License
