# CadQuery API リファレンス

## 概要

CadQueryは、Pythonベースのパラメトリック3D CADモデリングライブラリです。
OpenCASCADE（OCCT）をバックエンドとして使用します。

---

## 1. 基本構造

### Workplane（作業平面）

```python
import cadquery as cq

# XY平面で開始（最も一般的）
wp = cq.Workplane("XY")

# 他の平面
wp = cq.Workplane("XZ")  # 正面図
wp = cq.Workplane("YZ")  # 側面図

# オフセット平面
wp = cq.Workplane("XY", origin=(0, 0, 10))
```

### メソッドチェーン

```python
result = (
    cq.Workplane("XY")
    .box(100, 60, 40)        # 直方体作成
    .faces(">Z")             # 上面を選択
    .shell(-2)               # シェル化（肉厚2mm）
    .edges("|Z")             # 垂直エッジを選択
    .fillet(3)               # フィレット追加
)
```

---

## 2. 2Dスケッチ

### 基本形状

```python
# 長方形
wp.rect(width, height)

# 円
wp.circle(radius)

# 多角形
wp.polygon(6, 10)  # 六角形、外接円半径10

# 楕円
wp.ellipse(a_radius, b_radius)

# スロット
wp.slot2D(length, diameter)
```

### スケッチの組み合わせ

```python
# 穴のある長方形
wp.rect(100, 60).circle(10)  # 中央に穴

# 複数の円
wp.pushPoints([(20, 0), (-20, 0)]).circle(5)

# グリッドパターン
wp.rarray(20, 20, 3, 3).circle(3)  # 3x3グリッド
```

### 自由曲線

```python
# 線分
wp.moveTo(0, 0).lineTo(10, 0).lineTo(10, 10).close()

# 円弧
wp.moveTo(0, 0).radiusArc((10, 10), 5)

# スプライン
wp.spline([(0,0), (5,10), (10,5), (15,15)])

# 3点円弧
wp.threePointArc((5, 5), (10, 0))
```

---

## 3. 3D操作

### 押し出し（Extrude）

```python
# 単純な押し出し
wp.rect(10, 10).extrude(20)

# 両方向に押し出し
wp.rect(10, 10).extrude(20, both=True)

# テーパー付き押し出し
wp.rect(10, 10).extrude(20, taper=5)  # 5度のテーパー

# カット（引き算）
wp.rect(5, 5).cutBlind(-10)  # 10mmの深さでカット
wp.rect(5, 5).cutThruAll()   # 貫通カット
```

### 回転（Revolve）

```python
# 断面を回転
wp.moveTo(10, 0).lineTo(20, 0).lineTo(20, 30).lineTo(10, 30).close()
wp.revolve(360, (0, 0, 0), (0, 1, 0))  # Y軸周りに360度回転
```

### スイープ（Sweep）

```python
# パスに沿って断面を移動
path = cq.Workplane("XZ").spline([(0,0), (10,10), (20,0)])
result = (
    cq.Workplane("XY")
    .rect(5, 5)
    .sweep(path)
)
```

### ロフト（Loft）

```python
# 複数の断面を滑らかに接続
loft = (
    cq.Workplane("XY")
    .rect(10, 10)
    .workplane(offset=20)
    .circle(5)
    .loft()
)
```

---

## 4. プリミティブ形状

```python
# 直方体
wp.box(length, width, height)

# 円柱
wp.cylinder(height, radius)

# 球
wp.sphere(radius)

# 円錐
wp.cone(radius1, radius2, height)

# くさび形
wp.wedge(dx, dy, dz, xmin, zmin, xmax, zmax)
```

---

## 5. 選択（Selectors）

### 面の選択

```python
# 方向による選択
.faces(">Z")   # Z方向最大の面（上面）
.faces("<Z")   # Z方向最小の面（底面）
.faces(">X")   # X方向最大の面
.faces("+Z")   # Z方向を向いた面すべて
.faces("-Z")   # -Z方向を向いた面すべて

# 平行な面
.faces("|Z")   # XY平面に平行な面
.faces("#Z")   # Z軸に垂直な面（同上）

# 複合条件
.faces(">Z or <Z")  # 上面または底面
```

### エッジの選択

```python
# 方向による選択
.edges("|Z")   # Z軸に平行なエッジ
.edges(">Z")   # Z方向最大位置のエッジ

# フィルタ
.edges(cq.selectors.RadiusNthSelector(0))  # 最小半径のエッジ
```

### 頂点の選択

```python
.vertices(">Z")   # Z方向最大の頂点
.vertices("<X and <Y")  # X,Y最小の頂点
```

---

## 6. 修正操作

### フィレット・面取り

```python
# エッジフィレット
.edges().fillet(radius)

# 選択的フィレット
.edges("|Z").fillet(3)    # 垂直エッジのみ
.edges(">Z").fillet(2)    # 上部エッジのみ

# 面取り
.edges().chamfer(distance)
.edges().chamfer(distance1, distance2)  # 非対称面取り
```

### シェル（中空化）

```python
# 負の値で内側をくり抜き
.faces(">Z").shell(-2)  # 上面を開けて肉厚2mm

# 複数面を開ける
.faces(">Z or <Z").shell(-2)  # 上下面を開放
```

### 穴加工

```python
# 単純な穴
.hole(diameter)
.hole(diameter, depth)

# ざぐり穴
.cboreHole(hole_diameter, cbore_diameter, cbore_depth)

# 皿穴
.cskHole(hole_diameter, csk_diameter, csk_angle)

# 貫通穴
.hole(diameter, depth=None)
```

---

## 7. ブーリアン演算

```python
# 和（Union）
result = shape1.union(shape2)
result = shape1 | shape2

# 差（Subtract/Cut）
result = shape1.cut(shape2)
result = shape1 - shape2

# 積（Intersect）
result = shape1.intersect(shape2)
result = shape1 & shape2
```

---

## 8. 位置・変換

```python
# 移動
.translate((dx, dy, dz))

# 回転
.rotate((0, 0, 0), (0, 0, 1), 45)  # Z軸周りに45度

# ミラー
.mirror("XY")  # XY平面でミラー
.mirror("XZ", (0, 10, 0))  # オフセット位置でミラー
```

---

## 9. アセンブリ

```python
# アセンブリ作成
assy = cq.Assembly()

# パーツ追加
assy.add(part1, name="base", color=cq.Color("red"))
assy.add(part2, name="cover", loc=cq.Location((0, 0, 50)))

# 拘束
assy.constrain("base@faces@>Z", "cover@faces@<Z", "Plane")

# 解決
assy.solve()

# エクスポート
assy.save("assembly.step")
```

---

## 10. エクスポート

```python
from cadquery import exporters

# STEP（推奨、最も正確）
exporters.export(result, "output.step")

# STL（3Dプリント用）
exporters.export(result, "output.stl")

# DXF（2D図面）
exporters.exportDXF(result, "output.dxf")

# SVG
exporters.export(result, "output.svg")

# VRML
exporters.export(result, "output.wrl")
```

---

## 11. 検証・計測

```python
# 形状の妥当性チェック
shape = result.val()
assert shape.isValid(), "形状が無効です"

# 体積
volume = shape.Volume()  # mm³

# 表面積
area = shape.Area()  # mm²

# バウンディングボックス
bb = result.val().BoundingBox()
print(f"Size: {bb.xlen} x {bb.ylen} x {bb.zlen}")
```

---

## 12. よく使うパターン

### 穴付きボックス

```python
result = (
    cq.Workplane("XY")
    .box(100, 60, 40)
    .faces(">Z").shell(-2)
    .faces(">Z").workplane()
    .rarray(80, 40, 2, 2).hole(3.2)  # 四隅にM3穴
    .edges("|Z").fillet(3)
)
```

### ねじボス

```python
boss = (
    cq.Workplane("XY")
    .circle(6)
    .extrude(10)
    .faces(">Z").workplane()
    .hole(2.5, 8)  # M3タップ下穴
)
```

### リブ

```python
rib = (
    cq.Workplane("XZ")
    .moveTo(0, 0)
    .lineTo(20, 0)
    .lineTo(0, 15)
    .close()
    .extrude(2)
)
```
