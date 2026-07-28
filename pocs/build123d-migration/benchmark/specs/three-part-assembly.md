# Three-part separated assembly

- Case ID: `three-part-assembly`
- Units: mm
- Datum: origin at the centre of the base plate bottom face.
- Output: exactly three separate valid closed solids. Do not fuse them and do
  not add fasteners.

## Geometry

- R1: Define assembly datum `A0` as the world origin with identity rotation.
  Define each component in its own local datum with +Z normal to its bottom
  face, then apply the exact transforms below. No component may be positioned
  by contact inference.
- R2: `base_plate`, local datum `B0`: 100 X × 60 Y × 6 Z, local bbox
  `[-50,-30,0]` to
  `[50,30,6]`. Cut four Ø6 Z-through holes at `(±40,±20)`.
  Transform B0 to A0 by translation `(0,0,0)` and rotation `(0°,0°,0°)`.
- R3: `spacer_ring`, local datum `S0`: coaxial annulus, Ø40 outside and Ø20
  inside, local Z = 0..10. Transform S0 to A0 by translation `(0,0,16)` and
  rotation `(0°,0°,0°)`, giving world Z = 16..26.
- R4: `top_plate`, local datum `T0`: 60 X × 40 Y × 5 Z, local bbox
  `[-30,-20,0]` to `[30,20,5]`. Cut one concentric Ø12 Z-through hole.
  Transform T0 to A0 by translation `(0,0,36)` and rotation `(0°,0°,0°)`,
  giving world Z = 36..41.
- R5: Keep the 10-mm clear Z gaps between components and keep all edges sharp.

## Acceptance oracle

- Overall bbox: `[-50,-30,0]` to `[50,30,41]`.
- Solid count: 3.
- Volumes: base 35320.92..35321.92 mm³; spacer
  9424.28..9425.28 mm³; top 11434.01..11435.01 mm³; total
  56179.71..56181.71 mm³.
- Cylinders: base has four internal radius-3 +Z holes over Z = 0..6;
  spacer has external radius 20 and internal radius 10 over Z = 16..26;
  top has one internal radius-6 +Z hole over Z = 36..41.
- Material probes: `(0,0,3)`, `(15,0,21)`, `(20,0,38)`.
- Void probes: `(40,20,3)`, `(0,0,21)`, `(0,0,38)`, `(0,0,11)`,
  `(0,0,31)`.
- Transform checks: B0 `(0,0,0)`, S0 `(0,0,16)`, T0 `(0,0,36)`, all with
  identity rotation and coaxial world +Z axes.
