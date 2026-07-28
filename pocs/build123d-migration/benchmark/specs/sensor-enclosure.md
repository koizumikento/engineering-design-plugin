# Two-part sensor enclosure

- Case ID: `sensor-enclosure`
- Units: mm
- Datum: origin at the centre of the body bottom face.
- Output: exactly two separate valid closed solids: body and lid.

## Geometry

- R1: Body outside: 70 X × 50 Y × 30 Z, bbox `[-35,-25,0]` to
  `[35,25,30]`.
- R2: Form an open-top body cavity with bbox `[-31,-21,4]` to
  `[31,21,30]`, leaving 4-mm walls and floor.
- R3: Cut one Ø10 side port along +X, centred at Y = 0, Z = 15, through the
  left wall over X = -35..-31. It opens into the cavity.
- R4: Cut one Z-through obround slot through the body floor over Z = 0..4.
  The slot is centred at `(0,10)`, aligned with X, 20 mm overall length and
  6 mm width (14-mm straight segment plus two radius-3 semicircular ends).
- R5: Create a separate 70 X × 50 Y × 4 Z lid with bbox
  `[-35,-25,34]` to `[35,25,38]`; the 4-mm Z gap is intentional.
- R6: At lid XY positions `(±25,±15)`, cut four coaxial stepped holes:
  Ø4 through Z = 34..38 and Ø8 counterbores from the top over Z = 36..38.
- R7: Keep all edges sharp and add no other features.

## Acceptance oracle

- Overall bbox: `[-35,-25,0]` to `[35,25,38]`.
- Solid count: 2.
- Body bbox/volume: `[-35,-25,0]` to `[35,25,30]`,
  36532.24..36533.24 mm³.
- Lid bbox/volume: `[-35,-25,34]` to `[35,25,38]`,
  13496.85..13497.85 mm³.
- Total volume: 50029.09..50031.09 mm³.
- Cylinders: body internal radius-5 +X port over X = -35..-31; slot end
  cylinders radius 3 over Z = 0..4 at X = ±7, Y = 10; lid has four internal
  radius-2 +Z segments over Z = 34..36 and four internal radius-4 +Z
  counterbores over Z = 36..38.
- Material probes: body `(0,0,2)`, `(33,10,15)`; lid `(0,0,36)`,
  `(28,15,35)`.
- Void probes: body `(0,0,15)`, `(-33,0,15)`, `(0,10,2)`,
  `(7,10,2)`; lid `(25,15,35)`, `(25,15,37)`; assembly gap `(0,0,32)`.
