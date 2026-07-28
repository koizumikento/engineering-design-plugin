"""build123d candidate model for the L-bracket template intent."""

from build123d import (
    Align,
    Axis,
    Box,
    BuildPart,
    BuildSketch,
    Cylinder,
    Part,
    Plane,
    Polygon,
    Pos,
    extrude,
    fillet,
)


WIDTH = 40.0
LEG1_LENGTH = 50.0
LEG2_LENGTH = 60.0
THICKNESS = 5.0
CORNER_FILLET = 8.0
HOLE_DIAMETER = 6.4
LEG1_HOLE_POSITION = 25.0
LEG2_HOLE_POSITION = 30.0
RIB_THICKNESS = 3.0
RIB_HEIGHT = 15.0


def build() -> Part:
    align_min = (Align.MIN, Align.MIN, Align.MIN)
    horizontal = Box(LEG1_LENGTH, WIDTH, THICKNESS, align=align_min)
    vertical = Box(THICKNESS, WIDTH, LEG2_LENGTH, align=align_min)
    bracket = horizontal + vertical

    inner_edges = [
        edge
        for edge in bracket.edges().filter_by(Axis.Y)
        if abs(edge.center().X - THICKNESS) < 1e-6
        and abs(edge.center().Z - THICKNESS) < 1e-6
    ]
    assert len(inner_edges) == 1
    bracket = fillet(inner_edges, radius=CORNER_FILLET)

    base_hole = (
        Pos(LEG1_HOLE_POSITION, WIDTH / 2.0, THICKNESS / 2.0)
        * Cylinder(HOLE_DIAMETER / 2.0, THICKNESS + 2.0)
    )
    wall_hole = (
        Pos(THICKNESS / 2.0, WIDTH / 2.0, LEG2_HOLE_POSITION)
        * Cylinder(
            HOLE_DIAMETER / 2.0,
            THICKNESS + 2.0,
            rotation=(0.0, 90.0, 0.0),
        )
    )
    bracket = bracket - base_hole - wall_hole

    rib_plane = Plane(
        origin=(0.0, WIDTH / 2.0 + RIB_THICKNESS / 2.0, 0.0),
        x_dir=(1.0, 0.0, 0.0),
        z_dir=(0.0, -1.0, 0.0),
    )
    with BuildPart() as rib_builder:
        with BuildSketch(rib_plane):
            Polygon(
                (THICKNESS - 1.0, THICKNESS - 1.0),
                (THICKNESS + RIB_HEIGHT, THICKNESS - 1.0),
                (THICKNESS - 1.0, THICKNESS + RIB_HEIGHT),
            )
        extrude(amount=RIB_THICKNESS)
    return (bracket + rib_builder.part).clean()


result = build()
assert result.is_valid
