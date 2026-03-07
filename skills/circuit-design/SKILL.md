---
name: circuit-design
description: |
  SKiDLを使用した回路設計。以下の場合に使用:
  (1) 「回路を設計」「分圧回路」「フィルタ回路」などの電子回路リクエスト
  (2) ネットリスト・回路図（SVG）の生成
  (3) SPICEシミュレーション
  入力: 仕様書または自然言語要望
  出力: Pythonスクリプト、ネットリスト、BOM
  追加出力: 必要に応じて回路図（SVG）とシミュレーション結果
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
   - [ ] 部品値の計算（必要に応じて）
   - [ ] 仕様書との対応をコメントで明記

3. **ERC実行と標準出力生成**
   ```bash
   uv run python scripts/skidl_runner.py input.py -o outputs/ --bom
   ```
   - [ ] `uv run python -m py_compile input.py` で構文エラーがないことを確認
   - [ ] 未接続ピンの検出
   - [ ] 電源接続の確認
   - [ ] ネットリストとBOMが生成されたことを確認

4. **追加出力の要否を判定**
   - [ ] 回路図が必要な場合は `uv run python scripts/schemdraw_render.py input.py -o outputs/` を実行
   - [ ] シミュレーションが必要な場合は `references/spice-guide.md` を参照し、`uv run python scripts/pyspice_sim.py input.py -o outputs/ [--dc|--ac|--tran]` を実行
   - [ ] 追加出力が不要ならここで完了

5. **出力ファイル生成**
   - 標準出力:
     - ネットリスト: `outputs/[project-name].net`
     - BOM: `outputs/[project-name]-bom.csv`
   - 追加出力（要求時のみ）:
     - 回路図: `outputs/[project-name]-schematic.svg`
     - シミュレーション結果: `outputs/[project-name]-sim.png`, `outputs/[project-name]-sim.csv`

## 回路図生成

- `uv run python scripts/schemdraw_render.py input.py -o outputs/`
- 想定出力:
  - SVG: `outputs/[project-name]-schematic.svg`
  - PNG: `outputs/[project-name]-schematic.png`
- 描画方針:
  - IEC 規格準拠
  - 部品値と型番を表示
  - ネット名をラベル表示

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
- [ ] ネットリスト、BOM、必要なら回路図やシミュレーション結果が生成されている
- [ ] エラーがある場合は部品値、電源接続、ネット名、SPICE モデルの不足を確認する

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
- `references/circuit-patterns.md` - 回路パターン集
- `references/spice-guide.md` - SPICEシミュレーションガイド
