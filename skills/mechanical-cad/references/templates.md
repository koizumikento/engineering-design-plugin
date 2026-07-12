# CadQuery パターン集

## 目次

Plate / Enclosure / Bosses / Connector opening / Assembly / Validation

寸法は例示値である。仕様、メーカー図面、工程能力、公差解析から置き換え、各パターンを実行・検証する。

## Parametric plate with hole pattern

```python
import cadquery as cq

PLATE_X = 80.0
PLATE_Y = 50.0
PLATE_Z = 4.0
HOLE_D = 3.4
MOUNT_POINTS = [(-30.0, -15.0), (30.0, -15.0), (-30.0, 15.0), (30.0, 15.0)]

result = (
    cq.Workplane("XY")
    .box(PLATE_X, PLATE_Y, PLATE_Z)
    .faces(">Z").workplane()
    .pushPoints(MOUNT_POINTS)
    .hole(HOLE_D)
)

assert result.val().isValid()
```

## Hollow enclosure body

```python
import cadquery as cq

OUTER_X = 100.0
OUTER_Y = 60.0
OUTER_Z = 35.0
WALL = 2.4

outer = cq.Workplane("XY").box(OUTER_X, OUTER_Y, OUTER_Z)
result = outer.faces(">Z").shell(-WALL)

shape = result.val()
assert shape.isValid()
assert shape.Volume() > 0
```

shellが失敗する形状では、外形と内側cut toolを別々に構築する。蓋、lip、gasket、snap、draftをこの最小例へ無条件に足さない。

## Named bosses from interface coordinates

```python
import cadquery as cq

BOSS_Z = 6.0
BOSS_OD = 7.0
PILOT_D = 2.5
MOUNT_POINTS = [(-22.0, -12.0), (22.0, -12.0), (-22.0, 12.0), (22.0, 12.0)]

bosses = (
    cq.Workplane("XY")
    .pushPoints(MOUNT_POINTS)
    .circle(BOSS_OD / 2)
    .extrude(BOSS_Z)
    .faces(">Z").workplane()
    .pushPoints(MOUNT_POINTS)
    .hole(PILOT_D)
)
```

実際のpilot、外径、高さ、rib、insertは材質、締結方法、ねじ込み長さ、成形/造形条件から決める。

## Connector opening as sourced envelope

```python
OPENING_W = 10.2   # replace from connector + plug + tolerance stack
OPENING_H = 4.1
OPENING_Y = 0.0
OPENING_Z = 8.0

result = (
    body.faces(">X").workplane(centerOption="CenterOfBoundBox")
    .center(OPENING_Y, OPENING_Z)
    .rect(OPENING_W, OPENING_H)
    .cutThruAll()
)
```

開口寸法だけでなく、receptacle/plug datum、板厚、latch、挿抜、ケーブル、指アクセスを確認する。

## Assembly with explicit locations

```python
assembly = cq.Assembly(name="device")
assembly.add(enclosure, name="enclosure", loc=cq.Location((0, 0, 0)))
assembly.add(pcb_envelope, name="pcb", loc=cq.Location((0, 0, pcb_seating_z)))
assembly.add(lid, name="lid", loc=cq.Location((0, 0, lid_seating_z)))
```

Location値は統合仕様のtransformと対応させる。

## Validation block

```python
shape = result.val()
assert shape.isValid(), "invalid result"
bb = shape.BoundingBox()
assert bb.xlen > 0 and bb.ylen > 0 and bb.zlen > 0
assert shape.Volume() > 0
print({"bbox_mm": [bb.xlen, bb.ylen, bb.zlen], "volume_mm3": shape.Volume()})
```

標準成果物は `scripts/cadquery_runner.py --report --fail-on-invalid` で生成し、複数視点PNGも確認する。
