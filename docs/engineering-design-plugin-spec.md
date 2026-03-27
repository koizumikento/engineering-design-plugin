# Engineering Design Skills Architecture

## 概要

このリポジトリは、機械設計、回路設計、統合設計を扱うエージェントスキル集である。自然言語要望から仕様書を整理し、CadQuery / SKiDL ベースの設計作業と検証へつなげる。

以前は Claude Code プラグインとして構成されていたが、現在は `skills/` を正本とし、クライアント固有の `commands/` や `hooks/` に依存しない構成へ整理している。Claude Code 向けの `.claude-plugin/` はインストール互換のため維持し、旧互換レイヤーにあった運用ルールは本ドキュメントと `skills/*/SKILL.md` に移管した。

Codex plugin 化では repo ルートを plugin root とし、`.codex-plugin/plugin.json` から `./skills/` を参照する。Claude Code 向けの `.claude-plugin/` も同じ repo ルートに維持する。これにより、配布形式を追加しても `skills/` 正本の原則を崩さない。

## 設計原則

1. スキル正本
   - エージェントが参照する主定義は `skills/*/SKILL.md`
   - 詳細知識は各スキルの `references/` に置く
   - OpenAI/Codex 向けの軽量メタデータは `skills/*/agents/openai.yaml` に置く
2. クライアント非依存
   - 実行パスは `scripts/...` や `templates/...` のリポジトリ相対表現を使う
   - 特定クライアントのスラッシュコマンド名は仕様やテンプレートに持ち込まない
   - Codex plugin manifest は配布メタデータだけを持ち、運用手順は `skills/*/SKILL.md` に残す
3. 仕様書先行
   - まず `spec-writing` で検証可能な仕様に落とし込み、承認後に設計コード生成へ進む
4. 実行後検証を明示
   - 旧 hooks にあった検証観点は、各スキルの実行手順とチェックリストへ統合する

## ワークフロー

### 単体設計

```text
[ユーザー要望]
      ↓
[spec-writing]
      ↓
[仕様書レビュー/承認]
      ↓
[mechanical-cad または circuit-design]
      ↓
[検証と追加出力]
      ↓
[STEP/STL or Netlist/BOM/KiCad/Simulation]
```

### 統合設計

```text
[ユーザー要望（筐体+回路）]
      ↓
[spec-writing]
      ↓
[統合仕様書レビュー/承認]
      ↓
[mechanical-cad] + [circuit-design]
      ↓
[integration]
      ↓
[整合性レポート]
```

## ディレクトリ構造

```text
engineering-design-plugin/
├── .agents/
│   └── plugins/
│       └── marketplace.json
├── .codex-plugin/
│   └── plugin.json
├── skills/
│   ├── spec-writing/
│   │   ├── SKILL.md
│   │   ├── agents/
│   │   │   └── openai.yaml
│   │   └── references/
│   ├── mechanical-cad/
│   │   ├── SKILL.md
│   │   ├── agents/
│   │   │   └── openai.yaml
│   │   └── references/
│   ├── circuit-design/
│   │   ├── SKILL.md
│   │   ├── agents/
│   │   │   └── openai.yaml
│   │   ├── references/
│   │   └── scripts/
│   └── integration/
│       ├── SKILL.md
│       ├── agents/
│       │   └── openai.yaml
│       └── references/
├── .claude-plugin/
│   ├── plugin.json
│   └── marketplace.json
├── scripts/
│   ├── cadquery_runner.py
│   ├── preview_generator.py
│   ├── integration_checker.py
│   └── link_codex_skills.sh
├── templates/
│   └── spec/
├── examples/
├── docs/
├── README.md
└── LICENSE
```

## Codex plugin パッケージング

- plugin root は repo ルートとする
- required manifest は `.codex-plugin/plugin.json`
- `skills` フィールドは `./skills/` を指す
- Codex plugin 名は Claude 側と揃えて `engineering-design` とする
- `skills/*/SKILL.md` が operational source-of-truth のまま残る
- `skills/*/agents/openai.yaml` は repo 管理用メタデータとして維持し、plugin manifest に重複転記しない
- `.app.json` と `.mcp.json` は現時点では追加しない
- repo-local marketplace は `.agents/plugins/marketplace.json` に置き、`source.path: "./"` で repo ルートを指す
- `.claude-plugin/` は削らず、Codex と Claude の install metadata を同居させる

repo ルートを plugin directory として扱う方針は、OpenAI の plugin docs にある `source.path` が plugin directory を指すという要件からの適用であり、この repo では `./skills/` をそのまま公開対象にできる点と、Claude Code plugin 用の既存ルート構造を崩さずに済む点を優先している。

## スキルごとの責務

### `spec-writing`

- 入力: 自然言語要望
- 出力: `specs/[project-name]-spec.md` または `specs/[project-name]-integrated-spec.md`
- 参照先: `templates/spec/`, `skills/spec-writing/references/spec-templates.md`
- ルール:
  - 要件は検証可能な数値または明確な条件に落とす
  - 最後に承認チェックボックスを置く

### `mechanical-cad`

- 入力: 仕様書または自然言語要望
- 標準出力: STEP, STL
- 追加出力: PNG プレビュー
- 実行:
  - `uv run python scripts/cadquery_runner.py input.py -o outputs/`
  - `uv run python scripts/cadquery_runner.py input.py -o outputs/ --preview`
  - `uv run python scripts/preview_generator.py input.step -o outputs/`
- 実行後確認:
  - `uv run python -m py_compile input.py`
  - `isValid()` による形状妥当性
  - STEP/STL/PNG の生成確認

### `circuit-design`

- 入力: 仕様書または自然言語要望
- 標準出力: BOM, ERC summary, 設計メモ, KiCad v9 回路図/プロジェクト
- 追加出力: ネットリスト, シミュレーション結果
- 実行:
  - `uv run python skills/circuit-design/scripts/skidl_runner.py input.py -o outputs/`
  - `uv run python skills/circuit-design/scripts/kicad_sch_export.py input.py -o outputs/`
  - `uv run python skills/circuit-design/scripts/skidl_runner.py input.py -o outputs/ --netlist`（ネットリストが必要な場合のみ）
  - `uv run python skills/circuit-design/scripts/pyspice_sim.py input.py -o outputs/ --dc|--ac|--tran`
- 備考:
  - 製造/PCB 連携の正本は `kicad_sch_export.py` とする
  - 標準成果物は `outputs/reports/` にレポート類、`outputs/kicad/[project-name]/` に KiCad プロジェクト一式を分けて配置する
  - `skills/circuit-design/scripts/skidl_runner.py` と `skills/circuit-design/scripts/kicad_sch_export.py` は `skills/circuit-design/scripts/skidl_utils.py` の共通ローダを使い、importlib 起因の root hierarchy node warning を抑える
  - KiCad v9 exporter はサポート済みトポロジーから `.kicad_sch` / `.kicad_pro` を生成し、未対応回路は exporter 側にレイアウト/記号対応を追加する
  - 外部 I/O ネットは必要に応じてコネクタやテストポイントとしてモデル化し、KiCad 図にも同じ境界要素を出す
- 実行後確認:
  - `uv run python -m py_compile input.py`
  - `ERC()` の実行
  - BOM/ERC summary/設計メモ/`.kicad_sch`/`.kicad_pro` の生成確認

### `integration`

- 入力: 統合仕様書
- 出力: 整合性レポート
- 実行:
  - `uv run python scripts/integration_checker.py specs/[project-name]-integrated-spec.md -o outputs/`
- 実行後確認:
  - 基板外形と筐体内寸
  - コネクタ位置と開口位置
  - 取付穴位置
  - 部品高さとクリアランス

## 旧 hooks から移した検証ポリシー

Claude Code 固有の hook 実装に置かれていた検証観点は、今後はスキル実行時の明示チェックとして扱う。

### Python スクリプト共通

- `uv run python -m py_compile` で構文エラーを検出する
- `eval()` / `exec()` のような不要な動的実行は避ける
- `os`, `subprocess`, `shutil`, `sys` などのシステム操作系 import は必要性を説明できる場合だけ使う

### CadQuery スクリプト

- `isValid()` を含める
- 実行後に自己交差や `BOPAlgo_AlertSelfIntersection` を確認する

### SKiDL スクリプト

- `ERC()` を含める
- 電源ネット、未接続ピン、モデル不足を確認する

## テンプレートと承認フロー

- 仕様書テンプレートは `templates/spec/` に置く
- 承認文言は特定コマンド名ではなく、対応するスキル名で記述する
- 承認済みでない仕様書に対してはコード生成を進めない

## OpenAI/Codex メタデータ

- `agents/openai.yaml` では `interface.display_name`, `interface.short_description`, `interface.default_prompt` を設定する
- `policy.allow_implicit_invocation` を明示し、暗黙起動の可否をスキル単位で制御する
- この repo では追加の MCP 依存がないため `dependencies.tools` は未使用

## Codex plugin 仕様との差分

- 実装済み:
  - `.codex-plugin/plugin.json`
  - `./skills/` を束ねる plugin root 構成
  - 既存の `SKILL.md` / `references/` / `scripts/` / `templates/` の再利用
- 未実装:
  - `.app.json`
  - `.mcp.json`
  - plugin 用 `assets/`
  - install-surface 向けの `interface` 拡張メタデータ
- 判断:
  - 現段階では「Claude Code plugin 構造を維持したままローカル導入できる最小 Codex plugin」を優先し、公開ディレクトリ向けの装飾は後回しにする
