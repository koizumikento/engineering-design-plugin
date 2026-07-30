# SPICE simulation guide

## 目次

Purpose / Model provenance / Analysis / Corners / Measurements / Runner / Convergence / Validation / Sources

## Purpose

simulationは要求に結び付く問いへ答えるために行う。波形を生成すること自体を完了条件にしない。

```markdown
| Requirement | Scenario | Analysis | Measurement | Acceptance |
|---|---|---|---|---|
| CIR-PERF-001 | Vin min/nom/max, load max | OP/DC | Vout, device power | specified limits |
```

## Model provenance

各model/subcircuitについて記録する。

- manufacturer/source URL or controlled path
- model name、revision/date、license
- mapped MPN/package
- subcircuit pin order versus symbol
- supported simulator and syntax
- modeled effects and known omissions
- temperature/process applicability

generic/ideal modelはconcept検証に使えるが、採用部品の最悪性能を代表しない。

## Analysis selection

| Analysis | Question | Typical checks |
|---|---|---|
| OP | bias pointは成立するか | node voltage、branch current、device power |
| DC sweep | input/load variationへの静的応答 | transfer、headroom、limit |
| AC | linearized small-signal response | gain、phase、bandwidth、impedance |
| Transient | startup、pulse、settling | overshoot、rise/fall、settling、energy |
| Noise | specified bandのnoise | input/output referred noise |
| Temperature/parameter sweep | corner sensitivity | min/max margin |

AC analysisはoperating point周りのlinearized analysisである。large-signal slew、clipping、startupはtransientで確認する。

## Corners and tolerances

- supply min/nom/max
- source/load min/max
- component tolerance and bias derating
- temperature
- semiconductor model/process corner when provided
- startup initial conditions
- plausible fault and unpowered states

nominal 1 caseだけのpassをworst-case passと表現しない。

## Measurements

画像だけでなくCSVまたは数値summaryを保存する。

- extrema and margin to limits
- crossing frequency、gain/phase at specified points
- settling time with defined band
- RMS/integrated noise over defined bandwidth
- peak/RMS current and power
- simulation command、step、tolerances、model set

## Repository runner

```bash
uv run python skills/circuit-design/scripts/pyspice_sim.py input.py -o outputs/ --dc
uv run python skills/circuit-design/scripts/pyspice_sim.py input.py -o outputs/ --ac
uv run python skills/circuit-design/scripts/pyspice_sim.py input.py -o outputs/ --tran
```

runnerが対象script/modelを解釈できるかを先に確認する。unsupported circuitを空またはidealized resultでpassさせない。

projectはPySpice 1.5以上を宣言している。PySpice 1.6 docsのAPIを使う場合はlock更新と回帰確認を行う。

## Convergence

収束エラーは設計不良、浮遊node、model discontinuity、極端な時定数、初期条件、数値設定など複数原因を持つ。

1. netlist、ground、source、pin orderを確認する。
2. OPを単独で解き、浮遊nodeや不定状態を探す。
3. ideal switch/sourceを有限rise time/impedanceへ近づける。
4. modelの推奨optionを確認する。
5. time stepやsolver optionを変更した場合、結果感度を比較して記録する。

`timestep too small` に対して単純にstepを大きくするだけでは、重要transientを失う可能性がある。数値変更で物理結果が変わっていないか確認する。

## Validation

- hand calculation or datasheet curveとのsanity check
- expected limiting case（Rのみ、C open/shortなど）
- model pin mappingのsmall fixture test
- another simulator/measurementとのcross-check for critical claims
- convergence option sensitivity
- hardware test planへのhandoff

## Official sources

- [ngspice User's Manual](https://ngspice.sourceforge.io/docs/ngspice-manual.pdf)
- [ngspice official documentation](https://ngspice.sourceforge.io/docs.html)
- [PySpice 1.6 Simulator API](https://pyspice.fabrice-salvaire.fr/releases/v1.6/api/PySpice/Spice/Simulator.html)
- [SKiDL documentation](https://devbisme.github.io/skidl/)
