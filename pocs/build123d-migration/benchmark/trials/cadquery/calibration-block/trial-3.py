import cadquery as cq


# R1: datum-centred rectangular block, with the bottom face at Z = 0.
block_x = 50.0
block_y = 40.0
block_z = 20.0

# R2: fillet only the four edges parallel to Z.
vertical_edge_fillet_radius = 3.0

# R3: four Z-through holes.
hole_diameter = 5.0
hole_radius = hole_diameter / 2.0
hole_centres = [
    (-15.0, -10.0),
    (-15.0, 10.0),
    (15.0, -10.0),
    (15.0, 10.0),
]

# R4: centred rectangular pocket, cut 4 mm down from the top face.
pocket_x = 20.0
pocket_y = 12.0
pocket_depth = 4.0
pocket_bottom_z = block_z - pocket_depth

block = (
    cq.Workplane("XY")
    .box(block_x, block_y, block_z, centered=(True, True, False))
    .edges("|Z")
    .fillet(vertical_edge_fillet_radius)
)

hole_tool = (
    cq.Workplane("XY", origin=(0.0, 0.0, 0.0))
    .pushPoints(hole_centres)
    .circle(hole_radius)
    .extrude(block_z)
)

pocket_tool = (
    cq.Workplane("XY", origin=(0.0, 0.0, pocket_bottom_z))
    .box(pocket_x, pocket_y, pocket_depth, centered=(True, True, False))
)

result = block.cut(hole_tool).cut(pocket_tool).clean()
