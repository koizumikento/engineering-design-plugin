---
description: 承認済み仕様書からSKiDLコードを生成・実行
---

仕様書に基づいてSKiDLコードを生成し、回路設計を実行します。

## 前提条件

- 仕様書（`specs/*.md`）が存在すること
- 仕様書内の「承認チェックボックス」がオンであること

## 手順

1. **仕様書の読込・検証**
   - 電気的仕様（入出力電圧、電流）が明確か確認
   - シミュレーション要件を確認

2. **コード生成**
   - `skills/circuit-design/refs/skidl-api.md`を参照
   - 部品値の計算（必要に応じて）
   - 仕様書との対応をコメントで明記

3. **ERC実行**
   ```bash
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/skidl_runner.py input.py -o outputs/
   ```
   - 未接続ピンの検出
   - 電源接続の確認

4. **出力ファイル生成**
   - ネットリスト: `outputs/[project-name].net`
   - BOM: `outputs/[project-name]-bom.csv`

## 引数

`$ARGUMENTS` に仕様書のパスを指定できます。

## 使用例

```
/engineering-design:circuit specs/led-driver-spec.md
/engineering-design:circuit
```

## 部品値計算の例

- **電流制限抵抗**: R = (Vin - Vf) / If
- **分圧回路**: Vout = Vin × R2 / (R1 + R2)
- **RCフィルタ**: fc = 1 / (2π × R × C)
