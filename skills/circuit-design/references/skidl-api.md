# SKiDL API リファレンス

## 概要

SKiDLは、Pythonで回路設計を行うためのライブラリです。
KiCadのシンボルライブラリを使用し、ネットリストを生成します。

---

## 1. 基本構造

### インポート

```python
from skidl import *

# または特定の機能のみ
from skidl import Part, Net, ERC, generate_netlist
```

### 基本的な回路定義

```python
from skidl import *

# ネット定義
vcc = Net('VCC')
gnd = Net('GND')

# 部品定義
r1 = Part("Device", 'R', value='10K')
c1 = Part("Device", 'C', value='100n')

# 接続
vcc & r1 & c1 & gnd

# ERC（電気的ルールチェック）
ERC()

# ネットリスト生成
generate_netlist()
```

---

## 2. 部品（Part）

### 部品の作成

```python
# 基本形式
part = Part(library, device, value=value, footprint=footprint)

# 例
r = Part("Device", 'R', value='10K')
c = Part("Device", 'C', value='100n')
led = Part("Device", 'LED', value='RED')
```

### よく使うライブラリと部品

| ライブラリ | 部品名 | 説明 |
|-----------|--------|------|
| Device | R | 抵抗 |
| Device | C | コンデンサ |
| Device | L | インダクタ |
| Device | LED | LED |
| Device | D | ダイオード |
| Device | D_Zener | ツェナーダイオード |
| Device | Q_NPN_BCE | NPNトランジスタ |
| Device | Q_PNP_BCE | PNPトランジスタ |
| Connector_Generic | Conn_01x02 | 2ピンコネクタ |
| Connector_Generic | Conn_01x04 | 4ピンコネクタ |

### ピンへのアクセス

```python
r = Part("Device", 'R', value='10K')

# ピン番号でアクセス
r[1]  # ピン1
r[2]  # ピン2

# ピン名でアクセス（部品による）
ic = Part("Amplifier_Operational", 'LM358')
ic['IN+']   # 非反転入力
ic['IN-']   # 反転入力
ic['OUT']   # 出力
ic['V+']    # 正電源
ic['V-']    # 負電源
```

### 部品の複製

```python
# 同じ部品を複数作成
r1, r2, r3 = Part("Device", 'R', value='10K', dest=TEMPLATE) * 3

# リストとして取得
resistors = Part("Device", 'R', value='10K', dest=TEMPLATE) * 10
for r in resistors:
    vcc & r & gnd
```

---

## 3. ネット（Net）

### ネットの作成

```python
# 名前付きネット
vcc = Net('VCC')
gnd = Net('GND')
signal = Net('SIG1')

# 自動命名
net1 = Net()  # N$1, N$2, ... と命名される
```

### 電源ネット

```python
# 電源属性を設定
vcc = Net('VCC')
vcc.drive = POWER  # 電源ドライブ

gnd = Net('GND')
gnd.drive = POWER
```

---

## 4. 接続

### 演算子による接続

```python
# & 演算子（直列接続）
vcc & r1 & r2 & gnd

# | 演算子（並列接続）
vcc & (r1 | r2) & gnd  # r1とr2が並列

# += による接続
net1 += r1[1], r2[1]  # net1にr1[1]とr2[1]を接続
```

### 明示的な接続

```python
# connect()メソッド
r1[1].connect(vcc)
r1[2].connect(r2[1])

# ネットへの接続
vcc += r1[1]
gnd += r2[2]
```

### 複雑な接続例

```python
# 分圧回路
vin, vout, gnd = Net('VIN'), Net('VOUT'), Net('GND')
r1 = Part("Device", 'R', value='10K')
r2 = Part("Device", 'R', value='10K')

vin & r1 & vout & r2 & gnd

# 等価な記述
r1[1] += vin
r1[2] += vout
r2[1] += vout
r2[2] += gnd
```

---

## 5. オペアンプ回路

### 基本的なオペアンプ

```python
from skidl import *

# LM358（2回路入り）
opamp = Part("Amplifier_Operational", 'LM358', footprint='Package_DIP:DIP-8_W7.62mm')

# 電源接続
vcc, gnd = Net('VCC'), Net('GND')
vcc += opamp['V+']
gnd += opamp['V-']

# 1回路目を使用
# opamp.unit['A'] で1つ目のユニットにアクセス
vin = Net('VIN')
vout = Net('VOUT')

vin += opamp['1+']   # 非反転入力
opamp['1-'] += opamp['1OUT']  # 負帰還（ボルテージフォロワ）
vout += opamp['1OUT']
```

### 反転増幅回路

```python
from skidl import *

opamp = Part("Amplifier_Operational", 'TL072', footprint='Package_DIP:DIP-8_W7.62mm')
r_in = Part("Device", 'R', value='10K')
r_fb = Part("Device", 'R', value='100K')  # ゲイン=-10

vin, vout, gnd = Net('VIN'), Net('VOUT'), Net('GND')
vcc, vee = Net('VCC'), Net('VEE')

# 電源
vcc += opamp['V+']
vee += opamp['V-']

# 反転増幅
vin & r_in & opamp['1-'] & r_fb & vout
gnd += opamp['1+']
vout += opamp['1OUT']

ERC()
```

---

## 6. デジタルIC

### ロジックIC

```python
from skidl import *

# 74HC04（6回路インバータ）
inv = Part("74xx", '74HC04', footprint='Package_DIP:DIP-14_W7.62mm')

vcc, gnd = Net('VCC'), Net('GND')
vcc += inv['VCC']
gnd += inv['GND']

# 1回路目を使用
input_sig = Net('IN')
output_sig = Net('OUT')
input_sig += inv['1A']
output_sig += inv['1Y']
```

### マイコン

```python
from skidl import *

# ATmega328P
mcu = Part("MCU_Microchip_ATmega", 'ATmega328P-PU',
           footprint='Package_DIP:DIP-28_W7.62mm')

vcc, gnd = Net('VCC'), Net('GND')

# 電源接続
vcc += mcu['VCC'], mcu['AVCC']
gnd += mcu['GND']

# 発振子
xtal = Part("Device", 'Crystal', value='16MHz')
c_xtal1 = Part("Device", 'C', value='22p')
c_xtal2 = Part("Device", 'C', value='22p')

mcu['XTAL1'] & xtal & mcu['XTAL2']
mcu['XTAL1'] & c_xtal1 & gnd
mcu['XTAL2'] & c_xtal2 & gnd
```

---

## 7. ERC（電気的ルールチェック）

### 基本的なERC

```python
ERC()  # エラーがあれば例外を発生
```

### ERCルールの設定

```python
# 未接続ピンを許可
set_default_tool(KICAD)
set_default_tool_settings({'ignore_nc': True})

# 特定のピンを未接続可能に
part['NC'].do_erc = False
```

---

## 8. ネットリスト生成

### KiCad形式

```python
generate_netlist(file_='output.net')
```

### SPICE形式

```python
generate_netlist(file_='output.cir', tool=SPICE)
```

---

## 9. BOM生成

```python
from skidl import generate_csv

# BOMをCSV出力
generate_csv(file_='bom.csv')
```

---

## 10. サブ回路

### サブ回路の定義

```python
from skidl import *

@subcircuit
def voltage_divider(vin, vout, gnd, r1_val='10K', r2_val='10K'):
    """分圧回路サブサーキット"""
    r1 = Part("Device", 'R', value=r1_val)
    r2 = Part("Device", 'R', value=r2_val)
    vin & r1 & vout & r2 & gnd

# 使用
vin = Net('VIN')
vout = Net('VOUT')
gnd = Net('GND')

voltage_divider(vin, vout, gnd, r1_val='20K', r2_val='10K')
```

### 階層設計

```python
from skidl import *

@subcircuit
def rc_filter(input_net, output_net, gnd, r_val, c_val):
    r = Part("Device", 'R', value=r_val)
    c = Part("Device", 'C', value=c_val)
    input_net & r & output_net & c & gnd

# 複数のフィルタを使用
sig1, sig2, sig3 = Net('SIG1'), Net('SIG2'), Net('SIG3')
gnd = Net('GND')

rc_filter(sig1, sig2, gnd, '1K', '100n')
rc_filter(sig2, sig3, gnd, '1K', '100n')
```

---

## 11. フットプリント

### フットプリントの指定

```python
r = Part("Device", 'R', value='10K', footprint='Resistor_SMD:R_0603_1608Metric')
c = Part("Device", 'C', value='100n', footprint='Capacitor_SMD:C_0603_1608Metric')
```

### よく使うフットプリント

| 部品 | フットプリント |
|------|---------------|
| 抵抗(0603) | Resistor_SMD:R_0603_1608Metric |
| 抵抗(0805) | Resistor_SMD:R_0805_2012Metric |
| コンデンサ(0603) | Capacitor_SMD:C_0603_1608Metric |
| DIP-8 | Package_DIP:DIP-8_W7.62mm |
| SOIC-8 | Package_SO:SOIC-8_3.9x4.9mm_P1.27mm |

---

## 12. 完全な例

### LED駆動回路

```python
from skidl import *

# ネット定義
vcc = Net('VCC')
gnd = Net('GND')

# 部品
r_limit = Part("Device", 'R', value='150',
               footprint='Resistor_SMD:R_0603_1608Metric')
led = Part("Device", 'LED', value='RED',
           footprint='LED_SMD:LED_0603_1608Metric')

# 接続: VCC -> R -> LED -> GND
vcc & r_limit & led & gnd

# チェック
ERC()

# 出力
generate_netlist(file_='led_driver.net')
```
