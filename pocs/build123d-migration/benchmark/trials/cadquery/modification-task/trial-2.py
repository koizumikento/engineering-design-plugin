import cadquery as cq


# Plate and preserved starting-revision features (R1, R2).
plate_width = 70.0
plate_depth = 40.0
plate_height = 8.0

preserved_hole_diameter = 6.0
preserved_hole_centres = [
    (-25.0, -12.0),
    (-25.0, 12.0),
    (25.0, -12.0),
]

pocket_width = 16.0
pocket_depth = 6.0
pocket_height = 2.0
pocket_min_x = -8.0
pocket_min_y = -15.0
pocket_min_z = 6.0

# Revised through-hole (R3, R4).
revised_hole_diameter = 10.0
revised_hole_centre = (15.0, 8.0)

# Centred boss and concentric bore (R5, R6).
boss_diameter = 16.0
boss_height = 5.0
boss_base_z = plate_height
bore_diameter = 6.0
bore_height = plate_height + boss_height

plate = cq.Workplane("XY").box(
    plate_width,
    plate_depth,
    plate_height,
    centered=(True, True, False),
)

boss = (
    cq.Workplane("XY", origin=(0.0, 0.0, boss_base_z))
    .circle(boss_diameter / 2.0)
    .extrude(boss_height)
)

preserved_holes = (
    cq.Workplane("XY")
    .pushPoints(preserved_hole_centres)
    .circle(preserved_hole_diameter / 2.0)
    .extrude(plate_height)
)

revised_hole = (
    cq.Workplane(
        "XY",
        origin=(revised_hole_centre[0], revised_hole_centre[1], 0.0),
    )
    .circle(revised_hole_diameter / 2.0)
    .extrude(plate_height)
)

bore = (
    cq.Workplane("XY")
    .circle(bore_diameter / 2.0)
    .extrude(bore_height)
)

pocket = cq.Workplane(
    "XY",
    origin=(
        pocket_min_x + pocket_width / 2.0,
        pocket_min_y + pocket_depth / 2.0,
        pocket_min_z,
    ),
).box(
    pocket_width,
    pocket_depth,
    pocket_height,
    centered=(True, True, False),
)

# Direct final revision: the removed original hole is never cut, leaving
# material at (25, 12), while all specified cuts remain sharp (R3, R7).
result = (
    plate
    .union(boss)
    .cut(preserved_holes)
    .cut(revised_hole)
    .cut(bore)
    .cut(pocket)
    .clean()
)
