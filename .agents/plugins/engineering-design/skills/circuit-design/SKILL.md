---
name: circuit-design
description: |
  SKiDLを使用した回路設計。以下の場合に使用:
  (1) 「回路を設計」「分圧回路」「フィルタ回路」などの電子回路リクエスト
  (2) BOM・ERC summary・KiCad v9 回路図の生成
  (3) SPICEシミュレーション
  入力: 仕様書または自然言語要望
  出力: Pythonスクリプト、BOM、ERC summary、設計メモ、KiCad v9 回路図/プロジェクト
  追加出力: 必要に応じて ネットリスト、シミュレーション結果
allowed-tools: Read, Glob, Grep, Edit, Write, Bash
---

# Circuit Design Skill

## ワークフロー

1. **仕様確認**
   - [ ] 仕様書（specs/*.md）が存在するか確認
   - [ ] 電気的仕様（入出力電圧、電流）が明確か
   - [ ] シミュレーション要件を確認

2. **コード生成**
   - [ ] `references/skidl-api.md`を参照
   - [ ] KiCad v9 を使う場合は `references/kicad-v9-workflow.md` を参照
   - [ ] 部品値の計算（必要に応じて）
   - [ ] 仕様書との対応をコメントで明記
   - [ ] 可能なら KiCad 標準ライブラリ部品を直接使い、`tag=` を付ける
   - [ ] 外部 I/O はラベルだけで済ませず、可能ならコネクタやテストポイントとしてモデル化する

3. **ERC実行と標準出力生成**
   ```bash
   uv run python scripts/skidl_runner.py input.py -o outputs/
   uv run python scripts/kicad_sch_export.py input.py -o outputs/
   ```
   - [ ] `uv run python -m py_compile input.py` で構文エラーがないことを確認
   - [ ] SKiDL スクリプトの読み込みは可能なら `scripts/skidl_utils.py` の共通ローダ経由にする
   - [ ] 未接続ピンの検出
   - [ ] 電源接続の確認
   - [ ] BOM、ERC summary、設計メモ、`.kicad_sch`、`.kicad_pro` が生成されたことを確認

4. **追加出力の要否を判定**
   - [ ] ネットリストが必要な場合だけ `uv run python scripts/skidl_runner.py input.py -o outputs/ --netlist` を実行する
   - [ ] シミュレーションが必要な場合は `references/spice-guide.md` を参照し、`uv run python scripts/pyspice_sim.py input.py -o outputs/ [--dc|--ac|--tran]` を実行
   - [ ] 追加出力が不要ならここで完了
   - [ ] KiCad 実行前提なら `scripts/kicad_env.py` によりライブラリ環境が初期化されることを前提にしてよい

5. **出力ファイル生成**
   - 標準出力:
     - BOM: `outputs/reports/[project-name]-bom.csv`
     - ERC summary: `outputs/reports/[project-name]-erc-summary.md`
     - 設計メモ: `outputs/reports/[project-name]-design-summary.md`
     - KiCad 回路図: `outputs/kicad/[project-name]/[project-name].kicad_sch`
     - KiCad プロジェクト: `outputs/kicad/[project-name]/[project-name].kicad_pro`
   - 追加出力（要求時のみ）:
     - ネットリスト: `outputs/reports/[project-name].net`
     - シミュレーション結果: `outputs/sim/[project-name]-sim.png`, `outputs/sim/[project-name]-sim.csv`

## 回路図生成

- `uv run python scripts/skidl_runner.py input.py -o outputs/`
- `uv run python scripts/kicad_sch_export.py input.py -o outputs/`
- `uv run python scripts/skidl_runner.py input.py -o outputs/ --netlist`
- 想定出力:
  - `-bom.csv`: `outputs/reports/[project-name]-bom.csv`
  - `-erc-summary.md`: `outputs/reports/[project-name]-erc-summary.md`
  - `-design-summary.md`: `outputs/reports/[project-name]-design-summary.md`
  - `.kicad_sch`: `outputs/kicad/[project-name]/[project-name].kicad_sch`
  - `.kicad_pro`: `outputs/kicad/[project-name]/[project-name].kicad_pro`
- 描画方針:
  - 製造/PCB 連携の正本は KiCad v9 にする
  - 部品値、型番、フットプリントを保持
  - exporter はサポート済みトポロジーを正しく `.kicad_sch` に落とす。未対応回路では回避策ではなく exporter を拡張する
  - マルチユニット部品は `U1A/U1B/U1C(power)` のように KiCad 流儀で分割して描く
  - 外部 I/O を置く場合は、回路図にも同じコネクタ/テストポイントを描いて ERC と見た目を一致させる

## シミュレーション

- `uv run python scripts/pyspice_sim.py input.py -o outputs/ --dc`
- `uv run python scripts/pyspice_sim.py input.py -o outputs/ --ac`
- `uv run python scripts/pyspice_sim.py input.py -o outputs/ --tran`

| 種類 | オプション | 説明 |
|------|-----------|------|
| DC解析 | `--dc` | 動作点解析、DCスイープ |
| AC解析 | `--ac` | 周波数特性、ボード線図 |
| 過渡解析 | `--tran` | 時間応答、パルス応答 |

## 実行後の確認

- [ ] `ERC()` が実行され、未接続や電源系エラーが解消されている
- [ ] BOM、ERC summary、設計メモ、`.kicad_sch`、`.kicad_pro`、必要ならシミュレーション結果が生成されている
- [ ] エラーがある場合は部品値、電源接続、ネット名、SPICE モデルの不足を確認する
- [ ] 外部入力ネットが未モデルなら `net.drive`、コネクタ、テストポイントのいずれかで意図を明示する
- [ ] KiCad 正本側で外部 I/O、電源、未使用ユニットの扱いが誤読されない

## 基本パターン

```python
from skidl import *

# 分圧回路
vin, vout, gnd = Net('VIN'), Net('VOUT'), Net('GND')
r1 = Part("Device", 'R', value='10K')
r2 = Part("Device", 'R', value='10K')

vin & r1 & vout & r2 & gnd

ERC()
generate_netlist()
```

## 部品値計算

### 電流制限抵抗
```
R = (Vin - Vf) / If
例: LED（Vf=2V, If=20mA）を5Vで駆動
R = (5 - 2) / 0.02 = 150Ω → 150Ω（E24）
```

### 分圧回路
```
Vout = Vin × R2 / (R1 + R2)
R2 = Vout × (R1 + R2) / Vin
```

### RCフィルタ
```
fc = 1 / (2π × R × C)
例: fc=1kHz, C=100nF
R = 1 / (2π × 1000 × 100e-9) = 1.59kΩ → 1.6kΩ
```

## 詳細

- `references/skidl-api.md` - SKiDL APIリファレンス
- `references/kicad-v9-workflow.md` - KiCad v9 ネイティブ運用メモ
- `references/circuit-patterns.md` - 回路パターン集
- `references/spice-guide.md` - SPICEシミュレーションガイド
