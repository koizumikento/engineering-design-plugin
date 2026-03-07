# Engineering Design Agent Skills

機械設計、電子回路設計、統合設計を扱うためのエージェントスキル集です。自然言語の要望から仕様書を作り、CadQuery と SKiDL を使った設計作業につなげます。

このリポジトリでは `skills/` を正本とし、エージェントが読むべき運用知識は `SKILL.md` と `references/`、`templates/`、`scripts/` に集約しています。OpenAI/Codex 向けのメタデータは各スキルの `agents/openai.yaml` に置き、Claude Code 向けにはインストール用メタデータとして `.claude-plugin/` を残しています。

## できること

- **仕様策定**: 自然言語要望から機械/回路/統合仕様書を生成
- **機械設計**: CadQuery による 3D CAD モデル生成と STEP/STL 出力
- **回路設計**: SKiDL による回路生成、ネットリスト/BOM 出力
- **追加検証**: 回路図生成、SPICE シミュレーション、3D プレビュー生成
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

### Python 依存関係

```bash
uv sync
```

### システム依存関係

```bash
# macOS
brew install openscad ngspice

# Ubuntu/Debian
sudo apt install openscad ngspice
```

### Codex で使う

Codex でこのリポジトリのスキルを読み込ませる場合は、`skills/` 配下を `~/.codex/skills` にリンクします。

repo-local discovery が必要な場合は、作業用 clone の中で `.agents/skills -> ../skills` のようなローカル symlink を作ってください。この管理リポジトリ自体には `.agents/skills` をコミットしていません。

```bash
./scripts/link_codex_skills.sh
```

確認だけしたい場合:

```bash
./scripts/link_codex_skills.sh --dry-run
```

既存リンクを外す場合:

```bash
./scripts/link_codex_skills.sh --remove
```

## 基本ワークフロー

### 1. 仕様書を作る

`spec-writing` を使って `templates/spec/` ベースの仕様書を `specs/` に生成します。

```text
温度センサー用の防水筐体の仕様書を作って
spec-writing を使って ESP32 センサーデバイスの統合仕様をまとめて
```

### 2. 設計コードを作る

- 機械設計は `mechanical-cad` を使って `scripts/cadquery_runner.py` で STEP/STL を生成
- 回路設計は `circuit-design` を使って `scripts/skidl_runner.py --bom` でネットリスト/BOM を生成

```text
mechanical-cad を使って specs/sensor-enclosure-spec.md から CadQuery コードを生成して
circuit-design を使って specs/led-driver-spec.md から SKiDL コードと BOM を生成して
```

### 3. 必要な追加出力を作る

- 3D プレビュー: `scripts/preview_generator.py`
- 回路図: `scripts/schemdraw_render.py`
- SPICE シミュレーション: `scripts/pyspice_sim.py --dc|--ac|--tran`

### 4. 統合チェックを行う

`integration` を使って `scripts/integration_checker.py` で基板と筐体の整合性を確認します。

## ディレクトリ構造

```text
engineering-design-plugin/
├── skills/                   # エージェントが参照する主定義
│   ├── spec-writing/
│   │   ├── SKILL.md
│   │   ├── agents/openai.yaml
│   │   └── references/
│   ├── mechanical-cad/
│   ├── circuit-design/
│   └── integration/
├── .claude-plugin/           # Claude Code インストール用メタデータ
├── scripts/                  # スキルから呼び出す実行スクリプト
├── templates/                # 仕様書や設計テンプレート
├── examples/                 # サンプルプロジェクト
├── docs/                     # 設計メモと移行後の構成説明
├── README.md
└── LICENSE
```

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
- `skills/circuit-design/references/circuit-patterns.md` - 回路パターン集
- `skills/circuit-design/references/spice-guide.md` - SPICE シミュレーションガイド

## ライセンス

MIT License
