# Engineering Design Agent Skills

機械設計、電子回路設計、統合設計を扱うためのエージェントスキル集です。自然言語の要望から仕様書を作り、CadQuery と SKiDL を使った設計作業につなげます。

このリポジトリでは `skills/` を正本とし、エージェントが読むべき運用知識は `SKILL.md` と `references/`、`templates/`、`scripts/` に集約しています。OpenAI/Codex 向けのメタデータは各スキルの `agents/openai.yaml` に置き、Claude Code 向けにはインストール用メタデータとして `.claude-plugin/` を残しています。

Codex plugin 対応では、`plugins/engineering-design` を plugin root として扱います。plugin root には `skills/` を実ディレクトリとして同梱し、GitHub からのインストール時に symlink へ依存しない構成にしています。.claude-plugin/ はそのまま残し、repo ルートに Claude の manifest と Codex 用 marketplace を共存させます。

## できること

- **仕様策定**: 自然言語要望から機械/回路/統合仕様書を生成
- **機械設計**: CadQuery による 3D CAD モデル生成と STEP/STL 出力
- **回路設計**: SKiDL による回路生成、BOM、ERC summary、設計メモ、KiCad v9 正本回路図出力
- **追加検証**: ネットリスト、SPICE シミュレーション、3D プレビュー生成
- **統合設計**: 基板と筐体の整合性チェック

## 含まれるスキル

- `spec-writing`: 自然言語から機械/回路/統合仕様書を生成
- `mechanical-cad`: CadQuery による 3D CAD モデル生成とプレビュー
- `circuit-design`: SKiDL による回路設計、回路図生成、SPICE シミュレーション
- `integration`: 基板と筐体の整合性チェック

各スキルは以下の構成に寄せています。

- `SKILL.md`: 実行手順とトリガー条件
- `references/`: 必要になったときだけ読む参照資料
- `agents/openai.yaml`: OpenAI/Codex 向けの表示名、短い説明、既定プロンプト、起動ポリシー

## セットアップ

### 前提条件

- `uv`
- Python 3.9 以上
- CadQuery / SKiDL / PySpice などの関連ライブラリを実行できる環境
- KiCad v9（ネイティブ回路図 `.kicad_sch` / `.kicad_pro` の生成とプレビューに使用）

### Python 依存関係

```bash
uv sync
```

### システム依存関係

```bash
# macOS
brew install openscad ngspice
brew install --cask kicad

# Ubuntu/Debian
sudo apt install openscad ngspice
sudo apt install kicad
```

### Codex plugin として使う

この repo は `plugins/engineering-design` を plugin root として扱います。

- 必須 manifest: `plugins/engineering-design/.codex-plugin/plugin.json`
- bundled skills: `plugins/engineering-design/skills/`
- source-of-truth: `skills/*/SKILL.md`（配布前に bundled skills へ同期）
- Claude Code 互換: `.claude-plugin/` を同じ repo ルートに維持

この repo を Codex で開くと、repo-local marketplace [`.agents/plugins/marketplace.json`](/Users/koizumikenjin/workspace/engineering-design-plugin/.agents/plugins/marketplace.json) から `plugins/engineering-design` を指す `engineering-design` plugin を install できます。

必要なら Codex を再起動して、Plugin Directory から `Engineering Design` を `+` で install します。

## 基本ワークフロー

### 1. 仕様書を作る

`spec-writing` を使って `templates/spec/` ベースの仕様書を `specs/` に生成します。

```text
温度センサー用の防水筐体の仕様書を作って
spec-writing を使って ESP32 センサーデバイスの統合仕様をまとめて
```

### 2. 設計コードを作る

- 機械設計は `mechanical-cad` を使って `scripts/cadquery_runner.py` で STEP/STL を生成
- 回路設計は `circuit-design` を使って `skills/circuit-design/scripts/skidl_runner.py` と `skills/circuit-design/scripts/kicad_sch_export.py` で BOM / ERC summary / 設計メモ / KiCad 正本を生成

```text
mechanical-cad を使って specs/sensor-enclosure-spec.md から CadQuery コードを生成して
circuit-design を使って specs/led-driver-spec.md から SKiDL コードと KiCad 正本を生成して
```

### 3. 任意の追加出力を作る

- 3D プレビュー: `scripts/preview_generator.py`
- 必要時のみのネットリスト: `skills/circuit-design/scripts/skidl_runner.py --netlist`
- SPICE シミュレーション: `skills/circuit-design/scripts/pyspice_sim.py --dc|--ac|--tran`
- `skills/circuit-design/scripts/kicad_sch_export.py` はサポート済みトポロジーから KiCad v9 ネイティブ回路図を生成する。未対応回路はこの exporter を拡張する
- `skills/circuit-design/scripts/kicad_env.py` は KiCad ライブラリ環境変数と `fp-lib-table` / `sym-lib-table` を初期化する

### 4. 統合チェックを行う

`integration` を使って `scripts/integration_checker.py` で基板と筐体の整合性を確認します。

## ディレクトリ構造

```text
engineering-design-plugin/
├── .agents/
│   └── plugins/
│       └── marketplace.json # Codex repo-local marketplace
├── plugins/
│   └── engineering-design/  # Codex plugin root
│       ├── .codex-plugin/
│       │   └── plugin.json
│       └── skills/          # GitHub install 用に同梱
├── skills/                   # エージェントが参照する主定義
│   ├── spec-writing/
│   │   ├── SKILL.md
│   │   ├── agents/openai.yaml
│   │   └── references/
│   ├── mechanical-cad/
│   ├── circuit-design/
│   └── integration/
├── .claude-plugin/           # Claude Code インストール用メタデータ
├── scripts/                  # 複数スキルで共有する実行スクリプト
├── templates/                # 仕様書や設計テンプレート
├── examples/                 # サンプルプロジェクト
├── docs/                     # 設計メモと移行後の構成説明
├── README.md
└── LICENSE
```

`circuit-design` 専用スクリプトは [skills/circuit-design/scripts](/Users/koizumikenjin/workspace/engineering-design-plugin/skills/circuit-design/scripts) に置き、共有物だけを repo 直下の [scripts](/Users/koizumikenjin/workspace/engineering-design-plugin/scripts) に残しています。

## サンプルプロジェクト

### sensor-enclosure

温度センサー用の防水筐体（IP65相当）

```bash
cd examples/sensor-enclosure
uv run python src/enclosure.py
```

### led-driver

5V入力でLED3個を並列駆動する回路

```bash
cd examples/led-driver
uv run python src/led_driver.py
```

### rc-lowpass-filter

1kHz の 1次 RC ローパスフィルタ。`VIN` / `VOUT` / `GND` を明示し、AC 特性の目安を表示する sample です。

```bash
uv run python examples/rc-lowpass-filter/src/circuit.py
uv run python skills/circuit-design/scripts/skidl_runner.py examples/rc-lowpass-filter/src/circuit.py -o examples/rc-lowpass-filter/outputs
```

### voltage-divider

5V から約 3.3V を得る 2 抵抗の分圧回路。後段が高インピーダンス入力であることを前提にした最小構成 sample です。

```bash
uv run python examples/voltage-divider/src/circuit.py
uv run python skills/circuit-design/scripts/skidl_runner.py examples/voltage-divider/src/circuit.py -o examples/voltage-divider/outputs
```

### non-inverting-amplifier

TL072 を使った両電源の非反転増幅回路（ゲイン +11）。`KiCad v9` ネイティブ回路図と、外部 `VIN` / `VOUT` を明示した I/O 付きのサンプルです。

```bash
uv run python skills/circuit-design/scripts/skidl_runner.py examples/non-inverting-amplifier/src/circuit.py -o examples/non-inverting-amplifier/outputs
uv run python skills/circuit-design/scripts/kicad_sch_export.py examples/non-inverting-amplifier/src/circuit.py -o examples/non-inverting-amplifier/outputs
```

標準生成物は `outputs/reports/` に `-bom.csv`, `-erc-summary.md`, `-design-summary.md`、`outputs/kicad/[project-name]/` に `.kicad_sch`, `.kicad_pro` をまとめます。必要に応じて `--netlist` を追加します。

### inverting-amplifier

TL072 を使った両電源の反転増幅回路（ゲイン -10）。既存の非反転 sample と比較しやすい構成で、未使用チャネル終端とデカップリングも含みます。

```bash
uv run python examples/inverting-amplifier/src/circuit.py
uv run python skills/circuit-design/scripts/skidl_runner.py examples/inverting-amplifier/src/circuit.py -o examples/inverting-amplifier/outputs
```

### linear-regulator

`L7805` を使った 9V-15V 入力から 5V を生成する線形レギュレータ回路。入出力コネクタと安定化コンデンサを含む電源 sample です。

```bash
uv run python examples/linear-regulator/src/circuit.py
uv run python skills/circuit-design/scripts/skidl_runner.py examples/linear-regulator/src/circuit.py -o examples/linear-regulator/outputs
```

`non-inverting-amplifier` 以外の新規回路は、現状の `kicad_sch_export.py` が未対応のため `.kicad_sch` / `.kicad_pro` はまだ生成できません。KiCad 正本が必要なら exporter を拡張します。

### iot-device

ESP32 を使った温湿度センサーデバイス（筐体+回路の統合設計）

```bash
cd examples/iot-device
uv run python src/enclosure.py
uv run python src/circuit.py
```

## リファレンス

- `skills/mechanical-cad/references/cadquery-api.md` - CadQuery API リファレンス
- `skills/mechanical-cad/references/jis-drawing.md` - JIS 製図規格
- `skills/circuit-design/references/skidl-api.md` - SKiDL API リファレンス
- `skills/circuit-design/references/kicad-v9-workflow.md` - KiCad v9 ネイティブ運用メモ
- `skills/circuit-design/references/circuit-patterns.md` - 回路パターン集
- `skills/circuit-design/references/spice-guide.md` - SPICE シミュレーションガイド

## ライセンス

MIT License
