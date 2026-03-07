"""
RC low-pass filter - SKiDL implementation.

Specification: specs/rc-lowpass-filter-spec.md
"""

import math
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


PROJECT_NAME = "rc-lowpass-filter"
FILTER_TYPE = "lowpass"
TARGET_CUTOFF_HZ = 1_000.0
CAPACITANCE_F = 100e-9
RESISTANCE_OHMS = 1_600
ACTUAL_CUTOFF_HZ = 1.0 / (2.0 * math.pi * RESISTANCE_OHMS * CAPACITANCE_F)


def format_resistance(value_ohms: int) -> str:
    if value_ohms >= 1_000_000:
        return f"{value_ohms / 1_000_000:.1f}M"
    if value_ohms >= 1_000:
        return f"{value_ohms / 1_000:.1f}K"
    return str(value_ohms)


set_default_tool(KICAD)
default_circuit.name = PROJECT_NAME

# -----------------------------------------------------------------------------
# Nets
# -----------------------------------------------------------------------------

vin = Net("VIN")
vout = Net("VOUT")
gnd = Net("GND")

gnd.drive = POWER
vin.drive = Pin.drives.PASSIVE
vout.drive = Pin.drives.PASSIVE

# -----------------------------------------------------------------------------
# External I/O and passive network
# -----------------------------------------------------------------------------

vin_io = Part(
    "Connector_Generic",
    "Conn_01x01",
    footprint="Connector_PinHeader_2.54mm:PinHeader_1x01_P2.54mm_Vertical",
    tag="j_signal_in",
)
vout_io = Part(
    "Connector_Generic",
    "Conn_01x01",
    footprint="Connector_PinHeader_2.54mm:PinHeader_1x01_P2.54mm_Vertical",
    tag="j_signal_out",
)
gnd_io = Part(
    "Connector_Generic",
    "Conn_01x01",
    footprint="Connector_PinHeader_2.54mm:PinHeader_1x01_P2.54mm_Vertical",
    tag="j_ground",
)

r_filter = Part(
    "Device",
    "R",
    value=format_resistance(RESISTANCE_OHMS),
    footprint="Resistor_SMD:R_0603_1608Metric",
    tag="r_filter",
)
c_filter = Part(
    "Device",
    "C",
    value="100n",
    footprint="Capacitor_SMD:C_0603_1608Metric",
    tag="c_filter",
)

vin += vin_io[1]
vout += vout_io[1]
gnd += gnd_io[1]

if FILTER_TYPE != "lowpass":
    raise ValueError("This sample is fixed to a first-order low-pass topology.")

vin & r_filter & vout & c_filter & gnd


def response_gain_db(frequency_hz: float) -> float:
    gain = 1.0 / math.sqrt(1.0 + (frequency_hz / ACTUAL_CUTOFF_HZ) ** 2)
    return 20.0 * math.log10(gain)


def print_summary() -> None:
    print("=== RC Low-Pass Filter ===")
    print(f"Target cutoff: {TARGET_CUTOFF_HZ:.1f} Hz")
    print(f"Actual cutoff: {ACTUAL_CUTOFF_HZ:.1f} Hz")
    print(f"R: {format_resistance(RESISTANCE_OHMS)}ohm")
    print(f"C: {CAPACITANCE_F * 1e9:.0f}nF")
    print(f"Parts: {len(default_circuit.parts)}")
    print(f"Nets: {len(default_circuit.nets)}")
    print("Reference gain:")
    for frequency_hz in (100.0, 1_000.0, 10_000.0):
        print(f"  {frequency_hz:>7.1f} Hz: {response_gain_db(frequency_hz):>6.2f} dB")


if __name__ == "__main__":
    ERC()
    print_summary()
