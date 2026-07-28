# Six-bolt circular flange

- Case ID: `flange`
- Units: mm
- Datum: origin at the centre of the bottom face; flange axis is +Z.
- Output: one valid closed solid.

## Geometry

- R1: Create an Ø80 × 12-thick circular flange spanning Z = 0..12.
- R2: Cut a concentric Ø30 through-bore.
- R3: Cut six Ø8 through-holes on a Ø60 pitch circle at polar angles
  0°, 60°, 120°, 180°, 240°, and 300°, where 0° is +X.
- R4: Apply a 2 × 2 mm 45° chamfer to the outer top edge only. The remaining
  Ø80 cylindrical surface spans Z = 0..10 and the top planar annulus starts
  at radius 38.
- R5: Apply a 1 × 1 mm 45° chamfer to the central bore bottom edge only. The
  Ø30 cylindrical bore starts at Z = 1.
- R6: Keep every other edge sharp and add no other features.

## Acceptance oracle

- Overall bbox: `[-40,-40,0]` to `[40,40,12]`.
- Solid count: 1.
- Volume: 47674.22..47675.22 mm³.
- Cylinders: one external radius-40 +Z feature over Z = 0..10, one internal
  radius-15 +Z
  bore, and six internal radius-4 +Z holes at the pitch-circle positions; all
  holes span Z = 0..12 and the bore cylindrical span is Z = 1..12.
- Chamfers: external 45° conical face from radius 40/Z10 to radius 38/Z12;
  internal 45° conical face from radius 16/Z0 to radius 15/Z1.
- Material probes: `(35,0,6)`, `(0,22,6)`, `(38,0,11.5)`.
- Void probes: `(0,0,6)`, `(30,0,6)`, `(39.5,0,11.5)`, `(41,0,6)`.
