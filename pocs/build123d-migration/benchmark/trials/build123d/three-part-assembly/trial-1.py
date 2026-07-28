from build123d import Align, Box, Compound, Cylinder, Pos


# Assembly datum A0 is the world origin with identity rotation.

# Base plate parameters and local component geometry at B0.
base_length_x = 100.0
base_width_y = 60.0
base_height_z = 6.0
base_hole_radius = 3.0
base_hole_centers = (
    (-40.0, -20.0),
    (-40.0, 20.0),
    (40.0, -20.0),
    (40.0, 20.0),
)
base_translation = (0.0, 0.0, 0.0)

base_plate_local = Box(
    base_length_x,
    base_width_y,
    base_height_z,
    align=(Align.CENTER, Align.CENTER, Align.MIN),
)
for hole_x, hole_y in base_hole_centers:
    base_plate_local = base_plate_local - (
        Pos(hole_x, hole_y, 0.0)
        * Cylinder(
            base_hole_radius,
            base_height_z,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
    )
base_plate = Pos(*base_translation) * base_plate_local.clean()

# Spacer ring parameters and local component geometry at S0.
spacer_outer_radius = 20.0
spacer_inner_radius = 10.0
spacer_height_z = 10.0
spacer_translation = (0.0, 0.0, 16.0)

spacer_outer_local = Cylinder(
    spacer_outer_radius,
    spacer_height_z,
    align=(Align.CENTER, Align.CENTER, Align.MIN),
)
spacer_inner_local = Cylinder(
    spacer_inner_radius,
    spacer_height_z,
    align=(Align.CENTER, Align.CENTER, Align.MIN),
)
spacer_ring_local = (spacer_outer_local - spacer_inner_local).clean()
spacer_ring = Pos(*spacer_translation) * spacer_ring_local

# Top plate parameters and local component geometry at T0.
top_length_x = 60.0
top_width_y = 40.0
top_height_z = 5.0
top_hole_radius = 6.0
top_translation = (0.0, 0.0, 36.0)

top_plate_blank_local = Box(
    top_length_x,
    top_width_y,
    top_height_z,
    align=(Align.CENTER, Align.CENTER, Align.MIN),
)
top_hole_local = Cylinder(
    top_hole_radius,
    top_height_z,
    align=(Align.CENTER, Align.CENTER, Align.MIN),
)
top_plate_local = (top_plate_blank_local - top_hole_local).clean()
top_plate = Pos(*top_translation) * top_plate_local

result = Compound(children=[base_plate, spacer_ring, top_plate])
