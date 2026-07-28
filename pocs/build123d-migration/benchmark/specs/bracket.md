# Right-angle bracket

- Case ID: `bracket`
- Units: mm
- Datum: origin at the centre of the foot bottom face; +Y points toward the
  vertical plate.
- Output: one fused valid closed solid.

## Geometry

- R1: Foot: 60 X × 40 Y × 8 Z, bbox `[-30,-20,0]` to `[30,20,8]`.
- R2: Vertical plate: 60 X × 8 Y × 40 Z, bbox `[-30,12,8]` to
  `[30,20,48]`, fused to the foot along its bottom face.
- R3: Cut two Ø6 Z-through holes in the foot at `(-20,-5)` and `(20,-5)`,
  spanning Z = 0..8.
- R4: Cut two Ø8 Y-through holes in the vertical plate at X/Z =
  `(-18,28)` and `(18,28)`, spanning Y = 12..20.
- R5: Add a radius-4 internal fillet along the full inside foot/plate corner
  at Y = 12, Z = 8. Its tangent lines are Y = 8 on the foot and Z = 12 on
  the plate. The rib in R6 is allowed to obscure the middle of this face.
- R6: Add one centred triangular rib spanning X = -3..3. In the YZ plane its
  vertices are `(0,8)`, `(12,8)`, and `(12,20)`. Fuse it to the foot and
  plate.
- R7: Keep every other edge sharp and add no other features.

## Acceptance oracle

- Overall bbox: `[-30,-20,0]` to `[30,20,48]`.
- Solid count: 1.
- Volume: 37760.28..37761.28 mm³.
- Cylinders: two internal radius-3 +Z features over Z = 0..8, and two
  internal radius-4 +Y features over Y = 12..20, at the centres above.
- Fillet: concave radius-4 cylindrical face with +X axis, excluding the
  rib-obscured interval X = -3..3.
- Rib: triangular prism with the R6 YZ section over X = -3..3.
- Material probes: `(0,0,4)`, `(0,16,28)`, `(0,10,9)`, `(0,6,10)`.
- Void probes: `(0,0,28)`, `(-20,-5,4)`, `(-18,16,28)`, `(10,6,10)`.
