"""
RCフィルタ - SKiDLテンプレート

1次RCローパス/ハイパスフィルタ。
"""
from skidl import *
import math

# =============================================================================
# パラメータ（仕様書に合わせて変更）
# =============================================================================

# フィルタタイプ
FILTER_TYPE = "lowpass"  # "lowpass" または "highpass"

# カットオフ周波数
CUTOFF_FREQ = 1000  # カットオフ周波数 [Hz]

# コンデンサ値（固定）
C_VALUE = 100e-9  # 100nF

# 抵抗値を計算
# fc = 1 / (2π × R × C)
# R = 1 / (2π × fc × C)
R_VALUE = 1 / (2 * math.pi * CUTOFF_FREQ * C_VALUE)

# E24系列に丸める
def round_to_e24(value):
    e24 = [1.0, 1.1, 1.2, 1.3, 1.5, 1.6, 1.8, 2.0, 2.2, 2.4, 2.7, 3.0,
           3.3, 3.6, 3.9, 4.3, 4.7, 5.1, 5.6, 6.2, 6.8, 7.5, 8.2, 9.1]
    magnitude = 10 ** int(len(str(int(value))) - 1)
    normalized = value / magnitude
    closest = min(e24, key=lambda x: abs(x - normalized))
    return closest * magnitude

R_ROUNDED = round_to_e24(R_VALUE)

# 実際のカットオフ周波数
ACTUAL_FC = 1 / (2 * math.pi * R_ROUNDED * C_VALUE)

print(f"フィルタタイプ: {FILTER_TYPE}")
print(f"目標カットオフ: {CUTOFF_FREQ} Hz")
print(f"設計値: R={R_VALUE:.0f}Ω, C={C_VALUE*1e9:.0f}nF")
print(f"E24選定: R={R_ROUNDED:.0f}Ω")
print(f"実際のfc: {ACTUAL_FC:.1f} Hz")

# 抵抗値の文字列表現
if R_ROUNDED >= 1000:
    R_STR = f'{R_ROUNDED/1000:.1f}K'
else:
    R_STR = f'{int(R_ROUNDED)}'

# =============================================================================
# 回路定義
# =============================================================================

set_default_tool(KICAD)

# ネット定義
vin = Net('VIN')
vout = Net('VOUT')
gnd = Net('GND')
gnd.drive = POWER

# 部品定義
r = Part("Device", 'R', value=R_STR,
         footprint='Resistor_SMD:R_0603_1608Metric')
c = Part("Device", 'C', value='100n',
         footprint='Capacitor_SMD:C_0603_1608Metric')

# 接続（フィルタタイプによって異なる）
if FILTER_TYPE == "lowpass":
    # ローパス: VIN -> R -> VOUT -> C -> GND
    vin & r & vout & c & gnd
else:
    # ハイパス: VIN -> C -> VOUT -> R -> GND
    vin & c & vout & r & gnd

# =============================================================================
# 検証
# =============================================================================

ERC()

print(f"\n回路情報:")
print(f"  部品数: {len(default_circuit.parts)}")
print(f"  ネット数: {len(default_circuit.nets)}")

# =============================================================================
# 周波数特性（参考）
# =============================================================================

print(f"\n周波数特性（参考）:")
freqs = [CUTOFF_FREQ/10, CUTOFF_FREQ, CUTOFF_FREQ*10]
for f in freqs:
    if FILTER_TYPE == "lowpass":
        # |H(f)| = 1 / sqrt(1 + (f/fc)²)
        gain = 1 / math.sqrt(1 + (f/ACTUAL_FC)**2)
    else:
        # |H(f)| = (f/fc) / sqrt(1 + (f/fc)²)
        gain = (f/ACTUAL_FC) / math.sqrt(1 + (f/ACTUAL_FC)**2)

    gain_db = 20 * math.log10(gain)
    print(f"  {f:>8.0f} Hz: {gain_db:>6.1f} dB")

# =============================================================================
# 出力（必要に応じてコメント解除）
# =============================================================================

# generate_netlist(file_='rc_filter.net')
