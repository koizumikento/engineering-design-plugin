# SPICEシミュレーションガイド

## 概要

PySpiceを使用した回路シミュレーションのガイドです。
SKiDLで設計した回路をSPICEでシミュレーションできます。

---

## 1. 基本構造

### PySpiceのインポート

```python
from PySpice.Spice.NgSpice.Shared import NgSpiceShared
from PySpice.Probe.Plot import plot
import PySpice.Logging.Logging as Logging

# ログ設定
logger = Logging.setup_logging()

# シミュレータ
from PySpice.Spice.Parser import SpiceParser
from PySpice.Unit import *
```

### シンプルな回路定義

```python
from PySpice.Spice.Library import SpiceLibrary
from PySpice.Spice.Netlist import Circuit

# 回路作成
circuit = Circuit('Simple RC Circuit')

# 電源（DC 5V）
circuit.V('input', 'vin', circuit.gnd, 5@u_V)

# 抵抗
circuit.R('1', 'vin', 'vout', 1@u_kOhm)

# コンデンサ
circuit.C('1', 'vout', circuit.gnd, 100@u_nF)
```

---

## 2. 部品の定義

### 受動部品

```python
# 抵抗
circuit.R('name', 'node1', 'node2', value@u_Ohm)
circuit.R('1', 'in', 'out', 10@u_kOhm)

# コンデンサ
circuit.C('name', 'node1', 'node2', value@u_F)
circuit.C('1', 'out', circuit.gnd, 100@u_nF)

# インダクタ
circuit.L('name', 'node1', 'node2', value@u_H)
circuit.L('1', 'in', 'out', 1@u_mH)
```

### 電源

```python
# DC電圧源
circuit.V('dc', 'vcc', circuit.gnd, 5@u_V)

# AC電圧源
circuit.SinusoidalVoltageSource('ac', 'vin', circuit.gnd,
    amplitude=1@u_V, frequency=1@u_kHz)

# パルス電圧源
circuit.PulseVoltageSource('pulse', 'vin', circuit.gnd,
    initial_value=0@u_V, pulsed_value=5@u_V,
    delay_time=0@u_us, rise_time=1@u_us, fall_time=1@u_us,
    pulse_width=500@u_us, period=1@u_ms)

# PWL（区分線形）電圧源
circuit.PieceWiseLinearVoltageSource('pwl', 'vin', circuit.gnd,
    values=[(0, 0), (1@u_ms, 5), (2@u_ms, 0)])
```

### 半導体

```python
# ダイオード
circuit.D('1', 'anode', 'cathode', model='1N4148')

# ダイオードモデル定義
circuit.model('1N4148', 'D', Is=2.52e-9, Rs=0.568, N=1.752)

# NPNトランジスタ
circuit.BJT('1', 'collector', 'base', 'emitter', model='2N2222')
circuit.model('2N2222', 'NPN', Is=14.34e-15, Bf=255.9)

# MOSFET
circuit.MOSFET('1', 'drain', 'gate', 'source', circuit.gnd, model='IRF540')
```

### オペアンプ

```python
# 理想オペアンプ（VCVSで代用）
# E(name, n+, n-, control+, control-, gain)
circuit.VoltageControlledVoltageSource('opamp', 'out', circuit.gnd,
    'in_plus', 'in_minus', voltage_gain=1e6)

# サブサーキットを使用
circuit.include('/path/to/opamp.lib')
circuit.X('1', 'TL072', 'in_plus', 'in_minus', 'vcc', 'vee', 'out')
```

---

## 3. 解析の種類

### DC動作点解析

```python
from PySpice.Spice.Netlist import Circuit

circuit = Circuit('DC Analysis')
circuit.V('input', 'vin', circuit.gnd, 5@u_V)
circuit.R('1', 'vin', 'vout', 10@u_kOhm)
circuit.R('2', 'vout', circuit.gnd, 10@u_kOhm)

# シミュレータ作成
simulator = circuit.simulator(temperature=25, nominal_temperature=25)

# 動作点解析
analysis = simulator.operating_point()

# 結果取得
print(f"Vout = {float(analysis['vout']):.3f} V")
```

### DCスイープ

```python
# Vinputを0Vから10Vまでスイープ
analysis = simulator.dc(Vinput=slice(0, 10, 0.1))

# 結果プロット
import matplotlib.pyplot as plt
plt.plot(analysis['vinput'], analysis['vout'])
plt.xlabel('Vin (V)')
plt.ylabel('Vout (V)')
plt.grid(True)
plt.savefig('dc_sweep.png')
```

### AC解析（周波数特性）

```python
from PySpice.Unit import *

circuit = Circuit('AC Analysis')

# AC電圧源
circuit.SinusoidalVoltageSource('input', 'vin', circuit.gnd, amplitude=1@u_V)

# RCフィルタ
circuit.R('1', 'vin', 'vout', 1@u_kOhm)
circuit.C('1', 'vout', circuit.gnd, 100@u_nF)

simulator = circuit.simulator()

# AC解析：10Hz〜1MHz、decade当たり10ポイント
analysis = simulator.ac(start_frequency=10@u_Hz, stop_frequency=1@u_MHz,
                        number_of_points=10, variation='dec')

# ボード線図
import numpy as np
import matplotlib.pyplot as plt

frequency = np.array(analysis.frequency)
vout = np.array(analysis['vout'])

# ゲイン（dB）
gain_db = 20 * np.log10(np.abs(vout))

# 位相（度）
phase_deg = np.angle(vout, deg=True)

fig, (ax1, ax2) = plt.subplots(2, 1, sharex=True, figsize=(10, 8))

ax1.semilogx(frequency, gain_db)
ax1.set_ylabel('Gain (dB)')
ax1.grid(True)

ax2.semilogx(frequency, phase_deg)
ax2.set_xlabel('Frequency (Hz)')
ax2.set_ylabel('Phase (deg)')
ax2.grid(True)

plt.savefig('bode_plot.png')
```

### 過渡解析

```python
from PySpice.Unit import *

circuit = Circuit('Transient Analysis')

# パルス入力
circuit.PulseVoltageSource('input', 'vin', circuit.gnd,
    initial_value=0@u_V, pulsed_value=5@u_V,
    rise_time=1@u_us, fall_time=1@u_us,
    pulse_width=100@u_us, period=200@u_us)

# RCフィルタ
circuit.R('1', 'vin', 'vout', 1@u_kOhm)
circuit.C('1', 'vout', circuit.gnd, 100@u_nF)

simulator = circuit.simulator()

# 過渡解析：0〜500us、ステップ1us
analysis = simulator.transient(step_time=1@u_us, end_time=500@u_us)

# プロット
import matplotlib.pyplot as plt

plt.figure(figsize=(10, 6))
plt.plot(analysis.time * 1e6, analysis['vin'], label='Vin')
plt.plot(analysis.time * 1e6, analysis['vout'], label='Vout')
plt.xlabel('Time (us)')
plt.ylabel('Voltage (V)')
plt.legend()
plt.grid(True)
plt.savefig('transient.png')
```

---

## 4. 実践的な例

### LED駆動回路のシミュレーション

```python
from PySpice.Spice.Netlist import Circuit
from PySpice.Unit import *

circuit = Circuit('LED Driver')

# 電源
circuit.V('cc', 'vcc', circuit.gnd, 5@u_V)

# 電流制限抵抗
circuit.R('limit', 'vcc', 'led_anode', 150@u_Ohm)

# LED（ダイオードモデル）
circuit.D('led', 'led_anode', circuit.gnd, model='LED_RED')
circuit.model('LED_RED', 'D', Is=1e-20, N=1.5, Rs=2)

# シミュレーション
simulator = circuit.simulator()
analysis = simulator.operating_point()

# LED電流計算
i_led = (float(analysis['vcc']) - float(analysis['led_anode'])) / 150
print(f"LED Current: {i_led*1000:.1f} mA")
print(f"LED Voltage: {float(analysis['led_anode']):.2f} V")
```

### オペアンプ増幅回路

```python
from PySpice.Spice.Netlist import Circuit
from PySpice.Unit import *

circuit = Circuit('OpAmp Amplifier')

# 電源
circuit.V('cc', 'vcc', circuit.gnd, 12@u_V)
circuit.V('ee', 'vee', circuit.gnd, -12@u_V)

# 信号源
circuit.SinusoidalVoltageSource('in', 'vin', circuit.gnd,
    amplitude=100@u_mV, frequency=1@u_kHz)

# オペアンプ（理想モデル）
# 非反転増幅：Gain = 1 + Rf/Ri = 1 + 90k/10k = 10
circuit.R('i', 'inv_in', circuit.gnd, 10@u_kOhm)
circuit.R('f', 'inv_in', 'vout', 90@u_kOhm)

# 理想オペアンプ
circuit.VoltageControlledVoltageSource('opamp', 'vout', circuit.gnd,
    'vin', 'inv_in', voltage_gain=1e6)

# シミュレーション
simulator = circuit.simulator()
analysis = simulator.transient(step_time=1@u_us, end_time=5@u_ms)

# プロット
import matplotlib.pyplot as plt

plt.figure(figsize=(10, 6))
plt.plot(analysis.time * 1e3, analysis['vin'] * 10, label='Vin x10')
plt.plot(analysis.time * 1e3, analysis['vout'], label='Vout')
plt.xlabel('Time (ms)')
plt.ylabel('Voltage (V)')
plt.legend()
plt.grid(True)
plt.title('Non-inverting Amplifier (Gain=10)')
plt.savefig('opamp_amp.png')
```

---

## 5. SKiDLとの連携

### SKiDL→SPICE変換

```python
from skidl import *

# SKiDLで回路設計
vcc = Net('VCC')
gnd = Net('GND')
gnd.drive = POWER

r1 = Part("Device", 'R', value='10K')
r2 = Part("Device", 'R', value='10K')
vcc & r1 & Net('VOUT') & r2 & gnd

# SPICEネットリスト生成
generate_netlist(file_='circuit.cir', tool=SPICE)

# PySpiceで読み込み
from PySpice.Spice.Parser import SpiceParser

parser = SpiceParser(path='circuit.cir')
circuit = parser.build_circuit()

# シミュレーション実行
simulator = circuit.simulator()
analysis = simulator.operating_point()
```

---

## 6. トラブルシューティング

### よくあるエラー

| エラー | 原因 | 対処 |
|--------|------|------|
| `no DC path to ground` | グラウンドへの経路がない | GNDノードの確認 |
| `singular matrix` | 回路が不定 | 浮いているノードを確認 |
| `timestep too small` | 収束しない | ステップを大きく |
| `node not found` | ノード名エラー | スペルチェック |

### デバッグのコツ

```python
# 回路のネットリスト確認
print(circuit)

# ノード一覧
print(circuit.node_names)

# ngspiceのログ
simulator = circuit.simulator()
simulator.options(filetype='ascii')  # 出力形式
```
