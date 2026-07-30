"""
分圧回路 - SKiDLテンプレート

2つの抵抗による分圧回路。
"""
from skidl import *

# =============================================================================
# パラメータ（仕様書に合わせて変更）
# =============================================================================

# 電圧仕様
VIN_VOLTAGE = 5.0     # 入力電圧 [V]
VOUT_VOLTAGE = 3.3    # 出力電圧 [V]

# 電流仕様
DIVIDER_CURRENT = 0.001  # 分圧回路電流 [A]（1mA）

# 計算
R_TOTAL = VIN_VOLTAGE / DIVIDER_CURRENT
R2_VALUE = R_TOTAL * (VOUT_VOLTAGE / VIN_VOLTAGE)
R1_VALUE = R_TOTAL - R2_VALUE

# E24系列に丸める関数
def round_to_e24(value):
    e24 = [1.0, 1.1, 1.2, 1.3, 1.5, 1.6, 1.8, 2.0, 2.2, 2.4, 2.7, 3.0,
           3.3, 3.6, 3.9, 4.3, 4.7, 5.1, 5.6, 6.2, 6.8, 7.5, 8.2, 9.1]
    magnitude = 10 ** int(len(str(int(value))) - 1)
    normalized = value / magnitude
    closest = min(e24, key=lambda x: abs(x - normalized))
    return closest * magnitude

R1_ROUNDED = round_to_e24(R1_VALUE)
R2_ROUNDED = round_to_e24(R2_VALUE)

# 実際の出力電圧を計算
ACTUAL_VOUT = VIN_VOLTAGE * R2_ROUNDED / (R1_ROUNDED + R2_ROUNDED)

print(f"設計値: R1={R1_VALUE:.0f}Ω, R2={R2_VALUE:.0f}Ω")
print(f"E24選定: R1={R1_ROUNDED:.0f}Ω, R2={R2_ROUNDED:.0f}Ω")
print(f"実際のVout: {ACTUAL_VOUT:.3f}V（目標: {VOUT_VOLTAGE}V）")

# =============================================================================
# 回路定義
# =============================================================================

# デフォルトツールをKiCADに設定
set_default_tool(KICAD)

# ネット定義
vin = Net('VIN')
vout = Net('VOUT')
gnd = Net('GND')

# 電源属性設定
gnd.drive = POWER

# 部品定義
r1 = Part("Device", 'R', value=f'{int(R1_ROUNDED)}',
          footprint='Resistor_SMD:R_0603_1608Metric')
r2 = Part("Device", 'R', value=f'{int(R2_ROUNDED)}',
          footprint='Resistor_SMD:R_0603_1608Metric')

# 接続
vin & r1 & vout & r2 & gnd

# =============================================================================
# 検証
# =============================================================================

# ERC実行
ERC()

# 回路情報
print(f"\n回路情報:")
print(f"  部品数: {len(default_circuit.parts)}")
print(f"  ネット数: {len(default_circuit.nets)}")

# =============================================================================
# 出力（必要に応じてコメント解除）
# =============================================================================

# generate_netlist(file_='voltage_divider.net')
