"""
Linear regulator sample - SKiDL implementation.

Specification: specs/linear-regulator-spec.md
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


PROJECT_NAME = "linear-regulator"
VIN_MIN = 9.0
VIN_NOM = 12.0
VIN_MAX = 15.0
VOUT_NOM = 5.0
IOUT_TARGET_MA = 100


set_default_tool(KICAD)
default_circuit.name = PROJECT_NAME

# -----------------------------------------------------------------------------
# Nets
# -----------------------------------------------------------------------------

vin = Net("VIN")
vout = Net("VOUT")
gnd = Net("GND")

vin.drive = POWER
vout.drive = POWER
gnd.drive = POWER

# -----------------------------------------------------------------------------
# External I/O
# -----------------------------------------------------------------------------

j_in = Part(
    "Connector_Generic",
    "Conn_01x02",
    footprint="Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical",
    tag="j_input",
)
j_out = Part(
    "Connector_Generic",
    "Conn_01x02",
    footprint="Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical",
    tag="j_output",
)

vin += j_in[1]
gnd += j_in[2], j_out[2]
vout += j_out[1]

# -----------------------------------------------------------------------------
# Regulator core
# -----------------------------------------------------------------------------

reg = Part(
    "Regulator_Linear",
    "L7805",
    footprint="Package_TO_SOT_THT:TO-220-3_Vertical",
    tag="u1_regulator",
)

vin += reg["IN"]
gnd += reg["GND"]
vout += reg["OUT"]

# -----------------------------------------------------------------------------
# Stability capacitors
# -----------------------------------------------------------------------------

c_in_bulk = Part(
    "Device",
    "C",
    value="10u",
    footprint="Capacitor_THT:CP_Radial_D5.0mm_P2.00mm",
    tag="c_in_bulk",
)
c_in_hf = Part(
    "Device",
    "C",
    value="100n",
    footprint="Capacitor_SMD:C_0603_1608Metric",
    tag="c_in_hf",
)
c_out_bulk = Part(
    "Device",
    "C",
    value="10u",
    footprint="Capacitor_THT:CP_Radial_D5.0mm_P2.00mm",
    tag="c_out_bulk",
)
c_out_hf = Part(
    "Device",
    "C",
    value="100n",
    footprint="Capacitor_SMD:C_0603_1608Metric",
    tag="c_out_hf",
)

vin += c_in_bulk[1], c_in_hf[1]
gnd += c_in_bulk[2], c_in_hf[2]
vout += c_out_bulk[1], c_out_hf[1]
gnd += c_out_bulk[2], c_out_hf[2]


def print_summary() -> None:
    print("=== Linear Regulator ===")
    print(f"Project: {PROJECT_NAME}")
    print(f"Input range: {VIN_MIN:.1f}V to {VIN_MAX:.1f}V")
    print(f"Nominal input: {VIN_NOM:.1f}V")
    print(f"Nominal output: {VOUT_NOM:.1f}V")
    print(f"Target load current: {IOUT_TARGET_MA}mA")
    print(f"Parts: {len(default_circuit.parts)}")
    print(f"Nets: {len(default_circuit.nets)}")


if __name__ == "__main__":
    ERC()
    print_summary()
