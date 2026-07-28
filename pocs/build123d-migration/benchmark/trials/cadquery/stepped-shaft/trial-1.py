import cadquery as cq


# Nominal dimensions in millimetres.
lower_diameter = 36.0
lower_z_start = 0.0
lower_length = 12.0

middle_diameter = 24.0
middle_z_start = 12.0
middle_length = 30.0

upper_diameter = 16.0
upper_z_start = 42.0
upper_length = 20.0

bore_diameter = 6.0
shaft_length = 62.0

keyway_width = 6.0
keyway_y_start = 9.0
keyway_y_end = 20.0
keyway_z_start = 16.0
keyway_z_end = 38.0

top_chamfer = 1.0


# R1-R3: three coaxial shaft steps, all based on the explicit +Z datum.
lower_step = (
    cq.Workplane("XY", origin=(0.0, 0.0, lower_z_start))
    .circle(lower_diameter / 2.0)
    .extrude(lower_length)
)
middle_step = (
    cq.Workplane("XY", origin=(0.0, 0.0, middle_z_start))
    .circle(middle_diameter / 2.0)
    .extrude(middle_length)
)
upper_step = (
    cq.Workplane("XY", origin=(0.0, 0.0, upper_z_start))
    .circle(upper_diameter / 2.0)
    .extrude(upper_length)
    .edges(">Z")
    .chamfer(top_chamfer)
)

# R4: fuse the steps and cut the concentric through bore.
bore = (
    cq.Workplane("XY", origin=(0.0, 0.0, lower_z_start))
    .circle(bore_diameter / 2.0)
    .extrude(shaft_length)
)

# R5: explicit rectangular cutter creates the +Y-open middle-step keyway.
keyway = cq.Workplane(
    "XY", origin=(0.0, keyway_y_start, keyway_z_start)
).box(
    keyway_width,
    keyway_y_end - keyway_y_start,
    keyway_z_end - keyway_z_start,
    centered=(True, False, False),
)

# R6-R7: only the upper outer top edge was chamfered; all other edges remain sharp.
result = (
    lower_step
    .union(middle_step)
    .union(upper_step)
    .cut(bore)
    .cut(keyway)
    .clean()
)
