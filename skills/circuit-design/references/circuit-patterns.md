# 回路パターン集

## 概要

よく使う回路パターンのSKiDL実装例です。

---

## 1. 電源回路

### 3端子レギュレータ（7805）

```python
from skidl import *

vcc_in = Net('VCC_IN')    # 入力（7〜25V）
vcc_out = Net('VCC_5V')   # 出力（5V）
gnd = Net('GND')

# 7805
reg = Part("Regulator_Linear", 'L7805', footprint='Package_TO_SOT_THT:TO-220-3_Vertical')

# 入力コンデンサ
c_in = Part("Device", 'CP', value='100u', footprint='Capacitor_THT:CP_Radial_D8.0mm_P3.50mm')

# 出力コンデンサ
c_out = Part("Device", 'C', value='100n', footprint='Capacitor_SMD:C_0603_1608Metric')

# 接続
vcc_in & c_in['+'] & reg['VI']
c_in['-'] += gnd
reg['GND'] += gnd
reg['VO'] & c_out & gnd
vcc_out += reg['VO']

ERC()
```

### LDO（AMS1117-3.3）

```python
from skidl import *

vcc_in = Net('VCC_IN')    # 入力（4.5〜12V）
vcc_out = Net('VCC_3V3')  # 出力（3.3V）
gnd = Net('GND')

# AMS1117-3.3
ldo = Part("Regulator_Linear", 'AMS1117-3.3', footprint='Package_TO_SOT_SMD:SOT-223-3_TabPin2')

# コンデンサ
c_in = Part("Device", 'C', value='10u', footprint='Capacitor_SMD:C_0805_2012Metric')
c_out = Part("Device", 'C', value='10u', footprint='Capacitor_SMD:C_0805_2012Metric')

# 接続
vcc_in += ldo['VI'], c_in[1]
c_in[2] += gnd
ldo['GND'] += gnd
ldo['VO'] += vcc_out, c_out[1]
c_out[2] += gnd

ERC()
```

---

## 2. LED駆動

### 単純LED駆動

```python
from skidl import *

def led_driver(vcc_net, gnd_net, vcc_voltage=5.0, led_vf=2.0, led_current=0.020):
    """
    LED駆動回路
    R = (Vcc - Vf) / If
    """
    r_value = (vcc_voltage - led_vf) / led_current
    # E24系列に丸める
    e24_values = [10, 11, 12, 13, 15, 16, 18, 20, 22, 24, 27, 30,
                  33, 36, 39, 43, 47, 51, 56, 62, 68, 75, 82, 91]

    # 近い値を選択
    magnitude = 10 ** int(len(str(int(r_value))) - 2)
    normalized = r_value / magnitude
    closest = min(e24_values, key=lambda x: abs(x - normalized))
    r_final = closest * magnitude

    r_limit = Part("Device", 'R', value=f'{int(r_final)}')
    led = Part("Device", 'LED')

    vcc_net & r_limit & led & gnd_net

    return r_limit, led

# 使用例
vcc = Net('VCC')
gnd = Net('GND')
r, led = led_driver(vcc, gnd, vcc_voltage=5.0, led_vf=2.0, led_current=0.020)
# R = (5-2)/0.02 = 150Ω
```

### 定電流LED駆動（トランジスタ）

```python
from skidl import *

vcc = Net('VCC')
gnd = Net('GND')
ctrl = Net('CTRL')  # 制御信号

# NPNトランジスタ
q = Part("Device", 'Q_NPN_BCE', value='2SC1815')

# 抵抗
r_base = Part("Device", 'R', value='1K')   # ベース電流制限
r_sense = Part("Device", 'R', value='10')  # 電流センス

# LED
led = Part("Device", 'LED')

# 接続
ctrl & r_base & q['B']
vcc & led & q['C']
q['E'] & r_sense & gnd

ERC()
```

---

## 3. 信号処理

### 分圧回路

```python
from skidl import *

def voltage_divider(vin_net, vout_net, gnd_net, vin_voltage, vout_voltage, current=0.001):
    """
    分圧回路
    Vout = Vin × R2 / (R1 + R2)
    """
    r_total = vin_voltage / current
    r2 = r_total * (vout_voltage / vin_voltage)
    r1 = r_total - r2

    r1_part = Part("Device", 'R', value=f'{int(r1)}')
    r2_part = Part("Device", 'R', value=f'{int(r2)}')

    vin_net & r1_part & vout_net & r2_part & gnd_net

    return r1_part, r2_part

# 使用例：5V → 3.3V
vin = Net('VIN')
vout = Net('VOUT')
gnd = Net('GND')
r1, r2 = voltage_divider(vin, vout, gnd, 5.0, 3.3, current=0.001)
```

### RCローパスフィルタ

```python
from skidl import *

def rc_lowpass(input_net, output_net, gnd_net, cutoff_freq, r_value=10000):
    """
    1次RCローパスフィルタ
    fc = 1 / (2π × R × C)
    """
    import math
    c_value = 1 / (2 * math.pi * r_value * cutoff_freq)

    # pF/nF/uF表記に変換
    if c_value >= 1e-6:
        c_str = f'{c_value*1e6:.1f}u'
    elif c_value >= 1e-9:
        c_str = f'{c_value*1e9:.0f}n'
    else:
        c_str = f'{c_value*1e12:.0f}p'

    r = Part("Device", 'R', value=f'{int(r_value/1000)}K')
    c = Part("Device", 'C', value=c_str)

    input_net & r & output_net & c & gnd_net

    return r, c

# 使用例：1kHzカットオフ
sig_in = Net('SIG_IN')
sig_out = Net('SIG_OUT')
gnd = Net('GND')
r, c = rc_lowpass(sig_in, sig_out, gnd, cutoff_freq=1000)
```

### RCハイパスフィルタ

```python
from skidl import *

def rc_highpass(input_net, output_net, gnd_net, cutoff_freq, c_value=100e-9):
    """
    1次RCハイパスフィルタ
    fc = 1 / (2π × R × C)
    """
    import math
    r_value = 1 / (2 * math.pi * c_value * cutoff_freq)

    c = Part("Device", 'C', value='100n')
    r = Part("Device", 'R', value=f'{int(r_value/1000)}K')

    input_net & c & output_net & r & gnd_net

    return c, r

# 使用例：100Hzカットオフ（DCカット）
sig_in = Net('SIG_IN')
sig_out = Net('SIG_OUT')
gnd = Net('GND')
c, r = rc_highpass(sig_in, sig_out, gnd, cutoff_freq=100)
```

---

## 4. オペアンプ回路

### ボルテージフォロワ（バッファ）

```python
from skidl import *

vcc = Net('VCC')
vee = Net('VEE')  # または GND（単電源の場合）
gnd = Net('GND')
vin = Net('VIN')
vout = Net('VOUT')

opamp = Part("Amplifier_Operational", 'TL072')

# 電源
vcc += opamp['V+']
vee += opamp['V-']

# ボルテージフォロワ（ゲイン=1）
vin += opamp['1+']
opamp['1-'] += opamp['1OUT']  # 100%負帰還
vout += opamp['1OUT']

ERC()
```

### 非反転増幅回路

```python
from skidl import *

def non_inverting_amp(vin_net, vout_net, vcc_net, vee_net, gain):
    """
    非反転増幅回路
    Gain = 1 + Rf/Ri
    Rf = (Gain - 1) × Ri
    """
    ri_value = 10000  # 10K固定
    rf_value = (gain - 1) * ri_value

    opamp = Part("Amplifier_Operational", 'TL072')
    ri = Part("Device", 'R', value=f'{int(ri_value/1000)}K')
    rf = Part("Device", 'R', value=f'{int(rf_value/1000)}K')

    # 電源
    vcc_net += opamp['V+']
    vee_net += opamp['V-']

    # 非反転増幅
    vin_net += opamp['1+']

    # 帰還回路
    gnd = Net('GND')
    gnd & ri & opamp['1-'] & rf & opamp['1OUT']
    vout_net += opamp['1OUT']

    return opamp, ri, rf

# 使用例：ゲイン10倍
vin = Net('VIN')
vout = Net('VOUT')
vcc = Net('VCC')
vee = Net('VEE')
op, ri, rf = non_inverting_amp(vin, vout, vcc, vee, gain=10)
```

### 反転増幅回路

```python
from skidl import *

def inverting_amp(vin_net, vout_net, vcc_net, vee_net, gnd_net, gain):
    """
    反転増幅回路
    Gain = -Rf/Ri
    """
    ri_value = 10000
    rf_value = abs(gain) * ri_value

    opamp = Part("Amplifier_Operational", 'TL072')
    ri = Part("Device", 'R', value=f'{int(ri_value/1000)}K')
    rf = Part("Device", 'R', value=f'{int(rf_value/1000)}K')

    # 電源
    vcc_net += opamp['V+']
    vee_net += opamp['V-']

    # 反転増幅
    gnd_net += opamp['1+']
    vin_net & ri & opamp['1-'] & rf & vout_net
    vout_net += opamp['1OUT']

    return opamp, ri, rf
```

---

## 5. センサー回路

### 温度センサー（サーミスタ）

```python
from skidl import *

vcc = Net('VCC')
gnd = Net('GND')
adc = Net('ADC')  # ADC入力へ

# サーミスタ + 分圧
thermistor = Part("Device", 'Thermistor_NTC', value='10K')
r_ref = Part("Device", 'R', value='10K')

# フィルタ用コンデンサ
c_filter = Part("Device", 'C', value='100n')

# 分圧回路
vcc & r_ref & adc & thermistor & gnd

# ADCフィルタ
adc & c_filter & gnd

ERC()
```

### 光センサー（CdS）

```python
from skidl import *

vcc = Net('VCC')
gnd = Net('GND')
adc = Net('ADC')

# CdS + 分圧抵抗
cds = Part("Device", 'R_PHOTO', value='CdS')
r_ref = Part("Device", 'R', value='10K')

# 明るい時にADC値が高くなる接続
vcc & r_ref & adc & cds & gnd

ERC()
```

---

## 6. インターフェース回路

### I2Cプルアップ

```python
from skidl import *

vcc = Net('VCC')
sda = Net('SDA')
scl = Net('SCL')

# プルアップ抵抗（3.3V系では2.2K〜4.7K）
r_sda = Part("Device", 'R', value='4K7')
r_scl = Part("Device", 'R', value='4K7')

vcc & r_sda & sda
vcc & r_scl & scl

ERC()
```

### UARTレベル変換

```python
from skidl import *

# 5V側
vcc_5v = Net('VCC_5V')
tx_5v = Net('TX_5V')
rx_5v = Net('RX_5V')

# 3.3V側
vcc_3v3 = Net('VCC_3V3')
tx_3v3 = Net('TX_3V3')
rx_3v3 = Net('RX_3V3')

gnd = Net('GND')

# 分圧でTX 5V→3.3V
r1 = Part("Device", 'R', value='1K')
r2 = Part("Device", 'R', value='2K')
tx_5v & r1 & rx_3v3 & r2 & gnd

# MOSFETでRX 3.3V→5V（双方向可）
q = Part("Device", 'Q_NMOS_GSD', value='2N7000')
r_5v = Part("Device", 'R', value='10K')
r_3v3 = Part("Device", 'R', value='10K')

# MOSFET接続
vcc_3v3 & r_3v3 & tx_3v3
tx_3v3 += q['G']
q['S'] += gnd
vcc_5v & r_5v & rx_5v
rx_5v += q['D']

ERC()
```

---

## 7. 保護回路

### 逆接続保護（ダイオード）

```python
from skidl import *

vin = Net('VIN')
vcc = Net('VCC')
gnd = Net('GND')

# ショットキーダイオード
d_protect = Part("Device", 'D_Schottky', value='SS14')

vin & d_protect & vcc
# Vf約0.4Vの電圧降下あり
```

### ESD保護

```python
from skidl import *

signal = Net('SIGNAL')
gnd = Net('GND')

# TVSダイオード
tvs = Part("Device", 'D_TVS', value='SMBJ5.0A')

signal += tvs[1]
gnd += tvs[2]
```
