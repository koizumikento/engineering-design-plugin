# Open-top enclosure

- Case ID: `open-enclosure`
- Units: mm
- Datum: origin at the centre of the outside bottom face.
- Output: one valid closed solid; the top is open.

## Geometry

- R1: Start from an outer 80 X × 50 Y × 30 Z box, bbox
  `[-40,-25,0]` to `[40,25,30]`.
- R2: Form an open-top cavity with bbox `[-37,-22,3]` to `[37,22,30]`.
  This leaves 3-mm walls and a 3-mm bottom.
- R3: Add four internal cylindrical standoffs of radius 4 over Z = 3..12,
  centred at `(±28,±13)`, and fuse them to the bottom.
- R4: Cut a blind radius-1.5 hole into each standoff from its top, spanning
  Z = 6..12. Material must remain below each hole over Z = 3..6.
- R5: Keep all edges sharp and add no lid or other features.

## Acceptance oracle

- Overall bbox: `[-40,-25,0]` to `[40,25,30]`.
- Solid count: 1.
- Volume: 33727.41..33728.41 mm³.
- Cylinders: four external radius-4 +Z standoff surfaces over Z = 3..12 and
  four internal radius-1.5 +Z blind-hole surfaces over Z = 6..12, all at
  `(±28,±13)`.
- Material probes: `(0,0,1.5)`, `(38.5,0,15)`, `(0,23.5,15)`,
  `(31,13,9)`, `(28,13,4.5)`.
- Void probes: `(0,0,15)`, `(28,13,9)`, `(0,0,31)`.
