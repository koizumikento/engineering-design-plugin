# KiCad v9 Workflow Notes

このリポジトリで KiCad v9 を主成果物として扱う際の実務メモ。

## 基本方針

- 回路設計の標準成果物では、正本は `.kicad_sch` / `.kicad_pro` にする
- `outputs/reports/` に BOM / ERC summary / design summary を集約し、`outputs/kicad/[project-name]/` に KiCad プロジェクト一式をまとめる
- 見た目確認のために別ソースの図を作るのではなく、KiCad ネイティブ出力を直接検証する

## SKiDL 側の方針

- KiCad が利用可能な環境では、可能な限り KiCad 標準ライブラリを直接使う
  - 例: `Part("Amplifier_Operational", "TL072")`
  - 例: `Part("Device", "R")`, `Part("Device", "C")`
- 部品には `tag=` を付ける
  - ランダムタグ生成 warning を減らせる
- 外部入出力ネットは未モデルのまま放置しない
  - 少なくとも `net.drive = Pin.drives.PASSIVE` を検討する
  - 実回路に近づけるならコネクタやテストポイントとして明示する
  - 可能なら `VIN` / `VOUT` のような境界ネットは 1 ピンコネクタやテストポイントを置き、KiCad 図でも同じ要素を描く

## KiCad ライブラリ環境

- `scripts/kicad_env.py` で以下を自動設定する
  - `KICAD_SYMBOL_DIR`
  - `KICAD6_SYMBOL_DIR` ... `KICAD9_SYMBOL_DIR`
  - `KICAD_FOOTPRINT_DIR`
  - `KICAD6_FOOTPRINT_DIR` ... `KICAD9_FOOTPRINT_DIR`
- KiCad グローバルテーブルが無い環境では、テンプレートから以下を自動初期化する
  - `~/.config/kicad/fp-lib-table`
  - `~/.config/kicad/6.0/fp-lib-table` ... `~/.config/kicad/9.0/fp-lib-table`
  - `sym-lib-table` も同様
- `scripts/skidl_utils.py` の共通ローダを使い、importlib 経由で読んだ SKiDL スクリプトの root hierarchy node warning を抑える
  - root node は空 hierarchy のまま維持し、`check_tags()` だけを安定名ベースで扱う

## 回路図表現

- マルチユニット部品は KiCad の標準的な分割表現に従う
  - 例: TL072 は `U1A`, `U1B`, `U1C(power)`
- 信号経路を優先して配置し、電源ユニットとデカップリングは別ブロックに分離する
- 未使用ユニットは図上で終端方法が分かるように残す
- 外部 I/O は「ラベルだけある線」よりも、入出力部品として配置した方が ERC と可読性が安定する

## Exporter の方針

- `scripts/kicad_sch_export.py` はサポート済みトポロジーを `.kicad_sch` に落とす
- 未対応回路が来たら stopgap の補助図を増やすのではなく、exporter を拡張する
- 追加したトポロジーは、このメモか `SKILL.md` に検証手順と制約を書く

## 最低限の検証

```bash
uv run python -m py_compile input.py
uv run python scripts/skidl_runner.py input.py -o outputs/
uv run python scripts/kicad_sch_export.py input.py -o outputs/
kicad-cli sch export netlist outputs/kicad/[project-name]/[project-name].kicad_sch -o outputs/reports/
```

確認項目:

- ERC エラーが 0
- `outputs/reports/` に `-bom.csv`, `-erc-summary.md`, `-design-summary.md` が生成される
- `outputs/kicad/[project-name]/` に `.kicad_sch`, `.kicad_pro` が生成される
- `kicad-cli` が `outputs/kicad/[project-name]/[project-name].kicad_sch` を読める
- 外部 I/O がある場合、回路モデルと KiCad 図の両方に同じ境界要素が存在する
