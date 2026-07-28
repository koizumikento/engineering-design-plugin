"""Corrected CadQuery comparison model for the L-bracket template intent."""

import cadquery as cq


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


def build() -> cq.Workplane:
    horizontal = cq.Workplane("XY").box(
        LEG1_LENGTH,
        WIDTH,
        THICKNESS,
        centered=(False, False, False),
    )
    vertical = cq.Workplane("XY").box(
        THICKNESS,
        WIDTH,
        LEG2_LENGTH,
        centered=(False, False, False),
    )
    bracket = horizontal.union(vertical)

    inner_edges = [
        edge
        for edge in bracket.edges("|Y").vals()
        if abs(edge.Center().x - THICKNESS) < 1e-6
        and abs(edge.Center().z - THICKNESS) < 1e-6
    ]
    assert len(inner_edges) == 1
    bracket = bracket.newObject(inner_edges).fillet(CORNER_FILLET)

    base_hole = (
        cq.Workplane("XY", origin=(0.0, 0.0, -1.0))
        .center(LEG1_HOLE_POSITION, WIDTH / 2.0)
        .circle(HOLE_DIAMETER / 2.0)
        .extrude(THICKNESS + 2.0)
    )
    wall_hole = (
        cq.Workplane("YZ", origin=(-1.0, 0.0, 0.0))
        .center(WIDTH / 2.0, LEG2_HOLE_POSITION)
        .circle(HOLE_DIAMETER / 2.0)
        .extrude(THICKNESS + 2.0)
    )
    bracket = bracket.cut(base_hole).cut(wall_hole)

    rib = (
        cq.Workplane("XZ", origin=(0.0, WIDTH / 2.0 + RIB_THICKNESS / 2.0, 0.0))
        .moveTo(THICKNESS - 1.0, THICKNESS - 1.0)
        .lineTo(THICKNESS + RIB_HEIGHT, THICKNESS - 1.0)
        .lineTo(THICKNESS - 1.0, THICKNESS + RIB_HEIGHT)
        .close()
        .extrude(RIB_THICKNESS)
    )
    return bracket.union(rib).clean()


result = build()
assert result.val().isValid()
