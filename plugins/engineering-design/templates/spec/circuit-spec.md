# 回路設計仕様書

## 文書管理

- **プロジェクト名**: [name]
- **版**: 0.1
- **作成日**: YYYY-MM-DD
- **成熟度**: Concept | Prototype | Production handoff
- **ステータス**: Draft | Review | Approved
- **owner/reviewer**:

## Scope

- 回路の目的:
- 接続するsystem/board:
- 対象外（PCB layout、firmware、認証など）:
- 上位仕様・datasheet・既存設計とrevision:

## Requirements

| ID | 要求 | 条件・範囲 | 根拠/出典 | 検証 | 合格基準 |
|---|---|---|---|---|---|
| CIR-FUNC-001 | [回路]は[機能]を満たすこと | [conditions] | [source] | Analysis/Test | [criterion] |

## Electrical operating conditions

| ID | item | min | nominal | max | unit | conditions/source |
|---|---|---:|---:|---:|---|---|
| CIR-ELEC-001 | input voltage | | | | V | |
| CIR-ELEC-002 | load current | | | | A | |
| CIR-ELEC-003 | ambient temperature | | | | °C | |

## Interfaces

| Interface ID | name | direction | voltage/current/logic | connector/pin | source/load impedance | fault/unpowered behavior |
|---|---|---|---|---|---|---|
| IF-CIR-001 | | input/output/bidirectional | | | | |

## Power tree and grounding

- source and protection:
- rails and current budget:
- sequencing/startup/shutdown:
- ground/chassis/shield domains:
- decoupling requirements and datasheet source:

## Component selection

| Ref/function | manufacturer | MPN | symbol | footprint | model source/revision | status |
|---|---|---|---|---|---|---|
| | | | | | | proposed/approved |

## Worst-case and fault cases

- tolerance/temperature/corner:
- absolute-maximum and derating checks:
- open/short/reverse/unpowered states:
- thermal and SOA:
- protection threat and applicable test/standard:

## Simulation requirements

| Requirement ID | scenario | analysis | model set | measurement | acceptance |
|---|---|---|---|---|---|
| CIR-FUNC-001 | | OP/DC/AC/Transient/Noise | | | |

## Deliverables

- [ ] SKiDL Python
- [ ] BOM with manufacturer/MPN where known
- [ ] SKiDL ERC summary
- [ ] KiCad 9 schematic/project
- [ ] KiCad CLI ERC report
- [ ] design summary
- [ ] netlist（downstream requirementがある場合）
- [ ] simulation CSV/plot/summary（要求がある場合）

## Assumptions, TBDs, and TBRs

| ID | type | item | impact | owner | resolution | milestone |
|---|---|---|---|---|---|---|
| TBR-001 | TBR | | | | | |

## Verification matrix

| Requirement ID | method | setup/model | acceptance | evidence | result |
|---|---|---|---|---|---|
| CIR-FUNC-001 | | | | | Not run |

## Approval

- [ ] Baseline approved by [name/role] on [date]
- Approved exceptions/unresolved items:
