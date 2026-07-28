# Two-arm clevis

- Case ID: `clevis`
- Units: mm
- Datum: origin at the centre of the base bottom face; the arm gap opens in
  +Z.
- Output: one fused valid closed solid.

## Geometry

- R1: Base: 50 X × 30 Y × 10 Z, bbox `[-25,-15,0]` to `[25,15,10]`.
- R2: Left arm: bbox `[-25,-15,10]` to `[-15,15,50]`.
- R3: Right arm: bbox `[15,-15,10]` to `[25,15,50]`.
- R4: Fuse both arms to the base. The clear gap between arms is X = -15..15
  above Z = 10.
- R5: Cut one Ø8 Y-through hole in each arm, centred at X/Z = `(-20,38)` and
  `(20,38)`, spanning Y = -15..15. Each arm must retain material on both
  X sides of its hole so the upper arm remains connected.
- R6: Keep all edges sharp and add no other features.

## Acceptance oracle

- Overall bbox: `[-25,-15,0]` to `[25,15,50]`.
- Solid count: 1.
- Volume: 35983.57..35984.57 mm³.
- Cylinders: two internal radius-4 +Y features over Y = -15..15 at the
  centres above.
- Material probes: `(0,0,5)`, `(-20,0,20)`, `(20,0,20)`,
  `(-15.5,0,38)`, `(15.5,0,38)`.
- Void probes: `(0,0,30)`, `(-20,0,38)`, `(26,0,5)`.
