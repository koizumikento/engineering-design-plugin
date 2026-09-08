# KiCad 9/10 schematic workflow

## Source ownership

- SKiDL Python: logical connectivity, hierarchy, parameterization.
- generated `.kicad_sch` / `.kicad_pro`: human review and PCB handoff.
- `.kicad_pcb`: layout/fabrication source when PCB work begins; this skill does not generate or certify layout.

Generated KiCad filesを手編集する場合は、SKiDLへ戻す方法またはKiCadを以後の正本に切り替える決定を記録する。二重編集を放置しない。

## Generation paths

### Native SKiDL

SKiDL 2.3.0の `generate_schematic()` を標準経路とする。repository entrypointは出力を一時ディレクトリに生成し、今回の出力が存在することを確認してから成果物をコピーする。過去のファイルの存在を今回の生成成功と扱わない。

```bash
uv run python skills/circuit-design/scripts/kicad_sch_export.py input.py -o outputs/ --backend native --kicad-version 9
```

KiCad 10へ出力する場合は `--kicad-version 10` と対応するsource/libraryを使う。配置・配線、階層sheet、multi-unit、power、外部I/O、footprintを独立して確認する。

### Repository exporter

`--backend compatibility` はKiCad 9の確認済みtopology向け互換pathである。対象はdivider、RC lowpass、L7805 regulator、TL072 amplifier、comet LED sequencerなど。未対応回路やKiCad 10には使わない。nativeの失敗を自動で隠すfallbackにしない。

```bash
uv run python skills/circuit-design/scripts/kicad_sch_export.py input.py -o outputs/ --backend compatibility --kicad-version 9
```

## Independent KiCad checks

KiCad 9/10 CLIはschematic ERCとBOM exportを直接提供する。使用版を `kicad-cli version` で確認する。

```bash
kicad-cli sch erc \
  --exit-code-violations \
  --format json \
  -o outputs/reports/project-kicad-erc.json \
  outputs/kicad/project/project.kicad_sch

kicad-cli sch export bom \
  -o outputs/reports/project-kicad-bom.csv \
  outputs/kicad/project/project.kicad_sch
```

Windows PowerShellでは行継続を使わず1行で実行してよい。

KiCadの通常のschematic-to-PCB flowはlegacy netlist fileを必要としない。netlist exportは外部toolや明示的検証用途に限定する。

移行の検証では `kicad-cli sch export netlist --format kicadxml` とSKiDLのnetlistを比較し、各netのreference/pin集合が等しいか確認する。自動net名の違いはpin集合で照合する。BOMはreference、value、footprintを比較する。ERCが通るだけでは接続の同一性を証明しない。CLI未導入・未実行は `NOT_EVALUATED` と記録し、parse確認やファイル存在確認と区別する。

## Visual review

- left-to-right signal flow and named interfaces
- rails, grounds, power flags, decoupling
- multi-unit parts and hidden/power units
- unused pins/units and no-connect markers
- connector pin order and polarity
- part value, MPN, footprint, DNP/variant fields
- net labels versus actual connectivity
- overlapping wires, dangling stubs, unreadable auto-placement

KiCadがfileをparseできても、読みやすさやpinout妥当性は保証されない。

## Handoff gate

- SKiDL ERC結果を保存
- KiCad CLI ERCをviolationsで非0終了させる
- BOMをSKiDL側とKiCad側で比較
- schematicをGUIまたはrenderで視覚確認
- symbol/footprint/MPNをdatasheetと照合
- external I/Oとpower boundaryをreview
- unresolved warningとexception rationaleをreport

## Official sources

- [KiCad 9 Command-Line Interface](https://docs.kicad.org/9.0/en/cli/cli.html)
- [KiCad 9 Introduction](https://docs.kicad.org/9.0/en/introduction/introduction.html)
- [KiCad 9 Schematic Editor](https://docs.kicad.org/9.0/en/eeschema/eeschema.html)
- [KiCad 10 Command-Line Interface](https://docs.kicad.org/10.0/en/cli/cli.html)
- [SKiDL KiCad schematic generation](https://devbisme.github.io/skidl/#kicad-schematics)
