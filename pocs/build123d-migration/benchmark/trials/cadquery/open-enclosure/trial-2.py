import cadquery as cq


# Enclosure dimensions (mm)
outer_x = 80.0
outer_y = 50.0
outer_z = 30.0
wall_thickness = 3.0
bottom_thickness = 3.0

# Internal standoff dimensions and locations (mm)
standoff_radius = 4.0
standoff_z_min = 3.0
standoff_z_max = 12.0
standoff_x_offset = 28.0
standoff_y_offset = 13.0

# Blind-hole dimensions (mm)
hole_radius = 1.5
hole_z_min = 6.0
hole_z_max = 12.0

cavity_x = outer_x - 2.0 * wall_thickness
cavity_y = outer_y - 2.0 * wall_thickness
cavity_z = outer_z - bottom_thickness

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

result = outer.cut(cavity)

standoff_centers = [
    (-standoff_x_offset, -standoff_y_offset),
    (-standoff_x_offset, standoff_y_offset),
    (standoff_x_offset, -standoff_y_offset),
    (standoff_x_offset, standoff_y_offset),
]

for center_x, center_y in standoff_centers:
    standoff = (
        cq.Workplane("XY", origin=(center_x, center_y, standoff_z_min))
        .circle(standoff_radius)
        .extrude(standoff_z_max - standoff_z_min)
    )
    result = result.union(standoff)

for center_x, center_y in standoff_centers:
    blind_hole = (
        cq.Workplane("XY", origin=(center_x, center_y, hole_z_min))
        .circle(hole_radius)
        .extrude(hole_z_max - hole_z_min)
    )
    result = result.cut(blind_hole)

result = result.clean()
