"""
LEDドライバ回路 - SKiDL実装

仕様書: specs/led-driver-spec.md
"""
from skidl import *

# =============================================================================
# 仕様書からのパラメータ
# =============================================================================

# 電源
VIN = 5.0  # 入力電圧 [V]

# LED仕様
LED_VF = 3.2    # 順方向電圧 [V]
LED_IF = 0.020  # 順方向電流 [A]
LED_COUNT = 3   # LED数

# 電流制限抵抗計算
R_LIMIT = (VIN - LED_VF) / LED_IF
print(f"計算値: R = {R_LIMIT:.1f}Ω")

# E24系列に丸める
R_SELECTED = 100  # 100Ω選定
ACTUAL_IF = (VIN - LED_VF) / R_SELECTED
print(f"選定値: R = {R_SELECTED}Ω")
print(f"実際のIf = {ACTUAL_IF*1000:.1f}mA")

# =============================================================================
# 回路定義
# =============================================================================

set_default_tool(KICAD)

# ネット定義
vcc = Net('VCC')
gnd = Net('GND')

# 電源属性
vcc.drive = POWER
gnd.drive = POWER

# 電源コネクタ
conn = Part("Connector_Generic", "Conn_01x02",
            footprint='Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical')
conn[1] += vcc
conn[2] += gnd

# LED回路（3並列）
for i in range(LED_COUNT):
    # 電流制限抵抗
    r = Part("Device", 'R', value=f'{R_SELECTED}',
             footprint='Resistor_SMD:R_0603_1608Metric')

    # LED
    led = Part("Device", 'LED', value='WHITE',
               footprint='LED_SMD:LED_0805_2012Metric')

    # 接続: VCC -> R -> LED -> GND
    vcc & r & led & gnd

# =============================================================================
# バイパスコンデンサ
# =============================================================================

c_bypass = Part("Device", 'C', value='100n',
                footprint='Capacitor_SMD:C_0603_1608Metric')
vcc & c_bypass & gnd

# =============================================================================
# 検証
# =============================================================================

ERC()

# 回路情報
print(f"\n=== LED駆動回路 ===")
print(f"LED数: {LED_COUNT}")
print(f"電流制限抵抗: {R_SELECTED}Ω × {LED_COUNT}")
print(f"LED電流: {ACTUAL_IF*1000:.1f}mA/個")
print(f"総消費電流: {ACTUAL_IF*LED_COUNT*1000:.1f}mA")
print(f"\n部品数: {len(default_circuit.parts)}")
print(f"ネット数: {len(default_circuit.nets)}")

# 部品一覧
print("\n部品一覧:")
for part in default_circuit.parts:
    print(f"  {part.ref}: {part.name} ({part.value})")

# =============================================================================
# 出力
# =============================================================================

generate_netlist(file_='outputs/led-driver.net')

# BOM生成
import csv
with open('outputs/led-driver-bom.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['Reference', 'Name', 'Value', 'Footprint', 'Quantity'])

    parts_dict = {}
    for part in default_circuit.parts:
        key = (part.name, part.value, getattr(part, 'footprint', ''))
        if key not in parts_dict:
            parts_dict[key] = {'refs': [], 'count': 0}
        parts_dict[key]['refs'].append(part.ref)
        parts_dict[key]['count'] += 1

    for (name, value, fp), info in sorted(parts_dict.items()):
        writer.writerow([
            ', '.join(sorted(info['refs'])),
            name,
            value,
            fp,
            info['count']
        ])

print("\n出力ファイル:")
print("  outputs/led-driver.net")
print("  outputs/led-driver-bom.csv")
