"""
オペアンプ増幅回路 - SKiDLテンプレート

非反転増幅回路 / 反転増幅回路。
"""
from skidl import *

# =============================================================================
# パラメータ（仕様書に合わせて変更）
# =============================================================================

# 増幅器タイプ
AMP_TYPE = "non_inverting"  # "non_inverting" または "inverting"

# ゲイン
GAIN = 10  # 電圧ゲイン（非反転: 1以上, 反転: 任意）

# 入力抵抗（固定）
RI_VALUE = 10000  # 10kΩ

# フィードバック抵抗を計算
if AMP_TYPE == "non_inverting":
    # 非反転: Gain = 1 + Rf/Ri
    # Rf = (Gain - 1) × Ri
    RF_VALUE = (GAIN - 1) * RI_VALUE
else:
    # 反転: Gain = -Rf/Ri
    # Rf = |Gain| × Ri
    RF_VALUE = abs(GAIN) * RI_VALUE

# 抵抗値の文字列表現
def format_resistance(value):
    if value >= 1000000:
        return f'{value/1000000:.1f}M'
    elif value >= 1000:
        return f'{value/1000:.0f}K'
    else:
        return f'{int(value)}'

RI_STR = format_resistance(RI_VALUE)
RF_STR = format_resistance(RF_VALUE)

print(f"増幅器タイプ: {AMP_TYPE}")
print(f"設計ゲイン: {GAIN}")
print(f"Ri = {RI_STR}Ω")
print(f"Rf = {RF_STR}Ω")

if AMP_TYPE == "non_inverting":
    actual_gain = 1 + RF_VALUE / RI_VALUE
else:
    actual_gain = -RF_VALUE / RI_VALUE
print(f"実際のゲイン: {actual_gain:.2f}")

# =============================================================================
# 回路定義
# =============================================================================

set_default_tool(KICAD)

# ネット定義
vin = Net('VIN')
vout = Net('VOUT')
vcc = Net('VCC')
vee = Net('VEE')  # 負電源（単電源の場合はGNDに接続）
gnd = Net('GND')

# 電源属性
vcc.drive = POWER
vee.drive = POWER
gnd.drive = POWER

# 内部ネット
inv_input = Net('INV_INPUT')

# 部品定義
opamp = Part("Amplifier_Operational", 'TL072',
             footprint='Package_DIP:DIP-8_W7.62mm')
ri = Part("Device", 'R', value=RI_STR,
          footprint='Resistor_SMD:R_0603_1608Metric')
rf = Part("Device", 'R', value=RF_STR,
          footprint='Resistor_SMD:R_0603_1608Metric')

# 電源接続
vcc += opamp['V+']
vee += opamp['V-']

# 増幅回路接続
if AMP_TYPE == "non_inverting":
    # 非反転増幅回路
    # VIN -> + 入力
    # GND -> Ri -> - 入力 -> Rf -> VOUT
    vin += opamp['1+']
    gnd & ri & inv_input & rf & vout
    inv_input += opamp['1-']
    vout += opamp['1OUT']
else:
    # 反転増幅回路
    # VIN -> Ri -> - 入力 -> Rf -> VOUT
    # GND -> + 入力
    gnd += opamp['1+']
    vin & ri & inv_input & rf & vout
    inv_input += opamp['1-']
    vout += opamp['1OUT']

# =============================================================================
# バイパスコンデンサ（オプション）
# =============================================================================

# 電源バイパスコンデンサ
c_bypass_p = Part("Device", 'C', value='100n',
                  footprint='Capacitor_SMD:C_0603_1608Metric')
c_bypass_n = Part("Device", 'C', value='100n',
                  footprint='Capacitor_SMD:C_0603_1608Metric')

vcc & c_bypass_p & gnd
vee & c_bypass_n & gnd

# =============================================================================
# 検証
# =============================================================================

ERC()

print(f"\n回路情報:")
print(f"  部品数: {len(default_circuit.parts)}")
print(f"  ネット数: {len(default_circuit.nets)}")

# =============================================================================
# 出力（必要に応じてコメント解除）
# =============================================================================

# generate_netlist(file_='opamp_amplifier.net')
