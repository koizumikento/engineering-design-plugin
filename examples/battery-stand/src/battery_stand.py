"""
Battery rack for 4 batteries per level and 5 levels.

Specification:
examples/battery-stand/specs/battery-stand-spec.md
"""

import cadquery as cq

# Assumed battery dimensions
BATTERY_LENGTH = 151.0
BATTERY_WIDTH = 65.0
BATTERY_HEIGHT = 94.0
BATTERY_MASS = 2.3  # kg, typical 12V 7Ah SLA battery

# Rack layout
LEVEL_COUNT = 5
CELLS_X = 2
CELLS_Y = 2
LEVEL_SETBACK = 8.0
LEVEL_PITCH = 108.0

# Shelf dimensions
CELL_CLEARANCE_X = 1.0
CELL_CLEARANCE_Y = 1.0
DIVIDER_THICKNESS = 4.0
TRAY_WALL_THICKNESS = 4.0
TRAY_PLATE_THICKNESS = 4.0
SIDE_WALL_HEIGHT = 18.0
FRONT_LIP_HEIGHT = 10.0

# Frame dimensions
BASE_WIDTH = 380.0
BASE_DEPTH = 260.0
BASE_THICKNESS = 8.0
SIDE_PANEL_THICKNESS = 8.0
SIDE_PANEL_DEPTH = 222.0
SIDE_PANEL_HEIGHT = 590.0
CROSSBAR_HEIGHT = 12.0
CROSSBAR_DEPTH = 14.0
FIRST_LEVEL_Z = BASE_THICKNESS + CROSSBAR_HEIGHT
BASE_SHELF_CENTER_Y = 18.0

# Base mounting
BASE_HOLE_DIAMETER = 8.5
BASE_HOLE_X = 145.0
BASE_HOLE_Y = 100.0
BASE_SLOT_LENGTH = 220.0
BASE_SLOT_WIDTH = 12.0
BASE_SLOT_Y = (-55.0, 0.0, 55.0)

# Derived shelf dimensions
CELL_LENGTH = BATTERY_LENGTH + (2 * CELL_CLEARANCE_X)
CELL_DEPTH = BATTERY_WIDTH + (2 * CELL_CLEARANCE_Y)
TRAY_INNER_WIDTH = (CELLS_X * CELL_LENGTH) + ((CELLS_X - 1) * DIVIDER_THICKNESS)
TRAY_INNER_DEPTH = (CELLS_Y * CELL_DEPTH) + ((CELLS_Y - 1) * DIVIDER_THICKNESS)
TRAY_OUTER_WIDTH = TRAY_INNER_WIDTH + (2 * TRAY_WALL_THICKNESS)
TRAY_OUTER_DEPTH = TRAY_INNER_DEPTH + (2 * TRAY_WALL_THICKNESS)
OVERALL_HEIGHT = BASE_THICKNESS + SIDE_PANEL_HEIGHT


def make_base() -> cq.Workplane:
    base = (
        cq.Workplane("XY")
        .box(BASE_WIDTH, BASE_DEPTH, BASE_THICKNESS, centered=(True, True, False))
        .edges("|Z")
        .fillet(10.0)
    )

    base = (
        base.faces(">Z")
        .workplane()
        .pushPoints([(0.0, y) for y in BASE_SLOT_Y])
        .slot2D(BASE_SLOT_LENGTH, BASE_SLOT_WIDTH)
        .cutThruAll()
    )

    return (
        base.faces(">Z")
        .workplane()
        .pushPoints(
            [
                (-BASE_HOLE_X, -BASE_HOLE_Y),
                (-BASE_HOLE_X, BASE_HOLE_Y),
                (BASE_HOLE_X, -BASE_HOLE_Y),
                (BASE_HOLE_X, BASE_HOLE_Y),
            ]
        )
        .hole(BASE_HOLE_DIAMETER)
    )


def make_side_panel() -> cq.Workplane:
    return cq.Workplane("XY").box(
        SIDE_PANEL_THICKNESS,
        SIDE_PANEL_DEPTH,
        SIDE_PANEL_HEIGHT,
        centered=(True, True, False),
    )


def make_shelf() -> cq.Workplane:
    shelf = cq.Workplane("XY").box(
        TRAY_OUTER_WIDTH,
        TRAY_OUTER_DEPTH,
        TRAY_PLATE_THICKNESS,
        centered=(True, True, False),
    )

    rear_wall = (
        cq.Workplane("XY")
        .workplane(offset=TRAY_PLATE_THICKNESS)
        .center(0.0, (TRAY_OUTER_DEPTH - TRAY_WALL_THICKNESS) / 2)
        .box(
            TRAY_OUTER_WIDTH,
            TRAY_WALL_THICKNESS,
            SIDE_WALL_HEIGHT,
            centered=(True, True, False),
        )
    )
    front_lip = (
        cq.Workplane("XY")
        .workplane(offset=TRAY_PLATE_THICKNESS)
        .center(0.0, -(TRAY_OUTER_DEPTH - TRAY_WALL_THICKNESS) / 2)
        .box(
            TRAY_OUTER_WIDTH,
            TRAY_WALL_THICKNESS,
            FRONT_LIP_HEIGHT,
            centered=(True, True, False),
        )
    )
    left_wall = (
        cq.Workplane("XY")
        .workplane(offset=TRAY_PLATE_THICKNESS)
        .center(-(TRAY_OUTER_WIDTH - TRAY_WALL_THICKNESS) / 2, 0.0)
        .box(
            TRAY_WALL_THICKNESS,
            TRAY_OUTER_DEPTH,
            SIDE_WALL_HEIGHT,
            centered=(True, True, False),
        )
    )
    right_wall = (
        cq.Workplane("XY")
        .workplane(offset=TRAY_PLATE_THICKNESS)
        .center((TRAY_OUTER_WIDTH - TRAY_WALL_THICKNESS) / 2, 0.0)
        .box(
            TRAY_WALL_THICKNESS,
            TRAY_OUTER_DEPTH,
            SIDE_WALL_HEIGHT,
            centered=(True, True, False),
        )
    )
    x_divider = (
        cq.Workplane("XY")
        .workplane(offset=TRAY_PLATE_THICKNESS)
        .box(
            DIVIDER_THICKNESS,
            TRAY_INNER_DEPTH,
            SIDE_WALL_HEIGHT - 2.0,
            centered=(True, True, False),
        )
    )
    y_divider = (
        cq.Workplane("XY")
        .workplane(offset=TRAY_PLATE_THICKNESS)
        .box(
            TRAY_INNER_WIDTH,
            DIVIDER_THICKNESS,
            SIDE_WALL_HEIGHT - 2.0,
            centered=(True, True, False),
        )
    )

    shelf = shelf.union(rear_wall)
    shelf = shelf.union(front_lip)
    shelf = shelf.union(left_wall)
    shelf = shelf.union(right_wall)
    shelf = shelf.union(x_divider)
    shelf = shelf.union(y_divider)

    return shelf.edges(">Z").chamfer(0.8)


def make_crossbar(y_center: float, z_base: float) -> cq.Workplane:
    return (
        cq.Workplane("XY")
        .workplane(offset=z_base)
        .center(0.0, y_center)
        .box(
            BASE_WIDTH - (2 * SIDE_PANEL_THICKNESS),
            CROSSBAR_DEPTH,
            CROSSBAR_HEIGHT,
            centered=(True, True, False),
        )
    )


def battery_centers(level_index: int) -> list[tuple[float, float, float]]:
    shelf_center_y = BASE_SHELF_CENTER_Y + (level_index * LEVEL_SETBACK)
    shelf_bottom_z = FIRST_LEVEL_Z + (level_index * LEVEL_PITCH)
    x_step = CELL_LENGTH + DIVIDER_THICKNESS
    y_step = CELL_DEPTH + DIVIDER_THICKNESS
    x_positions = (-x_step / 2, x_step / 2)
    y_positions = (-y_step / 2, y_step / 2)
    z_center = shelf_bottom_z + TRAY_PLATE_THICKNESS + (BATTERY_HEIGHT / 2)

    centers = []
    for x_pos in x_positions:
        for y_pos in y_positions:
            centers.append((x_pos, shelf_center_y + y_pos, z_center))
    return centers


base = make_base()
result = base

side_panel_y = (BASE_DEPTH - SIDE_PANEL_DEPTH) / 2
side_panel_x = (BASE_WIDTH / 2) - (SIDE_PANEL_THICKNESS / 2)
left_panel = make_side_panel().translate((-side_panel_x, side_panel_y, BASE_THICKNESS))
right_panel = make_side_panel().translate((side_panel_x, side_panel_y, BASE_THICKNESS))
result = result.union(left_panel).union(right_panel)

top_brace = (
    cq.Workplane("XY")
    .workplane(offset=OVERALL_HEIGHT - 24.0)
    .center(0.0, BASE_SHELF_CENTER_Y + 52.0)
    .box(
        BASE_WIDTH - (2 * SIDE_PANEL_THICKNESS),
        18.0,
        18.0,
        centered=(True, True, False),
    )
)
result = result.union(top_brace)

for level in range(LEVEL_COUNT):
    shelf_center_y = BASE_SHELF_CENTER_Y + (level * LEVEL_SETBACK)
    shelf_bottom_z = FIRST_LEVEL_Z + (level * LEVEL_PITCH)

    front_bar_y = shelf_center_y - (TRAY_OUTER_DEPTH / 2) + 10.0
    rear_bar_y = shelf_center_y + (TRAY_OUTER_DEPTH / 2) - 10.0

    result = result.union(make_crossbar(front_bar_y, shelf_bottom_z - CROSSBAR_HEIGHT))
    result = result.union(make_crossbar(rear_bar_y, shelf_bottom_z - CROSSBAR_HEIGHT))
    result = result.union(make_shelf().translate((0.0, shelf_center_y, shelf_bottom_z)))


shape = result.val()
assert shape.isValid(), "The generated rack shape is invalid"

loaded_battery_centers = []
for level in range(LEVEL_COUNT):
    loaded_battery_centers.extend(battery_centers(level))

loaded_cg_x = sum(center[0] for center in loaded_battery_centers) / len(loaded_battery_centers)
loaded_cg_y = sum(center[1] for center in loaded_battery_centers) / len(loaded_battery_centers)
loaded_cg_z = sum(center[2] for center in loaded_battery_centers) / len(loaded_battery_centers)

front_margin = (BASE_DEPTH / 2) + loaded_cg_y
rear_margin = (BASE_DEPTH / 2) - loaded_cg_y
side_margin = (BASE_WIDTH / 2) - abs(loaded_cg_x)
total_battery_mass = len(loaded_battery_centers) * BATTERY_MASS

bb = shape.BoundingBox()

print("=== Battery Rack 4x5 ===")
print(f"Assumed battery size: {BATTERY_LENGTH:.1f} x {BATTERY_WIDTH:.1f} x {BATTERY_HEIGHT:.1f} mm")
print(f"Levels / batteries per level: {LEVEL_COUNT} / {CELLS_X * CELLS_Y}")
print(f"Overall size: {bb.xlen:.1f} x {bb.ylen:.1f} x {bb.zlen:.1f} mm")
print(f"Shelf inner size: {TRAY_INNER_WIDTH:.1f} x {TRAY_INNER_DEPTH:.1f} x {SIDE_WALL_HEIGHT:.1f} mm")
print(f"Estimated loaded battery mass: {total_battery_mass:.1f} kg")
print(f"Battery-only CG: x={loaded_cg_x:.1f}, y={loaded_cg_y:.1f}, z={loaded_cg_z:.1f} mm")
print(
    "Support margins (battery-only projection): "
    f"front={front_margin:.1f} mm, rear={rear_margin:.1f} mm, side={side_margin:.1f} mm"
)
print(f"Rack volume: {shape.Volume():.1f} mm^3")
