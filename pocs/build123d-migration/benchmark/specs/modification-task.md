# Revision task: move a hole and add a bored boss

- Case ID: `modification-task`
- Units: mm
- Datum: origin at the centre of the plate bottom face.
- Output: the final revised geometry as one fused valid closed solid.

## Starting revision

The starting revision is a 70 X × 40 Y × 8 Z plate spanning
`[-35,-20,0]` to `[35,20,8]`, with four Ø6 Z-through holes at
`(±25,±12)`. It also has a 16 X × 6 Y blind rectangular pocket spanning
X = -8..8, Y = -15..-9, Z = 6..8.

## Required modification

- R1: Preserve the plate dimensions and the holes at `(-25,-12)`,
  `(-25,12)`, and `(25,-12)`.
- R2: Preserve the non-target blind pocket exactly, including its location and
  depth.
- R3: Remove the original hole at `(25,12)`. The final model must contain
  material at that old centre.
- R4: Add a Ø10 Z-through hole centred at `(15,8)`, spanning Z = 0..8.
- R5: Add and fuse a centred Ø16 boss spanning Z = 8..13.
- R6: Cut a concentric Ø6 bore through the plate and boss over Z = 0..13.
- R7: Keep all edges sharp and add no other features.

## Acceptance oracle

- Overall bbox: `[-35,-20,0]` to `[35,20,13]`.
- Solid count: 1.
- Volume: 21538.34..21539.34 mm³.
- Cylinders: three internal radius-3 +Z holes over Z = 0..8 at the preserved
  centres; one internal radius-5 +Z hole over Z = 0..8 at `(15,8)`; one
  external radius-8 +Z boss over Z = 8..13; one internal radius-3 +Z bore
  over Z = 0..13 at `(0,0)`.
- Preserved rectangular void: `[-8,-15,6]` to `[8,-9,8]`, open toward +Z.
- Material probes: `(30,0,4)`, `(6,0,10)`, `(25,12,4)`, `(0,-12,4)`.
- Void probes: `(-25,-12,4)`, `(15,8,4)`, `(0,0,4)`, `(0,0,10)`,
  `(0,-12,7)`, `(0,0,14)`.
