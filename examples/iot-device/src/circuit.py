"""
IoTデバイス回路 - SKiDL実装

仕様書: specs/iot-device-integrated-spec.md
"""
from skidl import *

# =============================================================================
# 回路定義
# =============================================================================

set_default_tool(KICAD)

# -----------------------------------------------------------------------------
# 電源ネット
# -----------------------------------------------------------------------------

vbus = Net('VBUS')      # USB 5V
vcc = Net('VCC')        # 3.3V
gnd = Net('GND')

vbus.drive = POWER
vcc.drive = POWER
gnd.drive = POWER

# -----------------------------------------------------------------------------
# USB-Cコネクタ
# -----------------------------------------------------------------------------

usb = Part("Connector", "USB_C_Receptacle_USB2.0",
           footprint='Connector_USB:USB_C_Receptacle_Palconn_UTC16-G')

vbus += usb['VBUS']
gnd += usb['GND'], usb['SHIELD']

# USB CC抵抗（5.1k - UFPとして認識）
r_cc1 = Part("Device", 'R', value='5.1K',
             footprint='Resistor_SMD:R_0603_1608Metric')
r_cc2 = Part("Device", 'R', value='5.1K',
             footprint='Resistor_SMD:R_0603_1608Metric')

usb['CC1'] & r_cc1 & gnd
usb['CC2'] & r_cc2 & gnd

# -----------------------------------------------------------------------------
# 3.3Vレギュレータ (AMS1117-3.3)
# -----------------------------------------------------------------------------

reg = Part("Regulator_Linear", "AMS1117-3.3",
           footprint='Package_TO_SOT_SMD:SOT-223-3_TabPin2')

# 入力コンデンサ
c_in = Part("Device", 'C', value='10u',
            footprint='Capacitor_SMD:C_0805_2012Metric')

# 出力コンデンサ
c_out = Part("Device", 'C', value='10u',
             footprint='Capacitor_SMD:C_0805_2012Metric')

vbus += reg['VI'], c_in[1]
c_in[2] += gnd
reg['GND'] += gnd
reg['VO'] += vcc, c_out[1]
c_out[2] += gnd

# -----------------------------------------------------------------------------
# ESP32 (簡略化 - 主要ピンのみ)
# -----------------------------------------------------------------------------

# 注: 完全なESP32回路は多くのピンを使用
# ここでは主要な接続のみ示す

# ESP32モジュール（シンボル簡略化）
esp32 = Part("RF_Module", "ESP32-WROOM-32",
             footprint='RF_Module:ESP32-WROOM-32')

# 電源接続
vcc += esp32['VDD'], esp32['EN']
gnd += esp32['GND']

# EN用プルアップ + RC遅延
r_en = Part("Device", 'R', value='10K',
            footprint='Resistor_SMD:R_0603_1608Metric')
c_en = Part("Device", 'C', value='100n',
            footprint='Capacitor_SMD:C_0603_1608Metric')

vcc & r_en & esp32['EN']
esp32['EN'] & c_en & gnd

# バイパスコンデンサ
c_esp1 = Part("Device", 'C', value='100n',
              footprint='Capacitor_SMD:C_0603_1608Metric')
c_esp2 = Part("Device", 'C', value='10u',
              footprint='Capacitor_SMD:C_0805_2012Metric')

vcc & c_esp1 & gnd
vcc & c_esp2 & gnd

# -----------------------------------------------------------------------------
# DHT22 温湿度センサー
# -----------------------------------------------------------------------------

dht22 = Part("Sensor", "DHT22",
             footprint='Sensor:Aosong_DHT22_5.5x23x0.5mm_P2.54mm')

# DHT22接続コネクタ（4ピン）
conn_dht = Part("Connector_Generic", "Conn_01x04",
                footprint='Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical')

# DHT22ピン配置: 1=VCC, 2=DATA, 3=NC, 4=GND
dht_data = Net('DHT_DATA')

vcc += conn_dht[1]
dht_data += conn_dht[2]
gnd += conn_dht[4]

# データライン用プルアップ
r_dht = Part("Device", 'R', value='4.7K',
             footprint='Resistor_SMD:R_0603_1608Metric')

vcc & r_dht & dht_data
dht_data += esp32['IO4']

# -----------------------------------------------------------------------------
# ステータスLED
# -----------------------------------------------------------------------------

led = Part("Device", 'LED', value='GREEN',
           footprint='LED_SMD:LED_0805_2012Metric')
r_led = Part("Device", 'R', value='1K',
             footprint='Resistor_SMD:R_0603_1608Metric')

led_net = Net('LED')
led_net += esp32['IO2']

led_net & r_led & led & gnd

# -----------------------------------------------------------------------------
# リセットボタン
# -----------------------------------------------------------------------------

sw_reset = Part("Switch", "SW_Push",
                footprint='Button_Switch_SMD:SW_SPST_PTS645')
r_rst = Part("Device", 'R', value='10K',
             footprint='Resistor_SMD:R_0603_1608Metric')
c_rst = Part("Device", 'C', value='100n',
             footprint='Capacitor_SMD:C_0603_1608Metric')

# EN(リセット)ピンにプルアップ済み
# ボタンでGNDに落とす
esp32['EN'] & sw_reset & gnd

# =============================================================================
# 検証
# =============================================================================

ERC()

print("=== IoTデバイス回路 ===")
print(f"部品数: {len(default_circuit.parts)}")
print(f"ネット数: {len(default_circuit.nets)}")

print("\n主要部品:")
for part in default_circuit.parts:
    print(f"  {part.ref}: {part.name} ({part.value})")

# =============================================================================
# 出力
# =============================================================================

generate_netlist(file_='outputs/iot-device.net')

# BOM生成
import csv
with open('outputs/iot-device-bom.csv', 'w', newline='') as f:
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
print("  outputs/iot-device.net")
print("  outputs/iot-device-bom.csv")
