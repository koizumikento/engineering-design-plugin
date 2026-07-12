# 統合設計仕様書

## 文書管理

- **プロジェクト名**: [name]
- **版**: 0.1
- **作成日**: YYYY-MM-DD
- **成熟度**: Concept | Prototype | Production handoff
- **ステータス**: Draft | Review | Approved
- **owner/reviewer**:

## Scope and sources

- 製品・用途:
- 対象外:
- PCB source/revision:
- enclosure source/revision:
- component/hardware drawings and revisions:

## Assembly coordinate frame

- 単位: mm
- assembly origin:
- +X / +Y / +Z:
- PCB frame and transform to assembly:
- enclosure datums:

## System requirements

| ID | 要求 | 条件・範囲 | 根拠/出典 | 検証 | 合格基準 |
|---|---|---|---|---|---|
| SYS-FUNC-001 | | | | | |

## 基板-筐体インターフェース

### 基板仕様

| 項目 | 値 | tolerance/limit | frame/datum | source/revision |
|---|---|---|---|---|
| 基板サイズ | W × D mm | | PCB frame | |
| 基板厚 | mm | | PCB frame | |
| 取付穴位置 | (x1, y1), (x2, y2), ... | | PCB frame | |
| 最大部品高 | mm | | PCB top seating plane | |
| 下面最大部品高 | mm | | PCB bottom plane | |

### 筐体仕様

| 項目 | 値 | tolerance/limit | frame/datum | source/revision |
|---|---|---|---|---|
| 内寸 | W × D × H mm | | assembly frame | |
| ボス位置 | (x1, y1), (x2, y2), ... | | assembly frame | |
| ボス高さ | mm | | enclosure bottom datum | |

### Acceptance thresholds

| 項目 | 値 | source/rationale |
|---|---:|---|
| 基板外周最小クリアランス | mm | |
| 上面最小クリアランス | mm | |
| 下面最小クリアランス | mm | |
| 取付位置許容差 | mm | |

### Interface control table

| ID | interface | owner A | owner B | nominal | tolerance | required margin | verification |
|---|---|---|---|---|---|---|---|
| IF-MNT-001 | PCB hole to boss | EE | ME | | | | CAD + inspection |

### Connectors, controls, and openings

| ID | item/MPN | PCB datum position | opening datum/size | plug/tool/cable envelope | tolerance | source/revision |
|---|---|---|---|---|---|---|
| IF-CON-001 | | | | | | |

### Component and keep-out envelopes

| ID | item | side | bounding/envelope geometry | position/frame | tolerance | source/revision |
|---|---|---|---|---|---|---|
| IF-ENV-001 | highest component | top | | | | |

## Thermal, EMC/ESD, ingress, and environment

| ID | requirement/interface | conditions | acceptance | method | evidence |
|---|---|---|---|---|---|
| SYS-THERM-001 | | | | Analysis/Test | |
| SYS-EMC-001 | | | | Inspection/Test | |
| SYS-ING-001 | | | | Test | |

## Assembly and service

- assembly order:
- fasteners/inserts and source:
- tool/finger access:
- cable routing and bend/service envelope:
- rework/maintenance:

## Deliverables

- [ ] integrated specification and interface table
- [ ] mechanical CadQuery/STEP and validation report
- [ ] SKiDL/KiCad/BOM/ERC artifacts
- [ ] text screening report
- [ ] 3D interference/minimum-gap evidence
- [ ] required thermal/EMC/ingress/test evidence

## Assumptions, TBDs, and TBRs

| ID | type | item | impact | owner | resolution | milestone |
|---|---|---|---|---|---|---|
| TBR-001 | TBR | | | | | |

## Verification matrix

| Requirement/Interface ID | method | setup/model | acceptance | evidence | result |
|---|---|---|---|---|---|
| IF-MNT-001 | Analysis/Inspection | | | | Not run |

## Approval

- [ ] Baseline approved by [name/role] on [date]
- Approved exceptions/unresolved items:
