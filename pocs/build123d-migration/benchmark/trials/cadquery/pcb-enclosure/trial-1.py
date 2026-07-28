import cadquery as cq


outer_x = 100.0
outer_y = 70.0
outer_z = 30.0

wall_thickness = 4.0
bottom_thickness = 3.0
cavity_x = outer_x - 2.0 * wall_thickness
cavity_y = outer_y - 2.0 * wall_thickness
cavity_z = outer_z - bottom_thickness

boss_radius = 4.0
boss_z_min = bottom_thickness
boss_z_max = 9.0
boss_height = boss_z_max - boss_z_min
boss_x = 38.0
boss_y = 23.0

hole_radius = 1.5
hole_z_min = 0.0
hole_z_max = boss_z_max
hole_height = hole_z_max - hole_z_min

boss_centres = [
    (-boss_x, -boss_y),
    (-boss_x, boss_y),
    (boss_x, -boss_y),
    (boss_x, boss_y),
]

outer = cq.Workplane("XY").box(
    outer_x,
    outer_y,
    outer_z,
    centered=(True, True, False),
)

cavity = cq.Workplane(
    "XY",
    origin=(0.0, 0.0, bottom_thickness),
).box(
    cavity_x,
    cavity_y,
    cavity_z,
    centered=(True, True, False),
)

bosses = (
    cq.Workplane("XY", origin=(0.0, 0.0, boss_z_min))
    .pushPoints(boss_centres)
    .circle(boss_radius)
    .extrude(boss_height)
)

holes = (
    cq.Workplane("XY", origin=(0.0, 0.0, hole_z_min))
    .pushPoints(boss_centres)
    .circle(hole_radius)
    .extrude(hole_height)
)

result = outer.cut(cavity).union(bosses).cut(holes).clean()
