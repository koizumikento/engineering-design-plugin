import cadquery as cq


# R1: outer enclosure dimensions and datum.
outer_size_x = 100.0
outer_size_y = 70.0
outer_height = 30.0

# R2: open-top cavity and resulting wall dimensions.
side_wall_thickness = 4.0
bottom_thickness = 3.0
cavity_size_x = outer_size_x - 2.0 * side_wall_thickness
cavity_size_y = outer_size_y - 2.0 * side_wall_thickness
cavity_height = outer_height - bottom_thickness

# R3-R4: integrated boss and coaxial through-hole dimensions.
boss_radius = 4.0
boss_base_z = bottom_thickness
boss_height = 6.0
hole_radius = 1.5
hole_base_z = 0.0
hole_height = boss_base_z + boss_height
boss_offset_x = 38.0
boss_offset_y = 23.0
boss_centres = (
    (-boss_offset_x, -boss_offset_y),
    (-boss_offset_x, boss_offset_y),
    (boss_offset_x, -boss_offset_y),
    (boss_offset_x, boss_offset_y),
)

outer = cq.Workplane("XY").box(
    outer_size_x,
    outer_size_y,
    outer_height,
    centered=(True, True, False),
)
cavity = (
    cq.Workplane("XY", origin=(0.0, 0.0, bottom_thickness))
    .box(
        cavity_size_x,
        cavity_size_y,
        cavity_height,
        centered=(True, True, False),
    )
)

result = outer.cut(cavity)

for centre_x, centre_y in boss_centres:
    boss = (
        cq.Workplane("XY", origin=(centre_x, centre_y, boss_base_z))
        .circle(boss_radius)
        .extrude(boss_height)
    )
    result = result.union(boss)

for centre_x, centre_y in boss_centres:
    hole = (
        cq.Workplane("XY", origin=(centre_x, centre_y, hole_base_z))
        .circle(hole_radius)
        .extrude(hole_height)
    )
    result = result.cut(hole)

result = result.clean()
