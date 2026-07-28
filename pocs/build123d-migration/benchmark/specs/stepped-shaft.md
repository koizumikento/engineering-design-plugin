# Three-diameter hollow stepped shaft

- Case ID: `stepped-shaft`
- Units: mm
- Datum: origin at the centre of the largest-diameter bottom face; shaft axis
  is +Z.
- Output: one fused valid closed solid.

## Geometry

- R1: Lower step: Ø36 over Z = 0..12.
- R2: Middle step: Ø24 over Z = 12..42.
- R3: Upper step: Ø16 over Z = 42..62.
- R4: Fuse all three coaxial steps and cut one concentric Ø6 bore through
  Z = 0..62.
- R5: Cut a longitudinal rectangular keyway into the +Y side of the middle
  step over Z = 16..38. The cutter spans X = -3..3 and Y = 9..20, so the
  finished keyway is 6 mm wide with a planar floor at Y = 9 and is open
  radially outward.
- R6: Apply a 1 × 1 mm 45° chamfer to the upper step outer top edge only.
  Its remaining radius-8 cylindrical surface ends at Z = 61 and its top
  planar face ends at radius 7.
- R7: Keep every other edge sharp and add no other features.

## Acceptance oracle

- Overall bbox: `[-18,-18,0]` to `[18,18,62]`.
- Solid count: 1.
- Volume: 27650.50..27651.50 mm³.
- Cylinders: external radius 18 over Z = 0..12, external radius 12 over
  Z = 12..42 except where interrupted by the keyway, external radius 8 over
  Z = 42..61, and an internal radius-3
  bore over Z = 0..62; all axes are +Z through `(0,0,0)`.
- Keyway: planar floor X = -3..3, Y = 9 at Z = 16..38, open toward +Y.
- Chamfer: external 45° conical face from radius 8/Z61 to radius 7/Z62.
- Material probes: `(10,0,6)`, `(10,0,30)`, `(6,0,50)`, `(0,8,30)`,
  `(7,0,61.5)`.
- Void probes: `(0,0,6)`, `(0,10,30)`, `(15,0,30)`, `(9,0,50)`,
  `(7.7,0,61.5)`, `(0,0,63)`.
