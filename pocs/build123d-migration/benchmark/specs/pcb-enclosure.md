# PCB enclosure with integrated bosses

- Case ID: `pcb-enclosure`
- Units: mm
- Datum: origin at the centre of the outside bottom face.
- Output: one fused valid closed solid; the top is open.

## Geometry

- R1: Start from an outer 100 X × 70 Y × 30 Z box, bbox
  `[-50,-35,0]` to `[50,35,30]`.
- R2: Form an open-top cavity with bbox `[-46,-31,3]` to `[46,31,30]`.
  This leaves 4-mm side walls and a 3-mm bottom.
- R3: Add four internal cylindrical bosses, radius 4, spanning Z = 3..9,
  centred at `(±38,±23)`. Fuse each boss to the bottom.
- R4: Cut a radius-1.5 hole coaxially through each boss and bottom, spanning
  Z = 0..9.
- R5: Keep all edges sharp and add no lid or other features.

## Acceptance oracle

- Overall bbox: `[-50,-35,0]` to `[50,35,30]`.
- Solid count: 1.
- Volume: 56943.40..56944.40 mm³.
- Cylinders: four external radius-4 +Z boss surfaces over Z = 3..9 and four
  internal radius-1.5 +Z features over Z = 0..9, all at `(±38,±23)`.
- Material probes: `(0,0,1.5)`, `(48,0,15)`, `(41,23,6)`.
- Void probes: `(0,0,15)`, `(38,23,6)`, `(0,0,31)`.
