import cadquery as cq


outer_width = 80.0
outer_depth = 50.0
outer_height = 30.0

wall_thickness = 3.0
bottom_thickness = 3.0
cavity_width = outer_width - 2.0 * wall_thickness
cavity_depth = outer_depth - 2.0 * wall_thickness
cavity_height = outer_height - bottom_thickness

standoff_radius = 4.0
standoff_base_z = bottom_thickness
standoff_top_z = 12.0
standoff_height = standoff_top_z - standoff_base_z
standoff_centres = [
    (-28.0, -13.0),
    (-28.0, 13.0),
    (28.0, -13.0),
    (28.0, 13.0),
]

blind_hole_radius = 1.5
blind_hole_bottom_z = 6.0
blind_hole_top_z = standoff_top_z
blind_hole_depth = blind_hole_top_z - blind_hole_bottom_z

outer = cq.Workplane("XY").box(
    outer_width,
    outer_depth,
    outer_height,
    centered=(True, True, False),
)

cavity = (
    cq.Workplane("XY", origin=(0.0, 0.0, bottom_thickness))
    .box(
        cavity_width,
        cavity_depth,
        cavity_height,
        centered=(True, True, False),
    )
)

standoffs = (
    cq.Workplane("XY", origin=(0.0, 0.0, standoff_base_z))
    .pushPoints(standoff_centres)
    .circle(standoff_radius)
    .extrude(standoff_height)
)

blind_holes = (
    cq.Workplane("XY", origin=(0.0, 0.0, blind_hole_bottom_z))
    .pushPoints(standoff_centres)
    .circle(blind_hole_radius)
    .extrude(blind_hole_depth)
)

result = outer.cut(cavity).union(standoffs).cut(blind_holes).clean()
