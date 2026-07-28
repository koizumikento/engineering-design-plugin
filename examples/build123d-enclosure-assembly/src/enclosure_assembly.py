"""Two-part enclosure assembly for the build123d production route."""

from build123d import Align, Box, Compound, Location, RigidJoint


base_width = 60.0
base_depth = 40.0
base_height = 4.0
lid_width = 58.0
lid_depth = 38.0
lid_thickness = 3.0

base = Box(
    base_width,
    base_depth,
    base_height,
    align=(Align.CENTER, Align.CENTER, Align.MIN),
)
base.label = "base"

lid = Box(
    lid_width,
    lid_depth,
    lid_thickness,
    align=(Align.CENTER, Align.CENTER, Align.MIN),
)
lid.label = "lid"

RigidJoint(
    label="lid_seat",
    to_part=base,
    joint_location=Location((0, 0, base_height)),
)
RigidJoint(
    label="underside",
    to_part=lid,
    joint_location=Location((0, 0, 0)),
)

# The joint on the fixed base moves the lid joint into coincidence.
base.joints["lid_seat"].connect_to(lid.joints["underside"])

result = Compound(
    label="enclosure_assembly",
    children=[base, lid],
)

cad_metadata = {
    "units": "mm",
    "kind": "assembly",
    "coordinate_system": {
        "origin": "base footprint center at its bottom face",
        "xy": "base footprint",
        "positive_z": "from base toward lid",
    },
    "relationships": [
        {
            "type": "rigid",
            "fixed": "base.lid_seat",
            "moving": "lid.underside",
        }
    ],
    "step_constraint_semantics": "resolved static placement only",
}

cad_expectations = {
    "tolerance_mm": 1e-6,
    "topology": {"solids": 2},
    "bounding_box": {
        "x_len": 60.0,
        "y_len": 40.0,
        "z_len": 7.0,
    },
    "components": {
        "base": {
            "position": {"x": 0.0, "y": 0.0, "z": 0.0},
            "bounding_box": {"z_min": 0.0, "z_max": 4.0},
        },
        "lid": {
            "position": {"x": 0.0, "y": 0.0, "z": 4.0},
            "bounding_box": {"z_min": 4.0, "z_max": 7.0},
        },
    },
}
