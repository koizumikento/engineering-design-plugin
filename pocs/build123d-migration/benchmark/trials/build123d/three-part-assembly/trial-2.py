from build123d import Align, Box, Compound, Cylinder, Pos


# Assembly datum A0 is the world origin with identity rotation.

# Base plate parameters in local datum B0.
base_length_x = 100.0
base_width_y = 60.0
base_thickness_z = 6.0
base_hole_radius = 3.0
base_hole_x_positions = (-40.0, 40.0)
base_hole_y_positions = (-20.0, 20.0)
base_translation = (0.0, 0.0, 0.0)

base_local = Box(
    base_length_x,
    base_width_y,
    base_thickness_z,
    align=(Align.CENTER, Align.CENTER, Align.MIN),
)
for hole_x in base_hole_x_positions:
    for hole_y in base_hole_y_positions:
        base_hole = Pos(hole_x, hole_y, 0.0) * Cylinder(
            base_hole_radius,
            base_thickness_z,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        base_local = base_local - base_hole
base_plate = Pos(*base_translation) * base_local.clean()

# Spacer ring parameters in local datum S0.
spacer_outer_radius = 20.0
spacer_inner_radius = 10.0
spacer_height_z = 10.0
spacer_translation = (0.0, 0.0, 16.0)

spacer_outer = Cylinder(
    spacer_outer_radius,
    spacer_height_z,
    align=(Align.CENTER, Align.CENTER, Align.MIN),
)
spacer_inner = Cylinder(
    spacer_inner_radius,
    spacer_height_z,
    align=(Align.CENTER, Align.CENTER, Align.MIN),
)
spacer_local = (spacer_outer - spacer_inner).clean()
spacer_ring = Pos(*spacer_translation) * spacer_local

# Top plate parameters in local datum T0.
top_length_x = 60.0
top_width_y = 40.0
top_thickness_z = 5.0
top_hole_radius = 6.0
top_translation = (0.0, 0.0, 36.0)

top_local = Box(
    top_length_x,
    top_width_y,
    top_thickness_z,
    align=(Align.CENTER, Align.CENTER, Align.MIN),
)
top_hole = Cylinder(
    top_hole_radius,
    top_thickness_z,
    align=(Align.CENTER, Align.CENTER, Align.MIN),
)
top_plate = Pos(*top_translation) * (top_local - top_hole).clean()

result = Compound(children=[base_plate, spacer_ring, top_plate])
