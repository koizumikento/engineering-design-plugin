---
description: 3Dモデルのプレビュー画像を生成
---

CadQueryモデルのプレビュー画像を生成します。

## 前提条件

- STEP/STLファイルまたはCadQueryスクリプトが存在すること

## 手順

1. **ファイル読み込み**
   - STEP/STLファイルを読み込み
   - またはCadQueryスクリプトを実行

2. **プレビュー生成**
   ```bash
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/preview_generator.py input.step -o outputs/
   ```
   - 複数アングルからレンダリング
   - 寸法情報を付与（オプション）

3. **出力**
   - PNG: `outputs/[project-name]-preview.png`
   - 複数視点: `outputs/[project-name]-[front|top|iso].png`

## 引数

`$ARGUMENTS` にSTEP/STLファイルまたはスクリプトのパスを指定できます。

## 使用例

```
/engineering-design:preview outputs/enclosure.step
/engineering-design:preview src/enclosure.py
```

## プレビューオプション

| オプション | 説明 |
|-----------|------|
| `--iso` | 等角図（デフォルト） |
| `--front` | 正面図 |
| `--top` | 上面図 |
| `--all` | 全視点 |
| `--dims` | 寸法表示 |
