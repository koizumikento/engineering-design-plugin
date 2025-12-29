# 機械設計テンプレート集

## 概要

よく使う機械設計パターンのCadQueryテンプレート集です。

---

## 1. 基本筐体（ボックス）

### シンプルボックス（開放型）

```python
import cadquery as cq

# パラメータ
width = 100      # 幅
depth = 60       # 奥行
height = 40      # 高さ
wall = 2.0       # 肉厚
fillet = 3.0     # 外側フィレット

# ボディ生成
body = (
    cq.Workplane("XY")
    .box(width, depth, height)
    .faces(">Z").shell(-wall)
    .edges("|Z").fillet(fillet)
)

# 検証
assert body.val().isValid()
```

### フタ付きボックス

```python
import cadquery as cq

# パラメータ
width, depth, height = 100, 60, 40
wall = 2.0
lip_height = 3.0  # 嵌合部高さ
lip_clearance = 0.2  # クリアランス

# ボディ（下部）
body = (
    cq.Workplane("XY")
    .box(width, depth, height)
    .faces(">Z").shell(-wall)
    .edges("|Z").fillet(3)
)

# フタ
lid_width = width - 2 * wall + 2 * lip_clearance
lid_depth = depth - 2 * wall + 2 * lip_clearance

lid = (
    cq.Workplane("XY")
    .box(width, depth, wall)
    .faces("<Z").workplane()
    .rect(lid_width, lid_depth)
    .extrude(-lip_height)
    .edges("|Z").fillet(3)
)
```

---

## 2. 取付穴パターン

### 四隅穴

```python
import cadquery as cq

width, depth, height = 100, 60, 20
hole_diameter = 3.2  # M3貫通穴
hole_offset = 5.0    # 端からのオフセット

result = (
    cq.Workplane("XY")
    .box(width, depth, height)
    .faces(">Z").workplane()
    .rect(width - 2*hole_offset, depth - 2*hole_offset, forConstruction=True)
    .vertices()
    .hole(hole_diameter)
)
```

### ざぐり穴

```python
import cadquery as cq

hole_dia = 3.2      # M3貫通穴
cbore_dia = 6.5     # ざぐり径
cbore_depth = 3.5   # ざぐり深さ

result = (
    cq.Workplane("XY")
    .box(100, 60, 20)
    .faces(">Z").workplane()
    .rect(80, 40, forConstruction=True)
    .vertices()
    .cboreHole(hole_dia, cbore_dia, cbore_depth)
)
```

### 皿穴

```python
import cadquery as cq

hole_dia = 3.2      # M3貫通穴
csk_dia = 6.3       # 皿穴径
csk_angle = 82      # 皿穴角度

result = (
    cq.Workplane("XY")
    .box(100, 60, 20)
    .faces(">Z").workplane()
    .rect(80, 40, forConstruction=True)
    .vertices()
    .cskHole(hole_dia, csk_dia, csk_angle)
)
```

---

## 3. ボス（ねじ受け）

### 単純ボス

```python
import cadquery as cq

boss_od = 6.0       # ボス外径
boss_height = 8.0   # ボス高さ
hole_dia = 2.5      # M3タップ下穴
hole_depth = 6.0    # 穴深さ

boss = (
    cq.Workplane("XY")
    .circle(boss_od / 2)
    .extrude(boss_height)
    .faces(">Z").workplane()
    .hole(hole_dia, hole_depth)
)
```

### リブ付きボス

```python
import cadquery as cq

boss_od = 8.0
boss_height = 10.0
hole_dia = 2.5
rib_thickness = 1.5
rib_height = 8.0

# ボス本体
boss = (
    cq.Workplane("XY")
    .circle(boss_od / 2)
    .extrude(boss_height)
    .faces(">Z").workplane()
    .hole(hole_dia, boss_height - 2)
)

# リブ（4方向）
for angle in [0, 90, 180, 270]:
    rib = (
        cq.Workplane("XZ")
        .moveTo(boss_od/2, 0)
        .lineTo(boss_od/2 + 5, 0)
        .lineTo(boss_od/2, rib_height)
        .close()
        .extrude(rib_thickness/2, both=True)
        .rotate((0,0,0), (0,0,1), angle)
    )
    boss = boss.union(rib)
```

---

## 4. 開口部・スロット

### 長穴（スロット）

```python
import cadquery as cq

slot_length = 20.0
slot_width = 6.0

result = (
    cq.Workplane("XY")
    .box(100, 60, 5)
    .faces(">Z").workplane()
    .slot2D(slot_length, slot_width)
    .cutThruAll()
)
```

### 通気スリット

```python
import cadquery as cq

slit_width = 2.0
slit_length = 30.0
slit_spacing = 5.0
slit_count = 5

result = (
    cq.Workplane("XY")
    .box(100, 60, 5)
    .faces(">Z").workplane()
    .rarray(slit_spacing, 1, slit_count, 1)
    .slot2D(slit_length, slit_width)
    .cutThruAll()
)
```

### コネクタ開口

```python
import cadquery as cq

# USB-C開口（9.0 x 3.2mm）
usb_width = 9.0
usb_height = 3.2
usb_fillet = 1.0

result = (
    cq.Workplane("XY")
    .box(100, 60, 40)
    .faces(">X").workplane(centerOption="CenterOfMass")
    .rect(usb_width, usb_height)
    .extrude(-5, "cut")
    .edges("|X").edges(cq.selectors.BoxSelector(
        (45, -5, 15), (55, 5, 25)
    )).fillet(usb_fillet)
)
```

---

## 5. シャフト

### 段付きシャフト

```python
import cadquery as cq

result = (
    cq.Workplane("XY")
    # 第1段
    .circle(10).extrude(20)
    # 第2段
    .faces(">Z").workplane()
    .circle(8).extrude(30)
    # 第3段
    .faces(">Z").workplane()
    .circle(6).extrude(25)
    # 面取り
    .edges(">Z").chamfer(1)
    .edges("<Z").chamfer(1)
)
```

### キー溝付きシャフト

```python
import cadquery as cq

shaft_dia = 20.0
shaft_length = 50.0
key_width = 6.0
key_depth = 3.5
key_length = 30.0

# シャフト本体
shaft = (
    cq.Workplane("XY")
    .circle(shaft_dia / 2)
    .extrude(shaft_length)
)

# キー溝
keyway = (
    cq.Workplane("XZ")
    .workplane(offset=shaft_dia/2 - key_depth)
    .rect(key_length, key_width)
    .extrude(key_depth + 1)
)

result = shaft.cut(keyway)
```

---

## 6. ブラケット

### L字ブラケット

```python
import cadquery as cq

# パラメータ
width = 40.0
leg1_length = 50.0
leg2_length = 60.0
thickness = 5.0
hole_dia = 6.4  # M6貫通穴

result = (
    cq.Workplane("XZ")
    .moveTo(0, 0)
    .lineTo(leg1_length, 0)
    .lineTo(leg1_length, thickness)
    .lineTo(thickness, thickness)
    .lineTo(thickness, leg2_length)
    .lineTo(0, leg2_length)
    .close()
    .extrude(width)
    # 穴加工
    .faces("<Z").workplane()
    .center(leg1_length/2, width/2)
    .hole(hole_dia)
    .faces(">X").workplane()
    .center(leg2_length/2, width/2)
    .hole(hole_dia)
    # フィレット
    .edges("|Y").edges(
        cq.selectors.BoxSelector((0,0,0), (thickness+1, width+1, thickness+1))
    ).fillet(thickness * 0.8)
)
```

---

## 7. 基板収納筐体

### PCBマウント用筐体

```python
import cadquery as cq

# 基板サイズ
pcb_width = 50.0
pcb_depth = 30.0
pcb_thickness = 1.6
pcb_clearance = 2.0  # 基板周囲クリアランス

# 筐体サイズ
wall = 2.0
internal_height = 20.0  # 部品高さ考慮

width = pcb_width + 2 * pcb_clearance + 2 * wall
depth = pcb_depth + 2 * pcb_clearance + 2 * wall
height = internal_height + wall

# ボス位置（基板穴位置から計算）
pcb_hole_offset = 3.0  # 基板端からの穴オフセット
boss_x = pcb_width/2 - pcb_hole_offset
boss_y = pcb_depth/2 - pcb_hole_offset

# 筐体本体
body = (
    cq.Workplane("XY")
    .box(width, depth, height)
    .faces(">Z").shell(-wall)
    .edges("|Z").fillet(3)
)

# ボス追加
boss_height = 5.0  # 基板下の高さ
boss_od = 5.0
boss_hole = 2.1  # M2.5タップ下穴

for x, y in [(boss_x, boss_y), (-boss_x, boss_y),
             (boss_x, -boss_y), (-boss_x, -boss_y)]:
    boss = (
        cq.Workplane("XY")
        .workplane(offset=wall)
        .center(x, y)
        .circle(boss_od/2)
        .extrude(boss_height)
        .faces(">Z").workplane()
        .hole(boss_hole)
    )
    body = body.union(boss)

result = body
```

---

## 8. 検証とエクスポート

### 標準的な検証・出力コード

```python
import cadquery as cq
from cadquery import exporters

# ... モデル生成コード ...

# 検証
shape = result.val()
assert shape.isValid(), "形状が無効です"

# 情報出力
bb = shape.BoundingBox()
print(f"サイズ: {bb.xlen:.1f} x {bb.ylen:.1f} x {bb.zlen:.1f} mm")
print(f"体積: {shape.Volume():.1f} mm³")
print(f"表面積: {shape.Area():.1f} mm²")

# エクスポート
exporters.export(result, "output.step")
exporters.export(result, "output.stl")
```
