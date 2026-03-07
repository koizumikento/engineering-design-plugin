"""
Voltage divider - SKiDL implementation.

Specification: specs/voltage-divider-spec.md
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "skills" / "circuit-design" / "scripts"))

from kicad_env import configure_kicad_env

configure_kicad_env()

from skidl import *
from skidl.logger import stop_log_file_output

try:
    stop_log_file_output()
except FileNotFoundError:
    pass
default_circuit._no_files = True


PROJECT_NAME = "voltage-divider"
VIN_NOMINAL = 5.0
TARGET_VOUT = 3.3
R1_OHMS = 1_000
R2_OHMS = 2_000
ACTUAL_VOUT = VIN_NOMINAL * R2_OHMS / (R1_OHMS + R2_OHMS)
DIVIDER_CURRENT_MA = VIN_NOMINAL / (R1_OHMS + R2_OHMS) * 1_000


def format_resistance(value_ohms: int) -> str:
    if value_ohms >= 1_000_000:
        return f"{value_ohms / 1_000_000:.1f}M"
    if value_ohms >= 1_000:
        return f"{value_ohms / 1_000:.0f}K"
    return str(value_ohms)


set_default_tool(KICAD)
default_circuit.name = PROJECT_NAME

# -----------------------------------------------------------------------------
# Nets
# -----------------------------------------------------------------------------

vin = Net("VIN")
vout = Net("VOUT")
gnd = Net("GND")

vin.drive = Pin.drives.PASSIVE
gnd.drive = POWER

# -----------------------------------------------------------------------------
# External I/O
# -----------------------------------------------------------------------------

vin_io = Part(
    "Connector_Generic",
    "Conn_01x01",
    footprint="Connector_PinHeader_2.54mm:PinHeader_1x01_P2.54mm_Vertical",
    tag="j_input",
)
vout_io = Part(
    "Connector_Generic",
    "Conn_01x01",
    footprint="Connector_PinHeader_2.54mm:PinHeader_1x01_P2.54mm_Vertical",
    tag="j_output",
)
gnd_io = Part(
    "Connector_Generic",
    "Conn_01x01",
    footprint="Connector_PinHeader_2.54mm:PinHeader_1x01_P2.54mm_Vertical",
    tag="j_ground",
)

vin += vin_io[1]
vout += vout_io[1]
gnd += gnd_io[1]

# -----------------------------------------------------------------------------
# Divider network
# -----------------------------------------------------------------------------

r1 = Part(
    "Device",
    "R",
    value=format_resistance(R1_OHMS),
    footprint="Resistor_SMD:R_0603_1608Metric",
    tag="r_top",
)
r2 = Part(
    "Device",
    "R",
    value=format_resistance(R2_OHMS),
    footprint="Resistor_SMD:R_0603_1608Metric",
    tag="r_bottom",
)

vin & r1 & vout & r2 & gnd


def print_summary() -> None:
    print("=== Voltage Divider ===")
    print(f"Vin nominal: {VIN_NOMINAL:.2f} V")
    print(f"Target Vout: {TARGET_VOUT:.2f} V")
    print(f"Actual Vout: {ACTUAL_VOUT:.3f} V")
    print(f"Divider current: {DIVIDER_CURRENT_MA:.2f} mA")
    print(f"R1: {format_resistance(R1_OHMS)}ohm")
    print(f"R2: {format_resistance(R2_OHMS)}ohm")
    print(f"Parts: {len(default_circuit.parts)}")
    print(f"Nets: {len(default_circuit.nets)}")


if __name__ == "__main__":
    ERC()
    print_summary()
