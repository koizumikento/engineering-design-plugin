import cadquery as cq


outer_x = 100.0
outer_y = 70.0
outer_z = 30.0

cavity_x = 92.0
cavity_y = 62.0
bottom_thickness = 3.0
cavity_height = outer_z - bottom_thickness

boss_radius = 4.0
boss_base_z = bottom_thickness
boss_top_z = 9.0
boss_height = boss_top_z - boss_base_z
boss_offset_x = 38.0
boss_offset_y = 23.0
boss_centres = [
    (-boss_offset_x, -boss_offset_y),
    (-boss_offset_x, boss_offset_y),
    (boss_offset_x, -boss_offset_y),
    (boss_offset_x, boss_offset_y),
]

hole_radius = 1.5
hole_base_z = 0.0
hole_top_z = boss_top_z
hole_height = hole_top_z - hole_base_z

outer = cq.Workplane("XY").box(
    outer_x,
    outer_y,
    outer_z,
    centered=(True, True, False),
)
cavity = (
    cq.Workplane("XY", origin=(0.0, 0.0, bottom_thickness))
    .box(
        cavity_x,
        cavity_y,
        cavity_height,
        centered=(True, True, False),
    )
)
bosses = (
    cq.Workplane("XY", origin=(0.0, 0.0, boss_base_z))
    .pushPoints(boss_centres)
    .circle(boss_radius)
    .extrude(boss_height)
)
holes = (
    cq.Workplane("XY", origin=(0.0, 0.0, hole_base_z))
    .pushPoints(boss_centres)
    .circle(hole_radius)
    .extrude(hole_height)
)

result = outer.cut(cavity).union(bosses).cut(holes).clean()
