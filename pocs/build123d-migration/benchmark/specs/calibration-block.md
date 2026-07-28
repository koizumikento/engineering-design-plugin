# Calibration block

- Case ID: `calibration-block`
- Units: mm
- Datum: origin at the centre of the bottom face; block edges parallel to XYZ.
- Output: one valid closed solid.

## Geometry

- R1: Create a rectangular block 50 X × 40 Y × 20 Z, spanning
  X = -25..25, Y = -20..20, Z = 0..20.
- R2: Apply radius-3 fillets to exactly the four vertical edges over
  Z = 0..20. Keep every horizontal edge sharp.
- R3: Cut four Ø5 Z-through holes at `(±15,±10)`, spanning Z = 0..20.
- R4: Cut a centred 20 X × 12 Y rectangular blind pocket from the top face,
  spanning X = -10..10, Y = -6..6, Z = 16..20.
- R5: Add no other features.

## Acceptance oracle

- Overall bbox: `[-25,-20,0]` to `[25,20,20]`.
- Solid count: 1.
- Volume: 37314.19..37315.19 mm³.
- Cylinders: four internal radius-2.5 +Z holes over Z = 0..20 at
  `(±15,±10)`; four convex radius-3 quarter-cylinder fillet faces over
  Z = 0..20, centred in XY at `(±22,±17)`.
- Rectangular void: `[-10,-6,16]` to `[10,6,20]`, open toward +Z.
- Material probes: `(0,0,10)`, `(24,18,10)`, `(0,0,15)`.
- Void probes: `(15,10,10)`, `(0,0,18)`, `(24.5,19.5,10)`,
  `(26,0,10)`.
