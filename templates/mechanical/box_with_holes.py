"""
穴付きボックス - CadQueryテンプレート

基本的な筐体で、取付穴付き。
"""
import cadquery as cq

# =============================================================================
# パラメータ（仕様書に合わせて変更）
# =============================================================================

# 外形寸法
WIDTH = 100.0       # 幅 [mm]
DEPTH = 60.0        # 奥行 [mm]
HEIGHT = 40.0       # 高さ [mm]

# 肉厚
WALL_THICKNESS = 2.0  # 肉厚 [mm]

# フィレット
OUTER_FILLET = 3.0    # 外側フィレット半径 [mm]
INNER_FILLET = 1.0    # 内側フィレット半径 [mm]

# 取付穴
HOLE_DIAMETER = 3.2   # 穴径 [mm]（M3貫通穴）
HOLE_OFFSET = 5.0     # 端からのオフセット [mm]

# =============================================================================
# モデル生成
# =============================================================================

# ボックス本体
result = (
    cq.Workplane("XY")
    # 外形
    .box(WIDTH, DEPTH, HEIGHT)
    # 上面を開けてシェル化
    .faces(">Z").shell(-WALL_THICKNESS)
    # 外側フィレット
    .edges("|Z").fillet(OUTER_FILLET)
)

# 取付穴を追加（四隅）
hole_positions = [
    (WIDTH/2 - HOLE_OFFSET, DEPTH/2 - HOLE_OFFSET),
    (-WIDTH/2 + HOLE_OFFSET, DEPTH/2 - HOLE_OFFSET),
    (WIDTH/2 - HOLE_OFFSET, -DEPTH/2 + HOLE_OFFSET),
    (-WIDTH/2 + HOLE_OFFSET, -DEPTH/2 + HOLE_OFFSET),
]

result = (
    result
    .faces("<Z").workplane()
    .pushPoints(hole_positions)
    .hole(HOLE_DIAMETER)
)

# =============================================================================
# 検証
# =============================================================================

shape = result.val()
assert shape.isValid(), "形状が無効です"

# 情報出力
bb = shape.BoundingBox()
print(f"サイズ: {bb.xlen:.1f} x {bb.ylen:.1f} x {bb.zlen:.1f} mm")
print(f"体積: {shape.Volume():.1f} mm³")
print(f"表面積: {shape.Area():.1f} mm²")

# =============================================================================
# エクスポート（必要に応じてコメント解除）
# =============================================================================

# from cadquery import exporters
# exporters.export(result, "box_with_holes.step")
# exporters.export(result, "box_with_holes.stl")
