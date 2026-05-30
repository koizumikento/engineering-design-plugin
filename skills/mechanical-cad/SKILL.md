---
name: mechanical-cad
description: |
  CadQueryを使用した3D CADモデルの生成。以下の場合に使用:
  (1) 「3Dモデルを作成」「筐体を設計」「ボックスを作って」などの機械設計リクエスト
  (2) STEP/STLファイルの生成が必要な場合
  (3) パラメトリック設計や穴・フィレット加工の指定
  入力: 仕様書または自然言語要望
  出力: Pythonスクリプト、STEP（一次成果物）、STL
  追加出力: PNGプレビュー、DXF/SVG、検査レポート
allowed-tools: Read, Glob, Grep, Edit, Write, Bash
---

# Mechanical CAD Skill

## ワークフロー

1. **仕様確認**
   - [ ] 仕様書（`specs/*.md`）が存在するか確認
   - [ ] 承認チェックボックスがオンか確認
   - [ ] 必須項目（寸法、材質、出力形式、用途）が揃っているか
   - [ ] 自然言語要望だけの場合は、先に内部CAD briefを作って寸法・基準面・未確定点を明示

2. **設計方針の整理**
   - [ ] STEP/STPを一次成果物、STL/DXF/SVG/PNGを用途別の副成果物として扱う
   - [ ] 単位はmm、基準面はXY、上方向は+Zを既定とする
   - [ ] 原点は単体部品の中心、または組立rootに置く
   - [ ] 閉じた正体積ソリッドを作る。表示用だけの面やゼロ厚み形状は避ける
   - [ ] 既製部品が含まれる場合は `references/off-the-shelf-parts.md` を必要時だけ参照
   - [ ] 組立・基板収納・嵌合がある場合は `references/assembly-positioning.md` を必要時だけ参照
   - [ ] 出力形式の扱いに迷う場合は `references/export-policy.md` を参照

3. **コード生成**
   - [ ] `references/cadquery-api.md` と `references/templates.md` を必要な範囲だけ参照
   - [ ] パラメトリック設計を優先し、magic numberを寸法パラメータに分離
   - [ ] 仕様書との対応をコメントまたはパラメータ名で明記
   - [ ] 小型筐体の肉厚未指定時は2.0-3.0mmを目安にし、根拠を報告
   - [ ] 装飾フィレット未指定時は安全な範囲で1.0-3.0mmを目安にする
   - [ ] 一般的な貫通クリアランスはM3=3.4mm、M4=4.5mm、M5=5.5mmを目安にする

4. **実行・検証**
   ```bash
   uv run python -m py_compile input.py
   uv run python scripts/cadquery_runner.py input.py -o outputs/ --report --fail-on-invalid
   ```
   - [ ] `isValid()`で形状の妥当性確認
   - [ ] 体積・表面積・重心・バウンディングボックス・トポロジ数を確認
   - [ ] STEPとSTLが生成されたことを確認
   - [ ] `outputs/reports/[project-name]-cad-summary.json` が生成されたことを確認

5. **プレビュー生成**
   - [ ] 新規作成または可視形状を変更した場合は、原則として複数視点PNGを生成
   ```bash
   uv run python scripts/preview_generator.py outputs/[project-name].step -o outputs/ --all-views
   ```
   - [ ] `outputs/[project-name]-iso.png`
   - [ ] `outputs/[project-name]-front.png`
   - [ ] `outputs/[project-name]-top.png`
   - [ ] `outputs/[project-name]-right.png`

6. **出力ファイル確認**
   - 標準出力:
     - STEP: `outputs/[project-name].step`
     - STL: `outputs/[project-name].stl`
     - 検査レポート: `outputs/reports/[project-name]-cad-summary.json`
   - レビュー出力:
     - PNG: `outputs/[project-name]-[iso|front|top|right].png`
   - 要求時のみ:
     - DXF/SVG: 2D形状または図示が必要な場合

## 内部CAD brief

自然言語要望から直接コードに入らず、最低限以下を整理する。

- 目的: 試作、3Dプリント、機構検討、筐体、治具、展示用など
- 主要寸法: width/depth/height、穴径、板厚、クリアランス
- 基準: 原点、基準面、上方向、嵌合面、取付穴パターン
- 成果物: STEP/STL/PNG/DXF/SVGのうち必要なもの
- 未確定点: 推定した値と、あとでユーザー確認が必要な値

## プレビュー生成

- 入力はSTEP / STL / CadQueryスクリプトのいずれでもよい
- プレビューだけ欲しい場合は `uv run python scripts/preview_generator.py input.step -o outputs/ --all-views` を実行
- CadQueryやrenderer依存が不足してプレビュー生成できない場合は、失敗理由と代替検証結果を報告する

## 実行後の確認

- [ ] 実行ログに `isValid() = False` や自己交差エラーが出ていない
- [ ] 検査レポートのバウンディングボックスが仕様寸法と大きくずれていない
- [ ] STEP / STL / PNG / report の期待ファイルが生成されている
- [ ] エラーがある場合はフィレット、ブーリアン順序、肉厚、穴位置を見直す
- [ ] 配布コピーが必要な変更では `plugins/engineering-design/skills/mechanical-cad/` も同期する

## 基本パターン

```python
import cadquery as cq

# パラメータ（仕様書またはCAD briefから）
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
```

## エラー対処

| エラー | 原因 | 対処 |
|--------|------|------|
| `isValid() = False` | 自己交差 | フィレット半径を小さく、ブーリアン順序を変更 |
| `BOPAlgo_AlertSelfIntersection` | 形状重複 | cut/union対象の重なりと順序を見直し |
| `StdFail_NotDone` | 形状生成失敗 | パラメータ値、穴位置、最小肉厚を確認 |
| STEP/STL生成失敗 | 結果変数が不明または無効 | `result`, `model`, `shape`, `part`, `assembly` のいずれかを定義 |

## 詳細

- `references/cadquery-api.md` - CadQuery APIリファレンス
- `references/jis-drawing.md` - JIS製図規格
- `references/templates.md` - テンプレート集
- `references/export-policy.md` - 出力形式の使い分け
- `references/off-the-shelf-parts.md` - 既製部品STEP/CADの扱い
- `references/assembly-positioning.md` - 組立、データム、クリアランスの整理
