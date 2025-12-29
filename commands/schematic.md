---
description: 回路図（SVG）を生成
---

SKiDLコードから回路図を生成します。

## 前提条件

- SKiDLスクリプトが存在すること

## 手順

1. **スクリプト読み込み**
   - SKiDLスクリプトを解析
   - 部品と接続情報を抽出

2. **回路図生成**
   ```bash
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/schemdraw_render.py input.py -o outputs/
   ```
   - schemdrawを使用して描画
   - 自動レイアウト

3. **出力**
   - SVG: `outputs/[project-name]-schematic.svg`
   - PNG: `outputs/[project-name]-schematic.png`

## 引数

`$ARGUMENTS` にSKiDLスクリプトのパスを指定できます。

## 使用例

```
/engineering-design:schematic src/led_driver.py
/engineering-design:schematic src/voltage_divider.py
```

## 回路図スタイル

- IEC規格準拠
- 部品値・型番を表示
- ネット名をラベル表示
