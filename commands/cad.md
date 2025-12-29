---
description: 承認済み仕様書からCadQueryコードを生成・実行
---

仕様書に基づいてCadQueryコードを生成し、3Dモデルを出力します。

## 前提条件

- 仕様書（`specs/*.md`）が存在すること
- 仕様書内の「承認チェックボックス」がオンであること

## 手順

1. **仕様書の読込・検証**
   - 承認状態を確認
   - 必須項目（寸法、材質、出力形式）が揃っているか確認

2. **コード生成**
   - `skills/mechanical-cad/refs/cadquery-api.md`を参照
   - パラメトリック設計を優先
   - 仕様書との対応をコメントで明記

3. **実行・検証**
   ```bash
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/cadquery_runner.py input.py -o outputs/
   ```
   - `isValid()`で形状の妥当性確認
   - 体積・表面積を算出して報告

4. **出力ファイル生成**
   - STEP: `outputs/[project-name].step`
   - STL: `outputs/[project-name].stl`
   - PNG: `outputs/[project-name]-preview.png`

## 引数

`$ARGUMENTS` に仕様書のパスを指定できます。

## 使用例

```
/engineering-design:cad specs/sensor-enclosure-spec.md
/engineering-design:cad
```

## エラー対処

| エラー | 原因 | 対処 |
|--------|------|------|
| `isValid() = False` | 自己交差 | フィレット半径を小さく |
| `BOPAlgo_AlertSelfIntersection` | 形状重複 | 操作順序を見直し |
