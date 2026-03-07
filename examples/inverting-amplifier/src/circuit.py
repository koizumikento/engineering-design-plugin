"""
Inverting amplifier - SKiDL implementation.

Specification: specs/inverting-amplifier-spec.md
"""

from skidl import *


PROJECT_NAME = "inverting-amplifier"
GAIN_TARGET = -10.0
RI_OHMS = 10_000
RF_OHMS = 100_000
ACTUAL_GAIN = -(RF_OHMS / RI_OHMS)


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

vcc = Net("VCC")
vee = Net("VEE")
gnd = Net("GND")
vin = Net("VIN")
vout = Net("VOUT")
inv_node = Net("INV_NODE")
unused_out = Net("UNUSED_OUT")

vcc.drive = POWER
vee.drive = POWER
gnd.drive = POWER
vin.drive = Pin.drives.PASSIVE

# -----------------------------------------------------------------------------
# Amplifier core
# -----------------------------------------------------------------------------

opamp = Part("Amplifier_Operational", "TL072", footprint="Package_DIP:DIP-8_W7.62mm", tag="u1_main")
ri = Part("Device", "R", value=format_resistance(RI_OHMS), footprint="Resistor_SMD:R_0603_1608Metric", tag="r_input")
rf = Part("Device", "R", value=format_resistance(RF_OHMS), footprint="Resistor_SMD:R_0603_1608Metric", tag="r_feedback")
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

vcc += opamp[8]
vee += opamp[4]

vin += vin_io[1]
vin & ri & inv_node
inv_node += opamp[2]
inv_node & rf & vout
gnd += opamp[3]
vout += opamp[1]
vout += vout_io[1]

# -----------------------------------------------------------------------------
# Terminate the unused second channel to keep the part electrically defined.
# -----------------------------------------------------------------------------

gnd += opamp[5]
opamp[6] += unused_out
unused_out += opamp[7]

# -----------------------------------------------------------------------------
# Decoupling
# -----------------------------------------------------------------------------

c_pos = Part("Device", "C", value="100n", footprint="Capacitor_SMD:C_0603_1608Metric", tag="c_vcc_decouple")
c_neg = Part("Device", "C", value="100n", footprint="Capacitor_SMD:C_0603_1608Metric", tag="c_vee_decouple")

vcc & c_pos & gnd
vee & c_neg & gnd


def print_summary() -> None:
    print("=== Inverting Amplifier ===")
    print(f"Target gain: {GAIN_TARGET:.2f} V/V")
    print(f"Actual gain: {ACTUAL_GAIN:.2f} V/V")
    print(f"Ri: {format_resistance(RI_OHMS)}ohm")
    print(f"Rf: {format_resistance(RF_OHMS)}ohm")
    print(f"Parts: {len(default_circuit.parts)}")
    print(f"Nets: {len(default_circuit.nets)}")


if __name__ == "__main__":
    ERC()
    print_summary()
