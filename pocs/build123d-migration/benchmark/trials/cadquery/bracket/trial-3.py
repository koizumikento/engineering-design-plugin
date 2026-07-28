import cadquery as cq


# R1: foot dimensions and datum
foot_width = 60.0
foot_depth = 40.0
foot_thickness = 8.0

# R2: vertical plate dimensions and placement
plate_width = 60.0
plate_thickness = 8.0
plate_height = 40.0
plate_center_y = 16.0
plate_base_z = 8.0

# R3: foot mounting holes
foot_hole_diameter = 6.0
foot_hole_centers = [(-20.0, -5.0), (20.0, -5.0)]

# R4: vertical plate holes
plate_hole_diameter = 8.0
plate_hole_centers_xz = [(-18.0, 28.0), (18.0, 28.0)]
plate_front_y = 12.0
plate_back_y = 20.0

# R5: full inside corner fillet
inside_fillet_radius = 4.0
inside_corner_point = (0.0, 12.0, 8.0)

# R6: centered triangular rib
rib_x_min = -3.0
rib_x_max = 3.0
rib_yz_vertices = [(0.0, 8.0), (12.0, 8.0), (12.0, 20.0)]

foot = cq.Workplane("XY").box(
    foot_width,
    foot_depth,
    foot_thickness,
    centered=(True, True, False),
)

plate = cq.Workplane("XY", origin=(0.0, plate_center_y, plate_base_z)).box(
    plate_width,
    plate_thickness,
    plate_height,
    centered=(True, True, False),
)

bracket = foot.union(plate).clean()
bracket = bracket.edges(
    cq.selectors.NearestToPointSelector(inside_corner_point)
).fillet(inside_fillet_radius)

rib = (
    cq.Workplane("YZ", origin=(rib_x_min, 0.0, 0.0))
    .polyline(rib_yz_vertices)
    .close()
    .extrude(rib_x_max - rib_x_min)
)
bracket = bracket.union(rib).clean()

foot_holes = (
    cq.Workplane("XY")
    .pushPoints(foot_hole_centers)
    .circle(foot_hole_diameter / 2.0)
    .extrude(foot_thickness)
)

plate_holes = (
    cq.Workplane("XZ", origin=(0.0, plate_back_y, 0.0))
    .pushPoints(plate_hole_centers_xz)
    .circle(plate_hole_diameter / 2.0)
    .extrude(plate_back_y - plate_front_y)
)

result = bracket.cut(foot_holes).cut(plate_holes).clean()
