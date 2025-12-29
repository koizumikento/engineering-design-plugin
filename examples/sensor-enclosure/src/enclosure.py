"""
センサー筐体 - CadQuery実装

仕様書: specs/sensor-enclosure-spec.md
"""
import cadquery as cq
from cadquery import exporters

# =============================================================================
# 仕様書からのパラメータ
# =============================================================================

# 外形寸法
WIDTH = 60.0          # 全長 [mm]
DEPTH = 40.0          # 全幅 [mm]
HEIGHT = 25.0         # 全高（蓋含む）[mm]

# 肉厚
WALL = 2.0            # 肉厚 [mm]

# 蓋
LID_HEIGHT = 5.0      # 蓋高さ [mm]
LID_LIP = 2.0         # 嵌合部高さ [mm]

# 蓋固定穴（M3ざぐり穴）
SCREW_HOLE = 3.2      # 穴径 [mm]
SCREW_CBORE = 6.5     # ざぐり径 [mm]
SCREW_CBORE_DEPTH = 3.5  # ざぐり深さ [mm]
SCREW_OFFSET = 5.0    # 端からのオフセット [mm]

# ケーブルグランド（PG7）
GLAND_HOLE = 12.5     # グランド穴径 [mm]

# 壁掛け穴
MOUNT_SLOT_LENGTH = 8.0   # 長穴長さ [mm]
MOUNT_SLOT_WIDTH = 5.0    # 長穴幅 [mm]
MOUNT_SLOT_SPACING = 30.0 # 穴間隔 [mm]

# フィレット
OUTER_FILLET = 3.0    # 外側フィレット [mm]
INNER_FILLET = 1.5    # 内側フィレット [mm]

# =============================================================================
# ボディ（下部）
# =============================================================================

body_height = HEIGHT - LID_HEIGHT

body = (
    cq.Workplane("XY")
    # 外形
    .box(WIDTH, DEPTH, body_height)
    # 上面を開けてシェル化
    .faces(">Z").shell(-WALL)
    # 外側フィレット
    .edges("|Z").fillet(OUTER_FILLET)
)

# 内側フィレット（底面コーナー）
body = body.edges("<Z").edges("|Z").fillet(INNER_FILLET)

# ケーブルグランド穴（-X面、中央）
body = (
    body
    .faces("<X").workplane(centerOption="CenterOfMass")
    .center(0, -(body_height/2 - WALL - GLAND_HOLE/2 - 2))
    .hole(GLAND_HOLE)
)

# 壁掛け穴（底面）
body = (
    body
    .faces("<Z").workplane()
    .rarray(MOUNT_SLOT_SPACING, 1, 2, 1)
    .slot2D(MOUNT_SLOT_LENGTH, MOUNT_SLOT_WIDTH, angle=90)
    .cutThruAll()
)

# ボス（蓋固定用、内側）
boss_od = 6.0
boss_height = body_height - WALL - 2
boss_hole = 2.5  # M3タップ下穴

boss_positions = [
    (WIDTH/2 - SCREW_OFFSET, DEPTH/2 - SCREW_OFFSET),
    (-WIDTH/2 + SCREW_OFFSET, DEPTH/2 - SCREW_OFFSET),
    (WIDTH/2 - SCREW_OFFSET, -DEPTH/2 + SCREW_OFFSET),
    (-WIDTH/2 + SCREW_OFFSET, -DEPTH/2 + SCREW_OFFSET),
]

for x, y in boss_positions:
    boss = (
        cq.Workplane("XY")
        .workplane(offset=WALL)
        .center(x, y)
        .circle(boss_od / 2)
        .extrude(boss_height)
        .faces(">Z").workplane()
        .hole(boss_hole)
    )
    body = body.union(boss)

# =============================================================================
# 蓋（上部）
# =============================================================================

lid = (
    cq.Workplane("XY")
    # 外形
    .box(WIDTH, DEPTH, LID_HEIGHT)
    # 外側フィレット
    .edges("|Z").fillet(OUTER_FILLET)
)

# 嵌合部（蓋下面に突起）
lip_width = WIDTH - 2 * WALL - 0.4  # クリアランス0.2mm
lip_depth = DEPTH - 2 * WALL - 0.4

lid = (
    lid
    .faces("<Z").workplane()
    .rect(lip_width, lip_depth)
    .extrude(-LID_LIP)
)

# 蓋のざぐり穴（皿穴も可）
lid = (
    lid
    .faces(">Z").workplane()
    .pushPoints(boss_positions)
    .cboreHole(SCREW_HOLE, SCREW_CBORE, SCREW_CBORE_DEPTH)
)

# =============================================================================
# 蓋を所定位置に移動
# =============================================================================

lid = lid.translate((0, 0, body_height))

# =============================================================================
# 検証
# =============================================================================

body_shape = body.val()
lid_shape = lid.val()

assert body_shape.isValid(), "ボディ形状が無効です"
assert lid_shape.isValid(), "蓋形状が無効です"

# 情報出力
print("=== センサー筐体 ===")
print(f"外形: {WIDTH} x {DEPTH} x {HEIGHT} mm")
print(f"肉厚: {WALL} mm")
print(f"ボディ体積: {body_shape.Volume():.1f} mm³")
print(f"蓋体積: {lid_shape.Volume():.1f} mm³")

# =============================================================================
# エクスポート
# =============================================================================

# ボディ
exporters.export(body, "outputs/sensor-enclosure-body.step")
exporters.export(body, "outputs/sensor-enclosure-body.stl")

# 蓋
exporters.export(lid, "outputs/sensor-enclosure-lid.step")
exporters.export(lid, "outputs/sensor-enclosure-lid.stl")

# アセンブリ用（単一ファイル）
result = body.union(lid)
exporters.export(result, "outputs/sensor-enclosure-assembly.step")

print("\n出力ファイル:")
print("  outputs/sensor-enclosure-body.step")
print("  outputs/sensor-enclosure-body.stl")
print("  outputs/sensor-enclosure-lid.step")
print("  outputs/sensor-enclosure-lid.stl")
print("  outputs/sensor-enclosure-assembly.step")
