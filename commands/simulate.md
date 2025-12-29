---
description: 回路のSPICEシミュレーションを実行
---

SKiDLコードに基づいてSPICEシミュレーションを実行します。

## 前提条件

- SKiDLスクリプトが存在すること
- ngspiceがインストールされていること

## 手順

1. **シミュレーション設定の確認**
   - DC動作点解析
   - AC周波数特性
   - 過渡応答解析

2. **シミュレーション実行**
   ```bash
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/pyspice_sim.py input.py -o outputs/
   ```

3. **結果出力**
   - グラフ: `outputs/[project-name]-sim.png`
   - データ: `outputs/[project-name]-sim.csv`

## 引数

`$ARGUMENTS` にSKiDLスクリプトのパスとシミュレーション種類を指定できます。

## 使用例

```
/engineering-design:simulate src/led_driver.py --dc
/engineering-design:simulate src/rc_filter.py --ac
/engineering-design:simulate src/amplifier.py --tran
```

## シミュレーション種類

| 種類 | オプション | 説明 |
|------|-----------|------|
| DC解析 | `--dc` | 動作点解析、DCスイープ |
| AC解析 | `--ac` | 周波数特性、ボード線図 |
| 過渡解析 | `--tran` | 時間応答、パルス応答 |
