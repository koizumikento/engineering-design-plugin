import cadquery as cq


# R1: block dimensions and bottom-face datum
block_x = 50.0
block_y = 40.0
block_z = 20.0

# R2: vertical-edge fillet
vertical_fillet_radius = 3.0

# R3: four Z-through holes
hole_diameter = 5.0
hole_radius = hole_diameter / 2.0
hole_centers = [
    (-15.0, -10.0),
    (-15.0, 10.0),
    (15.0, -10.0),
    (15.0, 10.0),
]

# R4: centered blind pocket opening from the top face
pocket_x = 20.0
pocket_y = 12.0
pocket_depth = 4.0
pocket_bottom_z = block_z - pocket_depth

body = (
    cq.Workplane("XY")
    .box(block_x, block_y, block_z, centered=(True, True, False))
    .edges("|Z")
    .fillet(vertical_fillet_radius)
)

through_holes = (
    cq.Workplane("XY")
    .pushPoints(hole_centers)
    .circle(hole_radius)
    .extrude(block_z)
)

blind_pocket = (
    cq.Workplane("XY", origin=(0.0, 0.0, pocket_bottom_z))
    .rect(pocket_x, pocket_y)
    .extrude(pocket_depth)
)

result = body.cut(through_holes).cut(blind_pocket).clean()
