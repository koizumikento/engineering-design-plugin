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
from typing import Any, Dict, List, Optional

from circuit_artifacts import (
    collect_artifact_paths,
    ensure_standard_output_dirs,
    read_erc_summary,
    write_design_summary,
)
from kicad_env import configure_kicad_env
from skidl_utils import load_skidl_circuit, suppress_skidl_file_output


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


@dataclass(frozen=True)
class SupportedDesign:
    kind: str
    data: Dict[str, Any]


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


def part_matches(part: Dict, *, name: Optional[str] = None, value: Optional[str] = None) -> bool:
    if name and part["name"].upper() != name.upper():
        return False
    if value and str(part["value"]).upper() != value.upper():
        return False
    return True


def find_two_terminal_part(circuit_info: Dict, part_name: str, net_a: str, net_b: str) -> Optional[Dict]:
    target_nets = {net_a, net_b}
    for part in circuit_info["parts"]:
        if not part_matches(part, name=part_name):
            continue
        nets = {pin["net"] for pin in part["pins"] if pin.get("net")}
        if len(nets) == 2 and nets == target_nets:
            return part
    return None


def find_single_pin_part(circuit_info: Dict, part_name: str, net_name: str, exclude_ref: Optional[str] = None) -> Optional[Dict]:
    for part in circuit_info["parts"]:
        if exclude_ref and part["ref"] == exclude_ref:
            continue
        if not part_matches(part, name=part_name):
            continue
        if len(part["pins"]) != 1:
            continue
        pin = part["pins"][0]
        if pin.get("net") == net_name:
            return part
    return None


def find_parts_between(circuit_info: Dict, part_name: str, net_a: str, net_b: str) -> List[Dict]:
    target_nets = {net_a, net_b}
    matches = []
    for part in circuit_info["parts"]:
        if not part_matches(part, name=part_name):
            continue
        nets = {pin["net"] for pin in part["pins"] if pin.get("net")}
        if len(nets) == 2 and nets == target_nets:
            matches.append(part)
    return matches


def find_two_pin_connector(circuit_info: Dict, net_a: str, net_b: str) -> Optional[Dict]:
    target_nets = {net_a, net_b}
    for part in circuit_info["parts"]:
        if not part_matches(part, name="Conn_01x02"):
            continue
        nets = {pin["net"] for pin in part["pins"] if pin.get("net")}
        if nets == target_nets:
            return part
    return None


def detect_opamp_amplifier(circuit_info: Dict) -> Optional[SupportedDesign]:
    for part in circuit_info["parts"]:
        if not part_matches(part, value="TL072"):
            continue

        pin_nets = get_pin_net_map(part)
        pin_nums = get_pin_number_map(part)
        vcc_net = pin_nums.get("8") or pin_nets.get("VCC") or pin_nets.get("V+")
        vee_net = pin_nums.get("4") or pin_nets.get("VEE") or pin_nets.get("V-")
        gnd_net = "GND" if any(net["name"] == "GND" for net in circuit_info["nets"]) else None
        plus_net = pin_nums.get("3") or pin_nets.get("1+") or pin_nets.get("IN+")
        inv_net = pin_nums.get("2") or pin_nets.get("1-") or pin_nets.get("IN-")
        vout_net = pin_nums.get("1") or pin_nets.get("1OUT") or pin_nets.get("OUT")
        unused_plus = pin_nums.get("5") or pin_nets.get("2+")
        unused_minus = pin_nums.get("6") or pin_nets.get("2-")
        unused_out = pin_nums.get("7") or pin_nets.get("2OUT")

        if not all([vcc_net, vee_net, gnd_net, plus_net, inv_net, vout_net, unused_plus, unused_minus, unused_out]):
            continue

        non_inverting_ri = find_two_terminal_part(circuit_info, "R", gnd_net, inv_net)
        rf = find_two_terminal_part(circuit_info, "R", inv_net, vout_net)
        c_pos = find_two_terminal_part(circuit_info, "C", vcc_net, gnd_net)
        c_neg = find_two_terminal_part(circuit_info, "C", vee_net, gnd_net)
        vout_io = find_single_pin_part(circuit_info, "Conn_01x01", vout_net, exclude_ref=part["ref"])

        if not all([rf, c_pos, c_neg]):
            continue

        if non_inverting_ri and plus_net != gnd_net:
            vin_net = plus_net
            return SupportedDesign(
                kind="opamp_amplifier",
                data={
                    "mode": "non_inverting",
                    "opamp": part,
                    "ri": non_inverting_ri,
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
                    "vin_io": find_single_pin_part(circuit_info, "Conn_01x01", vin_net, exclude_ref=part["ref"]),
                    "vout_io": vout_io,
                },
            )

        for candidate in find_parts_between(circuit_info, "R", inv_net, gnd_net):
            if candidate["ref"] != rf["ref"]:
                non_inverting_ri = candidate
                break

        input_resistor = None
        vin_net = None
        for candidate in circuit_info["parts"]:
            if not part_matches(candidate, name="R") or candidate["ref"] == rf["ref"]:
                continue
            nets = {pin["net"] for pin in candidate["pins"] if pin.get("net")}
            if inv_net not in nets or len(nets) != 2:
                continue
            other_net = next(net for net in nets if net != inv_net)
            if other_net in {gnd_net, vcc_net, vee_net, vout_net, unused_out, unused_plus, unused_minus}:
                continue
            input_resistor = candidate
            vin_net = other_net
            break

        if input_resistor and plus_net == gnd_net and vin_net:
            return SupportedDesign(
                kind="opamp_amplifier",
                data={
                    "mode": "inverting",
                    "opamp": part,
                    "ri": input_resistor,
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
                    "vin_io": find_single_pin_part(circuit_info, "Conn_01x01", vin_net, exclude_ref=part["ref"]),
                    "vout_io": vout_io,
                },
            )

    return None


def detect_voltage_divider(circuit_info: Dict) -> Optional[SupportedDesign]:
    if not all(any(net["name"] == name for net in circuit_info["nets"]) for name in ("VIN", "VOUT", "GND")):
        return None

    r_top = find_two_terminal_part(circuit_info, "R", "VIN", "VOUT")
    r_bottom = find_two_terminal_part(circuit_info, "R", "VOUT", "GND")
    if not all([r_top, r_bottom]):
        return None

    return SupportedDesign(
        kind="voltage_divider",
        data={
            "vin_net": "VIN",
            "vout_net": "VOUT",
            "gnd_net": "GND",
            "r_top": r_top,
            "r_bottom": r_bottom,
            "vin_io": find_single_pin_part(circuit_info, "Conn_01x01", "VIN"),
            "vout_io": find_single_pin_part(circuit_info, "Conn_01x01", "VOUT"),
            "gnd_io": find_single_pin_part(circuit_info, "Conn_01x01", "GND"),
        },
    )


def detect_rc_lowpass(circuit_info: Dict) -> Optional[SupportedDesign]:
    if not all(any(net["name"] == name for net in circuit_info["nets"]) for name in ("VIN", "VOUT", "GND")):
        return None

    resistor = find_two_terminal_part(circuit_info, "R", "VIN", "VOUT")
    capacitor = find_two_terminal_part(circuit_info, "C", "VOUT", "GND")
    if not all([resistor, capacitor]):
        return None

    return SupportedDesign(
        kind="rc_lowpass",
        data={
            "vin_net": "VIN",
            "vout_net": "VOUT",
            "gnd_net": "GND",
            "resistor": resistor,
            "capacitor": capacitor,
            "vin_io": find_single_pin_part(circuit_info, "Conn_01x01", "VIN"),
            "vout_io": find_single_pin_part(circuit_info, "Conn_01x01", "VOUT"),
            "gnd_io": find_single_pin_part(circuit_info, "Conn_01x01", "GND"),
        },
    )


def detect_linear_regulator(circuit_info: Dict) -> Optional[SupportedDesign]:
    for part in circuit_info["parts"]:
        if not part_matches(part, value="L7805"):
            continue

        pin_nets = get_pin_net_map(part)
        pin_nums = get_pin_number_map(part)
        vin_net = pin_nums.get("1") or pin_nets.get("IN")
        gnd_net = pin_nums.get("2") or pin_nets.get("GND")
        vout_net = pin_nums.get("3") or pin_nets.get("OUT")
        if not all([vin_net, gnd_net, vout_net]):
            continue

        input_caps = find_parts_between(circuit_info, "C", vin_net, gnd_net)
        output_caps = find_parts_between(circuit_info, "C", vout_net, gnd_net)
        if not input_caps or not output_caps:
            continue

        return SupportedDesign(
            kind="linear_regulator",
            data={
                "regulator": part,
                "vin_net": vin_net,
                "gnd_net": gnd_net,
                "vout_net": vout_net,
                "input_caps": sorted(input_caps, key=lambda p: p["ref"]),
                "output_caps": sorted(output_caps, key=lambda p: p["ref"]),
                "input_connector": find_two_pin_connector(circuit_info, vin_net, gnd_net),
                "output_connector": find_two_pin_connector(circuit_info, vout_net, gnd_net),
            },
        )

    return None


def detect_comet_led_sequencer(circuit_info: Dict) -> Optional[SupportedDesign]:
    required_nets = {"VCC", "GND", "CLOCK", "RESET", "TIMING", "DISCHARGE", "CARRY_OUT"}
    available_nets = {net["name"] for net in circuit_info["nets"]}
    if not required_nets.issubset(available_nets):
        return None

    timer = next((part for part in circuit_info["parts"] if part_matches(part, value="NE555P")), None)
    counter = next((part for part in circuit_info["parts"] if part_matches(part, value="4017")), None)
    potentiometer = next((part for part in circuit_info["parts"] if part_matches(part, name="R_Potentiometer")), None)
    reset_switch = next((part for part in circuit_info["parts"] if part_matches(part, name="SW_Push")), None)

    if not all([timer, counter, potentiometer, reset_switch]):
        return None

    timer_pins = get_pin_number_map(timer)
    counter_pins = get_pin_number_map(counter)

    if timer_pins.get("8") != "VCC" or timer_pins.get("1") != "GND":
        return None
    if timer_pins.get("4") != "VCC" or timer_pins.get("3") != "CLOCK":
        return None
    if timer_pins.get("7") != "DISCHARGE":
        return None
    if {timer_pins.get("6"), timer_pins.get("2")} != {"TIMING"}:
        return None

    control_net = timer_pins.get("5")
    if not control_net:
        return None

    expected_counter_pins = {
        "16": "VCC",
        "8": "GND",
        "14": "CLOCK",
        "13": "GND",
        "15": "RESET",
        "12": "CARRY_OUT",
    }
    if any(counter_pins.get(pin) != net_name for pin, net_name in expected_counter_pins.items()):
        return None

    for index, pin_number in enumerate(("3", "2", "4", "7", "10", "1", "5", "6", "9", "11")):
        if counter_pins.get(pin_number) != f"LED_STEP_{index}":
            return None

    potentiometer_pin_map = {pin["num"]: pin["net"] for pin in potentiometer["pins"] if pin.get("net")}
    pot_drive_net = potentiometer_pin_map.get("1")
    if not pot_drive_net or pot_drive_net in {"VCC", "GND", "TIMING", "DISCHARGE"}:
        return None

    power_connector = find_two_pin_connector(circuit_info, "VCC", "GND")
    carry_connector = find_single_pin_part(circuit_info, "Conn_01x01", "CARRY_OUT")
    charge_resistor = find_two_terminal_part(circuit_info, "R", "VCC", "DISCHARGE")
    speed_resistor = find_two_terminal_part(circuit_info, "R", "DISCHARGE", pot_drive_net)
    timing_capacitor = find_two_terminal_part(circuit_info, "C", "TIMING", "GND")
    control_capacitor = find_two_terminal_part(circuit_info, "C", control_net, "GND")
    reset_pull = find_two_terminal_part(circuit_info, "R", "RESET", "GND")

    if not all(
        [
            power_connector,
            carry_connector,
            charge_resistor,
            speed_resistor,
            timing_capacitor,
            control_capacitor,
            reset_pull,
        ]
    ):
        return None

    reset_switch_nets = {pin["net"] for pin in reset_switch["pins"] if pin.get("net")}
    if reset_switch_nets != {"VCC", "RESET"}:
        return None

    potentiometer_nets = {pin["net"] for pin in potentiometer["pins"] if pin.get("net")}
    if potentiometer_nets != {pot_drive_net, "TIMING"}:
        return None

    vcc_caps = [
        capacitor
        for capacitor in find_parts_between(circuit_info, "C", "VCC", "GND")
        if capacitor["ref"] not in {timing_capacitor["ref"], control_capacitor["ref"]}
    ]
    if len(vcc_caps) < 3:
        return None

    bulk_capacitor = next((capacitor for capacitor in vcc_caps if str(capacitor["value"]).lower() != "100n"), None)
    if bulk_capacitor is None:
        bulk_capacitor = sorted(vcc_caps, key=lambda capacitor: capacitor["ref"])[0]

    decoupling_caps = sorted(
        [capacitor for capacitor in vcc_caps if capacitor["ref"] != bulk_capacitor["ref"]],
        key=lambda capacitor: capacitor["ref"],
    )
    if len(decoupling_caps) < 2:
        return None

    reserved_resistors = {charge_resistor["ref"], speed_resistor["ref"], reset_pull["ref"]}
    used_leds = set()
    led_channels = []

    for index in range(10):
        step_net = f"LED_STEP_{index}"
        led_resistor = None
        led_part = None
        intermediate_net = None

        for candidate in circuit_info["parts"]:
            if not part_matches(candidate, name="R") or candidate["ref"] in reserved_resistors:
                continue
            nets = {pin["net"] for pin in candidate["pins"] if pin.get("net")}
            if step_net not in nets or len(nets) != 2:
                continue
            other_net = next(net for net in nets if net != step_net)
            led_candidate = find_two_terminal_part(circuit_info, "LED", other_net, "GND")
            if led_candidate and led_candidate["ref"] not in used_leds:
                led_resistor = candidate
                led_part = led_candidate
                intermediate_net = other_net
                break

        if not all([led_resistor, led_part, intermediate_net]):
            return None

        reserved_resistors.add(led_resistor["ref"])
        used_leds.add(led_part["ref"])
        led_channels.append(
            {
                "step_net": step_net,
                "resistor": led_resistor,
                "led": led_part,
                "intermediate_net": intermediate_net,
            }
        )

    return SupportedDesign(
        kind="comet_led_sequencer",
        data={
            "timer": timer,
            "counter": counter,
            "power_connector": power_connector,
            "carry_connector": carry_connector,
            "bulk_capacitor": bulk_capacitor,
            "timer_decoupling": decoupling_caps[0],
            "counter_decoupling": decoupling_caps[1],
            "charge_resistor": charge_resistor,
            "speed_resistor": speed_resistor,
            "potentiometer": potentiometer,
            "timing_capacitor": timing_capacitor,
            "control_capacitor": control_capacitor,
            "reset_pull": reset_pull,
            "reset_switch": reset_switch,
            "led_channels": led_channels,
            "vcc_net": "VCC",
            "gnd_net": "GND",
            "clock_net": "CLOCK",
            "reset_net": "RESET",
            "timing_net": "TIMING",
            "discharge_net": "DISCHARGE",
            "carry_net": "CARRY_OUT",
            "control_net": control_net,
            "pot_drive_net": pot_drive_net,
        },
    )


def identify_supported_design(circuit_info: Dict) -> Optional[SupportedDesign]:
    detectors = [
        detect_opamp_amplifier,
        detect_comet_led_sequencer,
        detect_linear_regulator,
        detect_voltage_divider,
        detect_rc_lowpass,
    ]
    for detector in detectors:
        design = detector(circuit_info)
        if design:
            return design
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
		(symbol "Connector_Generic:Conn_01x02"
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
				(at 0 3.81 0)
				(effects
					(font
						(size 1.27 1.27)
					)
				)
			)
			(property "Value" "Conn_01x02"
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
			(property "Description" "Generic connector, single row, 2 pins"
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
			(symbol "Conn_01x02_1_1"
				(rectangle
					(start -1.27 2.54)
					(end 1.27 -2.54)
					(stroke
						(width 0.254)
						(type default)
					)
					(fill
						(type none)
					)
				)
				(pin passive line
					(at -5.08 1.27 0)
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
				(pin passive line
					(at -5.08 -1.27 0)
					(length 3.81)
					(name "Pin_2"
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
		(symbol "Regulator_Linear:L7805"
			(pin_names
				(offset 1.016)
			)
			(exclude_from_sim no)
			(in_bom yes)
			(on_board yes)
			(property "Reference" "U"
				(at 0 6.35 0)
				(effects
					(font
						(size 1.27 1.27)
					)
				)
			)
			(property "Value" "L7805"
				(at 0 -6.35 0)
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
			(property "Description" "Positive 5V linear regulator"
				(at 0 0 0)
				(effects
					(font
						(size 1.27 1.27)
					)
					(hide yes)
				)
			)
			(symbol "L7805_0_1"
				(rectangle
					(start -5.08 3.81)
					(end 5.08 -3.81)
					(stroke
						(width 0.254)
						(type default)
					)
					(fill
						(type background)
					)
				)
			)
			(symbol "L7805_1_1"
				(pin power_in line
					(at -7.62 2.54 0)
					(length 2.54)
					(name "IN"
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
				(pin power_in line
					(at 0 -6.35 90)
					(length 2.54)
					(name "GND"
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
				(pin power_out line
					(at 7.62 2.54 180)
					(length 2.54)
					(name "OUT"
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
		(symbol "Timer:NE555P"
			(pin_names
				(offset 1.016)
			)
			(exclude_from_sim no)
			(in_bom yes)
			(on_board yes)
			(property "Reference" "U"
				(at 0 13.97 0)
				(effects
					(font
						(size 1.27 1.27)
					)
				)
			)
			(property "Value" "NE555P"
				(at 0 -13.97 0)
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
			(property "Datasheet" "http://www.ti.com/lit/ds/symlink/ne555.pdf"
				(at 0 0 0)
				(effects
					(font
						(size 1.27 1.27)
					)
					(hide yes)
				)
			)
			(property "Description" "Precision timer, 555 compatible, PDIP-8"
				(at 0 0 0)
				(effects
					(font
						(size 1.27 1.27)
					)
					(hide yes)
				)
			)
			(symbol "NE555P_0_1"
				(rectangle
					(start -7.62 10.16)
					(end 7.62 -10.16)
					(stroke
						(width 0.254)
						(type default)
					)
					(fill
						(type background)
					)
				)
			)
			(symbol "NE555P_1_1"
				(pin input line
					(at -10.16 7.62 0)
					(length 2.54)
					(name "~RST"
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
				(pin input line
					(at -10.16 2.54 0)
					(length 2.54)
					(name "THRES"
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
				(pin input line
					(at -10.16 -2.54 0)
					(length 2.54)
					(name "TRIG"
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
				(pin input line
					(at -10.16 -7.62 0)
					(length 2.54)
					(name "CONT"
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
				(pin passive line
					(at 10.16 7.62 180)
					(length 2.54)
					(name "DISCH"
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
				(pin output line
					(at 10.16 0 180)
					(length 2.54)
					(name "OUT"
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
				(pin power_in line
					(at 0 12.7 270)
					(length 2.54)
					(name "VCC"
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
					(at 0 -12.7 90)
					(length 2.54)
					(name "GND"
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
		(symbol "4xxx_IEEE:4017"
			(pin_names
				(offset 1.016)
			)
			(exclude_from_sim no)
			(in_bom yes)
			(on_board yes)
			(property "Reference" "U"
				(at 0 31.75 0)
				(effects
					(font
						(size 1.27 1.27)
					)
				)
			)
			(property "Value" "4017"
				(at 0 -31.75 0)
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
			(property "Description" "CMOS decade counter and decoder"
				(at 0 0 0)
				(effects
					(font
						(size 1.27 1.27)
					)
					(hide yes)
				)
			)
			(symbol "4017_0_1"
				(rectangle
					(start -12.7 27.94)
					(end 12.7 -27.94)
					(stroke
						(width 0.254)
						(type default)
					)
					(fill
						(type background)
					)
				)
			)
			(symbol "4017_1_1"
				(pin input line
					(at -15.24 20.32 0)
					(length 2.54)
					(name "CP0"
						(effects
							(font
								(size 1.27 1.27)
							)
						)
					)
					(number "14"
						(effects
							(font
								(size 1.27 1.27)
							)
						)
					)
				)
				(pin input line
					(at -15.24 15.24 0)
					(length 2.54)
					(name "~CP1"
						(effects
							(font
								(size 1.27 1.27)
							)
						)
					)
					(number "13"
						(effects
							(font
								(size 1.27 1.27)
							)
						)
					)
				)
				(pin input line
					(at -15.24 10.16 0)
					(length 2.54)
					(name "MR"
						(effects
							(font
								(size 1.27 1.27)
							)
						)
					)
					(number "15"
						(effects
							(font
								(size 1.27 1.27)
							)
						)
					)
				)
				(pin output line
					(at -15.24 0 0)
					(length 2.54)
					(name "Co"
						(effects
							(font
								(size 1.27 1.27)
							)
						)
					)
					(number "12"
						(effects
							(font
								(size 1.27 1.27)
							)
						)
					)
				)
				(pin power_in line
					(at 0 33.02 270)
					(length 5.08)
					(name "VDD"
						(effects
							(font
								(size 1.27 1.27)
							)
						)
					)
					(number "16"
						(effects
							(font
								(size 1.27 1.27)
							)
						)
					)
				)
				(pin power_in line
					(at 0 -33.02 90)
					(length 5.08)
					(name "VSS"
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
				(pin output line
					(at 15.24 22.86 180)
					(length 2.54)
					(name "Q0"
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
				(pin output line
					(at 15.24 17.78 180)
					(length 2.54)
					(name "Q1"
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
					(at 15.24 12.7 180)
					(length 2.54)
					(name "Q2"
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
				(pin output line
					(at 15.24 7.62 180)
					(length 2.54)
					(name "Q3"
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
				(pin output line
					(at 15.24 2.54 180)
					(length 2.54)
					(name "Q4"
						(effects
							(font
								(size 1.27 1.27)
							)
						)
					)
					(number "10"
						(effects
							(font
								(size 1.27 1.27)
							)
						)
					)
				)
				(pin output line
					(at 15.24 -2.54 180)
					(length 2.54)
					(name "Q5"
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
				(pin output line
					(at 15.24 -7.62 180)
					(length 2.54)
					(name "Q6"
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
				(pin output line
					(at 15.24 -12.7 180)
					(length 2.54)
					(name "Q7"
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
					(at 15.24 -17.78 180)
					(length 2.54)
					(name "Q8"
						(effects
							(font
								(size 1.27 1.27)
							)
						)
					)
					(number "9"
						(effects
							(font
								(size 1.27 1.27)
							)
						)
					)
				)
				(pin output line
					(at 15.24 -22.86 180)
					(length 2.54)
					(name "Q9"
						(effects
							(font
								(size 1.27 1.27)
							)
						)
					)
					(number "11"
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
		(symbol "Device:LED"
			(pin_names
				(offset 0.508)
			)
			(exclude_from_sim no)
			(in_bom yes)
			(on_board yes)
			(property "Reference" "D"
				(at 3.81 0 90)
				(effects
					(font
						(size 1.27 1.27)
					)
				)
			)
			(property "Value" "LED"
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
			(property "Description" "Light emitting diode"
				(at 0 0 0)
				(effects
					(font
						(size 1.27 1.27)
					)
					(hide yes)
				)
			)
			(symbol "LED_0_1"
				(polyline
					(pts
						(xy -2.54 1.27) (xy 0 -1.27) (xy 2.54 1.27) (xy -2.54 1.27)
					)
					(stroke
						(width 0.254)
						(type default)
					)
					(fill
						(type none)
					)
				)
				(polyline
					(pts
						(xy -2.54 -1.27) (xy 2.54 -1.27)
					)
					(stroke
						(width 0.254)
						(type default)
					)
					(fill
						(type none)
					)
				)
				(polyline
					(pts
						(xy 2.286 2.794) (xy 4.064 4.572)
					)
					(stroke
						(width 0.254)
						(type default)
					)
					(fill
						(type none)
					)
				)
				(polyline
					(pts
						(xy 4.064 2.794) (xy 4.064 4.572) (xy 2.286 4.572)
					)
					(stroke
						(width 0.254)
						(type default)
					)
					(fill
						(type none)
					)
				)
				(polyline
					(pts
						(xy 0.762 1.524) (xy 2.54 3.302)
					)
					(stroke
						(width 0.254)
						(type default)
					)
					(fill
						(type none)
					)
				)
				(polyline
					(pts
						(xy 2.54 1.524) (xy 2.54 3.302) (xy 0.762 3.302)
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
			(symbol "LED_1_1"
				(pin passive line
					(at 0 7.62 270)
					(length 5.08)
					(name "A"
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
				(pin passive line
					(at 0 -7.62 90)
					(length 5.08)
					(name "K"
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
		(symbol "Device:R_Potentiometer"
			(pin_numbers
				(hide yes)
			)
			(pin_names
				(offset 0)
			)
			(exclude_from_sim no)
			(in_bom yes)
			(on_board yes)
			(property "Reference" "RV"
				(at 3.81 0 90)
				(effects
					(font
						(size 1.27 1.27)
					)
				)
			)
			(property "Value" "R_Potentiometer"
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
			(property "Description" "Potentiometer"
				(at 0 0 0)
				(effects
					(font
						(size 1.27 1.27)
					)
					(hide yes)
				)
			)
			(symbol "R_Potentiometer_0_1"
				(polyline
					(pts
						(xy 0 7.62) (xy 1.27 6.35) (xy -1.27 5.08) (xy 1.27 3.81) (xy -1.27 2.54) (xy 1.27 1.27) (xy -1.27 0) (xy 1.27 -1.27) (xy -1.27 -2.54) (xy 1.27 -3.81) (xy -1.27 -5.08) (xy 1.27 -6.35) (xy 0 -7.62)
					)
					(stroke
						(width 0.254)
						(type default)
					)
					(fill
						(type none)
					)
				)
				(polyline
					(pts
						(xy -6.35 1.27) (xy -1.27 1.27)
					)
					(stroke
						(width 0.254)
						(type default)
					)
					(fill
						(type none)
					)
				)
				(polyline
					(pts
						(xy -2.54 3.81) (xy -1.27 1.27) (xy 1.27 2.54)
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
			(symbol "R_Potentiometer_1_1"
				(pin passive line
					(at 0 10.16 270)
					(length 2.54)
					(name "1"
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
					(at -7.62 0 0)
					(length 2.54)
					(name "2"
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
				(pin passive line
					(at 0 -10.16 90)
					(length 2.54)
					(name "3"
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
			)
			(embedded_fonts no)
		)
        """,
        """
		(symbol "Switch:SW_Push"
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
			(property "Reference" "SW"
				(at 0 3.81 0)
				(effects
					(font
						(size 1.27 1.27)
					)
				)
			)
			(property "Value" "SW_Push"
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
			(property "Description" "Push button switch, normally open"
				(at 0 0 0)
				(effects
					(font
						(size 1.27 1.27)
					)
					(hide yes)
				)
			)
			(symbol "SW_Push_0_1"
				(circle
					(center -2.54 0)
					(radius 0.762)
					(stroke
						(width 0.254)
						(type default)
					)
					(fill
						(type none)
					)
				)
				(circle
					(center 2.54 0)
					(radius 0.762)
					(stroke
						(width 0.254)
						(type default)
					)
					(fill
						(type none)
					)
				)
				(polyline
					(pts
						(xy -1.27 1.27) (xy 1.27 -1.27)
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
			(symbol "SW_Push_1_1"
				(pin passive line
					(at -7.62 0 0)
					(length 4.318)
					(name "1"
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
					(length 4.318)
					(name "2"
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


def start_schematic(output_path: Path) -> tuple[SchematicBuilder, str]:
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
    return builder, root_uuid


def finish_schematic(builder: SchematicBuilder, output_path: Path) -> str:
    builder.open("(sheet_instances")
    builder.open('(path "/"')
    builder.line('(page "1")')
    builder.close(")")
    builder.close(")")
    builder.line("(embedded_fonts no)")
    builder.close(")")
    output_path.write_text(builder.render(), encoding="utf-8")
    return str(output_path)


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


def export_inverting_amplifier(design: Dict, output_path: Path) -> str:
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
    vin_io_origin = Point(50.8, u1a_minus.y)
    vin_io_pin = Point(vin_io_origin.x + 5.08, vin_io_origin.y)
    vout_io_origin = Point(160.02, vout_node.y)
    vout_io_pin = Point(vout_io_origin.x - 5.08, vout_io_origin.y)

    ri_origin = Point(68.58, u1a_minus.y)
    ri_left = Point(ri_origin.x - 7.62, ri_origin.y)
    ri_right = Point(ri_origin.x + 7.62, ri_origin.y)

    rf_origin = Point(107.95, 71.12)
    rf_left = Point(rf_origin.x - 3.81, rf_origin.y)
    rf_right = Point(rf_origin.x + 3.81, rf_origin.y)

    c1_origin = Point(180.34, 81.28)
    c1_top = Point(c1_origin.x, c1_origin.y - 3.81)
    c1_bottom = Point(c1_origin.x, c1_origin.y + 3.81)
    c2_origin = Point(180.34, 127.0)
    c2_top = Point(c2_origin.x, c2_origin.y - 3.81)
    c2_bottom = Point(c2_origin.x, c2_origin.y + 3.81)

    plus_gnd = Point(86.36, u1a_plus.y)
    vcc_symbol = Point(193.04, 76.2)
    vee_symbol = Point(193.04, 132.08)
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
        builder.wire(vin_io_pin, ri_left)
    else:
        builder.label(design["vin_net"], Point(53.34, vin_io_origin.y - 0.635), 0, "left bottom")
        builder.wire(Point(58.42, vin_io_origin.y), ri_left)

    builder.symbol_instance(
        lib_id="edp:R_H",
        at=ri_origin,
        reference=design["ri"]["ref"],
        value=design["ri"]["value"],
        footprint=design["ri"]["footprint"],
        description="Input resistor",
        pin_numbers=["1", "2"],
        ref_at=Point(ri_origin.x - 5.08, ri_origin.y - 5.08),
        value_at=Point(ri_origin.x - 5.08, ri_origin.y + 4.445),
        footprint_at=ri_origin,
    )
    builder.wire(ri_right, sum_node)
    builder.wire(sum_node, u1a_minus)
    builder.wire(sum_node, Point(sum_node.x, rf_left.y))
    builder.wire(Point(sum_node.x, rf_left.y), rf_left)
    builder.junction(sum_node)

    builder.wire(u1a_plus, plus_gnd)
    builder.symbol_instance(
        lib_id="power:GND",
        at=plus_gnd,
        reference="#PWR0101",
        value=design["gnd_net"],
        footprint="",
        description='Power symbol creates a global label with name "GND" , ground',
        pin_numbers=["1"],
        ref_at=Point(plus_gnd.x, plus_gnd.y + 5.08),
        value_at=Point(plus_gnd.x, plus_gnd.y + 2.54),
        footprint_at=plus_gnd,
        ref_hidden=True,
    )

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


def export_passive_shunt_topology(design: Dict, output_path: Path, *, shunt_kind: str) -> str:
    builder, _ = start_schematic(output_path)

    vin_origin = Point(40.64, 88.9)
    vin_pin = Point(vin_origin.x + 5.08, vin_origin.y)
    vout_origin = Point(129.54, 88.9)
    vout_pin = Point(vout_origin.x - 5.08, vout_origin.y)
    gnd_origin = Point(40.64, 121.92)
    gnd_pin = Point(gnd_origin.x + 5.08, gnd_origin.y)

    series_origin = Point(71.12, 88.9)
    series_left = Point(series_origin.x - 7.62, series_origin.y)
    series_right = Point(series_origin.x + 7.62, series_origin.y)
    node = Point(96.52, 88.9)
    shunt_origin = Point(96.52, 104.14)
    shunt_top = Point(shunt_origin.x, shunt_origin.y - 7.62)
    shunt_bottom = Point(shunt_origin.x, shunt_origin.y + 7.62)
    gnd_symbol = Point(96.52, 121.92)

    if design.get("vin_io"):
        builder.symbol_instance(
            lib_id="Connector_Generic:Conn_01x01",
            at=vin_origin,
            reference=design["vin_io"]["ref"],
            value=design["vin_net"],
            footprint=design["vin_io"]["footprint"],
            description="External input",
            pin_numbers=["1"],
            ref_at=Point(vin_origin.x - 1.27, vin_origin.y - 4.445),
            value_at=Point(vin_origin.x - 2.54, vin_origin.y + 4.445),
            footprint_at=vin_origin,
            rotation=180,
        )
        builder.wire(vin_pin, series_left)
    else:
        builder.label(design["vin_net"], Point(48.26, vin_origin.y - 0.635))
        builder.wire(Point(53.34, vin_origin.y), series_left)

    if design.get("vout_io"):
        builder.symbol_instance(
            lib_id="Connector_Generic:Conn_01x01",
            at=vout_origin,
            reference=design["vout_io"]["ref"],
            value=design["vout_net"],
            footprint=design["vout_io"]["footprint"],
            description="External output",
            pin_numbers=["1"],
            ref_at=Point(vout_origin.x - 1.27, vout_origin.y - 4.445),
            value_at=Point(vout_origin.x - 1.27, vout_origin.y + 4.445),
            footprint_at=vout_origin,
            rotation=0,
        )
        builder.wire(node, vout_pin)
    else:
        builder.wire(node, Point(116.84, node.y))
        builder.label(design["vout_net"], Point(121.92, node.y - 0.635))

    if design.get("gnd_io"):
        builder.symbol_instance(
            lib_id="Connector_Generic:Conn_01x01",
            at=gnd_origin,
            reference=design["gnd_io"]["ref"],
            value=design["gnd_net"],
            footprint=design["gnd_io"]["footprint"],
            description="Ground connection",
            pin_numbers=["1"],
            ref_at=Point(gnd_origin.x - 1.27, gnd_origin.y - 4.445),
            value_at=Point(gnd_origin.x - 2.54, gnd_origin.y + 4.445),
            footprint_at=gnd_origin,
            rotation=180,
        )
        builder.wire(gnd_pin, gnd_symbol)

    series_part = design["r_top"] if shunt_kind == "divider" else design["resistor"]
    builder.symbol_instance(
        lib_id="edp:R_H",
        at=series_origin,
        reference=series_part["ref"],
        value=series_part["value"],
        footprint=series_part["footprint"],
        description="Series resistor",
        pin_numbers=["1", "2"],
        ref_at=Point(series_origin.x - 5.08, series_origin.y - 5.08),
        value_at=Point(series_origin.x - 5.08, series_origin.y + 4.445),
        footprint_at=series_origin,
    )
    builder.wire(series_right, node)
    builder.junction(node)

    shunt_part = design["r_bottom"] if shunt_kind == "divider" else design["capacitor"]
    builder.symbol_instance(
        lib_id="edp:R_V" if shunt_kind == "divider" else "edp:C_V",
        at=shunt_origin,
        reference=shunt_part["ref"],
        value=shunt_part["value"],
        footprint=shunt_part["footprint"],
        description="Shunt resistor" if shunt_kind == "divider" else "Shunt capacitor",
        pin_numbers=["1", "2"],
        ref_at=Point(shunt_origin.x + 4.445, shunt_origin.y - 1.27),
        value_at=Point(shunt_origin.x + 4.445, shunt_origin.y + 3.81),
        footprint_at=shunt_origin,
    )
    builder.wire(node, shunt_top)
    builder.wire(shunt_bottom, Point(shunt_bottom.x, gnd_symbol.y))
    builder.symbol_instance(
        lib_id="power:GND",
        at=gnd_symbol,
        reference="#PWR0101",
        value=design["gnd_net"],
        footprint="",
        description='Power symbol creates a global label with name "GND" , ground',
        pin_numbers=["1"],
        ref_at=Point(gnd_symbol.x, gnd_symbol.y + 5.08),
        value_at=Point(gnd_symbol.x, gnd_symbol.y + 2.54),
        footprint_at=gnd_symbol,
        ref_hidden=True,
    )

    return finish_schematic(builder, output_path)


def export_linear_regulator(design: Dict, output_path: Path) -> str:
    builder, _ = start_schematic(output_path)

    input_conn = Point(35.56, 90.17)
    input_pin_1 = Point(input_conn.x + 5.08, input_conn.y - 1.27)
    input_pin_2 = Point(input_conn.x + 5.08, input_conn.y + 1.27)
    output_conn = Point(132.08, 90.17)
    output_pin_1 = Point(output_conn.x - 5.08, output_conn.y - 1.27)
    output_pin_2 = Point(output_conn.x - 5.08, output_conn.y + 1.27)

    reg_origin = Point(81.28, 91.44)
    reg_in = local_to_sheet(reg_origin, -7.62, 2.54)
    reg_out = local_to_sheet(reg_origin, 7.62, 2.54)
    reg_gnd = local_to_sheet(reg_origin, 0, -6.35)

    vin_bus_y = reg_in.y
    vout_bus_y = reg_out.y
    gnd_bus_y = 111.76

    input_cap_x = [53.34, 63.5]
    output_cap_x = [99.06, 109.22]

    if design.get("input_connector"):
        builder.symbol_instance(
            lib_id="Connector_Generic:Conn_01x02",
            at=input_conn,
            reference=design["input_connector"]["ref"],
            value=design["vin_net"],
            footprint=design["input_connector"]["footprint"],
            description="Input connector",
            pin_numbers=["1", "2"],
            ref_at=Point(input_conn.x - 1.27, input_conn.y - 6.35),
            value_at=Point(input_conn.x - 2.54, input_conn.y + 6.35),
            footprint_at=input_conn,
            rotation=180,
        )
        builder.wire(input_pin_1, reg_in)
        builder.wire(input_pin_2, Point(input_pin_2.x, gnd_bus_y))
    else:
        builder.label(design["vin_net"], Point(45.72, vin_bus_y - 0.635))
        builder.wire(Point(50.8, vin_bus_y), reg_in)

    if design.get("output_connector"):
        builder.symbol_instance(
            lib_id="Connector_Generic:Conn_01x02",
            at=output_conn,
            reference=design["output_connector"]["ref"],
            value=design["vout_net"],
            footprint=design["output_connector"]["footprint"],
            description="Output connector",
            pin_numbers=["1", "2"],
            ref_at=Point(output_conn.x - 1.27, output_conn.y - 6.35),
            value_at=Point(output_conn.x - 2.54, output_conn.y + 6.35),
            footprint_at=output_conn,
            rotation=0,
        )
        builder.wire(reg_out, output_pin_1)
        builder.wire(output_pin_2, Point(output_pin_2.x, gnd_bus_y))
    else:
        builder.wire(reg_out, Point(119.38, reg_out.y))
        builder.label(design["vout_net"], Point(121.92, reg_out.y - 0.635))

    builder.symbol_instance(
        lib_id="Regulator_Linear:L7805",
        at=reg_origin,
        reference=design["regulator"]["ref"],
        value=design["regulator"]["value"],
        footprint=design["regulator"]["footprint"],
        description="Positive 5V linear regulator",
        pin_numbers=["1", "2", "3"],
        ref_at=Point(reg_origin.x - 5.08, reg_origin.y - 7.62),
        value_at=Point(reg_origin.x - 5.08, reg_origin.y + 7.62),
        footprint_at=reg_origin,
    )
    builder.wire(reg_gnd, Point(reg_gnd.x, gnd_bus_y))

    for x_pos, capacitor in zip(input_cap_x, design["input_caps"]):
        origin = Point(x_pos, vin_bus_y + 7.62)
        top = Point(origin.x, origin.y - 7.62)
        bottom = Point(origin.x, origin.y + 7.62)
        builder.symbol_instance(
            lib_id="edp:C_V",
            at=origin,
            reference=capacitor["ref"],
            value=capacitor["value"],
            footprint=capacitor["footprint"],
            description="Input decoupling capacitor",
            pin_numbers=["1", "2"],
            ref_at=Point(origin.x + 4.445, origin.y - 1.27),
            value_at=Point(origin.x + 4.445, origin.y + 3.81),
            footprint_at=origin,
        )
        builder.wire(top, Point(top.x, vin_bus_y))
        builder.wire(bottom, Point(bottom.x, gnd_bus_y))

    for x_pos, capacitor in zip(output_cap_x, design["output_caps"]):
        origin = Point(x_pos, vout_bus_y + 7.62)
        top = Point(origin.x, origin.y - 7.62)
        bottom = Point(origin.x, origin.y + 7.62)
        builder.symbol_instance(
            lib_id="edp:C_V",
            at=origin,
            reference=capacitor["ref"],
            value=capacitor["value"],
            footprint=capacitor["footprint"],
            description="Output decoupling capacitor",
            pin_numbers=["1", "2"],
            ref_at=Point(origin.x + 4.445, origin.y - 1.27),
            value_at=Point(origin.x + 4.445, origin.y + 3.81),
            footprint_at=origin,
        )
        builder.wire(top, Point(top.x, vout_bus_y))
        builder.wire(bottom, Point(bottom.x, gnd_bus_y))

    builder.symbol_instance(
        lib_id="power:GND",
        at=Point(81.28, gnd_bus_y),
        reference="#PWR0101",
        value=design["gnd_net"],
        footprint="",
        description='Power symbol creates a global label with name "GND" , ground',
        pin_numbers=["1"],
        ref_at=Point(81.28, gnd_bus_y + 5.08),
        value_at=Point(81.28, gnd_bus_y + 2.54),
        footprint_at=Point(81.28, gnd_bus_y),
        ref_hidden=True,
    )

    return finish_schematic(builder, output_path)


def export_comet_led_sequencer(design: Dict, output_path: Path) -> str:
    builder, _ = start_schematic(output_path)

    def place_gnd(reference: str, at: Point) -> None:
        builder.symbol_instance(
            lib_id="power:GND",
            at=at,
            reference=reference,
            value=design["gnd_net"],
            footprint="",
            description='Power symbol creates a global label with name "GND" , ground',
            pin_numbers=["1"],
            ref_at=Point(at.x, at.y + 5.08),
            value_at=Point(at.x, at.y + 2.54),
            footprint_at=at,
            ref_hidden=True,
        )

    def place_vcc(reference: str, at: Point) -> None:
        builder.symbol_instance(
            lib_id="power:VCC",
            at=at,
            reference=reference,
            value=design["vcc_net"],
            footprint="",
            description='Power symbol creates a global label with name "VCC"',
            pin_numbers=["1"],
            ref_at=Point(at.x, at.y + 5.08),
            value_at=Point(at.x, at.y - 2.54),
            footprint_at=at,
            ref_hidden=True,
        )

    power_conn = Point(30.48, 55.88)
    power_pin_vcc = Point(power_conn.x + 5.08, power_conn.y - 1.27)
    power_pin_gnd = Point(power_conn.x + 5.08, power_conn.y + 1.27)
    bulk_cap = Point(48.26, 60.96)
    bulk_cap_top = Point(bulk_cap.x, bulk_cap.y - 7.62)
    bulk_cap_bottom = Point(bulk_cap.x, bulk_cap.y + 7.62)

    timer = Point(81.28, 81.28)
    timer_rst = local_to_sheet(timer, -10.16, 7.62)
    timer_thres = local_to_sheet(timer, -10.16, 2.54)
    timer_trig = local_to_sheet(timer, -10.16, -2.54)
    timer_cont = local_to_sheet(timer, -10.16, -7.62)
    timer_disch = local_to_sheet(timer, 10.16, 7.62)
    timer_out = local_to_sheet(timer, 10.16, 0)
    timer_vcc = local_to_sheet(timer, 0, 12.7)
    timer_gnd = local_to_sheet(timer, 0, -12.7)

    timer_decouple = Point(66.04, 60.96)
    timer_decouple_top = Point(timer_decouple.x, timer_decouple.y - 7.62)
    timer_decouple_bottom = Point(timer_decouple.x, timer_decouple.y + 7.62)
    control_cap = Point(55.88, 96.52)
    control_cap_top = Point(control_cap.x, control_cap.y - 3.81)
    control_cap_bottom = Point(control_cap.x, control_cap.y + 3.81)

    charge_res = Point(119.38, 53.34)
    charge_res_left = Point(charge_res.x - 7.62, charge_res.y)
    charge_res_right = Point(charge_res.x + 7.62, charge_res.y)
    speed_res = Point(119.38, 63.5)
    speed_res_left = Point(speed_res.x - 7.62, speed_res.y)
    speed_res_right = Point(speed_res.x + 7.62, speed_res.y)
    speed_pot = Point(139.7, 73.66)
    pot_pin_1 = Point(speed_pot.x, speed_pot.y - 10.16)
    pot_pin_2 = Point(speed_pot.x - 7.62, speed_pot.y)
    pot_pin_3 = Point(speed_pot.x, speed_pot.y + 10.16)
    timing_cap = Point(147.32, 96.52)
    timing_cap_top = Point(timing_cap.x, timing_cap.y - 3.81)
    timing_cap_bottom = Point(timing_cap.x, timing_cap.y + 3.81)

    reset_switch = Point(104.14, 48.26)
    reset_switch_left = Point(reset_switch.x - 7.62, reset_switch.y)
    reset_switch_right = Point(reset_switch.x + 7.62, reset_switch.y)
    reset_pull = Point(111.76, 86.36)
    reset_pull_top = Point(reset_pull.x, reset_pull.y - 3.81)
    reset_pull_bottom = Point(reset_pull.x, reset_pull.y + 3.81)

    counter = Point(137.16, 81.28)
    counter_cp0 = local_to_sheet(counter, -15.24, 20.32)
    counter_cp1 = local_to_sheet(counter, -15.24, 15.24)
    counter_mr = local_to_sheet(counter, -15.24, 10.16)
    counter_co = local_to_sheet(counter, -15.24, 0)
    counter_vdd = local_to_sheet(counter, 0, 33.02)
    counter_vss = local_to_sheet(counter, 0, -33.02)
    counter_outputs = [
        local_to_sheet(counter, 15.24, 22.86),
        local_to_sheet(counter, 15.24, 17.78),
        local_to_sheet(counter, 15.24, 12.7),
        local_to_sheet(counter, 15.24, 7.62),
        local_to_sheet(counter, 15.24, 2.54),
        local_to_sheet(counter, 15.24, -2.54),
        local_to_sheet(counter, 15.24, -7.62),
        local_to_sheet(counter, 15.24, -12.7),
        local_to_sheet(counter, 15.24, -17.78),
        local_to_sheet(counter, 15.24, -22.86),
    ]

    counter_decouple = Point(154.94, 60.96)
    counter_decouple_top = Point(counter_decouple.x, counter_decouple.y - 7.62)
    counter_decouple_bottom = Point(counter_decouple.x, counter_decouple.y + 7.62)
    carry_conn = Point(101.6, 81.28)
    carry_pin = Point(carry_conn.x + 5.08, carry_conn.y)

    led_bus_x = 205.74
    led_ground_top = counter_outputs[0].y + 15.24
    led_ground_bottom = counter_outputs[-1].y + 15.24

    builder.symbol_instance(
        lib_id="Connector_Generic:Conn_01x02",
        at=power_conn,
        reference=design["power_connector"]["ref"],
        value=design["vcc_net"],
        footprint=design["power_connector"]["footprint"],
        description="5V power input",
        pin_numbers=["1", "2"],
        ref_at=Point(power_conn.x - 1.27, power_conn.y - 6.35),
        value_at=Point(power_conn.x - 2.54, power_conn.y + 6.35),
        footprint_at=power_conn,
        rotation=180,
    )
    builder.symbol_instance(
        lib_id="edp:C_V",
        at=bulk_cap,
        reference=design["bulk_capacitor"]["ref"],
        value=design["bulk_capacitor"]["value"],
        footprint=design["bulk_capacitor"]["footprint"],
        description="Input bulk capacitor",
        pin_numbers=["1", "2"],
        ref_at=Point(bulk_cap.x + 4.445, bulk_cap.y - 1.27),
        value_at=Point(bulk_cap.x + 4.445, bulk_cap.y + 3.81),
        footprint_at=bulk_cap,
    )
    builder.wire(power_pin_vcc, bulk_cap_top)
    builder.wire(power_pin_gnd, bulk_cap_bottom)
    place_vcc("#PWR0201", Point(bulk_cap_top.x, bulk_cap_top.y - 5.08))
    builder.wire(bulk_cap_top, Point(bulk_cap_top.x, bulk_cap_top.y - 5.08))
    place_gnd("#PWR0202", Point(bulk_cap_bottom.x, bulk_cap_bottom.y + 5.08))
    builder.wire(bulk_cap_bottom, Point(bulk_cap_bottom.x, bulk_cap_bottom.y + 5.08))

    builder.symbol_instance(
        lib_id="Timer:NE555P",
        at=timer,
        reference=design["timer"]["ref"],
        value=design["timer"]["value"],
        footprint=design["timer"]["footprint"],
        description="Precision timer, 555 compatible",
        pin_numbers=["1", "2", "3", "4", "5", "6", "7", "8"],
        ref_at=Point(timer.x - 6.35, timer.y - 13.97),
        value_at=Point(timer.x - 10.16, timer.y + 13.97),
        footprint_at=timer,
        datasheet="http://www.ti.com/lit/ds/symlink/ne555.pdf",
    )
    builder.symbol_instance(
        lib_id="edp:C_V",
        at=timer_decouple,
        reference=design["timer_decoupling"]["ref"],
        value=design["timer_decoupling"]["value"],
        footprint=design["timer_decoupling"]["footprint"],
        description="555 supply decoupling capacitor",
        pin_numbers=["1", "2"],
        ref_at=Point(timer_decouple.x + 4.445, timer_decouple.y - 1.27),
        value_at=Point(timer_decouple.x + 4.445, timer_decouple.y + 3.81),
        footprint_at=timer_decouple,
    )
    place_vcc("#PWR0203", Point(timer_vcc.x, timer_vcc.y - 5.08))
    builder.wire(timer_vcc, Point(timer_vcc.x, timer_vcc.y - 5.08))
    place_gnd("#PWR0204", Point(timer_gnd.x, timer_gnd.y + 5.08))
    builder.wire(timer_gnd, Point(timer_gnd.x, timer_gnd.y + 5.08))
    place_vcc("#PWR0205", Point(timer_decouple_top.x, timer_decouple_top.y - 5.08))
    builder.wire(timer_decouple_top, Point(timer_decouple_top.x, timer_decouple_top.y - 5.08))
    place_gnd("#PWR0206", Point(timer_decouple_bottom.x, timer_decouple_bottom.y + 5.08))
    builder.wire(timer_decouple_bottom, Point(timer_decouple_bottom.x, timer_decouple_bottom.y + 5.08))
    builder.wire(timer_rst, Point(timer_rst.x, timer_rst.y - 17.78))
    place_vcc("#PWR0207", Point(timer_rst.x, timer_rst.y - 22.86))
    builder.wire(Point(timer_rst.x, timer_rst.y - 17.78), Point(timer_rst.x, timer_rst.y - 22.86))

    builder.symbol_instance(
        lib_id="Device:C",
        at=control_cap,
        reference=design["control_capacitor"]["ref"],
        value=design["control_capacitor"]["value"],
        footprint=design["control_capacitor"]["footprint"],
        description="555 control pin bypass capacitor",
        pin_numbers=["1", "2"],
        ref_at=Point(control_cap.x - 10.16, control_cap.y - 1.27),
        value_at=Point(control_cap.x - 10.16, control_cap.y - 6.35),
        footprint_at=control_cap,
    )
    builder.wire(timer_cont, Point(control_cap_top.x, timer_cont.y))
    builder.wire(Point(control_cap_top.x, timer_cont.y), control_cap_top)
    place_gnd("#PWR0208", Point(control_cap_bottom.x, control_cap_bottom.y + 5.08))
    builder.wire(control_cap_bottom, Point(control_cap_bottom.x, control_cap_bottom.y + 5.08))

    builder.wire(timer_out, Point(timer_out.x + 10.16, timer_out.y))
    builder.label(design["clock_net"], Point(timer_out.x + 10.16, timer_out.y))
    builder.wire(timer_disch, Point(timer_disch.x + 10.16, timer_disch.y))
    builder.label(design["discharge_net"], Point(timer_disch.x + 10.16, timer_disch.y))
    builder.wire(timer_thres, Point(timer_thres.x - 7.62, timer_thres.y))
    builder.label(design["timing_net"], Point(timer_thres.x - 7.62, timer_thres.y))
    builder.wire(timer_trig, Point(timer_trig.x - 7.62, timer_trig.y))
    builder.label(design["timing_net"], Point(timer_trig.x - 7.62, timer_trig.y))

    builder.symbol_instance(
        lib_id="edp:R_H",
        at=charge_res,
        reference=design["charge_resistor"]["ref"],
        value=design["charge_resistor"]["value"],
        footprint=design["charge_resistor"]["footprint"],
        description="555 charge resistor",
        pin_numbers=["1", "2"],
        ref_at=Point(charge_res.x - 5.08, charge_res.y - 5.08),
        value_at=Point(charge_res.x - 5.08, charge_res.y + 4.445),
        footprint_at=charge_res,
    )
    builder.label(design["discharge_net"], charge_res_left)
    builder.wire(charge_res_right, Point(charge_res_right.x + 7.62, charge_res_right.y))
    place_vcc("#PWR0209", Point(charge_res_right.x + 7.62, charge_res_right.y))

    builder.symbol_instance(
        lib_id="edp:R_H",
        at=speed_res,
        reference=design["speed_resistor"]["ref"],
        value=design["speed_resistor"]["value"],
        footprint=design["speed_resistor"]["footprint"],
        description="555 minimum speed resistor",
        pin_numbers=["1", "2"],
        ref_at=Point(speed_res.x - 5.08, speed_res.y - 5.08),
        value_at=Point(speed_res.x - 5.08, speed_res.y + 4.445),
        footprint_at=speed_res,
    )
    builder.label(design["discharge_net"], speed_res_left)

    builder.symbol_instance(
        lib_id="Device:R_Potentiometer",
        at=speed_pot,
        reference=design["potentiometer"]["ref"],
        value=design["potentiometer"]["value"],
        footprint=design["potentiometer"]["footprint"],
        description="Speed control potentiometer",
        pin_numbers=["1", "2", "3"],
        ref_at=Point(speed_pot.x + 3.81, speed_pot.y - 7.62),
        value_at=Point(speed_pot.x + 3.81, speed_pot.y + 7.62),
        footprint_at=speed_pot,
    )
    builder.wire(speed_res_right, Point(pot_pin_1.x, speed_res_right.y))
    builder.wire(Point(pot_pin_1.x, speed_res_right.y), pot_pin_1)
    builder.wire(pot_pin_2, Point(pot_pin_2.x, pot_pin_3.y))
    builder.wire(Point(pot_pin_2.x, pot_pin_3.y), pot_pin_3)
    builder.label(design["timing_net"], Point(pot_pin_2.x - 7.62, pot_pin_2.y + 5.08))
    builder.wire(Point(pot_pin_2.x - 7.62, pot_pin_2.y + 5.08), Point(pot_pin_2.x, pot_pin_2.y + 5.08))

    builder.symbol_instance(
        lib_id="Device:C",
        at=timing_cap,
        reference=design["timing_capacitor"]["ref"],
        value=design["timing_capacitor"]["value"],
        footprint=design["timing_capacitor"]["footprint"],
        description="555 timing capacitor",
        pin_numbers=["1", "2"],
        ref_at=Point(timing_cap.x + 4.445, timing_cap.y - 1.27),
        value_at=Point(timing_cap.x + 4.445, timing_cap.y + 3.81),
        footprint_at=timing_cap,
    )
    builder.label(design["timing_net"], timing_cap_top)
    place_gnd("#PWR0210", Point(timing_cap_bottom.x, timing_cap_bottom.y + 5.08))
    builder.wire(timing_cap_bottom, Point(timing_cap_bottom.x, timing_cap_bottom.y + 5.08))

    builder.symbol_instance(
        lib_id="Switch:SW_Push",
        at=reset_switch,
        reference=design["reset_switch"]["ref"],
        value=design["reset_switch"]["value"],
        footprint=design["reset_switch"]["footprint"],
        description="Manual reset switch",
        pin_numbers=["1", "2"],
        ref_at=Point(reset_switch.x - 2.54, reset_switch.y - 5.08),
        value_at=Point(reset_switch.x - 5.08, reset_switch.y + 4.445),
        footprint_at=reset_switch,
    )
    place_vcc("#PWR0211", Point(reset_switch_left.x, reset_switch_left.y - 7.62))
    builder.wire(reset_switch_left, Point(reset_switch_left.x, reset_switch_left.y - 7.62))
    builder.wire(reset_switch_right, Point(reset_switch_right.x, reset_switch_right.y))
    builder.label(design["reset_net"], Point(reset_switch_right.x, reset_switch_right.y))

    builder.symbol_instance(
        lib_id="Device:R",
        at=reset_pull,
        reference=design["reset_pull"]["ref"],
        value=design["reset_pull"]["value"],
        footprint=design["reset_pull"]["footprint"],
        description="Reset pull-down resistor",
        pin_numbers=["1", "2"],
        ref_at=Point(reset_pull.x + 4.445, reset_pull.y - 1.27),
        value_at=Point(reset_pull.x + 4.445, reset_pull.y + 3.81),
        footprint_at=reset_pull,
    )
    builder.label(design["reset_net"], reset_pull_top)
    place_gnd("#PWR0212", Point(reset_pull_bottom.x, reset_pull_bottom.y + 5.08))
    builder.wire(reset_pull_bottom, Point(reset_pull_bottom.x, reset_pull_bottom.y + 5.08))

    builder.symbol_instance(
        lib_id="4xxx_IEEE:4017",
        at=counter,
        reference=design["counter"]["ref"],
        value=design["counter"]["value"],
        footprint=design["counter"]["footprint"],
        description="CMOS decade counter and decoder",
        pin_numbers=["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15", "16"],
        ref_at=Point(counter.x - 7.62, counter.y - 31.75),
        value_at=Point(counter.x - 10.16, counter.y + 31.75),
        footprint_at=counter,
    )
    builder.symbol_instance(
        lib_id="edp:C_V",
        at=counter_decouple,
        reference=design["counter_decoupling"]["ref"],
        value=design["counter_decoupling"]["value"],
        footprint=design["counter_decoupling"]["footprint"],
        description="4017 supply decoupling capacitor",
        pin_numbers=["1", "2"],
        ref_at=Point(counter_decouple.x + 4.445, counter_decouple.y - 1.27),
        value_at=Point(counter_decouple.x + 4.445, counter_decouple.y + 3.81),
        footprint_at=counter_decouple,
    )
    place_vcc("#PWR0213", Point(counter_vdd.x, counter_vdd.y - 5.08))
    builder.wire(counter_vdd, Point(counter_vdd.x, counter_vdd.y - 5.08))
    place_gnd("#PWR0214", Point(counter_vss.x, counter_vss.y + 5.08))
    builder.wire(counter_vss, Point(counter_vss.x, counter_vss.y + 5.08))
    builder.label(design["clock_net"], Point(counter_cp0.x - 10.16, counter_cp0.y))
    builder.wire(Point(counter_cp0.x - 10.16, counter_cp0.y), counter_cp0)
    place_gnd("#PWR0215", Point(counter_cp1.x - 10.16, counter_cp1.y))
    builder.wire(Point(counter_cp1.x - 10.16, counter_cp1.y), counter_cp1)
    builder.label(design["reset_net"], Point(counter_mr.x - 10.16, counter_mr.y))
    builder.wire(Point(counter_mr.x - 10.16, counter_mr.y), counter_mr)
    builder.symbol_instance(
        lib_id="Connector_Generic:Conn_01x01",
        at=carry_conn,
        reference=design["carry_connector"]["ref"],
        value=design["carry_net"],
        footprint=design["carry_connector"]["footprint"],
        description="Cascade clock output",
        pin_numbers=["1"],
        ref_at=Point(carry_conn.x - 1.27, carry_conn.y - 4.445),
        value_at=Point(carry_conn.x - 2.54, carry_conn.y + 4.445),
        footprint_at=carry_conn,
        rotation=180,
    )
    builder.wire(carry_pin, counter_co)
    place_vcc("#PWR0216", Point(counter_decouple_top.x, counter_decouple_top.y - 5.08))
    builder.wire(counter_decouple_top, Point(counter_decouple_top.x, counter_decouple_top.y - 5.08))
    place_gnd("#PWR0217", Point(counter_decouple_bottom.x, counter_decouple_bottom.y + 5.08))
    builder.wire(counter_decouple_bottom, Point(counter_decouple_bottom.x, counter_decouple_bottom.y + 5.08))

    builder.wire(Point(led_bus_x, led_ground_top), Point(led_bus_x, led_ground_bottom))
    place_gnd("#PWR0218", Point(led_bus_x, led_ground_bottom + 5.08))
    builder.wire(Point(led_bus_x, led_ground_bottom), Point(led_bus_x, led_ground_bottom + 5.08))

    for output_point, channel in zip(counter_outputs, design["led_channels"]):
        label_point = Point(output_point.x + 5.08, output_point.y)
        resistor_origin = Point(177.8, output_point.y)
        resistor_left = Point(resistor_origin.x - 7.62, resistor_origin.y)
        resistor_right = Point(resistor_origin.x + 7.62, resistor_origin.y)
        led_origin = Point(195.58, output_point.y + 7.62)
        led_anode = Point(led_origin.x, led_origin.y - 7.62)
        led_cathode = Point(led_origin.x, led_origin.y + 7.62)

        builder.wire(output_point, label_point)
        builder.label(channel["step_net"], label_point)
        builder.label(channel["step_net"], resistor_left)
        builder.symbol_instance(
            lib_id="edp:R_H",
            at=resistor_origin,
            reference=channel["resistor"]["ref"],
            value=channel["resistor"]["value"],
            footprint=channel["resistor"]["footprint"],
            description="LED current limit resistor",
            pin_numbers=["1", "2"],
            ref_at=Point(resistor_origin.x - 5.08, resistor_origin.y - 5.08),
            value_at=Point(resistor_origin.x - 5.08, resistor_origin.y + 4.445),
            footprint_at=resistor_origin,
        )
        builder.symbol_instance(
            lib_id="Device:LED",
            at=led_origin,
            reference=channel["led"]["ref"],
            value=channel["led"]["value"],
            footprint=channel["led"]["footprint"],
            description="Sequencer output LED",
            pin_numbers=["1", "2"],
            ref_at=Point(led_origin.x + 3.81, led_origin.y - 1.27),
            value_at=Point(led_origin.x + 3.81, led_origin.y + 3.81),
            footprint_at=led_origin,
        )
        builder.wire(resistor_right, led_anode)
        builder.wire(led_cathode, Point(led_bus_x, led_cathode.y))

    builder.text("555 astable clock + 4017 decade counter comet sequencer", Point(22.86, 27.94))
    builder.text("Local labels tie CLOCK, RESET, TIMING and DISCHARGE nets across the sheet.", Point(22.86, 33.02))

    return finish_schematic(builder, output_path)


def export_supported_design(design: SupportedDesign, output_path: Path) -> str:
    if design.kind == "opamp_amplifier":
        if design.data["mode"] == "non_inverting":
            return export_non_inverting_amplifier(design.data, output_path)
        return export_inverting_amplifier(design.data, output_path)
    if design.kind == "comet_led_sequencer":
        return export_comet_led_sequencer(design.data, output_path)
    if design.kind == "voltage_divider":
        return export_passive_shunt_topology(design.data, output_path, shunt_kind="divider")
    if design.kind == "rc_lowpass":
        return export_passive_shunt_topology(design.data, output_path, shunt_kind="lowpass")
    if design.kind == "linear_regulator":
        return export_linear_regulator(design.data, output_path)
    raise ValueError(f"Unsupported design kind: {design.kind}")


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
            suppress_skidl_file_output()
        except ImportError:
            print("Error: SKiDL is not installed. Run: uv sync", file=sys.stderr)
            sys.exit(1)

        circuit = load_skidl_circuit(args.script)
        circuit_info = analyze_circuit(circuit)
        design = identify_supported_design(circuit_info)
        if not design:
            raise ValueError(
                "KiCad schematic export could not map this circuit to a supported topology. "
                "Supported topology families currently include the comet LED sequencer, voltage-divider, "
                "rc-lowpass, L7805 linear regulator, and TL072 inverting/non-inverting amplifiers."
            )

        schematic_path = project_dir / f"{base_name}.kicad_sch"
        project_path = project_dir / f"{base_name}.kicad_pro"

        export_supported_design(design, schematic_path)
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
