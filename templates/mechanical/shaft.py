"""
シャフト - CadQueryテンプレート

段付きシャフト、キー溝オプション付き。
"""
import cadquery as cq

# =============================================================================
# パラメータ（仕様書に合わせて変更）
# =============================================================================

# シャフト段数と寸法 (直径, 長さ)
SHAFT_SEGMENTS = [
    (20.0, 30.0),   # 段1: φ20 x 30mm
    (15.0, 50.0),   # 段2: φ15 x 50mm
    (10.0, 20.0),   # 段3: φ10 x 20mm
]

# 面取り
CHAMFER_SIZE = 1.0  # 両端の面取り [mm]

# キー溝（Noneの場合はなし）
KEYWAY = {
    "segment": 1,     # キー溝を設ける段（0から）
    "width": 5.0,     # キー溝幅 [mm]
    "depth": 2.5,     # キー溝深さ [mm]
    "length": 40.0,   # キー溝長さ [mm]
}
# KEYWAY = None  # キー溝なしの場合

# センター穴（Noneの場合はなし）
CENTER_HOLE = {
    "diameter": 3.0,  # センター穴径 [mm]
    "depth": 5.0,     # センター穴深さ [mm]
    "angle": 60,      # センター穴角度 [度]
}
# CENTER_HOLE = None  # センター穴なしの場合

# =============================================================================
# モデル生成
# =============================================================================

# 最初の段
diameter, length = SHAFT_SEGMENTS[0]
result = (
    cq.Workplane("XY")
    .circle(diameter / 2)
    .extrude(length)
)

# 残りの段を追加
current_z = length
for diameter, length in SHAFT_SEGMENTS[1:]:
    result = (
        result
        .faces(">Z").workplane()
        .circle(diameter / 2)
        .extrude(length)
    )
    current_z += length

# 面取り
if CHAMFER_SIZE > 0:
    result = (
        result
        .edges("<Z").chamfer(CHAMFER_SIZE)
        .edges(">Z").chamfer(CHAMFER_SIZE)
    )

# キー溝
if KEYWAY:
    # キー溝を設ける段の開始位置を計算
    keyway_start_z = sum(seg[1] for seg in SHAFT_SEGMENTS[:KEYWAY["segment"]])
    keyway_segment_diameter = SHAFT_SEGMENTS[KEYWAY["segment"]][0]

    keyway_cut = (
        cq.Workplane("XZ")
        .workplane(offset=keyway_segment_diameter/2 - KEYWAY["depth"])
        .center(keyway_start_z + KEYWAY["length"]/2, 0)
        .rect(KEYWAY["length"], KEYWAY["width"])
        .extrude(KEYWAY["depth"] + 1)
    )
    result = result.cut(keyway_cut)

# センター穴
if CENTER_HOLE:
    # 両端にセンター穴
    # 下端
    result = (
        result
        .faces("<Z").workplane()
        .hole(CENTER_HOLE["diameter"], CENTER_HOLE["depth"])
    )
    # 上端
    result = (
        result
        .faces(">Z").workplane()
        .hole(CENTER_HOLE["diameter"], CENTER_HOLE["depth"])
    )

# =============================================================================
# 検証
# =============================================================================

shape = result.val()
assert shape.isValid(), "形状が無効です"

# 情報出力
total_length = sum(seg[1] for seg in SHAFT_SEGMENTS)
max_diameter = max(seg[0] for seg in SHAFT_SEGMENTS)
print(f"全長: {total_length:.1f} mm")
print(f"最大径: φ{max_diameter:.1f} mm")
print(f"段数: {len(SHAFT_SEGMENTS)}")
print(f"体積: {shape.Volume():.1f} mm³")

# =============================================================================
# エクスポート（必要に応じてコメント解除）
# =============================================================================

# from cadquery import exporters
# exporters.export(result, "shaft.step")
# exporters.export(result, "shaft.stl")
