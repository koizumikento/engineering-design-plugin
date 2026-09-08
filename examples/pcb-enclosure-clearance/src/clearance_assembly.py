"""Static PCB/enclosure envelopes in mm; example clearances are not process tolerances."""

from build123d import Align, Box, Compound, Location

align = (Align.CENTER, Align.CENTER, Align.MIN)
floor_thickness = 2.0
pcb_seating_z = 5.0
pcb_thickness = 1.6
bottom_component_height = 2.0
top_component_height = 1.4
lid_seating_z = 10.0

enclosure = Box(44, 24, 10, align=align) - Box(40, 20, 10, align=align).moved(Location((0, 0, floor_thickness)))
enclosure.label = "enclosure"
pcb = Box(36, 16, pcb_thickness, align=align).moved(Location((0, 0, pcb_seating_z)))
pcb.label = "pcb"
bottom = Box(8, 6, bottom_component_height, align=align).moved(Location((0, 0, pcb_seating_z - bottom_component_height)))
bottom.label = "bottom_component"
top = Box(8, 6, top_component_height, align=align).moved(Location((0, 0, pcb_seating_z + pcb_thickness)))
top.label = "top_component"
lid = Box(44, 24, 2, align=align).moved(Location((0, 0, lid_seating_z)))
lid.label = "lid"

result = Compound(children=[enclosure, pcb, bottom, top, lid], label="pcb_enclosure")
cad_metadata = {
    "units": "mm",
    "coordinate_system": "origin at enclosure exterior floor center; XY footprint; +Z toward lid",
    "scope": "static nominal envelopes; no hardware, thermal, motion, or manufacturing validation",
}
cad_expectations = {
    "topology": {"solids": 5},
    "bounding_box": {"x_len": 44.0, "y_len": 24.0, "z_len": 12.0},
    "components": {
        "bottom_component": {"bounding_box": {"z_min": 3.0, "z_max": 5.0}},
        "top_component": {"bounding_box": {"z_min": 6.6, "z_max": 8.0}},
        "lid": {"bounding_box": {"z_min": 10.0, "z_max": 12.0}},
    },
}
