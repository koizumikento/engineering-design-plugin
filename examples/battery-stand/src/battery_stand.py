"""Parametric five-level battery rack assembly in build123d."""

from build123d import Align, Box, Compound, Pos


LEVEL_COUNT = 5
BASE_WIDTH = 380.0
BASE_DEPTH = 260.0
BASE_THICKNESS = 8.0
SIDE_PANEL_THICKNESS = 8.0
SIDE_PANEL_DEPTH = 222.0
SIDE_PANEL_HEIGHT = 590.0
TRAY_WIDTH = 318.0
TRAY_DEPTH = 146.0
TRAY_THICKNESS = 4.0
TRAY_WALL_HEIGHT = 18.0
LEVEL_PITCH = 108.0
FIRST_LEVEL_Z = 20.0
LEVEL_SETBACK = 8.0


def centered_box(x: float, y: float, z: float):
    return Box(
        x,
        y,
        z,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )


children = []

base = centered_box(BASE_WIDTH, BASE_DEPTH, BASE_THICKNESS)
base.label = "base"
children.append(base)

panel_x = BASE_WIDTH / 2 - SIDE_PANEL_THICKNESS / 2
for label, x_position in (("side:left", -panel_x), ("side:right", panel_x)):
    panel = Pos(x_position, 0, BASE_THICKNESS) * centered_box(
        SIDE_PANEL_THICKNESS,
        SIDE_PANEL_DEPTH,
        SIDE_PANEL_HEIGHT,
    )
    panel.label = label
    children.append(panel)

for level in range(LEVEL_COUNT):
    z_position = FIRST_LEVEL_Z + level * LEVEL_PITCH
    y_position = level * LEVEL_SETBACK
    tray = Pos(0, y_position, z_position) * centered_box(
        TRAY_WIDTH,
        TRAY_DEPTH,
        TRAY_THICKNESS,
    )
    rear = Pos(0, y_position + TRAY_DEPTH / 2 - 2, z_position) * centered_box(
        TRAY_WIDTH,
        4.0,
        TRAY_WALL_HEIGHT,
    )
    left = Pos(-TRAY_WIDTH / 2 + 2, y_position, z_position) * centered_box(
        4.0,
        TRAY_DEPTH,
        TRAY_WALL_HEIGHT,
    )
    right = Pos(TRAY_WIDTH / 2 - 2, y_position, z_position) * centered_box(
        4.0,
        TRAY_DEPTH,
        TRAY_WALL_HEIGHT,
    )
    shelf = (tray + rear + left + right).clean()
    shelf.label = f"shelf:{level + 1}"
    children.append(shelf)

top_brace = Pos(0, 40, BASE_THICKNESS + SIDE_PANEL_HEIGHT - 18) * centered_box(
    BASE_WIDTH - 2 * SIDE_PANEL_THICKNESS,
    18.0,
    18.0,
)
top_brace.label = "top_brace"
children.append(top_brace)

result = Compound(label="battery_rack", children=children)
cad_metadata = {
    "units": "mm",
    "kind": "assembly",
    "level_count": LEVEL_COUNT,
}
cad_expectations = {
    "tolerance_mm": 1e-6,
    "topology": {"solids": len(children)},
    "bounding_box": {
        "x_len": BASE_WIDTH,
        "y_len": BASE_DEPTH,
        "z_len": BASE_THICKNESS + SIDE_PANEL_HEIGHT,
    },
}

assert result.is_valid
