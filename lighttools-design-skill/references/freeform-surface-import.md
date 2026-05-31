# Freeform Surface Import

Use this reference when importing optimized freeform surface CSV data into a LightTools `.lts` model.

## Proven Representation

Use one LightTools `FreeformSolid` with a `Loft` primitive and two `FreeformSurface` `restorePoints` blocks:

- First block: lower/front/entrance surface.
- Second block: upper/rear/exit surface.
- Units: millimeters.
- Proven grid sizes: `81 x 81` for single-cell lens and `121 x 121` for a decimated 6x6 tiled preview.

Start from a known LightTools template such as:

```text
D:\360Safe\lighttools\ExamplesLibrary\ProgramFeatures\Geometry\Freeform\Freeform_Solid_Cartesian_Oval.1.lts
```

Replace the first two `restorePoints` blocks instead of creating a freeform solid from scratch.

## CSV Requirements

Expect columns:

```text
x_mm,y_mm,z_mm
```

Validate point count before writing `.lts`:

- `81 x 81 = 6561` points for each surface.
- Preserve row order from the generated surface data. In the successful 10 mm x 10 mm model, row order was y-major and x-min to x-max.

Copy source CSV/OBJ files into the model folder so the prescription is traceable.

## restorePoints Format

The successful point block starts with metadata, all xyz triples, then mapper metadata:

```text
restorePoints:
ORAStartData;
0 0 NX NY 0 0 POINT_COUNT 0 0 0
x1 y1 z1 x2 y2 z2 ...
0 1 4 CartesianMapper 1 0 0 0 0
ORAEndData;
ORAReadForeignData;
```

Write values in compact decimal form and keep the exact LightTools block markers.

## Validation Loop

1. Generate a raw `.lts`.
2. Ask LightTools to open the raw file with dialogs disabled.
3. Query `LENS_MANAGER[1]` solids and first solid name.
4. SaveAs a validated `.lts`.
5. Append open/save status and object counts to an audit.

This catches malformed freeform blocks early.

## 6x6 Tiled Plate Strategy

For a 6x6 array from 10 mm x 10 mm cells:

- Cell pitch: `10 mm`.
- LED centers: `-25, -15, -5, 5, 15, 25 mm`.
- Full high-precision plate from `81 x 81` cells would become `481 x 481` points and may be too slow or unstable.
- A verified preview decimated each cell to `21 x 21`, producing a continuous `121 x 121` plate.
- Neighboring cells should share boundary vertices; avoid separate solids when the operation becomes unstable.

Document the sampling compromise in the audit.

## Common Freeform Audit Fields

Record:

- Source lower and upper CSV paths.
- Template path.
- Raw and validated model paths.
- Grid size.
- Material and refractive index.
- Surface names.
- Bounds for x, y, and z on both surfaces.
- Whether the LightTools open/save validation succeeded.
