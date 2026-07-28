import cadquery as cq


outer_x = 80.0
outer_y = 50.0
outer_z = 30.0

wall_thickness = 3.0
bottom_thickness = 3.0
cavity_x = outer_x - 2.0 * wall_thickness
cavity_y = outer_y - 2.0 * wall_thickness
cavity_z = outer_z - bottom_thickness

standoff_radius = 4.0
standoff_z_min = 3.0
standoff_z_max = 12.0
standoff_height = standoff_z_max - standoff_z_min
standoff_centres = [
    (-28.0, -13.0),
    (-28.0, 13.0),
    (28.0, -13.0),
    (28.0, 13.0),
]

hole_radius = 1.5
hole_z_min = 6.0
hole_z_max = 12.0
hole_depth = hole_z_max - hole_z_min

outer = cq.Workplane("XY").box(
    outer_x,
    outer_y,
    outer_z,
    centered=(True, True, False),
)

cavity = cq.Workplane("XY", origin=(0.0, 0.0, bottom_thickness)).box(
    cavity_x,
    cavity_y,
    cavity_z,
    centered=(True, True, False),
)

enclosure = outer.cut(cavity)

standoffs = (
    cq.Workplane("XY", origin=(0.0, 0.0, standoff_z_min))
    .pushPoints(standoff_centres)
    .circle(standoff_radius)
    .extrude(standoff_height)
)

blind_holes = (
    cq.Workplane("XY", origin=(0.0, 0.0, hole_z_min))
    .pushPoints(standoff_centres)
    .circle(hole_radius)
    .extrude(hole_depth)
)

result = enclosure.union(standoffs).cut(blind_holes).clean()
