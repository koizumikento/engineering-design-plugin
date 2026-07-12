# 機械設計仕様書

## 文書管理

- **プロジェクト名**: [name]
- **版**: 0.1
- **作成日**: YYYY-MM-DD
- **成熟度**: Concept | Prototype | Production handoff
- **ステータス**: Draft | Review | Approved
- **owner/reviewer**:

## Scope

- 対象:
- 用途・使用者:
- 対象外:
- 上位資料・図面・CADとrevision:

## 座標・単位・データム

- 単位: mm
- 原点:
- +X / +Y / +Z:
- primary / secondary / tertiary datum:
- mating/seating planes:

## Requirements

| ID | 要求 | 条件・範囲 | 根拠/出典 | 検証 | 合格基準 |
|---|---|---|---|---|---|
| MECH-FUNC-001 | [対象]は[機能]を満たすこと | [条件] | [source] | Inspection/Test | [criterion] |

## 寸法・公差

| ID | feature | nominal | tolerance/limit | datum/frame | source | verification |
|---|---|---:|---:|---|---|---|
| MECH-DIM-001 | 全長 | mm | mm | | | Inspection |
| MECH-DIM-002 | 全幅 | mm | mm | | | Inspection |
| MECH-DIM-003 | 全高 | mm | mm | | | Inspection |

## 穴・開口・嵌合

| Interface ID | feature | type | size | position/frame | tolerance | mating part/source |
|---|---|---|---|---|---|---|
| IF-MECH-001 | | through/counterbore/countersink/slot | | | | |

## 材料・製造

- 材料と規格/grade:
- 製造方法と装置/工程前提:
- 表面処理・色:
- 一般公差の適用範囲と版:
- 重要面の表面性状:
- 最小feature、draft、support、tool accessなど工程制約:

## Assembly and service envelopes

- 位置決め方法:
- 締結方法とhardware source:
- 組立順序:
- 工具/指/ケーブル/可動範囲:
- 保守・交換:

## Environment, loads, and life

| ID | condition | min/nom/max | duration/cycles | acceptance | verification |
|---|---|---|---|---|---|
| MECH-ENV-001 | temperature | | | | Test |
| MECH-LOAD-001 | load | | | | Analysis/Test |

## Deliverables

- [ ] CadQuery Python
- [ ] STEP
- [ ] STL/3MF（用途とtessellationを記録）
- [ ] DXF/SVG（対象面・単位を記録）
- [ ] 複数視点PNG
- [ ] CAD validation report

## Assumptions, TBDs, and TBRs

| ID | type | item | impact | owner | resolution | milestone |
|---|---|---|---|---|---|---|
| TBR-001 | TBR | | | | | |

## Verification matrix

| Requirement ID | method | setup/model | acceptance | evidence | result |
|---|---|---|---|---|---|
| MECH-FUNC-001 | | | | | Not run |

## Approval

- [ ] Baseline approved by [name/role] on [date]
- Approved exceptions/unresolved items:
