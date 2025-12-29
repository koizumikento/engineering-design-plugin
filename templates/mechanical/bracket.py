"""
L字ブラケット - CadQueryテンプレート

取付穴付きのL字ブラケット。
"""
import cadquery as cq

# =============================================================================
# パラメータ（仕様書に合わせて変更）
# =============================================================================

# ブラケット寸法
WIDTH = 40.0          # 幅（奥行方向）[mm]
LEG1_LENGTH = 50.0    # 第1辺の長さ [mm]
LEG2_LENGTH = 60.0    # 第2辺の長さ [mm]
THICKNESS = 5.0       # 板厚 [mm]

# フィレット
CORNER_FILLET = 8.0   # 内側コーナーフィレット [mm]
EDGE_FILLET = 1.0     # エッジフィレット [mm]

# 取付穴
HOLE_DIAMETER = 6.4   # 穴径（M6貫通穴）[mm]
LEG1_HOLE_POSITION = 25.0  # 第1辺の穴位置（端から）[mm]
LEG2_HOLE_POSITION = 30.0  # 第2辺の穴位置（端から）[mm]

# スロット（長穴）オプション
USE_SLOT = False
SLOT_LENGTH = 15.0    # スロット長さ [mm]
SLOT_WIDTH = 6.4      # スロット幅 [mm]

# リブ（補強）オプション
USE_RIB = True
RIB_THICKNESS = 3.0   # リブ厚 [mm]
RIB_HEIGHT = 15.0     # リブ高さ [mm]

# =============================================================================
# モデル生成
# =============================================================================

# L字断面を作成
result = (
    cq.Workplane("XZ")
    .moveTo(0, 0)
    .lineTo(LEG1_LENGTH, 0)
    .lineTo(LEG1_LENGTH, THICKNESS)
    .lineTo(THICKNESS, THICKNESS)
    .lineTo(THICKNESS, LEG2_LENGTH)
    .lineTo(0, LEG2_LENGTH)
    .close()
    .extrude(WIDTH)
)

# 内側コーナーフィレット
if CORNER_FILLET > 0 and CORNER_FILLET < min(LEG1_LENGTH, LEG2_LENGTH) - THICKNESS:
    # 内側コーナーのエッジを選択してフィレット
    result = (
        result
        .edges("|Y")
        .edges(cq.selectors.BoxSelector(
            (THICKNESS - 1, -1, THICKNESS - 1),
            (THICKNESS + 1, WIDTH + 1, THICKNESS + 1)
        ))
        .fillet(CORNER_FILLET)
    )

# 第1辺（水平部）の穴
if USE_SLOT:
    result = (
        result
        .faces("<Z").workplane()
        .center(LEG1_HOLE_POSITION, WIDTH/2)
        .slot2D(SLOT_LENGTH, SLOT_WIDTH)
        .cutThruAll()
    )
else:
    result = (
        result
        .faces("<Z").workplane()
        .center(LEG1_HOLE_POSITION, WIDTH/2)
        .hole(HOLE_DIAMETER)
    )

# 第2辺（垂直部）の穴
result = (
    result
    .faces(">X").workplane()
    .center(LEG2_HOLE_POSITION, WIDTH/2)
    .hole(HOLE_DIAMETER)
)

# リブ追加
if USE_RIB:
    rib = (
        cq.Workplane("XZ")
        .workplane(offset=WIDTH/2 - RIB_THICKNESS/2)
        .moveTo(THICKNESS, THICKNESS)
        .lineTo(THICKNESS + RIB_HEIGHT, THICKNESS)
        .lineTo(THICKNESS, THICKNESS + RIB_HEIGHT)
        .close()
        .extrude(RIB_THICKNESS)
    )
    result = result.union(rib)

# エッジフィレット（外側）
if EDGE_FILLET > 0:
    # 外側エッジにフィレット（選択的に適用）
    try:
        result = result.edges(">X or >Z").fillet(EDGE_FILLET)
    except:
        pass  # フィレットが適用できない場合はスキップ

# =============================================================================
# 検証
# =============================================================================

shape = result.val()
assert shape.isValid(), "形状が無効です"

# 情報出力
bb = shape.BoundingBox()
print(f"サイズ: {bb.xlen:.1f} x {bb.ylen:.1f} x {bb.zlen:.1f} mm")
print(f"第1辺: {LEG1_LENGTH:.1f} mm")
print(f"第2辺: {LEG2_LENGTH:.1f} mm")
print(f"板厚: {THICKNESS:.1f} mm")
print(f"体積: {shape.Volume():.1f} mm³")

# =============================================================================
# エクスポート（必要に応じてコメント解除）
# =============================================================================

# from cadquery import exporters
# exporters.export(result, "bracket.step")
# exporters.export(result, "bracket.stl")
