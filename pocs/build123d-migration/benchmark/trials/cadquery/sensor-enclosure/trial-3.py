import cadquery as cq


# Shared datum: the body bottom is at Z = 0 and both parts are centered on XY.
body_width = 70.0
body_depth = 50.0
body_height = 30.0
wall_thickness = 4.0

cavity_width = body_width - 2.0 * wall_thickness
cavity_depth = body_depth - 2.0 * wall_thickness
cavity_bottom_z = wall_thickness
cavity_height = body_height - cavity_bottom_z

port_diameter = 10.0
port_radius = port_diameter / 2.0
port_center_y = 0.0
port_center_z = 15.0

slot_overall_length = 20.0
slot_width = 6.0
slot_radius = slot_width / 2.0
slot_straight_length = slot_overall_length - slot_width
slot_center_y = 10.0
slot_end_offset_x = slot_straight_length / 2.0

lid_width = 70.0
lid_depth = 50.0
lid_height = 4.0
lid_bottom_z = 34.0

hole_offset_x = 25.0
hole_offset_y = 15.0
through_hole_diameter = 4.0
through_hole_radius = through_hole_diameter / 2.0
counterbore_diameter = 8.0
counterbore_radius = counterbore_diameter / 2.0
counterbore_bottom_z = 36.0

hole_positions = [
    (-hole_offset_x, -hole_offset_y),
    (-hole_offset_x, hole_offset_y),
    (hole_offset_x, -hole_offset_y),
    (hole_offset_x, hole_offset_y),
]


# R1-R2: rectangular body with an explicitly dimensioned open-top cavity.
body_outer = (
    cq.Workplane("XY")
    .box(body_width, body_depth, body_height, centered=(True, True, False))
)
cavity_tool = (
    cq.Workplane("XY", origin=(0.0, 0.0, cavity_bottom_z))
    .box(cavity_width, cavity_depth, cavity_height, centered=(True, True, False))
)
body = body_outer.cut(cavity_tool)

# R3: Ø10 port along +X, extending through the complete left wall.
port_tool = (
    cq.Workplane(
        "YZ",
        origin=(-body_width / 2.0 - 1.0, port_center_y, port_center_z),
    )
    .circle(port_radius)
    .extrude(wall_thickness + 2.0)
)
body = body.cut(port_tool)

# R4: 20 x 6 obround floor slot: 14-mm rectangle plus radius-3 ends.
slot_middle_tool = (
    cq.Workplane("XY", origin=(0.0, slot_center_y, -1.0))
    .box(
        slot_straight_length,
        slot_width,
        wall_thickness + 2.0,
        centered=(True, True, False),
    )
)
slot_left_end_tool = (
    cq.Workplane(
        "XY",
        origin=(-slot_end_offset_x, slot_center_y, -1.0),
    )
    .circle(slot_radius)
    .extrude(wall_thickness + 2.0)
)
slot_right_end_tool = (
    cq.Workplane(
        "XY",
        origin=(slot_end_offset_x, slot_center_y, -1.0),
    )
    .circle(slot_radius)
    .extrude(wall_thickness + 2.0)
)
slot_tool = slot_middle_tool.union(slot_left_end_tool).union(slot_right_end_tool)
body = body.cut(slot_tool).clean()

# R5: separate lid above the intentional 4-mm assembly gap.
lid = (
    cq.Workplane("XY", origin=(0.0, 0.0, lid_bottom_z))
    .box(lid_width, lid_depth, lid_height, centered=(True, True, False))
)

# R6: four Ø4 through holes with Ø8 counterbores over Z = 36..38.
through_hole_tools = (
    cq.Workplane("XY", origin=(0.0, 0.0, lid_bottom_z - 1.0))
    .pushPoints(hole_positions)
    .circle(through_hole_radius)
    .extrude(lid_height + 2.0)
)
counterbore_tools = (
    cq.Workplane("XY", origin=(0.0, 0.0, counterbore_bottom_z))
    .pushPoints(hole_positions)
    .circle(counterbore_radius)
    .extrude(lid_bottom_z + lid_height - counterbore_bottom_z + 1.0)
)
lid = lid.cut(through_hole_tools).cut(counterbore_tools).clean()

# R7: no edge treatments. Preserve the two enclosure parts as separate solids.
result = cq.Compound.makeCompound([body.val(), lid.val()])
