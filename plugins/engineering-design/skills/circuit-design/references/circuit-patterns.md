# 回路パターン設計チェック

## 目次

共通レビュー / Divider / LED / RC / Op-amp / Regulator / Digital bus / Protection / SKiDL representation

この文書は特定部品の推奨回路を代替しない。値、pinout、安定条件、保護、layoutは採用MPNの最新版datasheetとapplication noteを優先する。

## 共通レビュー

- operating、startup、shutdown、fault、unpowered states
- min/nom/max source and load conditions
- absolute maximumとrecommended operating conditionsの両方
- tolerance、temperature、aging、bias dependence
- power dissipation、junction temperature、SOA
- source/load impedanceとbandwidth/noise
- external connector、ESD/EFT/surge exposure
- decouplingとreturn path、layout-sensitive loop
- test pointと測定負荷
- exact symbol pinout、footprint、MPN、model provenance

## Divider and bias network

理想無負荷:

```text
Vout = Vin * R2 / (R1 + R2)
Rth = R1 || R2
```

後段負荷、input leakage、ADC sampling capacitor、source impedance、resistor tolerance、self-heating、power-up状態を含める。電力供給やlogic level translationへ分圧器を無条件に使わない。

## LED resistor

```text
R = (Vsupply - Vf - Vswitch) / Iled
P_R = Iled^2 * R
```

Vfの温度/lot範囲、supply範囲、driver saturation、resistor tolerance、LED pulse/continuous ratingを最悪条件で確認する。抵抗値は希望電流より安全側へ丸め、実電流範囲を再計算する。

## RC filters

理想1次:

```text
fc = 1 / (2*pi*R*C)
```

source/load impedanceがRに並列/直列で加わる。capacitor tolerance、DC bias、ESR/ESL、input/output protection、settling timeを確認する。anti-alias filterはsamplingと必要attenuationから設計する。

## Op-amp stage

非反転理想gain:

```text
Av = 1 + Rf/Rg
```

反転理想gain:

```text
Av = -Rf/Rin
```

必ず確認する項目:

- input common-mode range
- output swing versus load
- supply/current and power-on behavior
- gain bandwidth、slew rate、settling
- input bias/offset/noise and resistor noise
- capacitive load stability and phase margin
- common-mode/overvoltage protection
- unused amplifier treatment
- local decoupling and layout guidance

理想VCVS simulationだけで採用op-ampの安定性やrail behaviorを立証しない。

## Linear regulator

- input/output range and dropout across current/temperature
- output capacitor value、ESR、bias derating、placement
- quiescent current and reverse-current paths
- power dissipation: `(Vin - Vout) * Iout`
- thermal resistance、copper area、ambient
- startup、current limit、short circuit、enable
- input transient and reverse polarity

特定regulatorの入出力capacitorや最大入力を一般化しない。

## Digital and open-drain buses

pull-upは固定値から始めず、bus capacitance、required rise time、sink current、voltage、device leakageから範囲を決める。level translation topologyは方向、open-drain/push-pull、power-off behavior、speedを確認する。

## Protection

- threat waveform/standard and coupling point
- maximum normal signal and clamp threshold
- dynamic resistance, pulse energy, capacitance
- series impedance and current path
- return/ground inductance and placement
- downstream device abs max

TVSの型式名だけでESD/surge適合を主張しない。

## SKiDL representation

- external portsをconnector/test pointとして置く
- railsとground domainを命名する
- protection partsをboundary近くのlogical blockにまとめる
- modelにないintentはcomment/design summaryへ残す
- critical valuesにcalculation sourceとrequirement IDを付ける

回路例を追加する場合は、exact part、datasheet revision、operating conditions、calculation、ERC、必要simulation、known limitationsを同じ変更に含める。
