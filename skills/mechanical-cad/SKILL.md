---
name: mechanical-cad
description: |
  CadQueryを使用した3D CADモデルの生成。以下の場合に使用:
  (1) 「3Dモデルを作成」「筐体を設計」「ボックスを作って」などの機械設計リクエスト
  (2) STEP/STLファイルの生成が必要な場合
  (3) パラメトリック設計や穴・フィレット加工の指定
  入力: 仕様書または自然言語要望
  出力: Pythonスクリプト、STEP、STL、PNG
---

# Mechanical CAD Skill

## ワークフロー

1. **仕様確認**
   - [ ] 仕様書（specs/*.md）が存在するか確認
   - [ ] 承認チェックボックスがオンか確認
   - [ ] 必須項目（寸法、材質、出力形式）が揃っているか

2. **コード生成**
   - [ ] `refs/cadquery-api.md`を参照
   - [ ] パラメトリック設計を優先
   - [ ] 仕様書との対応をコメントで明記

3. **実行・検証**
   ```bash
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/cadquery_runner.py input.py -o outputs/
   ```
   - [ ] isValid()で形状の妥当性確認
   - [ ] 体積・表面積を算出して報告

4. **出力ファイル生成**
   - STEP: `outputs/[project-name].step`
   - STL: `outputs/[project-name].stl`
   - PNG: `outputs/[project-name]-preview.png`

## 基本パターン

```python
import cadquery as cq

# パラメータ（仕様書から）
width, depth, height = 100, 60, 40
wall_thickness = 2.0
hole_diameter = 5.0

result = (
    cq.Workplane("XY")
    .box(width, depth, height)
    .faces(">Z").shell(-wall_thickness)
    .faces(">Z").workplane()
    .hole(hole_diameter)
)

assert result.val().isValid(), "形状が無効です"
cq.exporters.export(result, "output.step")
cq.exporters.export(result, "output.stl")
```

## エラー対処

| エラー | 原因 | 対処 |
|--------|------|------|
| `isValid() = False` | 自己交差 | フィレット半径を小さく |
| `BOPAlgo_AlertSelfIntersection` | 形状重複 | 操作順序を見直し |
| `StdFail_NotDone` | 形状生成失敗 | パラメータ値を確認 |

## 詳細

- `refs/cadquery-api.md` - CadQuery APIリファレンス
- `refs/jis-drawing.md` - JIS製図規格
- `refs/templates.md` - テンプレート集
