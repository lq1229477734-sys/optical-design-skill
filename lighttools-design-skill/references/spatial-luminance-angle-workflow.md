# Spatial Luminance Angle Workflow

Use this workflow when a user edits ECT transmittance or a component's ray-trace state in the LightTools GUI and asks to rerun a spatial luminance meter at multiple latitude angles.

## Preserve the Active Edit

The user's current GUI changes may not yet exist on disk. Before opening any model or issuing `New`, run `scripts/snapshot_active_lighttools_model.ps1` to save the active model to a new versioned `.lts`. Then inspect the snapshot text and record:

- ECT optical-property `setTransmittance`.
- The target component's `setIsRayTraceable` value, such as `colli1_lc_2`.
- Spatial meter `setLat`, `setLong`, position, and orientation.

Do not infer these values from an older file or filename.

## Spatial Latitude Geometry

For the validated normal-view model with `Long=90`, the meter orbits the measured plane at `center_z=3 mm` with radius `600 mm`. Positive latitude moves toward negative global X:

```text
x = -R sin(L)
y = 0
z = center_z + R cos(L)
```

Use this orientation matrix:

```text
[-cos(L), 0,  sin(L)]
[       0, 1,       0]
[-sin(L), 0, -cos(L)]
```

Therefore:

- `L=0`: position `(0, 0, 603)`.
- `L=45`: position `(-424.2640687, 0, 427.2640687)`.

The positive-X solution is the opposite viewing direction and can produce a completely different luminance result. Do not rotate around the global origin with radius 603; the validated pivot is `z=3` with a 600 mm observation distance.

Use `scripts/set_spatial_lum_meter_angle.py` to patch the first spatial luminance meter block. Validate every patched file by opening and saving it through LightTools before simulation.

## Run and Export

For each angle:

1. Open the validated angle-specific model in a clean LightTools state.
2. Save a proof copy in the run directory.
3. Run `BeginAllSimulations` and require status 0.
4. Export `BLUReceiver` `Spatial_Luminance_Mesh` with native `GetMeshData`.
5. Record mesh dimensions, simulation status, source snapshot, ECT value, and component ray-trace state.

A known model exports a 600x600 spatial luminance mesh and a 21x21 illuminance mesh.

## Post-Processing

- Keep raw TXT output immutable.
- Compare L=0 and L=45 with one shared color scale.
- Report min, max, mean, median, upper-left ROI statistics, and nonzero fraction.
- Prefer a top-fraction mean or a high percentile over a single maximum for colorbar limits.
- Inspect edge rows separately. Bright top or bottom lines can be boundary artifacts and should not define the interior color scale.

## Diagnostic Lesson

Changing `colli1_lc_2` from ray traceable to non-ray-traceable can remove the angular privacy effect. In one validated run with ECT transmittance 0.65:

- Ray tracing on: L=0 mean 15.93, L=45 mean 6.24.
- Ray tracing off: L=0 mean 31.83, L=45 mean 30.81.

Treat these numbers as a regression example, not universal expected values. The reusable conclusion is that the ray-trace state must be captured and audited for every run.
