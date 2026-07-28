import cadquery as cq


# Shared enclosure dimensions (millimetres).
body_width = 70.0
body_depth = 50.0
body_height = 30.0
wall_thickness = 4.0
floor_thickness = 4.0

# R1-R2: sharp-edged body with an explicitly dimensioned open-top cavity.
body_outer = (
    cq.Workplane("XY", origin=(0.0, 0.0, 0.0))
    .box(body_width, body_depth, body_height, centered=(True, True, False))
)
cavity_width = body_width - 2.0 * wall_thickness
cavity_depth = body_depth - 2.0 * wall_thickness
cavity_height = body_height - floor_thickness
cavity = (
    cq.Workplane("XY", origin=(0.0, 0.0, floor_thickness))
    .box(cavity_width, cavity_depth, cavity_height, centered=(True, True, False))
)
body = body_outer.cut(cavity)

# R3: diameter-10 port through the left wall, directed along +X.
side_port_diameter = 10.0
side_port_radius = side_port_diameter / 2.0
side_port_y = 0.0
side_port_z = 15.0
side_port_x_start = -body_width / 2.0
side_port_length = wall_thickness
side_port = (
    cq.Workplane(
        "YZ",
        origin=(side_port_x_start, side_port_y, side_port_z),
    )
    .circle(side_port_radius)
    .extrude(side_port_length)
)
body = body.cut(side_port)

# R4: X-aligned obround through the floor, with 14-mm centre spacing.
slot_center_x = 0.0
slot_center_y = 10.0
slot_overall_length = 20.0
slot_width = 6.0
slot_radius = slot_width / 2.0
slot_straight_length = slot_overall_length - slot_width
slot_end_offset = slot_straight_length / 2.0
slot_bar = (
    cq.Workplane("XY", origin=(slot_center_x, slot_center_y, 0.0))
    .rect(slot_straight_length, slot_width)
    .extrude(floor_thickness)
)
slot_ends = (
    cq.Workplane("XY", origin=(slot_center_x, slot_center_y, 0.0))
    .pushPoints([(-slot_end_offset, 0.0), (slot_end_offset, 0.0)])
    .circle(slot_radius)
    .extrude(floor_thickness)
)
slot = slot_bar.union(slot_ends)
body = body.cut(slot)

# R5-R6: separate lid above the intentional gap, with four stepped holes.
lid_width = 70.0
lid_depth = 50.0
lid_thickness = 4.0
lid_bottom_z = 34.0
lid = (
    cq.Workplane("XY", origin=(0.0, 0.0, lid_bottom_z))
    .box(lid_width, lid_depth, lid_thickness, centered=(True, True, False))
)

hole_x_offset = 25.0
hole_y_offset = 15.0
hole_positions = [
    (-hole_x_offset, -hole_y_offset),
    (-hole_x_offset, hole_y_offset),
    (hole_x_offset, -hole_y_offset),
    (hole_x_offset, hole_y_offset),
]
through_hole_diameter = 4.0
through_hole_radius = through_hole_diameter / 2.0
through_holes = (
    cq.Workplane("XY", origin=(0.0, 0.0, lid_bottom_z))
    .pushPoints(hole_positions)
    .circle(through_hole_radius)
    .extrude(lid_thickness)
)
lid = lid.cut(through_holes)

counterbore_diameter = 8.0
counterbore_radius = counterbore_diameter / 2.0
counterbore_depth = 2.0
counterbore_bottom_z = lid_bottom_z + lid_thickness - counterbore_depth
counterbores = (
    cq.Workplane("XY", origin=(0.0, 0.0, counterbore_bottom_z))
    .pushPoints(hole_positions)
    .circle(counterbore_radius)
    .extrude(counterbore_depth)
)
lid = lid.cut(counterbores)

# Preserve the body and lid as exactly two separate closed solids.
result = cq.Compound.makeCompound([body.val(), lid.val()])
