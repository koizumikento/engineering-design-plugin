# SKiDL 2.2 / KiCad 9 実装リファレンス

## 目次

Version / Circuit ownership / Parts / Nets / Hierarchy / ERC / Outputs / Official sources

## Version and tool

現在のlockはSKiDL 2.2.1で、公式サイトは2.2.3系の資料を公開している。APIを使う前に実行版を確認する。

```bash
uv run python -c "import skidl; print(skidl.__version__)"
```

SKiDL 2.2の `KICAD` aliasは現在KiCad 9を指すが、成果物の互換性を固定したいコードでは `KICAD9` を明示する。

## Circuit ownership

単純なリポジトリスクリプトはdefault circuitを使える。再利用モジュール、複数回実行、testでは明示的 `Circuit` を優先する。

```python
from skidl import Circuit, Net, Part, KICAD9

circuit = Circuit(name="sensor_frontend")
with circuit:
    vin = Net("VIN")
    vout = Net("VOUT")
    gnd = Net("GND")
    r1 = Part("Device", "R", value="10k", tag="r_upper", tool=KICAD9)
    r2 = Part("Device", "R", value="10k", tag="r_lower", tool=KICAD9)
    vin & r1 & vout & r2 & gnd

circuit.ERC()
```

repository runnerはdefault circuitを読み取るため、明示的Circuitへ移行する場合はrunnerとの統合も同時に更新する。

## Parts

部品ごとに次を確認する。

- symbol library/nameとKiCad version
- reference prefixとstable `tag`
- pin number/name/electrical type
- multi-unit mappingとpower unit
- value、manufacturer、MPN
- footprintとpin-1 orientation
- DNP/variant属性
- SPICE model、subcircuit pin order、model revision

```python
from skidl import Part, KICAD9

r = Part(
    "Device",
    "R",
    value="10k",
    footprint="Resistor_SMD:R_0603_1608Metric",
    tag="input_bias",
    tool=KICAD9,
)
```

symbol名が存在するだけでは採用部品とのpinout一致を保証しない。正確なMPNのdatasheetとfootprint drawingで照合する。

## Nets and interfaces

外部境界はラベルだけでなくconnector/test point/interface partとして表現する。power、ground、analog、digital、high-current、sensitive netsを名前で分ける。

```python
from skidl import Net, Part, KICAD9

vin = Net("VIN")
gnd = Net("GND")
j1 = Part("Connector_Generic", "Conn_01x02", tag="power_in", tool=KICAD9)
vin += j1[1]
gnd += j1[2]
```

ERC抑制は回路意図を示す最小範囲に限定し、理由をコメントまたはdesign summaryへ残す。実電源源が外部にある場合は、connectorとpower flag/drive設定のどちらがhandoffで誤読されにくいかを選ぶ。

## Hierarchy and reuse

反復回路は `@subcircuit` または関数へ分け、interface netsとparameterを引数にする。サブ回路内部で同名global netを暗黙作成しない。複数instanceでtag/referenceが衝突しないことを確認する。

## ERC

SKiDL ERCはpin electrical typeや未接続などの論理的問題を検出するが、次を証明しない。

- ratings、absolute maximum、thermal、stability
- symbol/footprint/datasheet pinout一致
- PCB layout、return path、clearance/creepage
- EMC/ESD、安全規格、部品寿命

ERC warningを消すためだけにpin typeを弱めない。意図を修正するか、根拠付きの局所例外にする。

## Outputs

```python
circuit.ERC()
circuit.generate_netlist(file_="design.net", tool=KICAD9)
circuit.generate_schematic(filepath="outputs/kicad", top_name="design", tool=KICAD9)
```

SKiDL公式docsでは `generate_schematic()` がKiCad `.kicad_sch` を生成する。配置・routingは自動生成なので、開けること、ERC、可読性、multi-unit/power、external I/Oを別途確認する。

このリポジトリの標準summary/BOMには次を使う。

```bash
uv run python skills/circuit-design/scripts/skidl_runner.py input.py -o outputs/
```

legacy netlistは下流が要求する場合だけ `--netlist` で追加する。

## Official sources

- [SKiDL documentation](https://devbisme.github.io/skidl/)
- [SKiDL Circuit API](https://devbisme.github.io/skidl/api/html/rst_output/skidl.circuit.html)
- [KiCad 9 documentation](https://docs.kicad.org/9.0/en/)
