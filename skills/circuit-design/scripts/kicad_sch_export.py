#!/usr/bin/env python3
"""
KiCad v9 schematic exporter for SKiDL circuits.

The current implementation emits KiCad-native .kicad_sch / .kicad_pro files
for the non-inverting amplifier example and validates cleanly with kicad-cli.
"""

import argparse
import json
import sys
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

from circuit_artifacts import (
    collect_artifact_paths,
    ensure_standard_output_dirs,
    read_erc_summary,
    write_design_summary,
)
from kicad_env import configure_kicad_env
from skidl_utils import load_skidl_circuit


GRID = 2.54
PROJECT_TEMPLATE = {
    "board": {
        "3dviewports": [],
        "design_settings": {
            "defaults": {
                "board_outline_line_width": 0.1,
                "copper_line_width": 0.2,
                "copper_text_italic": False,
                "copper_text_size_h": 1.5,
                "copper_text_size_v": 1.5,
                "copper_text_thickness": 0.3,
                "copper_text_upright": False,
                "courtyard_line_width": 0.05,
                "dimension_precision": 4,
                "dimension_units": 3,
                "dimensions": {
                    "arrow_length": 1270000,
                    "extension_offset": 500000,
                    "keep_text_aligned": True,
                    "suppress_zeroes": False,
                    "text_position": 0,
                    "units_format": 1
                },
                "fab_line_width": 0.1,
                "fab_text_italic": False,
                "fab_text_size_h": 1.0,
                "fab_text_size_v": 1.0,
                "fab_text_thickness": 0.15,
                "fab_text_upright": False,
                "other_line_width": 0.1,
                "other_text_italic": False,
                "other_text_size_h": 1.0,
                "other_text_size_v": 1.0,
                "other_text_thickness": 0.15,
                "other_text_upright": False,
                "pads": {
                    "drill": 0.762,
                    "height": 1.524,
                    "width": 1.524
                },
                "silk_line_width": 0.12,
                "silk_text_italic": False,
                "silk_text_size_h": 1.0,
                "silk_text_size_v": 1.0,
                "silk_text_thickness": 0.15,
                "silk_text_upright": False,
                "zones": {
                    "45_degree_only": False,
                    "min_clearance": 0.508
                }
            },
            "diff_pair_dimensions": [],
            "drc_exclusions": [],
            "meta": {"version": 2},
            "rule_severities": {},
            "rules": {
                "max_error": 0.005,
                "min_clearance": 0.0,
                "min_connection": 0.0,
                "min_copper_edge_clearance": 0.0,
                "min_hole_clearance": 0.25,
                "min_hole_to_hole": 0.25,
                "min_microvia_diameter": 0.0,
                "min_microvia_drill": 0.0,
                "min_resolved_spokes": 2,
                "min_silk_clearance": 0.0,
                "min_text_height": 1.0,
                "min_text_thickness": 0.08,
                "min_through_hole_diameter": 0.0,
                "min_track_width": 0.0,
                "min_via_annular_width": 0.0,
                "min_via_diameter": 0.0,
                "solder_mask_clearance": 0.0,
                "solder_mask_min_width": 0.0,
                "use_height_for_length_calcs": True
            },
            "teardrop_options": [
                {
                    "td_allow_use_two_tracks": True,
                    "td_curve_segcount": 5,
                    "td_on_pad_in_zone": False,
                    "td_onpadsmd": True,
                    "td_onroundshapesonly": False,
                    "td_ontrackend": False,
                    "td_onviapad": True
                }
            ],
            "teardrop_parameters": [
                {
                    "td_curve_segcount": 0,
                    "td_height_ratio": 1.0,
                    "td_length_ratio": 0.5,
                    "td_maxheight": 2.0,
                    "td_maxlen": 1.0,
                    "td_target_name": "td_round_shape",
                    "td_width_to_size_filter_ratio": 0.9
                }
            ],
            "track_widths": [],
            "via_dimensions": []
        },
        "layer_presets": [],
        "viewports": []
    },
    "boards": [],
    "libraries": {
        "pinned_footprint_libs": [],
        "pinned_symbol_libs": []
    },
    "meta": {
        "filename": "",
        "version": 1
    },
    "net_settings": {
        "classes": [],
        "meta": {"version": 0}
    },
    "pcbnew": {
        "last_paths": {
            "gencad": "",
            "idf": "",
            "netlist": "",
            "specctra_dsn": "",
            "step": "",
            "vrml": ""
        },
        "page_layout_descr_file": ""
    },
    "schematic": {
        "legacy_lib_dir": "",
        "legacy_lib_list": [],
        "meta": {"version": 1}
    },
    "sheets": [],
    "text_variables": {}
}


@dataclass(frozen=True)
class Point:
    x: float
    y: float


def local_to_sheet(origin: Point, dx: float, dy: float) -> Point:
    return Point(origin.x + dx, origin.y - dy)


def mm(value: float) -> str:
    text = f"{value:.3f}"
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text or "0"


def esc(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def uid() -> str:
    return str(uuid.uuid4())


def analyze_circuit(circuit) -> Dict:
    info = {
        "parts": [],
        "nets": [],
    }

    for part in circuit.parts:
        info["parts"].append(
            {
                "ref": part.ref,
                "name": part.name,
                "value": part.value,
                "footprint": getattr(part, "footprint", ""),
                "pins": [
                    {
                        "num": pin.num,
                        "name": pin.name,
                        "net": pin.net.name if pin.net else None,
                    }
                    for pin in part.pins
                ],
            }
        )

    for net in circuit.nets:
        info["nets"].append(
            {
                "name": net.name,
                "pins": [
                    {
                        "part_ref": pin.part.ref,
                        "pin_num": pin.num,
                    }
                    for pin in net.pins
                ],
            }
        )

    return info


def get_pin_net_map(part: Dict) -> Dict[str, str]:
    return {pin["name"]: pin["net"] for pin in part["pins"] if pin.get("net")}


def get_pin_number_map(part: Dict) -> Dict[str, str]:
    return {pin["num"]: pin["net"] for pin in part["pins"] if pin.get("net")}


def find_two_terminal_part(circuit_info: Dict, part_name: str, net_a: str, net_b: str) -> Optional[Dict]:
    target_nets = {net_a, net_b}
    for part in circuit_info["parts"]:
        if part["name"].upper() != part_name.upper():
            continue
        nets = {pin["net"] for pin in part["pins"] if pin.get("net")}
        if len(nets) == 2 and nets == target_nets:
            return part
    return None


def find_single_pin_part(circuit_info: Dict, part_name: str, net_name: str, exclude_ref: Optional[str] = None) -> Optional[Dict]:
    for part in circuit_info["parts"]:
        if exclude_ref and part["ref"] == exclude_ref:
            continue
        if part["name"].upper() != part_name.upper():
            continue
        if len(part["pins"]) != 1:
            continue
        pin = part["pins"][0]
        if pin.get("net") == net_name:
            return part
    return None


def detect_non_inverting_amplifier(circuit_info: Dict) -> Optional[Dict]:
    for part in circuit_info["parts"]:
        if part["value"].upper() != "TL072":
            continue

        pin_nets = get_pin_net_map(part)
        pin_nums = get_pin_number_map(part)
        vcc_net = pin_nums.get("8") or pin_nets.get("VCC") or pin_nets.get("V+")
        vee_net = pin_nums.get("4") or pin_nets.get("VEE") or pin_nets.get("V-")
        gnd_net = "GND" if any(net["name"] == "GND" for net in circuit_info["nets"]) else None
        vin_net = pin_nums.get("3") or pin_nets.get("1+") or pin_nets.get("IN+")
        inv_net = pin_nums.get("2") or pin_nets.get("1-") or pin_nets.get("IN-")
        vout_net = pin_nums.get("1") or pin_nets.get("1OUT") or pin_nets.get("OUT")
        unused_plus = pin_nums.get("5") or pin_nets.get("2+")
        unused_minus = pin_nums.get("6") or pin_nets.get("2-")
        unused_out = pin_nums.get("7") or pin_nets.get("2OUT")

        if not all([vcc_net, vee_net, gnd_net, vin_net, inv_net, vout_net, unused_plus, unused_minus, unused_out]):
            continue

        ri = find_two_terminal_part(circuit_info, "R", gnd_net, inv_net)
        rf = find_two_terminal_part(circuit_info, "R", inv_net, vout_net)
        c_pos = find_two_terminal_part(circuit_info, "C", vcc_net, gnd_net)
        c_neg = find_two_terminal_part(circuit_info, "C", vee_net, gnd_net)
        vin_io = find_single_pin_part(circuit_info, "Conn_01x01", vin_net, exclude_ref=part["ref"])
        vout_io = find_single_pin_part(circuit_info, "Conn_01x01", vout_net, exclude_ref=part["ref"])

        if not all([ri, rf, c_pos, c_neg]):
            continue

        return {
            "opamp": part,
            "ri": ri,
            "rf": rf,
            "c_pos": c_pos,
            "c_neg": c_neg,
            "vcc_net": vcc_net,
            "vee_net": vee_net,
            "gnd_net": gnd_net,
            "vin_net": vin_net,
            "inv_net": inv_net,
            "vout_net": vout_net,
            "unused_plus_net": unused_plus,
            "unused_minus_net": unused_minus,
            "unused_out_net": unused_out,
            "vin_io": vin_io,
            "vout_io": vout_io,
        }

    return None


class SchematicBuilder:
    def __init__(self, project_name: str, root_uuid: str):
        self.project_name = project_name
        self.root_uuid = root_uuid
        self.lines = []
        self.indent = 0

    def line(self, text: str = "") -> None:
        self.lines.append("\t" * self.indent + text)

    def open(self, text: str) -> None:
        self.line(text)
        self.indent += 1

    def close(self, text: str = ")") -> None:
        self.indent -= 1
        self.line(text)

    def property_block(self, name: str, value: str, at: Point, rotation: int = 0, hidden: bool = False, justify: str = "") -> None:
        self.open(f'(property "{esc(name)}" "{esc(value)}"')
        self.line(f'(at {mm(at.x)} {mm(at.y)} {rotation})')
        self.open("(effects")
        self.open("(font")
        self.line("(size 1.27 1.27)")
        self.close(")")
        if hidden:
            self.line("(hide yes)")
        if justify:
            self.line(f"(justify {justify})")
        self.close(")")
        self.close(")")

    def wire(self, start: Point, end: Point) -> None:
        self.open("(wire")
        self.open("(pts")
        self.line(f"(xy {mm(start.x)} {mm(start.y)}) (xy {mm(end.x)} {mm(end.y)})")
        self.close(")")
        self.open("(stroke")
        self.line("(width 0)")
        self.line("(type default)")
        self.close(")")
        self.line(f'(uuid "{uid()}")')
        self.close(")")

    def junction(self, at: Point) -> None:
        self.open("(junction")
        self.line(f'(at {mm(at.x)} {mm(at.y)})')
        self.line("(diameter 1.016)")
        self.line("(color 0 0 0 0)")
        self.line(f'(uuid "{uid()}")')
        self.close(")")

    def label(self, text: str, at: Point, rotation: int = 0, justify: str = "left bottom") -> None:
        self.open(f'(label "{esc(text)}"')
        self.line(f'(at {mm(at.x)} {mm(at.y)} {rotation})')
        self.open("(effects")
        self.open("(font")
        self.line("(size 1.27 1.27)")
        self.close(")")
        self.line(f"(justify {justify})")
        self.close(")")
        self.line(f'(uuid "{uid()}")')
        self.close(")")

    def text(self, text: str, at: Point, rotation: int = 0) -> None:
        self.open(f'(text "{esc(text)}"')
        self.line("(exclude_from_sim no)")
        self.line(f'(at {mm(at.x)} {mm(at.y)} {rotation})')
        self.open("(effects")
        self.open("(font")
        self.line("(size 1.27 1.27)")
        self.close(")")
        self.line("(justify left bottom)")
        self.close(")")
        self.line(f'(uuid "{uid()}")')
        self.close(")")

    def symbol_instance(
        self,
        *,
        lib_id: str,
        at: Point,
        reference: str,
        value: str,
        footprint: str,
        description: str,
        pin_numbers,
        ref_at: Point,
        value_at: Point,
        footprint_at: Point,
        datasheet: str = "",
        rotation: int = 0,
        unit: int = 1,
        in_bom: bool = True,
        on_board: bool = True,
        ref_hidden: bool = False,
        value_hidden: bool = False,
    ) -> None:
        self.open("(symbol")
        self.line(f'(lib_id "{esc(lib_id)}")')
        self.line(f'(at {mm(at.x)} {mm(at.y)} {rotation})')
        self.line(f"(unit {unit})")
        self.line("(exclude_from_sim no)")
        self.line(f"(in_bom {'yes' if in_bom else 'no'})")
        self.line(f"(on_board {'yes' if on_board else 'no'})")
        self.line("(dnp no)")
        self.line(f'(uuid "{uid()}")')
        self.property_block("Reference", reference, ref_at, hidden=ref_hidden)
        self.property_block("Value", value, value_at, hidden=value_hidden)
        self.property_block("Footprint", footprint, footprint_at, hidden=True)
        self.property_block("Datasheet", datasheet, footprint_at, hidden=True)
        self.property_block("Description", description, footprint_at, hidden=True)
        for number in pin_numbers:
            self.open(f'(pin "{number}"')
            self.line(f'(uuid "{uid()}")')
            self.close(")")
        self.open("(instances")
        self.open(f'(project "{esc(self.project_name)}"')
        self.open(f'(path "/{self.root_uuid}"')
        self.line(f'(reference "{esc(reference)}")')
        self.line(f"(unit {unit})")
        self.close(")")
        self.close(")")
        self.close(")")
        self.close(")")

    def power_symbol_instance(self, net_name: str, reference: str, at: Point, value_rotation: int) -> None:
        description_map = {
            "GND": 'Power symbol creates a global label with name "GND" , ground',
            "VCC": 'Power symbol creates a global label with name "VCC"',
            "VEE": 'Power symbol creates a global label with name "VEE"',
        }
        justify = "left" if value_rotation == 90 else ""
        self.symbol_instance(
            lib_id=f"power:{net_name}",
            at=at,
            reference=reference,
            value=net_name,
            footprint="",
            description=description_map[net_name],
            pin_numbers=["1"],
            ref_at=Point(at.x, at.y + (3.81 if net_name != "GND" else 6.35)),
            value_at=Point(at.x, at.y + (-3.81 if net_name == "GND" else -3.81)),
            footprint_at=at,
            rotation=0,
            in_bom=True,
            on_board=True,
        )
        # KiCad power symbol value text is usually rotated for VCC/VEE.
        # Override the emitted property block would complicate the helper,
        # so keep the symbol valid and rely on the symbol graphic for clarity.

    def render(self) -> str:
        return "\n".join(self.lines) + "\n"


def build_library_section(builder: SchematicBuilder) -> None:
    builder.open("(lib_symbols")
    for block in library_symbol_blocks():
        for line in block.strip("\n").splitlines():
            builder.line(line)
    builder.close(")")


def library_symbol_blocks():
    return [
        """
		(symbol "Device:R"
			(pin_numbers
				(hide yes)
			)
			(pin_names
				(offset 0)
			)
			(exclude_from_sim no)
			(in_bom yes)
			(on_board yes)
			(property "Reference" "R"
				(at 2.032 0 90)
				(effects
					(font
						(size 1.27 1.27)
					)
				)
			)
			(property "Value" "R"
				(at 0 0 90)
				(effects
					(font
						(size 1.27 1.27)
					)
				)
			)
			(property "Footprint" ""
				(at -1.778 0 90)
				(effects
					(font
						(size 1.27 1.27)
					)
					(hide yes)
				)
			)
			(property "Datasheet" "~"
				(at 0 0 0)
				(effects
					(font
						(size 1.27 1.27)
					)
					(hide yes)
				)
			)
			(property "Description" "Resistor"
				(at 0 0 0)
				(effects
					(font
						(size 1.27 1.27)
					)
					(hide yes)
				)
			)
			(property "ki_keywords" "R res resistor"
				(at 0 0 0)
				(effects
					(font
						(size 1.27 1.27)
					)
					(hide yes)
				)
			)
			(property "ki_fp_filters" "R_*"
				(at 0 0 0)
				(effects
					(font
						(size 1.27 1.27)
					)
					(hide yes)
				)
			)
			(symbol "R_0_1"
				(rectangle
					(start -1.016 -2.54)
					(end 1.016 2.54)
					(stroke
						(width 0.254)
						(type default)
					)
					(fill
						(type none)
					)
				)
			)
			(symbol "R_1_1"
				(pin passive line
					(at 0 3.81 270)
					(length 1.27)
					(name "~"
						(effects
							(font
								(size 1.27 1.27)
							)
						)
					)
					(number "1"
						(effects
							(font
								(size 1.27 1.27)
							)
						)
					)
				)
				(pin passive line
					(at 0 -3.81 90)
					(length 1.27)
					(name "~"
						(effects
							(font
								(size 1.27 1.27)
							)
						)
					)
					(number "2"
						(effects
							(font
								(size 1.27 1.27)
							)
						)
					)
				)
			)
			(embedded_fonts no)
		)
        """,
        """
		(symbol "Device:C"
			(pin_numbers
				(hide yes)
			)
			(pin_names
				(offset 0.254)
			)
			(exclude_from_sim no)
			(in_bom yes)
			(on_board yes)
			(property "Reference" "C"
				(at 0.635 2.54 0)
				(effects
					(font
						(size 1.27 1.27)
					)
					(justify left)
				)
			)
			(property "Value" "C"
				(at 0.635 -2.54 0)
				(effects
					(font
						(size 1.27 1.27)
					)
					(justify left)
				)
			)
			(property "Footprint" ""
				(at 0.9652 -3.81 0)
				(effects
					(font
						(size 1.27 1.27)
					)
					(hide yes)
				)
			)
			(property "Datasheet" "~"
				(at 0 0 0)
				(effects
					(font
						(size 1.27 1.27)
					)
					(hide yes)
				)
			)
			(property "Description" "Unpolarized capacitor"
				(at 0 0 0)
				(effects
					(font
						(size 1.27 1.27)
					)
					(hide yes)
				)
			)
			(property "ki_keywords" "cap capacitor"
				(at 0 0 0)
				(effects
					(font
						(size 1.27 1.27)
					)
					(hide yes)
				)
			)
			(property "ki_fp_filters" "C_*"
				(at 0 0 0)
				(effects
					(font
						(size 1.27 1.27)
					)
					(hide yes)
				)
			)
			(symbol "C_0_1"
				(polyline
					(pts
						(xy -2.032 0.762) (xy 2.032 0.762)
					)
					(stroke
						(width 0.508)
						(type default)
					)
					(fill
						(type none)
					)
				)
				(polyline
					(pts
						(xy -2.032 -0.762) (xy 2.032 -0.762)
					)
					(stroke
						(width 0.508)
						(type default)
					)
					(fill
						(type none)
					)
				)
			)
			(symbol "C_1_1"
				(pin passive line
					(at 0 3.81 270)
					(length 2.794)
					(name "~"
						(effects
							(font
								(size 1.27 1.27)
							)
						)
					)
					(number "1"
						(effects
							(font
								(size 1.27 1.27)
							)
						)
					)
				)
				(pin passive line
					(at 0 -3.81 90)
					(length 2.794)
					(name "~"
						(effects
							(font
								(size 1.27 1.27)
							)
						)
					)
					(number "2"
						(effects
							(font
								(size 1.27 1.27)
							)
						)
					)
				)
			)
			(embedded_fonts no)
		)
        """,
        """
		(symbol "Connector_Generic:Conn_01x01"
			(pin_numbers
				(hide yes)
			)
			(pin_names
				(offset 1.016)
				(hide yes)
			)
			(exclude_from_sim no)
			(in_bom yes)
			(on_board yes)
			(property "Reference" "J"
				(at 0 2.54 0)
				(effects
					(font
						(size 1.27 1.27)
					)
				)
			)
			(property "Value" "Conn_01x01"
				(at 0 -2.54 0)
				(effects
					(font
						(size 1.27 1.27)
					)
				)
			)
			(property "Footprint" ""
				(at 0 0 0)
				(effects
					(font
						(size 1.27 1.27)
					)
					(hide yes)
				)
			)
			(property "Datasheet" "~"
				(at 0 0 0)
				(effects
					(font
						(size 1.27 1.27)
					)
					(hide yes)
				)
			)
			(property "Description" "Generic connector, single row, single pin"
				(at 0 0 0)
				(effects
					(font
						(size 1.27 1.27)
					)
					(hide yes)
				)
			)
			(property "ki_keywords" "connector"
				(at 0 0 0)
				(effects
					(font
						(size 1.27 1.27)
					)
					(hide yes)
				)
			)
			(symbol "Conn_01x01_1_1"
				(rectangle
					(start -1.27 1.27)
					(end 1.27 -1.27)
					(stroke
						(width 0.254)
						(type default)
					)
					(fill
						(type none)
					)
				)
				(pin passive line
					(at -5.08 0 0)
					(length 3.81)
					(name "Pin_1"
						(effects
							(font
								(size 1.27 1.27)
							)
						)
					)
					(number "1"
						(effects
							(font
								(size 1.27 1.27)
							)
						)
					)
				)
			)
			(embedded_fonts no)
		)
        """,
        """
		(symbol "edp:R_H"
			(pin_numbers
				(hide yes)
			)
			(pin_names
				(offset 0)
			)
			(exclude_from_sim no)
			(in_bom yes)
			(on_board yes)
			(property "Reference" "R"
				(at 0 3.81 0)
				(effects
					(font
						(size 1.27 1.27)
					)
				)
			)
			(property "Value" "R"
				(at 0 -3.81 0)
				(effects
					(font
						(size 1.27 1.27)
					)
				)
			)
			(property "Footprint" ""
				(at 0 0 0)
				(effects
					(font
						(size 1.27 1.27)
					)
					(hide yes)
				)
			)
			(property "Datasheet" "~"
				(at 0 0 0)
				(effects
					(font
						(size 1.27 1.27)
					)
					(hide yes)
				)
			)
			(property "Description" "Resistor"
				(at 0 0 0)
				(effects
					(font
						(size 1.27 1.27)
					)
					(hide yes)
				)
			)
			(symbol "R_H_0_1"
				(polyline
					(pts
						(xy -5.08 0) (xy -3.81 1.27) (xy -2.54 -1.27) (xy -1.27 1.27) (xy 0 -1.27) (xy 1.27 1.27) (xy 2.54 -1.27) (xy 3.81 1.27) (xy 5.08 0)
					)
					(stroke
						(width 0.254)
						(type default)
					)
					(fill
						(type none)
					)
				)
			)
			(symbol "R_H_1_1"
				(pin passive line
					(at -7.62 0 0)
					(length 2.54)
					(name "~"
						(effects
							(font
								(size 1.27 1.27)
							)
						)
					)
					(number "1"
						(effects
							(font
								(size 1.27 1.27)
							)
						)
					)
				)
				(pin passive line
					(at 7.62 0 180)
					(length 2.54)
					(name "~"
						(effects
							(font
								(size 1.27 1.27)
							)
						)
					)
					(number "2"
						(effects
							(font
								(size 1.27 1.27)
							)
						)
					)
				)
			)
			(embedded_fonts no)
		)
        """,
        """
		(symbol "edp:R_V"
			(pin_numbers
				(hide yes)
			)
			(pin_names
				(offset 0)
			)
			(exclude_from_sim no)
			(in_bom yes)
			(on_board yes)
			(property "Reference" "R"
				(at 3.81 0 90)
				(effects
					(font
						(size 1.27 1.27)
					)
				)
			)
			(property "Value" "R"
				(at -3.81 0 90)
				(effects
					(font
						(size 1.27 1.27)
					)
				)
			)
			(property "Footprint" ""
				(at 0 0 0)
				(effects
					(font
						(size 1.27 1.27)
					)
					(hide yes)
				)
			)
			(property "Datasheet" "~"
				(at 0 0 0)
				(effects
					(font
						(size 1.27 1.27)
					)
					(hide yes)
				)
			)
			(property "Description" "Resistor"
				(at 0 0 0)
				(effects
					(font
						(size 1.27 1.27)
					)
					(hide yes)
				)
			)
			(symbol "R_V_0_1"
				(polyline
					(pts
						(xy 0 5.08) (xy 1.27 3.81) (xy -1.27 2.54) (xy 1.27 1.27) (xy -1.27 0) (xy 1.27 -1.27) (xy -1.27 -2.54) (xy 1.27 -3.81) (xy 0 -5.08)
					)
					(stroke
						(width 0.254)
						(type default)
					)
					(fill
						(type none)
					)
				)
			)
			(symbol "R_V_1_1"
				(pin passive line
					(at 0 7.62 270)
					(length 2.54)
					(name "~"
						(effects
							(font
								(size 1.27 1.27)
							)
						)
					)
					(number "1"
						(effects
							(font
								(size 1.27 1.27)
							)
						)
					)
				)
				(pin passive line
					(at 0 -7.62 90)
					(length 2.54)
					(name "~"
						(effects
							(font
								(size 1.27 1.27)
							)
						)
					)
					(number "2"
						(effects
							(font
								(size 1.27 1.27)
							)
						)
					)
				)
			)
			(embedded_fonts no)
		)
        """,
        """
		(symbol "edp:C_V"
			(pin_numbers
				(hide yes)
			)
			(pin_names
				(offset 0.254)
			)
			(exclude_from_sim no)
			(in_bom yes)
			(on_board yes)
			(property "Reference" "C"
				(at 3.81 2.54 0)
				(effects
					(font
						(size 1.27 1.27)
					)
					(justify left)
				)
			)
			(property "Value" "C"
				(at 3.81 -2.54 0)
				(effects
					(font
						(size 1.27 1.27)
					)
					(justify left)
				)
			)
			(property "Footprint" ""
				(at 0 0 0)
				(effects
					(font
						(size 1.27 1.27)
					)
					(hide yes)
				)
			)
			(property "Datasheet" "~"
				(at 0 0 0)
				(effects
					(font
						(size 1.27 1.27)
					)
					(hide yes)
				)
			)
			(property "Description" "Unpolarized capacitor"
				(at 0 0 0)
				(effects
					(font
						(size 1.27 1.27)
					)
					(hide yes)
				)
			)
			(symbol "C_V_0_1"
				(polyline
					(pts
						(xy -2.032 1.27) (xy 2.032 1.27)
					)
					(stroke
						(width 0.508)
						(type default)
					)
					(fill
						(type none)
					)
				)
				(polyline
					(pts
						(xy -2.032 -1.27) (xy 2.032 -1.27)
					)
					(stroke
						(width 0.508)
						(type default)
					)
					(fill
						(type none)
					)
				)
			)
			(symbol "C_V_1_1"
				(pin passive line
					(at 0 7.62 270)
					(length 2.54)
					(name "~"
						(effects
							(font
								(size 1.27 1.27)
							)
						)
					)
					(number "1"
						(effects
							(font
								(size 1.27 1.27)
							)
						)
					)
				)
				(pin passive line
					(at 0 -7.62 90)
					(length 2.54)
					(name "~"
						(effects
							(font
								(size 1.27 1.27)
							)
						)
					)
					(number "2"
						(effects
							(font
								(size 1.27 1.27)
							)
						)
					)
				)
			)
			(embedded_fonts no)
		)
        """,
        """
		(symbol "Amplifier_Operational:TL072"
			(pin_names
				(offset 0.127)
			)
			(exclude_from_sim no)
			(in_bom yes)
			(on_board yes)
			(property "Reference" "U"
				(at 0 5.08 0)
				(effects
					(font
						(size 1.27 1.27)
					)
					(justify left)
				)
			)
			(property "Value" "TL072"
				(at 0 -5.08 0)
				(effects
					(font
						(size 1.27 1.27)
					)
					(justify left)
				)
			)
			(property "Footprint" ""
				(at 0 0 0)
				(effects
					(font
						(size 1.27 1.27)
					)
					(hide yes)
				)
			)
			(property "Datasheet" "http://www.ti.com/lit/ds/symlink/tl071.pdf"
				(at 0 0 0)
				(effects
					(font
						(size 1.27 1.27)
					)
					(hide yes)
				)
			)
			(property "Description" "Dual Low-Noise JFET-Input Operational Amplifiers, DIP-8/SOIC-8"
				(at 0 0 0)
				(effects
					(font
						(size 1.27 1.27)
					)
					(hide yes)
				)
			)
			(symbol "TL072_1_1"
				(polyline
					(pts
						(xy -5.08 5.08) (xy 5.08 0) (xy -5.08 -5.08) (xy -5.08 5.08)
					)
					(stroke
						(width 0.254)
						(type default)
					)
					(fill
						(type background)
					)
				)
				(pin input line
					(at -7.62 2.54 0)
					(length 2.54)
					(name "+"
						(effects
							(font
								(size 1.27 1.27)
							)
						)
					)
					(number "3"
						(effects
							(font
								(size 1.27 1.27)
							)
						)
					)
				)
				(pin input line
					(at -7.62 -2.54 0)
					(length 2.54)
					(name "-"
						(effects
							(font
								(size 1.27 1.27)
							)
						)
					)
					(number "2"
						(effects
							(font
								(size 1.27 1.27)
							)
						)
					)
				)
				(pin output line
					(at 7.62 0 180)
					(length 2.54)
					(name "~"
						(effects
							(font
								(size 1.27 1.27)
							)
						)
					)
					(number "1"
						(effects
							(font
								(size 1.27 1.27)
							)
						)
					)
				)
			)
			(symbol "TL072_2_1"
				(polyline
					(pts
						(xy -5.08 5.08) (xy 5.08 0) (xy -5.08 -5.08) (xy -5.08 5.08)
					)
					(stroke
						(width 0.254)
						(type default)
					)
					(fill
						(type background)
					)
				)
				(pin input line
					(at -7.62 2.54 0)
					(length 2.54)
					(name "+"
						(effects
							(font
								(size 1.27 1.27)
							)
						)
					)
					(number "5"
						(effects
							(font
								(size 1.27 1.27)
							)
						)
					)
				)
				(pin input line
					(at -7.62 -2.54 0)
					(length 2.54)
					(name "-"
						(effects
							(font
								(size 1.27 1.27)
							)
						)
					)
					(number "6"
						(effects
							(font
								(size 1.27 1.27)
							)
						)
					)
				)
				(pin output line
					(at 7.62 0 180)
					(length 2.54)
					(name "~"
						(effects
							(font
								(size 1.27 1.27)
							)
						)
					)
					(number "7"
						(effects
							(font
								(size 1.27 1.27)
							)
						)
					)
				)
			)
			(symbol "TL072_3_1"
				(pin power_in line
					(at -2.54 7.62 270)
					(length 3.81)
					(name "V+"
						(effects
							(font
								(size 1.27 1.27)
							)
						)
					)
					(number "8"
						(effects
							(font
								(size 1.27 1.27)
							)
						)
					)
				)
				(pin power_in line
					(at -2.54 -7.62 90)
					(length 3.81)
					(name "V-"
						(effects
							(font
								(size 1.27 1.27)
							)
						)
					)
					(number "4"
						(effects
							(font
								(size 1.27 1.27)
							)
						)
					)
				)
			)
			(embedded_fonts no)
		)
        """,
        """
		(symbol "power:GND"
			(power)
			(pin_numbers
				(hide yes)
			)
			(pin_names
				(offset 0)
				(hide yes)
			)
			(exclude_from_sim no)
			(in_bom yes)
			(on_board yes)
			(property "Reference" "#PWR"
				(at 0 -6.35 0)
				(effects
					(font
						(size 1.27 1.27)
					)
					(hide yes)
				)
			)
			(property "Value" "GND"
				(at 0 -3.81 0)
				(effects
					(font
						(size 1.27 1.27)
					)
				)
			)
			(property "Footprint" ""
				(at 0 0 0)
				(effects
					(font
						(size 1.27 1.27)
					)
					(hide yes)
				)
			)
			(property "Datasheet" ""
				(at 0 0 0)
				(effects
					(font
						(size 1.27 1.27)
					)
					(hide yes)
				)
			)
			(property "Description" "Power symbol creates a global label with name \\"GND\\" , ground"
				(at 0 0 0)
				(effects
					(font
						(size 1.27 1.27)
					)
					(hide yes)
				)
			)
			(property "ki_keywords" "global power"
				(at 0 0 0)
				(effects
					(font
						(size 1.27 1.27)
					)
					(hide yes)
				)
			)
			(symbol "GND_0_1"
				(polyline
					(pts
						(xy 0 0) (xy 0 -1.27) (xy 1.27 -1.27) (xy 0 -2.54) (xy -1.27 -1.27) (xy 0 -1.27)
					)
					(stroke
						(width 0)
						(type default)
					)
					(fill
						(type none)
					)
				)
			)
			(symbol "GND_1_1"
				(pin power_in line
					(at 0 0 270)
					(length 0)
					(name "~"
						(effects
							(font
								(size 1.27 1.27)
							)
						)
					)
					(number "1"
						(effects
							(font
								(size 1.27 1.27)
							)
						)
					)
				)
			)
			(embedded_fonts no)
		)
        """,
        """
		(symbol "power:VCC"
			(power)
			(pin_numbers
				(hide yes)
			)
			(pin_names
				(offset 0)
				(hide yes)
			)
			(exclude_from_sim no)
			(in_bom yes)
			(on_board yes)
			(property "Reference" "#PWR"
				(at 0 -3.81 0)
				(effects
					(font
						(size 1.27 1.27)
					)
					(hide yes)
				)
			)
			(property "Value" "VCC"
				(at 0 3.556 0)
				(effects
					(font
						(size 1.27 1.27)
					)
				)
			)
			(property "Footprint" ""
				(at 0 0 0)
				(effects
					(font
						(size 1.27 1.27)
					)
					(hide yes)
				)
			)
			(property "Datasheet" ""
				(at 0 0 0)
				(effects
					(font
						(size 1.27 1.27)
					)
					(hide yes)
				)
			)
			(property "Description" "Power symbol creates a global label with name \\"VCC\\""
				(at 0 0 0)
				(effects
					(font
						(size 1.27 1.27)
					)
					(hide yes)
				)
			)
			(property "ki_keywords" "global power"
				(at 0 0 0)
				(effects
					(font
						(size 1.27 1.27)
					)
					(hide yes)
				)
			)
			(symbol "VCC_0_1"
				(polyline
					(pts
						(xy -0.762 1.27) (xy 0 2.54)
					)
					(stroke
						(width 0)
						(type default)
					)
					(fill
						(type none)
					)
				)
				(polyline
					(pts
						(xy 0 2.54) (xy 0.762 1.27)
					)
					(stroke
						(width 0)
						(type default)
					)
					(fill
						(type none)
					)
				)
				(polyline
					(pts
						(xy 0 0) (xy 0 2.54)
					)
					(stroke
						(width 0)
						(type default)
					)
					(fill
						(type none)
					)
				)
			)
			(symbol "VCC_1_1"
				(pin power_in line
					(at 0 0 90)
					(length 0)
					(name "~"
						(effects
							(font
								(size 1.27 1.27)
							)
						)
					)
					(number "1"
						(effects
							(font
								(size 1.27 1.27)
							)
						)
					)
				)
			)
			(embedded_fonts no)
		)
        """,
        """
		(symbol "power:VEE"
			(power)
			(pin_numbers
				(hide yes)
			)
			(pin_names
				(offset 0)
				(hide yes)
			)
			(exclude_from_sim no)
			(in_bom yes)
			(on_board yes)
			(property "Reference" "#PWR"
				(at 0 -3.81 0)
				(effects
					(font
						(size 1.27 1.27)
					)
					(hide yes)
				)
			)
			(property "Value" "VEE"
				(at 0 3.556 0)
				(effects
					(font
						(size 1.27 1.27)
					)
				)
			)
			(property "Footprint" ""
				(at 0 0 0)
				(effects
					(font
						(size 1.27 1.27)
					)
					(hide yes)
				)
			)
			(property "Datasheet" ""
				(at 0 0 0)
				(effects
					(font
						(size 1.27 1.27)
					)
					(hide yes)
				)
			)
			(property "Description" "Power symbol creates a global label with name \\"VEE\\""
				(at 0 0 0)
				(effects
					(font
						(size 1.27 1.27)
					)
					(hide yes)
				)
			)
			(property "ki_keywords" "global power"
				(at 0 0 0)
				(effects
					(font
						(size 1.27 1.27)
					)
					(hide yes)
				)
			)
			(symbol "VEE_0_1"
				(polyline
					(pts
						(xy 0 0) (xy 0 2.54)
					)
					(stroke
						(width 0)
						(type default)
					)
					(fill
						(type none)
					)
				)
				(polyline
					(pts
						(xy 0.762 1.27) (xy -0.762 1.27) (xy 0 2.54) (xy 0.762 1.27)
					)
					(stroke
						(width 0)
						(type default)
					)
					(fill
						(type outline)
					)
				)
			)
			(symbol "VEE_1_1"
				(pin power_in line
					(at 0 0 90)
					(length 0)
					(name "~"
						(effects
							(font
								(size 1.27 1.27)
							)
						)
					)
					(number "1"
						(effects
							(font
								(size 1.27 1.27)
							)
						)
					)
				)
			)
			(embedded_fonts no)
		)
        """,
    ]


def export_non_inverting_amplifier(design: Dict, output_path: Path) -> str:
    project_name = output_path.stem
    root_uuid = uid()
    builder = SchematicBuilder(project_name, root_uuid)

    builder.open("(kicad_sch")
    builder.line("(version 20250114)")
    builder.line('(generator "engineering-design-plugin")')
    builder.line('(generator_version "0.1")')
    builder.line(f'(uuid "{root_uuid}")')
    builder.line('(paper "A4")')
    builder.open("(title_block")
    builder.line(f'(title "{esc(project_name)}")')
    builder.close(")")
    build_library_section(builder)

    u1a = Point(104.14, 88.9)
    u1b = Point(104.14, 129.54)
    u1p = Point(195.58, 109.22)

    u1a_plus = local_to_sheet(u1a, -7.62, 2.54)
    u1a_minus = local_to_sheet(u1a, -7.62, -2.54)
    u1a_out = local_to_sheet(u1a, 7.62, 0)
    u1b_plus = local_to_sheet(u1b, -7.62, 2.54)
    u1b_minus = local_to_sheet(u1b, -7.62, -2.54)
    u1b_out = local_to_sheet(u1b, 7.62, 0)
    u1_vcc = local_to_sheet(u1p, -2.54, 7.62)
    u1_vee = local_to_sheet(u1p, -2.54, -7.62)

    sum_node = Point(86.36, u1a_minus.y)
    vout_node = Point(132.08, u1a_out.y)
    vin_io_origin = Point(50.8, u1a_plus.y)
    vin_io_pin = Point(vin_io_origin.x + 5.08, vin_io_origin.y)
    vout_io_origin = Point(160.02, vout_node.y)
    vout_io_pin = Point(vout_io_origin.x - 5.08, vout_io_origin.y)

    ri_origin = Point(86.36, 95.25)
    ri_top = Point(ri_origin.x, ri_origin.y - 3.81)
    ri_bottom = Point(ri_origin.x, ri_origin.y + 3.81)

    rf_origin = Point(107.95, 71.12)
    rf_left = Point(rf_origin.x - 3.81, rf_origin.y)
    rf_right = Point(rf_origin.x + 3.81, rf_origin.y)

    c1_origin = Point(180.34, 81.28)
    c1_top = Point(c1_origin.x, c1_origin.y - 3.81)
    c1_bottom = Point(c1_origin.x, c1_origin.y + 3.81)
    c2_origin = Point(180.34, 127.0)
    c2_top = Point(c2_origin.x, c2_origin.y - 3.81)
    c2_bottom = Point(c2_origin.x, c2_origin.y + 3.81)

    vcc_symbol = Point(193.04, 76.2)
    vee_symbol = Point(193.04, 132.08)
    gnd_r1 = Point(86.36, 111.76)
    gnd_u1b = Point(83.82, 127.0)
    gnd_c1 = Point(180.34, 96.52)
    gnd_c2 = Point(180.34, 111.76)

    if design.get("vin_io"):
        builder.symbol_instance(
            lib_id="Connector_Generic:Conn_01x01",
            at=vin_io_origin,
            reference=design["vin_io"]["ref"],
            value=design["vin_net"],
            footprint=design["vin_io"]["footprint"],
            description="External signal input",
            pin_numbers=["1"],
            ref_at=Point(vin_io_origin.x - 1.27, vin_io_origin.y - 4.445),
            value_at=Point(vin_io_origin.x - 2.54, vin_io_origin.y + 4.445),
            footprint_at=vin_io_origin,
            rotation=180,
        )
        builder.wire(vin_io_pin, u1a_plus)
    else:
        builder.wire(Point(58.42, u1a_plus.y), u1a_plus)
        builder.label(design["vin_net"], Point(53.34, u1a_plus.y - 0.635), 0, "left bottom")

    builder.wire(sum_node, u1a_minus)
    builder.wire(sum_node, ri_top)
    builder.wire(sum_node, Point(sum_node.x, rf_left.y))
    builder.wire(Point(sum_node.x, rf_left.y), rf_left)
    builder.junction(sum_node)

    builder.wire(u1a_out, vout_node)
    if design.get("vout_io"):
        builder.wire(vout_node, vout_io_pin)
        builder.symbol_instance(
            lib_id="Connector_Generic:Conn_01x01",
            at=vout_io_origin,
            reference=design["vout_io"]["ref"],
            value=design["vout_net"],
            footprint=design["vout_io"]["footprint"],
            description="Amplifier output connector",
            pin_numbers=["1"],
            ref_at=Point(vout_io_origin.x - 1.27, vout_io_origin.y - 4.445),
            value_at=Point(vout_io_origin.x - 1.27, vout_io_origin.y + 4.445),
            footprint_at=vout_io_origin,
            rotation=0,
        )
    else:
        builder.wire(vout_node, Point(149.86, vout_node.y))
        builder.label(design["vout_net"], Point(154.94, vout_node.y - 0.635), 0, "left bottom")
    builder.wire(rf_right, Point(vout_node.x, rf_right.y))
    builder.wire(Point(vout_node.x, rf_right.y), vout_node)
    builder.junction(vout_node)

    builder.symbol_instance(
        lib_id="Amplifier_Operational:TL072",
        at=u1a,
        reference=design["opamp"]["ref"],
        value=design["opamp"]["value"],
        footprint=design["opamp"]["footprint"],
        description="Dual low-noise JFET-input operational amplifier",
        pin_numbers=["1", "2", "3"],
        ref_at=Point(u1a.x - 10.16, u1a.y - 7.62),
        value_at=Point(u1a.x - 10.16, u1a.y + 7.62),
        footprint_at=u1a,
        datasheet="http://www.ti.com/lit/ds/symlink/tl071.pdf",
        unit=1,
    )
    builder.symbol_instance(
        lib_id="Amplifier_Operational:TL072",
        at=u1b,
        reference=design["opamp"]["ref"],
        value=design["opamp"]["value"],
        footprint=design["opamp"]["footprint"],
        description="Dual low-noise JFET-input operational amplifier",
        pin_numbers=["5", "6", "7"],
        ref_at=Point(u1b.x - 10.16, u1b.y - 7.62),
        value_at=Point(u1b.x - 10.16, u1b.y + 7.62),
        footprint_at=u1b,
        datasheet="http://www.ti.com/lit/ds/symlink/tl071.pdf",
        unit=2,
        value_hidden=True,
    )
    builder.symbol_instance(
        lib_id="Amplifier_Operational:TL072",
        at=u1p,
        reference=design["opamp"]["ref"],
        value=design["opamp"]["value"],
        footprint=design["opamp"]["footprint"],
        description="Dual low-noise JFET-input operational amplifier",
        pin_numbers=["4", "8"],
        ref_at=Point(u1p.x + 8.89, u1p.y + 1.27),
        value_at=Point(u1p.x - 5.08, u1p.y + 2.54),
        footprint_at=u1p,
        datasheet="http://www.ti.com/lit/ds/symlink/tl071.pdf",
        unit=3,
        ref_hidden=False,
        value_hidden=True,
    )

    builder.symbol_instance(
        lib_id="Device:R",
        at=ri_origin,
        reference=design["ri"]["ref"],
        value=design["ri"]["value"],
        footprint=design["ri"]["footprint"],
        description="Gain-setting resistor to ground",
        pin_numbers=["1", "2"],
        ref_at=Point(ri_origin.x - 7.62, ri_origin.y + 2.54),
        value_at=Point(ri_origin.x - 7.62, ri_origin.y - 2.54),
        footprint_at=ri_origin,
        rotation=0,
    )
    builder.wire(ri_bottom, Point(ri_bottom.x, gnd_r1.y - 2.54))
    builder.symbol_instance(
        lib_id="power:GND",
        at=gnd_r1,
        reference="#PWR0101",
        value=design["gnd_net"],
        footprint="",
        description='Power symbol creates a global label with name "GND" , ground',
        pin_numbers=["1"],
        ref_at=Point(gnd_r1.x, gnd_r1.y + 5.08),
        value_at=Point(gnd_r1.x, gnd_r1.y + 2.54),
        footprint_at=gnd_r1,
        ref_hidden=True,
    )
    builder.wire(Point(ri_bottom.x, gnd_r1.y - 2.54), gnd_r1)

    builder.symbol_instance(
        lib_id="Device:R",
        at=rf_origin,
        reference=design["rf"]["ref"],
        value=design["rf"]["value"],
        footprint=design["rf"]["footprint"],
        description="Feedback resistor",
        pin_numbers=["1", "2"],
        ref_at=Point(rf_origin.x - 2.54, rf_origin.y - 5.08),
        value_at=Point(rf_origin.x - 2.54, rf_origin.y + 5.08),
        footprint_at=rf_origin,
        rotation=90,
    )

    builder.wire(u1b_out, Point(121.92, u1b_out.y))
    builder.wire(Point(121.92, u1b_out.y), Point(121.92, u1b_minus.y))
    builder.wire(Point(121.92, u1b_minus.y), u1b_minus)
    builder.wire(u1b_plus, Point(gnd_u1b.x, u1b_plus.y))
    builder.wire(Point(gnd_u1b.x, u1b_plus.y), Point(gnd_u1b.x, gnd_u1b.y - 2.54))
    builder.symbol_instance(
        lib_id="power:GND",
        at=gnd_u1b,
        reference="#PWR0102",
        value=design["gnd_net"],
        footprint="",
        description='Power symbol creates a global label with name "GND" , ground',
        pin_numbers=["1"],
        ref_at=Point(gnd_u1b.x, gnd_u1b.y + 5.08),
        value_at=Point(gnd_u1b.x, gnd_u1b.y + 2.54),
        footprint_at=gnd_u1b,
        ref_hidden=True,
    )
    builder.wire(Point(gnd_u1b.x, gnd_u1b.y - 2.54), gnd_u1b)

    builder.wire(u1_vcc, Point(vcc_symbol.x, u1_vcc.y))
    builder.wire(Point(vcc_symbol.x, u1_vcc.y), Point(vcc_symbol.x, vcc_symbol.y + 2.54))
    builder.symbol_instance(
        lib_id="power:VCC",
        at=vcc_symbol,
        reference="#PWR0103",
        value=design["vcc_net"],
        footprint="",
        description='Power symbol creates a global label with name "VCC"',
        pin_numbers=["1"],
        ref_at=Point(vcc_symbol.x, vcc_symbol.y + 5.08),
        value_at=Point(vcc_symbol.x, vcc_symbol.y - 2.54),
        footprint_at=vcc_symbol,
        ref_hidden=True,
    )
    builder.wire(Point(vcc_symbol.x, vcc_symbol.y + 2.54), vcc_symbol)

    builder.wire(u1_vee, Point(vee_symbol.x, u1_vee.y))
    builder.wire(Point(vee_symbol.x, u1_vee.y), Point(vee_symbol.x, vee_symbol.y - 2.54))
    builder.symbol_instance(
        lib_id="power:VEE",
        at=vee_symbol,
        reference="#PWR0104",
        value=design["vee_net"],
        footprint="",
        description='Power symbol creates a global label with name "VEE"',
        pin_numbers=["1"],
        ref_at=Point(vee_symbol.x, vee_symbol.y + 5.08),
        value_at=Point(vee_symbol.x, vee_symbol.y - 2.54),
        footprint_at=vee_symbol,
        ref_hidden=True,
    )
    builder.wire(Point(vee_symbol.x, vee_symbol.y - 2.54), vee_symbol)

    builder.symbol_instance(
        lib_id="Device:C",
        at=c1_origin,
        reference=design["c_pos"]["ref"],
        value=design["c_pos"]["value"],
        footprint=design["c_pos"]["footprint"],
        description="Positive supply decoupling capacitor",
        pin_numbers=["1", "2"],
        ref_at=Point(c1_origin.x - 12.7, c1_origin.y - 1.27),
        value_at=Point(c1_origin.x - 12.7, c1_origin.y - 6.35),
        footprint_at=c1_origin,
        rotation=0,
    )
    builder.wire(c1_top, Point(vcc_symbol.x, c1_top.y))
    builder.wire(Point(vcc_symbol.x, c1_top.y), Point(vcc_symbol.x, vcc_symbol.y + 2.54))
    builder.wire(c1_bottom, Point(gnd_c1.x, gnd_c1.y - 2.54))
    builder.symbol_instance(
        lib_id="power:GND",
        at=gnd_c1,
        reference="#PWR0105",
        value=design["gnd_net"],
        footprint="",
        description='Power symbol creates a global label with name "GND" , ground',
        pin_numbers=["1"],
        ref_at=Point(gnd_c1.x, gnd_c1.y + 5.08),
        value_at=Point(gnd_c1.x, gnd_c1.y + 2.54),
        footprint_at=gnd_c1,
        ref_hidden=True,
    )
    builder.wire(Point(gnd_c1.x, gnd_c1.y - 2.54), gnd_c1)

    builder.symbol_instance(
        lib_id="Device:C",
        at=c2_origin,
        reference=design["c_neg"]["ref"],
        value=design["c_neg"]["value"],
        footprint=design["c_neg"]["footprint"],
        description="Negative supply decoupling capacitor",
        pin_numbers=["1", "2"],
        ref_at=Point(c2_origin.x - 12.7, c2_origin.y - 1.27),
        value_at=Point(c2_origin.x - 12.7, c2_origin.y - 6.35),
        footprint_at=c2_origin,
        rotation=0,
    )
    builder.wire(c2_bottom, Point(vee_symbol.x, c2_bottom.y))
    builder.wire(Point(vee_symbol.x, c2_bottom.y), Point(vee_symbol.x, vee_symbol.y - 2.54))
    builder.wire(c2_top, Point(gnd_c2.x, gnd_c2.y - 2.54))
    builder.symbol_instance(
        lib_id="power:GND",
        at=gnd_c2,
        reference="#PWR0106",
        value=design["gnd_net"],
        footprint="",
        description='Power symbol creates a global label with name "GND" , ground',
        pin_numbers=["1"],
        ref_at=Point(gnd_c2.x, gnd_c2.y + 5.08),
        value_at=Point(gnd_c2.x, gnd_c2.y + 2.54),
        footprint_at=gnd_c2,
        ref_hidden=True,
    )
    builder.wire(Point(gnd_c2.x, gnd_c2.y - 2.54), gnd_c2)

    builder.text("U1B parked as follower", Point(116.84, 147.32))

    builder.open("(sheet_instances")
    builder.open('(path "/"')
    builder.line('(page "1")')
    builder.close(")")
    builder.close(")")
    builder.line("(embedded_fonts no)")
    builder.close(")")

    output_path.write_text(builder.render(), encoding="utf-8")
    return str(output_path)


def write_project_file(output_path: Path) -> str:
    project_data = json.loads(json.dumps(PROJECT_TEMPLATE))
    project_data["meta"]["filename"] = output_path.name
    output_path.write_text(json.dumps(project_data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return str(output_path)


def main():
    parser = argparse.ArgumentParser(description="Export KiCad v9-native schematic/project files from a SKiDL script.")
    parser.add_argument("script", type=Path, help="Input SKiDL script")
    parser.add_argument("-o", "--output", type=Path, default=Path("outputs"), help="Output directory")
    parser.add_argument("--name", type=str, default=None, help="Base filename for generated KiCad files")
    parser.add_argument("--json", action="store_true", help="Print result metadata as JSON")
    args = parser.parse_args()

    if not args.script.exists():
        print(f"Error: Script not found: {args.script}", file=sys.stderr)
        sys.exit(1)

    args.output.mkdir(parents=True, exist_ok=True)
    base_name = args.name or args.script.stem

    result = {
        "script": str(args.script),
        "output_dir": str(args.output),
        "exported_files": [],
    }

    try:
        report_dir, project_dir = ensure_standard_output_dirs(args.output, base_name)
        configure_kicad_env()

        try:
            from skidl import KICAD, set_default_tool

            set_default_tool(KICAD)
        except ImportError:
            print("Error: SKiDL is not installed. Run: uv sync", file=sys.stderr)
            sys.exit(1)

        circuit = load_skidl_circuit(args.script)
        circuit_info = analyze_circuit(circuit)
        design = detect_non_inverting_amplifier(circuit_info)
        if not design:
            raise ValueError("KiCad schematic export currently supports the non-inverting TL072 amplifier topology used in the example.")

        schematic_path = project_dir / f"{base_name}.kicad_sch"
        project_path = project_dir / f"{base_name}.kicad_pro"

        export_non_inverting_amplifier(design, schematic_path)
        write_project_file(project_path)
        result["exported_files"].extend([str(schematic_path), str(project_path)])

        summary_path = report_dir / f"{base_name}-design-summary.md"
        erc_summary_path = report_dir / f"{base_name}-erc-summary.md"
        summary_circuit_info = {
            "name": getattr(circuit, "name", base_name),
            "parts_count": len(circuit.parts),
            "nets_count": len(circuit.nets),
        }
        write_design_summary(
            summary_path,
            args.script,
            summary_circuit_info,
            read_erc_summary(erc_summary_path),
            collect_artifact_paths(args.output, base_name),
        )

    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        for file_path in result["exported_files"]:
            print(file_path)


if __name__ == "__main__":
    main()
