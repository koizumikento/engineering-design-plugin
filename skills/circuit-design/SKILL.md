---
name: circuit-design
description: |
  SKiDLを使用した回路設計。以下の場合に使用:
  (1) 「回路を設計」「分圧回路」「フィルタ回路」などの電子回路リクエスト
  (2) ネットリスト・回路図（SVG）の生成
  (3) SPICEシミュレーション
  入力: 仕様書または自然言語要望
  出力: Pythonスクリプト、ネットリスト、SVG、シミュレーション結果
---

# Circuit Design Skill

## ワークフロー

1. **仕様確認**
   - [ ] 仕様書（specs/*.md）が存在するか確認
   - [ ] 電気的仕様（入出力電圧、電流）が明確か
   - [ ] シミュレーション要件を確認

2. **コード生成**
   - [ ] `refs/skidl-api.md`を参照
   - [ ] 部品値の計算（必要に応じて）
   - [ ] 仕様書との対応をコメントで明記

3. **ERC実行**
   ```bash
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/skidl_runner.py input.py -o outputs/
   ```
   - [ ] 未接続ピンの検出
   - [ ] 電源接続の確認

4. **出力ファイル生成**
   - ネットリスト: `outputs/[project-name].net`
   - BOM: `outputs/[project-name]-bom.csv`

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

- `refs/skidl-api.md` - SKiDL APIリファレンス
- `refs/circuit-patterns.md` - 回路パターン集
- `refs/spice-guide.md` - SPICEシミュレーションガイド
