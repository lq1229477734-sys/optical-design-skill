# Spatially colored disk sources and ray display

Use this note when a LightTools task asks for one emitting face to show different ray colors in different spatial regions, especially for `DiskSource` objects and ray preview/path display.

## What actually controls visible ray color

- Do not rely on object `setColor` alone. It changes the source/object display color but does not reliably color traced rays.
- Do not use `RayPathColorNameAt` for source-region color. That API colors ray-path categories/data-set rows, so the 3D view can look like one mesh/path category has one color instead of one source region having one color.
- For ray preview colors that follow source regions, give each region its own `ORASpectralRegionEntityObj` with a discrete wavelength and set the wavelength `setColor` to a named color such as `RED`, `GREEN`, `BLUE`, or `YELLOW`.
- Utilities User Guide RGB Source examples are a useful mental model: multiple source/channel definitions are combined into one visual result. For 3D ray-line color, the practical mechanism is source region -> spectral region -> wavelength color.

## DiskSource region geometry

`DiskSource` supports circular disks, rings, and angular sectors:

- Outer radius comes from `restoreRadius` in the saved `.lts` disk primitive.
- Angular sectors use `restoreStartSweepAngle` and `restoreEndSweepAngle`.
- A ring can be represented by a disk primitive with an inner radius greater than zero. In saved `.lts` text for LightTools 8.6 this can be patched as `restoreInnerRadius: <r>;` immediately after `restoreRadius: <R>;`, then validated by reopening/saving in LightTools.

Examples:

```text
# full disk, radius 2 mm
restoreRadius: 2;

# outer ring, inner radius 2 mm, outer radius 7.5 mm
restoreRadius: 7.5;
restoreInnerRadius: 2;

# quadrant sector, radius 7.5 mm, 90-180 degrees
restoreRadius: 7.5;
restoreStartSweepAngle: 90.;
restoreEndSweepAngle: 180.;
```

## Robust workflow for spatially colored disk sources

1. Attach to the open LightTools session through COM/JumpStart and identify the active model name from `LENS_MANAGER[1] NAME`. If the full file path is not exposed, match the name to recently modified `.lts` files before editing.
2. Save or copy a backup before patching `.lts` text.
3. Represent each desired spatial region as a separate true source region, not as display-only helper geometry.
   - Four equal quadrants: four `DiskSource` objects with 90-degree sweep intervals.
   - Two concentric regions: one center disk plus one outer ring.
4. Assign each active region its own spectral region and wavelength color:

```text
setName: "DiskSource_21_CENTER_RED_630NM";
$ORAWavelengthObj create -> $ORAWavelengthObj_1
{
    setWavelength: 630.;
    setData: 1.;
    setColor: "RED";
} restoreWavln: $ORAWavelengthObj_1;
setDiscreteSpectrum: "Yes";
```

5. Bind each source to the intended spectral region:

```text
setSpectralRegion: $ORASpectralRegionEntityObj_1;
```

6. Set source powers intentionally.
   - If preserving uniform emitted power over an original disk, split total power by area fraction.
   - For a center disk of radius `r` inside original radius `R`: `center_power = total_power * r^2 / R^2`; `outer_power = total_power - center_power`.
7. Disable unused old source pieces instead of deleting them when working in a fragile user model:

```text
setIsRayTraceable: "No";
setLampPower: 0;
```

8. Reopen the patched `.lts` in LightTools, run a practical simulation, switch to preview rays, and save only after LightTools accepts the model:

```text
Open <path>
\V3D BeginAllSimulations
ShowOnlyPreviewRays
Save
```

9. Verify the saved file still contains the intended geometry and spectral settings. For rings, specifically confirm `restoreInnerRadius` survived the LightTools open/save cycle.

## Known pitfalls

- `ShowOnlyRayPathRays` displays collected ray paths. Those paths are sequence/category data, not necessarily source-region color channels.
- `ShowOnlyPreviewRays` is usually the better display mode when the user asks for traced rays to visually inherit wavelength colors.
- Source/object colors such as `setColor: "RED"` on a `DiskSource` are useful for visual identification, but the traced-ray color came from the wavelength color in the spectral region.
- LightTools COM database lists can return zero for `SOURCE`/`DISKSOURCE` in some models even when saved `.lts` text clearly contains `DiskSource` blocks. In those cases, patch text carefully and validate by opening/saving in LightTools.
