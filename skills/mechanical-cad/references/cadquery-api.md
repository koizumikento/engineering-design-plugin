# CadQuery 実装リファレンス

## 目次

対象と方針 / 最小構造 / 座標とWorkplane / selector / Boolean / Assembly / Validation / Export / 公式資料

## 対象と方針

このリポジトリは `cadquery>=2.4` を宣言し、現在のlockは対応PythonでCadQuery 2.7系を選ぶ。実行前に `uv run python -c "import cadquery; print(cadquery.__version__)"` で実版を確認し、最新版ドキュメントのAPIを古い環境へ無条件に持ち込まない。

CadQuery Pythonをパラメトリック定義、STEPを中立形状交換、STL/3MFをメッシュ用途の派生成果物として扱う。外部形式はパラメトリック履歴を保持しない。

## 最小構造

```python
import cadquery as cq

WIDTH = 100.0
DEPTH = 60.0
HEIGHT = 20.0

result = cq.Workplane("XY").box(WIDTH, DEPTH, HEIGHT)

shape = result.val()
assert isinstance(shape, cq.Shape)
assert shape.isValid()
```

runnerが探索できるよう、最終オブジェクトを `result`, `model`, `shape`, `part`, `assembly` のいずれかの明確な名前で公開する。

## 座標とWorkplane

- 単位、原点、軸方向をbriefに記録する。
- 部品ローカル座標とassembly座標を分ける。
- 加工面から派生する場合は `.faces(...).workplane()` を使うが、重要位置は名前付き寸法とdatumから求める。
- `centerOption="CenterOfMass"` は形状変更で基準が動く可能性がある。インターフェース位置には固定datumを優先する。

```python
base = cq.Workplane("XY")
mount_points = [(-20.0, -10.0), (20.0, -10.0), (-20.0, 10.0), (20.0, 10.0)]

result = (
    base.box(60.0, 40.0, 4.0)
    .faces(">Z").workplane()
    .pushPoints(mount_points)
    .hole(3.4)
)
```

穴径は例示値であり、採用ねじ、穴等級、工程、公差から決定する。

## 安定したselector

文字列selectorは簡潔だが、トポロジ変更で対象数が変わり得る。

- 面方向: `.faces(">Z")`, `.faces("|Z")`
- エッジ方向: `.edges("|Z")`
- 幾何種別: `.faces("%PLANE")`, `.edges("%CIRCLE")`
- 空間範囲: `BoxSelector`
- 特殊条件: 独自Selectorまたは明示的なShape

重要操作の前に対象数を検証する。

```python
top_faces = result.faces(">Z").vals()
assert len(top_faces) == 1, f"expected one top face, got {len(top_faces)}"
```

`edges()[3]` のような順序依存選択は避ける。

## Boolean・shell・fillet

- 大きい基本形状から穴/開口をcutし、装飾filletは後段に置く。
- 接するだけのBooleanは数値的に不安定になり得る。意図した重なりを作る。
- shellは局所曲率や狭い隙間で失敗しやすい。失敗時は半径、肉厚、開口面、操作順を分離して確認する。
- fillet/chamfer半径が隣接エッジ長、壁厚、局所曲率を超えないようにする。
- 各主要段階を一時変数に分け、どの操作で無効になったか追跡する。

## Assembly

部品形状と配置transformを分ける。

```python
assembly = cq.Assembly(name="product")
assembly.add(base_part, name="base", loc=cq.Location((0, 0, 0)))
assembly.add(lid_part, name="lid", loc=cq.Location((0, 0, lid_z)))
```

拘束solverを使う場合は、自由度、datum、選択対象を確認し、`solve()` 後のLocationを検査する。外部部品STEPはrevisionと座標前提を記録する。

## Validation

最低限:

```python
shape = result.val()
assert shape.isValid(), "invalid BREP"

bb = shape.BoundingBox()
assert bb.xlen > 0 and bb.ylen > 0 and bb.zlen > 0
assert shape.Volume() > 0
```

追加確認:

- 期待solid数、shell数、face/edge数
- バウンディングボックスと仕様外形
- 体積・重心の急変
- 穴中心、径、深さ、最小壁厚
- 部品間の位置と最小距離
- export後の再importと寸法比較（重要成果物）
- 複数視点プレビュー

`isValid()` はBREP整合性だけを確認し、設計意図、強度、工程能力、干渉なしを保証しない。

## Export

```python
from cadquery import exporters

exporters.export(result, "part.step")
exporters.export(result, "part.stl", tolerance=0.05, angularTolerance=0.1)
```

メッシュのlinear/angular toleranceは部品サイズと曲率に合わせて指定し、重要面のfacetを画像または再計測で確認する。DXFは2D断面または平面輪郭を明示して出す。

Assembly STEPは、色・名前・複数bodyを保持する通常モードと、単一fused compoundの目的を区別する。fused exportは性能と形状妥当性を再確認する。

## 公式資料

- [CadQuery Documentation](https://cadquery.readthedocs.io/en/stable/)
- [Selectors Reference](https://cadquery.readthedocs.io/en/stable/selectors.html)
- [Assemblies](https://cadquery.readthedocs.io/en/stable/assy.html)
- [Importing and Exporting Files](https://cadquery.readthedocs.io/en/latest/importexport.html)
- [CadQuery Class Reference](https://cadquery.readthedocs.io/en/latest/classreference.html)
