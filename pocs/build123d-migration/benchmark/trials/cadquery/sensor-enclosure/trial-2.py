import cadquery as cq


# Body dimensions and datum
body_length_x = 70.0
body_width_y = 50.0
body_height_z = 30.0
wall_thickness = 4.0

# Side port
port_diameter = 10.0
port_center_y = 0.0
port_center_z = 15.0
port_start_x = -35.0
port_length_x = 4.0

# Floor slot
slot_center_x = 0.0
slot_center_y = 10.0
slot_overall_length_x = 20.0
slot_width_y = 6.0
slot_radius = slot_width_y / 2.0
slot_straight_length_x = slot_overall_length_x - 2.0 * slot_radius

# Lid and stepped holes
lid_length_x = 70.0
lid_width_y = 50.0
lid_thickness_z = 4.0
lid_bottom_z = 34.0
hole_diameter = 4.0
counterbore_diameter = 8.0
counterbore_depth = 2.0
hole_positions = [
    (-25.0, -15.0),
    (-25.0, 15.0),
    (25.0, -15.0),
    (25.0, 15.0),
]

body_outer = (
    cq.Workplane("XY")
    .box(
        body_length_x,
        body_width_y,
        body_height_z,
        centered=(True, True, False),
    )
)

cavity = (
    cq.Workplane("XY", origin=(0.0, 0.0, wall_thickness))
    .box(
        body_length_x - 2.0 * wall_thickness,
        body_width_y - 2.0 * wall_thickness,
        body_height_z - wall_thickness,
        centered=(True, True, False),
    )
)

side_port = (
    cq.Workplane(
        "YZ",
        origin=(port_start_x, port_center_y, port_center_z),
    )
    .circle(port_diameter / 2.0)
    .extrude(port_length_x)
)

slot_rectangle = (
    cq.Workplane(
        "XY",
        origin=(slot_center_x, slot_center_y, 0.0),
    )
    .rect(slot_straight_length_x, slot_width_y)
    .extrude(wall_thickness)
)
slot_ends = (
    cq.Workplane(
        "XY",
        origin=(slot_center_x, slot_center_y, 0.0),
    )
    .pushPoints(
        [
            (-slot_straight_length_x / 2.0, 0.0),
            (slot_straight_length_x / 2.0, 0.0),
        ]
    )
    .circle(slot_radius)
    .extrude(wall_thickness)
)
floor_slot = slot_rectangle.union(slot_ends)

body = body_outer.cut(cavity).cut(side_port).cut(floor_slot).clean()

lid_outer = (
    cq.Workplane("XY", origin=(0.0, 0.0, lid_bottom_z))
    .box(
        lid_length_x,
        lid_width_y,
        lid_thickness_z,
        centered=(True, True, False),
    )
)
through_holes = (
    cq.Workplane("XY", origin=(0.0, 0.0, lid_bottom_z))
    .pushPoints(hole_positions)
    .circle(hole_diameter / 2.0)
    .extrude(lid_thickness_z)
)
counterbores = (
    cq.Workplane(
        "XY",
        origin=(
            0.0,
            0.0,
            lid_bottom_z + lid_thickness_z - counterbore_depth,
        ),
    )
    .pushPoints(hole_positions)
    .circle(counterbore_diameter / 2.0)
    .extrude(counterbore_depth)
)
lid = lid_outer.cut(through_holes).cut(counterbores).clean()

result = cq.Compound.makeCompound([body.val(), lid.val()])
