# KiCad 9 schematic workflow

## Source ownership

- SKiDL Python: logical connectivity, hierarchy, parameterization.
- generated `.kicad_sch` / `.kicad_pro`: human review and PCB handoff.
- `.kicad_pcb`: layout/fabrication source when PCB work begins; this skill does not generate or certify layout.

Generated KiCad filesを手編集する場合は、SKiDLへ戻す方法またはKiCadを以後の正本に切り替える決定を記録する。二重編集を放置しない。

## Generation paths

### Native SKiDL

SKiDL 2.2は `generate_schematic()` でKiCad schematicを生成できる。一般回路では第一候補とし、生成後の可読性とKiCad ERCを確認する。

### Repository exporter

`skills/circuit-design/scripts/kicad_sch_export.py` はリポジトリで確認済みのtopology向け互換pathである。未対応回路を「出力済み」とみなさない。必要ならnative SKiDLを試し、それでも不足する場合はexporter変更と回帰例を同時に追加する。

```bash
uv run python skills/circuit-design/scripts/kicad_sch_export.py input.py -o outputs/
```

## Independent KiCad checks

KiCad 9 CLIはschematic ERCとBOM exportを直接提供する。

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
- [SKiDL KiCad schematic generation](https://devbisme.github.io/skidl/#kicad-schematics)
